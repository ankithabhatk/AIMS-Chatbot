# LANGCHAIN INTEGRATION GUIDE FOR COLLEGE CHATBOT

**Purpose:** Map the architecture design to actual LangChain GitHub repos + provide concrete implementation paths

---

## 📍 REPOS YOU'LL USE

### Primary: LangChain Core Framework
**GitHub:** https://github.com/langchain-ai/langchain  
**Install:** `pip install langchain`

**Why:** This is exactly what your architecture needs:
- Document loaders (web scraping integration)
- Text splitting (chunking strategy)
- Embeddings abstraction (OpenAI integration)
- Retrieval chains (vector DB search)
- LLM chains (GPT-3.5-turbo integration)
- Memory management (chat history)

**You'll use these LangChain components:**
```
langchain.document_loaders          → Web scraping
langchain.text_splitter             → Chunking (module 2)
langchain.embeddings                → Embedding generation (module 3)
langchain.vectorstores              → Vector DB abstraction (module 4)
langchain.chains                    → LLM query engine (module 5)
langchain.retrievers                → Retrieval logic (module 4)
langchain.agents                    → Fallback + routing (module 6)
langchain.callbacks                 → Event logging (module 8)
```

---

### Secondary: LangChain Community Integrations
**GitHub:** https://github.com/langchain-ai/langchain-community  
**Install:** Already included with `pip install langchain`

**Useful for:**
- Additional document loaders (PDFs, specialized formats)
- Database adapters
- Tool integrations

---

### Reference: Course Projects + Examples
**GitHub:** https://github.com/emarco177/langchain-course  
**Use for:** Learning RAG patterns + seeing working examples

---

## 🏗️ HOW LANGCHAIN MAPS TO YOUR ARCHITECTURE

### Module 2: Data Preprocessing & Chunking

**Your Architecture:** BeautifulSoup + Selenium + custom chunking

**LangChain Way:**
```python
from langchain.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Load website
loader = WebBaseLoader("https://www.theaims.ac.in")
docs = loader.load()

# Chunk with overlap
splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=100
)
chunks = splitter.split_documents(docs)
```

**Why use LangChain here:**
- Automatic handling of metadata
- Built-in overlap logic
- Easy to switch strategies
- No custom regex parsing needed

---

### Module 3: Embedding Generation

**Your Architecture:** OpenAI text-embedding-3-small

**LangChain Way:**
```python
from langchain.embeddings import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=OPENAI_API_KEY
)

# Generate embeddings for chunks
embedded_chunks = embeddings.embed_documents(
    [chunk.page_content for chunk in chunks]
)
```

**Why use LangChain here:**
- Unified embedding interface
- Works with 20+ embedding providers (easy to switch)
- Built-in caching + batching
- Error handling + retry logic included

---

### Module 4: Vector Database & Retrieval

**Your Architecture:** PostgreSQL pgvector + semantic search

**LangChain Way:**
```python
from langchain.vectorstores import FAISS  # or Pinecone, Chroma, etc.
from langchain.retrievers import ContextualCompressionRetriever

# Create vector store
vector_store = FAISS.from_documents(
    documents=chunks,
    embedding=embeddings
)

# Create retriever
retriever = vector_store.as_retriever(
    search_kwargs={"k": 5}  # top-5 chunks
)

# Optional: Add re-ranking
from langchain.retrievers.document_compressors import LLMCompressor
compressor = LLMCompressor.from_llm_and_prompt(llm, prompt)
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=retriever
)
```

**Why use LangChain here:**
- Works with ANY vector DB (pgvector, Pinecone, Milvus, etc.)
- Abstract away implementation details
- Built-in retrieval optimization
- Re-ranking support for better results

---

### Module 5: LLM Query Engine

**Your Architecture:** GPT-3.5-turbo with RAG + confidence scoring

**LangChain Way:**
```python
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# Define LLM
llm = OpenAI(
    model_name="gpt-3.5-turbo",
    temperature=0.1,  # Lower = more deterministic
    max_tokens=300
)

# Define prompt template
prompt_template = """
You are a college information chatbot.
Answer ONLY based on the provided context.

CONTEXT:
{context}

QUESTION: {question}

RESPONSE:
"""

# Create retrieval chain
qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",  # Put all context in one prompt
    retriever=retriever,
    chain_type_kwargs={
        "prompt": PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
    }
)

# Run query
result = qa.run("What are B.Tech admission requirements?")
```

