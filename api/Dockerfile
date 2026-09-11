FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PyMuPDF and Tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create storage directory
RUN mkdir -p /data/storage

CMD ["uvicorn", "app.main:app", "--host", "0.0.0", "--port", "8000"]
