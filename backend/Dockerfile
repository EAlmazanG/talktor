FROM python:3.12.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libasound2-dev \
    portaudio19-dev \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir uvicorn fastapi sqlalchemy psycopg2-binary python-dotenv alembic

# Copy the backend directory
COPY . .

# Make the start script executable
RUN chmod +x /app/start.sh

# Run the start script
CMD ["/app/start.sh"]