**Why use LangChain here:**
- Handles prompt assembly automatically
- Token counting + overflow prevention
- Callbacks for logging/monitoring
- Easy to switch LLM providers

---

### Module 6: Fallback & Escalation

**Your Architecture:** No relevant chunks → fallback response

**LangChain Way:**
```python
from langchain.chains.router import MultiPromptChain
from langchain.agents import AgentExecutor

# Create fallback chain
fallback_chain = LLMChain(
    llm=llm,
    prompt=PromptTemplate(
        template="I don't have info about {question}. Contact: admissions@aims.ac.in",
        input_variables=["question"]
    )
)

# Create router that chooses between chains
router_chain = MultiPromptChain(
    router_chains=[qa, fallback_chain],
    default_chain=fallback_chain
)
```

**Why use LangChain here:**
- Abstraction for conditional logic
- Multiple chain routing
- Fallback handling built-in

---

## 🔄 LINE-BY-LINE IMPLEMENTATION PATH

### Step 1: Setup & Verification (Day 1)

```bash
# Install core packages
pip install langchain openai python-dotenv

# Verify installation
python -c "import langchain; print(langchain.__version__)"

# Test OpenAI API
python -c "
from langchain.embeddings import OpenAIEmbeddings
embeddings = OpenAIEmbeddings(model='text-embedding-3-small')
result = embeddings.embed_query('test')
print(f'Embedding size: {len(result)}')
"
```

---

### Step 2: Load College Website (Day 2)

```python
# scripts/load_website.py
from langchain.document_loaders import WebBaseLoader

loader = WebBaseLoader("https://www.theaims.ac.in")
docs = loader.load()

print(f"Loaded {len(docs)} documents")
for doc in docs[:3]:
    print(f"- {doc.metadata['source']}")
```

**Expected output:**
```
Loaded 132 documents
- https://www.theaims.ac.in/
- https://www.theaims.ac.in/about
- https://www.theaims.ac.in/admissions
...
```

---

### Step 3: Chunk Documents (Day 2)

```python
# scripts/chunk_documents.py
from langchain.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

loader = WebBaseLoader("https://www.theaims.ac.in")
docs = loader.load()

splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", ". ", " ", ""],
    chunk_size=512,
    chunk_overlap=100
)

chunks = splitter.split_documents(docs)

print(f"Split into {len(chunks)} chunks")
print(f"Chunk sizes: min={min(len(c.page_content) for c in chunks)}, "
      f"max={max(len(c.page_content) for c in chunks)}")
```

---

### Step 4: Generate Embeddings (Day 3)

```python
# scripts/generate_embeddings.py
from langchain.embeddings import OpenAIEmbeddings
import json

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Embed all chunks (batch them for efficiency)
embedded = embeddings.embed_documents(
    [chunk.page_content for chunk in chunks]
)

print(f"Generated {len(embedded)} embeddings")
print(f"Embedding dimension: {len(embedded[0])}")

# Save to file for debugging
with open("embeddings.json", "w") as f:
    json.dump({
        "count": len(embedded),
        "dimension": len(embedded[0]),
        "sample": embedded[0][:5]  # First 5 values
    }, f)
```

---

### Step 5: Create Vector Store & Retriever (Day 3)

```python
# scripts/create_retriever.py
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Load existing chunks
# (In real app, load from database)

vector_store = FAISS.from_documents(
    documents=chunks,
    embedding=embeddings
)

# Test retrieval
retriever = vector_store.as_retriever(search_kwargs={"k": 5})

results = retriever.get_relevant_documents(
    "What are B.Tech admission requirements?"
)

print(f"Retrieved {len(results)} chunks:")
for i, doc in enumerate(results, 1):
    print(f"\n{i}. {doc.page_content[:200]}...")
    print(f"   Source: {doc.metadata['source']}")
```

---

### Step 6: Create QA Chain (Day 4)

