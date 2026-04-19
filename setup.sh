#!/bin/bash

set -e

echo "🚀 AIMS College Chatbot - Development Environment Setup"
echo "======================================================\n"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${BLUE}✓ Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "  Python: $python_version"

# Create virtual environment
echo -e "\n${BLUE}✓ Setting up Python virtual environment...${NC}"
if [ ! -d "backend/.venv" ]; then
    python3 -m venv backend/.venv
    echo "  Created: backend/.venv"
else
    echo "  Already exists: backend/.venv"
fi

# Activate venv
source backend/.venv/bin/activate
echo "  ✓ Virtual environment activated"

# Install dependencies
echo -e "\n${BLUE}✓ Installing Python dependencies...${NC}"
cd backend
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
pip install -r requirements.txt
echo "  ✓ Dependencies installed"
cd ..

# Print summary
echo -e "\n${GREEN}✅ Setup Complete!${NC}\n"

echo "Next steps:"
echo "  1. Start the server:"
echo "     → make start"
echo ""
echo "  2. Test the RAG pipeline:"
echo "     → make test"
echo ""
echo "  3. View project brain:"
echo "     → make brain"
echo ""
echo "  4. Read setup guide:"
echo "     → cat RAG_SETUP_GUIDE.md"
echo ""
echo "Tips:"
echo "  • See all commands: make help"
echo "  • Debug with: python -m pdb"
echo "  • VSCode: Open workspace and install recommended extensions"
echo ""
echo -e "${BLUE}Read .ai-context.md for AI assistant guidelines${NC}"
