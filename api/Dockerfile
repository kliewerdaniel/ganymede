FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PyMuPDF, Tesseract, and ClamAV
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1 \
    clamav \
    clamav-daemon \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create storage directory
RUN mkdir -p /data/storage

# Start API (ClamAV available but not required for startup)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