```python
# scripts/qa_chain.py
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

llm = OpenAI(
    model_name="gpt-3.5-turbo",
    temperature=0.1,
    max_tokens=300
)

prompt_template = """You are a college information chatbot for AIMS College.
Answer ONLY based on the provided context. If the answer is not in the context, say "I don't have that information."

CONTEXT:
{context}

QUESTION: {question}

RESPONSE:"""

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    chain_type_kwargs={
        "prompt": PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
    },
    return_source_documents=True  # Important! Get sources
)

# Test
result = qa_chain({"query": "What are B.Tech admission requirements?"})
print(f"Response: {result['result']}")
print(f"Sources: {[doc.metadata['source'] for doc in result['source_documents']]}")
```

---

### Step 7: Integrate Confidence Scoring (Day 4-5)

```python
# app/services/llm/validators.py
from langchain.embeddings import OpenAIEmbeddings
import numpy as np

class ResponseValidator:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    def score_confidence(self, response: str, context_docs: list) -> float:
        """
        Score how well response is grounded in context
        """
        # Embed response
        response_embedding = self.embeddings.embed_query(response)
        
        # Embed context chunks
        context_embeddings = self.embeddings.embed_documents(
            [doc.page_content for doc in context_docs]
        )
        
        # Calculate max cosine similarity
        response_vec = np.array(response_embedding)
        max_similarity = max([
            np.dot(response_vec, np.array(ce)) / (
                np.linalg.norm(response_vec) * np.linalg.norm(np.array(ce)) + 1e-8
            )
            for ce in context_embeddings
        ])
        
        return float(max_similarity)
```

---

### Step 8: Build FastAPI Backend (Day 5-6)

```python
# app/api/chat.py
from fastapi import APIRouter, HTTPException
from langchain.chains import RetrievalQA
from app.services.llm.validators import ResponseValidator
import logging

router = APIRouter(prefix="/api/v1", tags=["chat"])
qa_chain: RetrievalQA = None  # Set during startup
validator = ResponseValidator()

@router.post("/chat")
async def chat(request: ChatRequest):
    """
    RAG-based chat endpoint using LangChain
    """
    try:
        # Run QA chain
        result = qa_chain({"query": request.query})
        response_text = result["result"]
        source_docs = result["source_documents"]
        
        # Score confidence
        confidence = validator.score_confidence(response_text, source_docs)
        
        # Check threshold
        if confidence < 0.7:
            return ChatResponse(
                response="I'm not confident about this. Contact admissions.",
                confidence_score=confidence,
                sources=[],
                is_fallback=True
            )
        
        # Extract sources
        sources = [
            {
                "url": doc.metadata["source"],
                "snippet": doc.page_content[:200]
            }
            for doc in source_docs
        ]
        
        return ChatResponse(
            response=response_text,
            confidence_score=float(confidence),
            sources=sources,
            is_fallback=False
        )
    
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail="Chat error")
```

---

### Step 9: Startup Hook (Connect Components)

```python
# app/main.py
from fastapi import FastAPI
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from app.api.chat import router as chat_router

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """Load LangChain components on startup"""
    global qa_chain
    
    # Initialize embeddings
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    # Load vector store from database
    # (In production, this loads from persistent storage)
    vector_store = FAISS.load_local("./vector_store", embeddings)
    
    # Initialize LLM
    llm = OpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0.1,
        max_tokens=300
    )
    
    # Create QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_store.as_retriever(search_kwargs={"k": 5}),
        return_source_documents=True
    )
    
    print("✅ LangChain components loaded")

app.include_router(chat_router)
```

---

## 🔌 INTEGRATION WITH YOUR ARCHITECTURE

### Where LangChain Fits:

| Module | LangChain Component | Your Customization |
|--------|-------------------|-------------------|
| **Module 2** | `text_splitter.RecursiveCharacterTextSplitter` | College-specific metadata, heading extraction |
| **Module 3** | `embeddings.OpenAIEmbeddings` | Caching layer, batch optimization |
| **Module 4** | `vectorstores.FAISS/Pinecone` + `retrievers` | PostgreSQL pgvector, distance thresholds |
| **Module 5** | `chains.RetrievalQA` + `llms.OpenAI` | Confidence scoring, fallback handling |
| **Module 6** | `agents.AgentExecutor` | CRM escalation logic |
| **Module 8** | `callbacks.BaseCallbackHandler` | Analytics logging to TimescaleDB |

