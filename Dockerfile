FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and config
COPY backend/ ./backend/
COPY antigravity.json .

# Expose FastAPI port
EXPOSE 8000

# Run uvicorn server
CMD ["uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8000"]
