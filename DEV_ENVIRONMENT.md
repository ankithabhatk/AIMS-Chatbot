# 🧠 Development Environment Guide

This document explains how to set up your development environment for working on the AIMS College Chatbot project, with special focus on the **brain-aware** setup.

## 🚀 Quick Start (One Command)

```bash
bash setup.sh
```

This will:
- ✅ Check Python 3.11+
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Verify setup complete

## 📕 What You Get

### 1. **Project Brain Integration** (Backend + AI)

Your backend automatically loads `project-brain/` on startup:

```python
# app/main.py loads:
from app.core.brain import BRAIN

# Every startup logs:
# 📖 Loading Project Brain...
#    Project: AIMS College Chatbot
#    Phase: RAG Implementation - COMPLETE ✅
#    Identified Risks: 5
```

### 2. **AI-Aware Development** (VSCode + Extensions)

When you use Continue.dev or other AI tools, they automatically read:

```
.ai-context.md
  ↓ (references)
project-brain/1_context.md
project-brain/2_architecture.md
project-brain/3_decisions.md
project-brain/memory.json
```

### 3. **Command Shortcuts** (Makefile)

```bash
make start          # Run backend dev server
make test           # Test RAG pipeline
make brain          # Show project status
make push           # Commit and push to GitHub
make docker-up      # Start all containers
```

### 4. **VSCode Configuration**

Automatically configured:
- ✅ Python formatter (black)
- ✅ Linting (pylint)
- ✅ Debug launchers (FastAPI + tests)
- ✅ Error Lens (inline errors)
- ✅ File exclusions (.venv, __pycache__)

### 5. **Recommended Extensions**

```
.vscode/extensions.json
  ↓ (VSCode suggests)
- Continue.dev (brain-aware coding)
- GitHub Copilot (AI completion)
- Codeium (free alternative)
- Python (debugging + linting)
- Error Lens (inline errors)
- Docker (container management)
- PostgreSQL Client (database)
```

## 🧠 How the "Brain-Aware" System Works

### For Backend Developers

Your API **always knows** what phase the project is in:

```python
# app/services/chat.py
from app.core.brain import BRAIN

@router.post("/chat")
async def chat(request: ChatRequest):
    current_phase = BRAIN.get_current_phase()  # "RAG Implementation"
    
    if BRAIN.is_phase_complete():
        # Phase complete, can proceed to next
        pass
    
    # Every response includes:
    return ChatResponse(
        response=...,
        project_phase=BRAIN.get_current_phase(),  # Client sees current phase
        ...
    )
```

### For AI Assistants (Continue / Copilot)

When you use Continue in VSCode:

1. You type: `"Implement lead capture endpoint"`
2. Continue reads `.ai-context.md`
3. AI reads `project-brain/` files
4. AI generates code aware of:
   - Current phase ← Must not contradict this
   - Decisions made ← Follows architecture
   - Risks identified ← Mitigates risks
   - Next priorities ← Aligns with roadmap

### For New Team Members

1. Clone repo
2. Run `bash setup.sh`
3. Read `.ai-context.md`
4. Open in VSCode
5. Install recommended extensions
6. You're ready to work

## 📂 Key Files

| File | Purpose |
|------|---------|
| `.ai-context.md` | Force AI to read brain before work |
| `Makefile` | Standardized commands |
| `setup.sh` | One-command environment setup |
| `.vscode/settings.json` | Formatting + linting rules |
| `.vscode/launch.json` | Debug configurations |
| `.vscode/extensions.json` | Recommended VSCode extensions |
| `.continue/config.json` | Continue.dev AI assistant config |
| `project-brain/` | Persistent project memory (8 files) |

## 🔧 Common Tasks

### Start Development

```bash
make start

# Or manually:
cd backend && uvicorn app.main:app --reload
```

Visit: http://localhost:8000/docs (Swagger UI)

### Test RAG Pipeline

```bash
make test

# Or manually:
cd backend && python test_rag.py
```

### View Project Status

```bash
make brain

# Or read files directly:
cat project-brain/memory.json
cat project-brain/5_progress.md
```

