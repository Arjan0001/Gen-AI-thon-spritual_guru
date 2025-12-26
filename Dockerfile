FROM python:3.11-slim

WORKDIR /app

# System deps (required for faiss-cpu)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy ONLY required application files
COPY api.py /app/api.py
COPY indexes /app/indexes

# Expose port for Cloud Run
ENV PORT=8080

# Start FastAPI
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port $PORT"]

