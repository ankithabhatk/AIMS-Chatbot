#!/bin/bash

# AIMS Chatbot Professional Deployment Script
# One-command startup for development/testing

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PORT=${1:-8000}
FRONTEND_PORT=${2:-8001}

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                🚀 AIMS CHATBOT DEPLOYMENT SCRIPT                          ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo -e "${BLUE}[1/5]${NC} Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Install Python 3.8+"
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✅${NC} Python $PYTHON_VERSION found"
echo ""

# Check dependencies
echo -e "${BLUE}[2/5]${NC} Checking dependencies..."
if [ ! -d "$PROJECT_DIR/backend/.venv" ]; then
    echo "📦 Creating virtual environment..."
    cd "$PROJECT_DIR/backend"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -q -r requirements.txt
    echo -e "${GREEN}✅${NC} Virtual environment ready"
else
    echo -e "${GREEN}✅${NC} Virtual environment exists"
fi
echo ""

# Check FAISS index
echo -e "${BLUE}[3/5]${NC} Checking FAISS index..."
if [ -f "/tmp/chatbot_faiss/index.faiss" ]; then
    SIZE=$(du -h /tmp/chatbot_faiss/index.faiss | awk '{print $1}')
    DOCS=$(python3 -c "import json; print(len(json.load(open('/tmp/chatbot_faiss/metadata.json'))))" 2>/dev/null || echo "?")
    echo -e "${GREEN}✅${NC} FAISS index ready (${SIZE}, ${DOCS} documents)"
else
    echo -e "${YELLOW}⚠️${NC} No FAISS index found. Initialize with:"
    echo "   python backend/scripts/ingest.py"
fi
echo ""

# Start Backend
echo -e "${BLUE}[4/5]${NC} Starting Backend API (port ${BACKEND_PORT})..."
cd "$PROJECT_DIR"
source backend/.venv/bin/activate
nohup python -m uvicorn backend.app.main:app \
    --host 0.0.0.0 \
    --port ${BACKEND_PORT} \
    --reload > /tmp/chatbot_backend.log 2>&1 &
BACKEND_PID=$!
sleep 2
if ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} Backend running (PID: $BACKEND_PID)"
else
    echo -e "${YELLOW}⚠️${NC} Backend may not have started. Check /tmp/chatbot_backend.log"
fi
echo ""

# Start Frontend
echo -e "${BLUE}[5/5]${NC} Starting Frontend Server (port ${FRONTEND_PORT})..."
nohup python serve_frontend.py --port ${FRONTEND_PORT} > /tmp/chatbot_frontend.log 2>&1 &
FRONTEND_PID=$!
sleep 1
if ps -p $FRONTEND_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} Frontend running (PID: $FRONTEND_PID)"
else
    echo -e "${YELLOW}⚠️${NC} Frontend may not have started. Check /tmp/chatbot_frontend.log"
fi
echo ""

# Success message
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo -e "║  ${GREEN}✅ DEPLOYMENT COMPLETE${NC}                                               ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Access the chatbot:"
echo "   Modern UI:  http://localhost:${FRONTEND_PORT}/index.html"
echo "   Pro UI:     http://localhost:${FRONTEND_PORT}/professional.html"
echo ""
echo "📊 API Health:"
echo "   curl http://localhost:${BACKEND_PORT}/api/health"
echo ""
echo "🧪 Run Tests:"
echo "   python backend/scripts/fast_test.py"
echo "   python backend/scripts/integration_test.py"
echo ""
echo "📝 Logs:"
echo "   Backend:  tail -f /tmp/chatbot_backend.log"
echo "   Frontend: tail -f /tmp/chatbot_frontend.log"
echo ""
echo "🛑 To stop:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo ""