---

## ⚠️ WHAT LANGCHAIN DOESN'T HANDLE

You still need to build:

1. **Web Scraping** (beyond WebBaseLoader)
   - LangChain's WebBaseLoader is basic
   - For JS-heavy sites, add Selenium yourself
   - Code: `app/services/scraper/`

2. **Vector DB Persistence**
   - LangChain provides abstraction
   - You choose: pgvector vs Pinecone
   - Code: Store vectors in your database

3. **Salesforce Integration**
   - LangChain has a tool connector
   - But sync logic is yours
   - Code: `app/services/crm/`

4. **Analytics & Monitoring**
   - LangChain has callbacks
   - But TimescaleDB logging is yours
   - Code: `app/services/analytics/`

5. **Frontend Integration**
   - React component + API calls
   - Code: `frontend/src/components/ChatWidget/`

---

## 🚀 RECOMMENDED ORDER TO BUILD

**Week 1-2:**
```
1. Load website (LangChain WebBaseLoader)
2. Chunk documents (LangChain TextSplitter)
3. Verify chunks look good
```

**Week 2-3:**
```
4. Generate embeddings (LangChain OpenAIEmbeddings)
5. Store in FAISS (in-memory, for testing)
6. Create retriever (LangChain Retriever)
7. Test retrieval accuracy
```

**Week 3-4:**
```
8. Create QA chain (LangChain RetrievalQA)
9. Test end-to-end (query → response)
10. Add confidence scoring (custom)
11. Tune prompts
```

**Week 4-5:**
```
12. FastAPI backend (integrate chain)
13. React frontend (call API)
14. End-to-end testing
```

**Week 5-6:**
```
15. Salesforce integration
16. Analytics logging
17. Production hardening
```

---

## 📚 KEY LANGCHAIN DOCS TO READ

1. **Document Loaders:** https://python.langchain.com/en/latest/modules/indexes/document_loaders.html
2. **Text Splitters:** https://python.langchain.com/en/latest/modules/indexes/text_splitters.html
3. **Embeddings:** https://python.langchain.com/en/latest/modules/models/embeddings.html
4. **Vector Stores:** https://python.langchain.com/en/latest/modules/indexes/vectorstores.html
5. **Retrievers:** https://python.langchain.com/en/latest/modules/indexes/retrievers.html
6. **Chains:** https://python.langchain.com/en/latest/modules/chains.html
7. **Memory:** https://python.langchain.com/en/latest/modules/memory.html

---

## ⚡ COMMON PITFALLS TO AVOID

❌ **Don't** try to learn everything at once
→ Learn one component, test it, move to next

❌ **Don't** use FAISS in production
→ Move to Pinecone after MVP testing

❌ **Don't** ignore the "source_documents"
→ Always return sources with responses (required for credibility)

❌ **Don't** skip prompt engineering
→ Default prompt won't work, iterate

❌ **Don't** forget error handling
→ LLM calls fail, network errors happen

✅ **Do** test locally first
→ Use FAISS in-memory before database

✅ **Do** log everything
→ Query, response, latency, confidence, error

✅ **Do** iterate on prompts
→ Spend 2-3 weeks tuning, not 1 day

✅ **Do** measure hallucination rate
→ Build test set of 50 Q&A, track accuracy

---

## 🎯 SUCCESS CRITERIA

After integrating LangChain:

- [ ] Website loads successfully
- [ ] Chunks generated with correct overlap
- [ ] Embeddings created (1536-dimension vectors)
- [ ] Retrieval returns relevant chunks
- [ ] LLM generates responses with citations
- [ ] Confidence scoring works (<0.7 = fallback)
- [ ] Response latency <2 seconds
- [ ] No hallucinations on test set
- [ ] FastAPI endpoint working
- [ ] React widget calling backend

**Once all checked ✅:** You're ready for production!

