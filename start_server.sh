#!/bin/bash
# Start the chatbot server with Python 3.10 environment

echo "Activating Python 3.10 environment..."
source /opt/anaconda3/bin/activate chatbot

cd "$(dirname "$0")/backend"

echo "Starting server on port 8000..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --loop asyncio
