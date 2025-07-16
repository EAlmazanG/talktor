FROM python:3.12.11-slim

WORKDIR /app

# Instalar dependencias necesarias para compilar PyAudio
RUN apt-get update && apt-get install -y \
    gcc \
    libasound2-dev \
    portaudio19-dev \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt from the current directory
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Asegurarse de que uvicorn esté instalado
RUN pip install --no-cache-dir uvicorn fastapi

# Copy the backend directory
COPY . .

# Create a basic main.py file if it doesn't exist
RUN echo 'from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get("/")\ndef read_root():\n    return {"message": "Welcome to Talktor API"}' > main.py

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]