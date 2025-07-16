FROM python:3.12.11-slim

WORKDIR /app

# Copy requirements.txt from the current directory
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend directory
COPY . .

# Create a basic main.py file if it doesn't exist
RUN echo 'from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get("/")\ndef read_root():\n    return {"message": "Welcome to Talktor API"}' > main.py

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]