# Project Context

## Project Name
AIMS College Chatbot System

## Goal
Build a production-grade AI chatbot that:
- 🤖 Answers student queries from college website (RAG)
- 📝 Captures student data (lead generation)
- 🔗 Integrates with Salesforce CRM for lead management
- 📊 Provides analytics on student interactions
- 💡 Recommends related questions (future)

## Problem Statement
College websites are hard to navigate. Students need:
- Quick answers to admission/academic questions
- Ability to leave contact for follow-up
- Personalized recommendations

## Data Source
- Primary: https://www.theaims.ac.in (AIMS College website)
- Fallback: Hardcoded sample data for testing

## Architecture Distribution
- **Frontend**: React 18 + TypeScript (placeholder, not implemented)
- **Backend**: FastAPI + Python 3.11 (working)
- **Database**: PostgreSQL + pgvector (configured, not used)
- **Vector Store**: FAISS (working, local)
- **Cache**: Redis (configured, not used)
- **Queue**: Celery (configured, not used)
- **Infrastructure**: Docker Compose (ready)

## Success Criteria
✅ Chat endpoint returns real answers (not placeholders)
✅ Confidence scoring (0-1)
✅ Source attribution (URLs + snippets)
✅ Fallback to contact info if unsure
✅ <500ms response time
✅ Zero external API dependencies (MVP)

## Current Phase
🟢 **RAG Implementation** - Core chat logic (JUST COMPLETED)

## Next Phase
🟡 **Data & Integration** - Database + Salesforce + scraper

## Team
- Solo: Building entire MVP

## Timeline
- MVP target: 2 weeks
- Production: 4-6 weeks

## Budget Context
- Development: $200K
- Operations: $1,200/month
- Tools: Free + Sentence-Transformers (local)
