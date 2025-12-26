// =====================
// GLOBAL STATE
// =====================
let selectedBook = null;
let selectedLanguage = "English";
let isTyping = false;

// =====================
// API CONFIG (MATCHES BACKEND)
// =====================
const API_CONFIG = {
    endpoint: "https://8bce8d3a8a60.ngrok-free.app/chat",
    timeout: 30000,
    retries: 2
};

// =====================
// BOOK + LANGUAGE MAP (BACKEND EXPECTS THESE)
// =====================
const BOOK_MAP = {
    "Bhagavad Gita": "gita",
    "Quran": "quran",
    "Bible": "bible"
};

const LANGUAGE_MAP = {
    "English": "en",
    "Hindi": "hindi",
    "Marathi": "marathi"
};

// =====================
// DOM READY
// =====================
document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("sacredTablet")) {
        initChat();
    } else {
        initSelection();
    }
});

// =====================
// SELECTION PAGE
// =====================
function initSelection() {
    const bookCards = document.querySelectorAll(".sacred-book-card");
    const continueBtn = document.getElementById("continueBtn");
    const languageSelect = document.getElementById("languageSelect");

    selectedLanguage = localStorage.getItem("selectedLanguage") || "English";
    languageSelect.value = selectedLanguage;

    languageSelect.addEventListener("change", e => {
        selectedLanguage = e.target.value;
        localStorage.setItem("selectedLanguage", selectedLanguage);
    });

    bookCards.forEach(card => {
        card.addEventListener("click", () => {
            bookCards.forEach(c => c.classList.remove("selected"));
            card.classList.add("selected");
            selectedBook = card.dataset.book;
            continueBtn.disabled = false;
        });
    });

    continueBtn.addEventListener("click", () => {
        localStorage.setItem("selectedBook", selectedBook);
        localStorage.setItem("selectedLanguage", selectedLanguage);
        window.location.href = "chat.html";
    });

    continueBtn.disabled = true;
}

// =====================
// CHAT PAGE
// =====================
function initChat() {
    const book = localStorage.getItem("selectedBook");
    const language = localStorage.getItem("selectedLanguage") || "English";

    if (!book) {
        window.location.href = "index.html";
        return;
    }

    const input = document.getElementById("soulInput");
    const sendBtn = document.getElementById("transcendBtn");
    const stream = document.getElementById("messageStream");

    sendBtn.addEventListener("click", () => sendMessage(book, language, input, stream));
    input.addEventListener("keydown", e => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage(book, language, input, stream);
        }
    });
}

// =====================
// SEND MESSAGE
// =====================
async function sendMessage(book, language, input, stream) {
    const text = input.value.trim();
    if (!text) return;

    addMessage(text, "seeker", stream);
    input.value = "";

    const thinking = addMessage("Contemplating divine wisdom…", "divine", stream, true);

    const payload = {
        scripture: BOOK_MAP[book],
        message: text,
        language: LANGUAGE_MAP[language] || "en"
    };

    try {
        const res = await callAPI(payload);
        thinking.remove();
        addDivineResponse(res, stream);
    } catch (err) {
        thinking.remove();
        addMessage("The divine connection is unavailable right now.", "divine", stream);
        console.error(err);
    }
}

// =====================
// API CALL
// =====================
async function callAPI(payload) {
    let lastError;

    for (let i = 0; i <= API_CONFIG.retries; i++) {
        try {
            const controller = new AbortController();
            const timer = setTimeout(() => controller.abort(), API_CONFIG.timeout);

            const res = await fetch(API_CONFIG.endpoint, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
                signal: controller.signal
            });

            clearTimeout(timer);

            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();

        } catch (e) {
            lastError = e;
            if (i === API_CONFIG.retries) throw e;
            await new Promise(r => setTimeout(r, 1000 * (i + 1)));
        }
    }
    throw lastError;
}

// =====================
// UI HELPERS
// =====================
function addDivineResponse(data, stream) {
    const div = document.createElement("div");
    div.className = "message divine-message";

    const p = document.createElement("p");
    p.textContent = data.reply;
    div.appendChild(p);

    if (data.sources && data.sources.length) {
        const src = document.createElement("div");
        src.className = "sources";
        src.textContent = "Sources: " + data.sources.join(", ");
        div.appendChild(src);
    }

    stream.appendChild(div);
    stream.scrollTop = stream.scrollHeight;
}

function addMessage(text, sender, stream, loading = false) {
    const div = document.createElement("div");
    div.className = `message ${sender}-message`;
    if (loading) div.classList.add("loading");

    const p = document.createElement("p");
    p.textContent = text;
    div.appendChild(p);

    stream.appendChild(div);
    stream.scrollTop = stream.scrollHeight;
    return div;
}