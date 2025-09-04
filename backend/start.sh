#!/bin/bash

# Wait for the database to be ready with active checks
echo "Waiting for database to be ready..."
ATTEMPT=1
MAX_ATTEMPTS=60
until python - <<'PY'
from db.database import test_connection
import sys
sys.exit(0 if test_connection() else 1)
PY
do
  echo "Database not ready yet (${ATTEMPT}/${MAX_ATTEMPTS})..."
  ATTEMPT=$((ATTEMPT+1))
  if [ ${ATTEMPT} -gt ${MAX_ATTEMPTS} ]; then
    echo "Database did not become ready in time. Exiting."
    exit 1
  fi
  sleep 1
done

echo "Database ready. Initializing tables..."
python - <<'PY'
from db.database import init_database
init_database()
print("Database initialized")
PY

# Start the application (production settings)
echo "Starting the application..."
uvicorn main:app --host 0.0.0.0 --port 8000
