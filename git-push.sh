#!/bin/bash
# Git initialization and push script

set -e

echo "🚀 Initializing Git repository..."

# Navigate to project root
cd /Users/maneeth/Desktop/Chat-Bot

# Initialize git
git init

# Add all files
echo "📦 Adding files to git..."
git add .

# Create initial commit
echo "✅ Creating initial commit..."
git commit -m "Initial commit: Full project structure with FastAPI backend scaffolding

- Project folder structure (backend, frontend, infra, docs)
- FastAPI application skeleton with async support
- Database models (SQLAlchemy) for documents, chunks, embeddings, chats, leads
- API endpoints: /chat (RAG), /leads (CRM), /analytics, /health
- Environment configuration and .env.example
- Docker and Docker Compose setup
- CompPrehensive documentation (8 files, 50K+ words)
- LangChain integration guide
- Requirements.txt with all dependencies

Status: Ready for backend implementation (Week 1 of implementation schedule)
"

# Add remote
echo "🔗 Adding GitHub remote..."
git remote add origin https://github.com/Project-of-DevOps/AIMS-ChatBot.git

# Rename branch to main
echo "🌳 Setting main branch..."
git branch -M main

# Push to GitHub
echo "📢 Pushing to GitHub..."
git push -u origin main

echo "✨ Success! Repository pushed to GitHub"
echo "📍 Repository: https://github.com/Project-of-DevOps/AIMS-ChatBot.git"
echo ""
echo "🎯 Next Steps:"
echo "1. Update .env with your OpenAI API key and Salesforce credentials"
echo "2. Run: docker-compose up -d"
echo "3. Visit: http://localhost:8000/docs for API documentation"
echo "4. Check implementation checklist in docs/ for development roadmap"
