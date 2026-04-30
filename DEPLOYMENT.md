# AIMS Chatbot Deployment Guide

This guide outlines the transition from local research mode to stable production deployment.

## Architecture Highlights
- **Conversational Engine**: Cloud-hosted LLM (Groq `llama-3.1-8b-instant` default)
- **Local Fallback**: Local Ollama + Qwen (for dev and fallback)
- **Memory & Intelligence**: Runs natively on the FastAPI backend without external vector databases or orchestration frameworks (No LangChain, MemGPT, etc.)

## Environment Variables

Ensure these are set in your deployment environment (e.g., Railway, Render):

```env
# API Keys for Cloud Inference
GROQ_API_KEY="your_groq_api_key_here"
OPENROUTER_API_KEY="your_openrouter_api_key_here"

# Model Selection
MODEL_NAME="llama-3.1-8b-instant"
```

## Local Development Setup

1. Start your local Ollama instance for fallback safety:
   ```bash
   ollama run qwen2.5-coder:7b-instruct-q4_K_M
   ```
2. Start the FastAPI backend:
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```
3. Start the Next.js frontend:
   ```bash
   npm run dev
   ```

## Production Deployment (Railway / Render)

### Backend Deployment (FastAPI)
1. Link your GitHub repository to your platform.
2. Set the Root Directory to `backend/`.
3. Set the Build Command:
   ```bash
   pip install -r requirements.txt
   ```
4. Set the Start Command:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
5. **Add Environment Variables**: Ensure `GROQ_API_KEY` is injected so the system uses lightweight cloud inference rather than crashing trying to find a local Ollama instance.

### Frontend Deployment (Next.js)
1. Link the repository.
2. Set the Root Directory to `/` (the main project folder).
3. Build Command: `npm install && npm run build`
4. Start Command: `npm start`
5. **Environment Variable**: 
   - `NEXT_PUBLIC_API_URL` -> URL of your deployed backend (e.g., `https://aims-backend.up.railway.app`)

## LLM Provider Fallback Behavior
The system uses a robust fallback chain for high availability:
1. **Groq**: Primary provider. Fast and cheap.
2. **OpenRouter**: Secondary cloud provider if Groq goes down.
3. **Ollama**: Local inference if cloud providers fail (useful mostly for local dev).
4. **Templates**: Deterministic fallback if all generative models fail. No downtime.
