# AIMS Chatbot - Railway Deployment Guide

This guide details exactly how to deploy the AIMS Chatbot repository to Railway. Since the project is a monorepo, you will create **two separate services** in your Railway project, both pulling from the same GitHub repository but using different Root Directories.

## 1. Prerequisites
- Your code is pushed to a GitHub repository.
- You have an active [Railway.app](https://railway.app) account.
- You have an active [Supabase](https://supabase.com) project for analytics (optional but recommended).
- You have an active [Groq](https://console.groq.com/keys) account for temporary cloud LLM inference during the public testing phase (since Railway free tiers cannot host local Ollama instances reliably).

---

## 2. Deploying the Backend (FastAPI)

1. In your Railway Dashboard, click **New Project** -> **Deploy from GitHub repo**.
2. Select your Chatbot repository.
3. Click on the newly created service card and go to **Settings**.
4. Scroll down to **Root Directory** and set it to: `/backend`
5. Save changes. Railway will automatically detect the `railway.json` file we created and use it to build (`pip install -r requirements.txt`) and start (`uvicorn app.main:app`) the backend.
6. Go to the **Variables** tab and add the following environment variables:

### Backend `.env` Template (Railway Variables)
```env
# Supabase Persistence
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# Model Inference (Temporary Cloud Fallback for Public Testing)
LLM_PROVIDER=groq
MODEL_NAME=llama-3.1-8b-instant
GROQ_API_KEY=your_groq_api_key

# Optional: CORS
FRONTEND_URL=https://your-frontend-railway-url.up.railway.app
```
*(Note: You can leave `FRONTEND_URL` empty initially until the frontend is deployed, then come back and add it).*

7. Go to **Settings** -> **Networking** -> click **Generate Domain** to get your public API URL (e.g. `https://your-backend.up.railway.app`). **Copy this URL.**

---

## 3. Deploying the Frontend (Next.js)

1. In the same Railway Project, click **New** -> **GitHub Repo**.
2. Select the *same* Chatbot repository.
3. Click on the new service card and go to **Settings**.
4. Leave the **Root Directory** empty (or `/`). This tells Railway to build the Next.js app.
5. Go to the **Variables** tab and add the following:

### Frontend `.env` Template (Railway Variables)
```env
NEXT_PUBLIC_API_BASE_URL=https://your-backend.up.railway.app/api/v1
```
*(Replace the URL with the domain you generated for the backend in Step 2.7).*

6. Go to **Settings** -> **Networking** -> click **Generate Domain** to get your public Chatbot URL.
7. **Important:** Copy this frontend URL, go back to your Backend service variables, and set `FRONTEND_URL=https://your-frontend-url.up.railway.app` to correctly configure CORS!

---

## 4. Deployment Verification Checklist

Once both services finish building and deploy:
- [ ] **Static Build Verified:** Did the Frontend service finish the `next build` phase without crashing?
- [ ] **Health Endpoint Verified:** Navigate to `https://your-backend.up.railway.app/api/v1/health` in your browser. It should return `{"status": "healthy"}`.
- [ ] **CORS Verified:** Open your public Frontend URL. Open the browser console. Send a message. Ensure there are no `Blocked by CORS policy` errors.
- [ ] **Cloud Inference Verified:** Send "I like coding" followed by "actually I hate coding". Ensure Groq successfully responds (this bypasses your local machine's Ollama during public testing).
- [ ] **Supabase Analytics Verified:** Check your Supabase `conversation_analytics` table. Ensure a new row was added for your test conversation.

---

## 5. Safe Rollback Instructions

If a deployment breaks the UX or crashes the API, Railway makes rollbacks instant.
1. Open the specific service (Frontend or Backend) in your Railway dashboard.
2. Go to the **Deployments** tab.
3. Find the previous deployment card with a green `Success` badge.
4. Click the three dots (`...`) on that card and select **Redeploy**.
5. Railway will instantly swap traffic back to the stable build without taking your app offline.