### Debug in VSCode

1. Open `backend/app/api/chat.py`
2. Press `F5` or Click "Run and Debug"
3. Select "FastAPI Backend"
4. Breakpoints work automatically

### Push Changes (Including Brain Updates)

```bash
# Update brain files if needed, then:
make push

# Or manually:
git add -A
git commit -m "Your message"
git push origin main
```

## 🐳 Docker Setup

If using Docker:

```bash
make docker-build  # Build images
make docker-up     # Start containers
make docker-logs   # Tail logs
make docker-down   # Stop
```

Or manually:
```bash
docker-compose up -d
```

## 🧪 Before You Commit

Checklist:

- [ ] Code passes `make lint`
- [ ] Tests pass with `make test`
- [ ] `project-brain/memory.json` updated if phase changed
- [ ] `project-brain/5_progress.md` has session notes
- [ ] All files formatted: `make format`

## 🤖 Using Continue.dev

Inside VSCode, open Continue panel (Ctrl+L or Cmd+L):

```
/brain          # Show current project brain
/context        # Read AI context guidelines
/decisions      # Review tech decisions
```

Then ask questions:

```
Based on project brain, how should I implement lead capture?
(Continue will read brain first, then answer)
```

## 🚨 If Something Breaks

### Virtual environment issue:
```bash
rm -rf backend/.venv
bash setup.sh
```

### FAISS index corrupted:
```bash
make reset-faiss
make start
```

### Git conflicts:
```bash
git fetch origin
git rebase origin/main
git add -A
git commit -m "Resolved conflicts"
git push origin main
```

## 📊 Architecture Diagram

```
┌─────────────────────────────────────────┐
│     VSCode + Recommended Extensions     │
│  (Continue, Copilot, Python, etc.)      │
└──────────────┬──────────────────────────┘
               │
               ├─→ .ai-context.md (force brain read)
               │
               ├─→ .vscode/settings.json (config)
               │
               └─→ .continue/config.json (AI config)
                                    │
                                    ↓
                        ┌───────────────────┐
                        │  Project Brain    │
                        │  (8 files)        │
                        │                   │
                        │ 1_context.md      │
                        │ 3_decisions.md    │
                        │ memory.json       │
                        │ etc.              │
                        └───────┬───────────┘
                                │
                                ↓
                   ┌────────────────────────┐
                   │  FastAPI Backend       │
                   │                        │
                   │ app/core/brain.py      │
                   │ (loads brain at        │
                   │  startup)              │
                   │                        │
                   │ /api/v1/chat           │
                   │ (includes project_     │
                   │  phase in response)    │
                   └────────────────────────┘
```

## 💡 Tips & Tricks

**Tip 1: Keep brain updated**
- After each feature, update `project-brain/5_progress.md`
- Before each session, read `project-brain/memory.json`

**Tip 2: Use slash commands in Continue**
```
/brain   → Quick status check
/context → Refresh on guidelines
```

**Tip 3: See command help**
```bash
make help
```

**Tip 4: Format before pushing**
```bash
make format  # Runs black + isort
make lint    # Checks syntax
```

**Tip 5: Debug with VSCode**
- Set breakpoints (click line number)
- Press F5 to start debugging
- Use Debug Console to inspect variables

## 📖 Further Reading

- [.ai-context.md](.ai-context.md) — AI guidelines + architecture
- [project-brain/1_context.md](project-brain/1_context.md) — Project definition
- [project-brain/3_decisions.md](project-brain/3_decisions.md) — Why we chose each tech
- [RAG_SETUP_GUIDE.md](RAG_SETUP_GUIDE.md) — RAG pipeline details
- [README.md](README.md) — Project overview

## 🤝 Questions?

1. Check `make help`
2. Read `.ai-context.md`
3. Review `project-brain/` files
4. Search GitHub issues
5. Check `RAG_SETUP_GUIDE.md`

---

**Last Updated:** 2026-04-19  
**Maintained By:** Solo Dev  
**Status:** Active ✅
