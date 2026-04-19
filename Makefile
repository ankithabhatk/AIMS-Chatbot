.PHONY: help start test brain push update-brain lint format clean

help:
	@echo "🚀 AIMS College Chatbot - Common Commands\n"
	@echo "Development:"
	@echo "  make start          - Start FastAPI dev server"
	@echo "  make test           - Run RAG pipeline test"
	@echo "  make test-all       - Run all tests with pytest"
	@echo "  make lint           - Check Python syntax"
	@echo "  make format         - Format Python code\n"
	@echo "Project Brain:"
	@echo "  make brain          - Show current project brain"
	@echo "  make update-brain   - Update brain status (run after features)"
	@echo "  make brain-view     - View brain files\n"
	@echo "Git:"
	@echo "  make push           - Commit all changes and push"
	@echo "  make status         - Show git status\n"
	@echo "Docker:"
	@echo "  make docker-build   - Build Docker images"
	@echo "  make docker-up      - Start Docker containers"
	@echo "  make docker-down    - Stop Docker containers\n"
	@echo "Cleanup:"
	@echo "  make clean          - Remove cache files\n"

# Development

start:
	@echo "🚀 Starting FastAPI dev server..."
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	@echo "🧪 Testing RAG pipeline..."
	cd backend && python test_rag.py

test-all:
	@echo "🧪 Running all tests..."
	cd backend && pytest tests/ -v

lint:
	@echo "🔍 Checking Python syntax..."
	cd backend && python -m py_compile app/**/*.py

format:
	@echo "📝 Formatting Python code..."
	cd backend && black app/ --line-length 100 --target-version py311 || true
	cd backend && isort app/ || true

# Project Brain

brain:
	@echo "📖 Displaying project brain...\n"
	@cat project-brain/memory.json | python -m json.tool | head -30

brain-view:
	@echo "📂 Project brain files:\n"
	@ls -lah project-brain/

update-brain:
	@echo "✏️  Updating brain with current progress..."
	@echo "Please update project-brain/ files manually, then run: make push"

# Git

push:
	@echo "📤 Committing and pushing to GitHub..."
	git add -A && git commit -m "Update: $(shell date '+%Y-%m-%d %H:%M')" && git push origin main

status:
	@echo "📊 Git Status:\n"
	git status

# Docker

docker-build:
	@echo "🐳 Building Docker images..."
	docker-compose build

docker-up:
	@echo "🐳 Starting Docker containers..."
	docker-compose up -d

docker-down:
	@echo "🛑 Stopping Docker containers..."
	docker-compose down

docker-logs:
	@echo "📝 Docker logs..."
	docker-compose logs -f backend

# Cleanup

clean:
	@echo "🧹 Cleaning cache files..."
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find backend -type f -name "*.pyc" -delete
	rm -rf backend/.pytest_cache
	rm -rf backend/.coverage
	@echo "✅ Cleaned!"

install-deps:
	@echo "📦 Installing Python dependencies..."
	cd backend && pip install -r requirements.txt

# Shortcuts

dev: start

logs:
	@tail -f /tmp/chatbot.log 2>/dev/null || echo "No logs yet"

reset-faiss:
	@echo "🔄 Resetting FAISS index..."
	rm -rf /tmp/chatbot_faiss/* 2>/dev/null
	@echo "✅ FAISS index reset. Will rebuild on next start."
