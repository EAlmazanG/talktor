#!/bin/bash

# Wait for the database to be ready
echo "Waiting for database to be ready..."
sleep 5

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting the application..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
