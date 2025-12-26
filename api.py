import logging
from typing import Dict, List, Optional
from pathlib import Path
import os

import faiss
import toml
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from langdetect import detect

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# =====================
# SETUP
# =====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

# =====================
# CONFIG
# =====================
class Config:
    INDEX_PATHS = {
        "quran": ("indexes/quran.index", "indexes/quran_id_map.toml"),
        "gita": ("indexes/gita.index", "indexes/gita_id_map.toml"),
        "bible": ("indexes/bible.index", "indexes/bible_id_map.toml"),
    }
    TOP_K = 3  # per scripture
    EMBEDDING_MODEL = "all-mpnet-base-v2"
    GEMINI_MODEL = "models/gemini-flash-latest"
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

config = Config()

# =====================
# APP STATE
# =====================
class AppState:
    embed_model: Optional[SentenceTransformer] = None
    gemini_model: Optional[genai.GenerativeModel] = None
    indexes: Dict[str, faiss.Index] = {}
    id_maps: Dict[str, List[Dict]] = {}

app_state = AppState()

# =====================
# STARTUP
# =====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting application...")

    if not config.GEMINI_API_KEY:
        raise RuntimeError("Missing GEMINI_API_KEY")

    app_state.embed_model = SentenceTransformer(config.EMBEDDING_MODEL)
    genai.configure(api_key=config.GEMINI_API_KEY)
    app_state.gemini_model = genai.GenerativeModel(config.GEMINI_MODEL)

    for book, (index_path, map_path) in config.INDEX_PATHS.items():
        if Path(index_path).exists() and Path(map_path).exists():
            app_state.indexes[book] = faiss.read_index(index_path)
            with open(map_path, "r", encoding="utf-8") as f:
                data = toml.load(f)
                app_state.id_maps[book] = data.get("verses", [])
            logger.info(f"✅ Loaded {book}")

    logger.info("✅ Ready")
    yield

# =====================
# FASTAPI
# =====================
app = FastAPI(
    title="Multilingual Multi-Scripture Chat API",
    version="2.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================
# MODELS
# =====================
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=3, max_length=500)

class ChatResponse(BaseModel):
    reply: str
    sources: Dict[str, List[str]]

# =====================
# HELPERS
# =====================
def detect_language(text: str) -> str:
    try:
        return detect(text)
    except:
        return "en"

def normalize_question(text: str) -> str:
    text = text.strip()
    if not text.endswith("?"):
        return f"Is this claim supported by the provided texts: {text}?"
    return text

def translate_to_english(text: str) -> str:
    prompt = f"""Translate the following text to English.
Return ONLY the translation.

TEXT:
{text}
"""
    return app_state.gemini_model.generate_content(prompt).text.strip()

def translate_from_english(text: str, target_lang: str) -> str:
    if target_lang == "en":
        return text

    prompt = f"""Translate the following text to {target_lang}.
Keep it natural and simple.
Return ONLY the translation.

TEXT:
{text}
"""
    return app_state.gemini_model.generate_content(prompt).text.strip()

def search_all_scriptures(query: str) -> Dict[str, List[Dict]]:
    vec = app_state.embed_model.encode([query], normalize_embeddings=True)
    results = {}

    for book, index in app_state.indexes.items():
        verses = app_state.id_maps[book]
        _, idxs = index.search(vec, config.TOP_K)
        found = []
        for i in idxs[0]:
            if i < len(verses):
                found.append(verses[i])
        results[book] = found

    return results

# =====================
# PROMPT (FINAL)
# =====================
def create_prompt(context: str, question: str) -> str:
    return f"""You are a calm, friendly guide talking to someone in everyday life.

STRICT RULES:
- Use ONLY the text provided below
- Do NOT add ideas or explanations not found in the text
- Do NOT guess or assume
- Do NOT mention verse numbers or technical references
- If the text does not clearly answer the question, say that simply
- ALWAYS reply in English

STYLE:
- Natural, everyday language
- Short and clear
- 2–3 sentences maximum
- No formal or academic tone

TEXT:
{context}

QUESTION:
{question}

Reply naturally, based only on the text above.
"""

# =====================
# ENDPOINTS
# =====================
@app.get("/")
async def root():
    return {"message": "💬 Multi-Scripture Chat API"}

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        user_lang = detect_language(req.message)
        question = normalize_question(req.message)

        if user_lang != "en":
            question = translate_to_english(question)

        all_verses = search_all_scriptures(question)

        total = sum(len(v) for v in all_verses.values())
        if total == 0:
            msg = "The provided texts do not clearly answer this question."
            if user_lang != "en":
                msg = translate_from_english(msg, user_lang)
            return ChatResponse(reply=msg, sources={})

        context_lines = []
        for book, verses in all_verses.items():
            if verses:
                context_lines.append(f"\n{book.upper()}:")
                for v in verses:
                    context_lines.append(v["content"])

        context = "\n".join(context_lines)

        prompt = create_prompt(context, question)
        answer_en = app_state.gemini_model.generate_content(prompt).text.strip()

        final_answer = (
            translate_from_english(answer_en, user_lang)
            if user_lang != "en"
            else answer_en
        )

        sources = {
            book: [v["id"] for v in verses]
            for book, verses in all_verses.items()
            if verses
        }

        return ChatResponse(reply=final_answer, sources=sources)

    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
