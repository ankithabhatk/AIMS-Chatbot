# 🚀 Ollama Qwen Integration - Quick Start Guide

## ✅ Status: RUNNING
- **Ollama Server**: Active on `http://localhost:11434`
- **Available Models**:
  - `qwen2.5-coder:7b-instruct-q4_K_M` (4.7 GB) - **Recommended**
  - `qwen3:8b` (5.2 GB)
  - `claude-opus-4-5:latest` (Legacy reference)
  - Others available

---

## 📖 Usage Options

### 1. **Demo Examples** (Quick Test)
```bash
python3 run_ollama_qwen.py --demo
```
Runs 3 examples:
- Code explanation
- Question answering
- Code generation

### 2. **Interactive Chat** (Conversational)
```bash
python3 run_ollama_qwen.py --interactive
```
Chat with Qwen 2.5 Coder in real-time. Type `exit` to quit.

### 3. **Single Prompt**
```bash
python3 run_ollama_qwen.py --text "Your prompt here"
```

### 4. **Backend Integration** (RAG + Qwen)
```bash
python3 run_ollama_qwen.py --backend
```
Tests Qwen with your Chat-Bot backend RAG system.

---

## 🔧 Configuration

### Change Model
```bash
python3 run_ollama_qwen.py --text "prompt" --model "qwen3:8b"
```

### Adjust Response Style
Edit `run_ollama_qwen.py`:
```python
runner = OllamaQwenRunner(
    model="qwen2.5-coder:7b-instruct-q4_K_M",
    temperature=0.3,        # 0.1-1.0 (lower = focused)
    num_thread=4            # Limit CPU threads
)
```

---

## ⚡ Mac Optimization Features

✅ **Memory Safe**:
- Limited threads: `4` (prevents CPU overload)
- Temperature: `0.3` (faster, more focused)
- Timeout: `180s` (prevents hanging)

✅ **No Crashes**:
- Graceful error handling
- Resource limits enforced
- Streaming to prevent buffering

✅ **Fast Responses**:
- Streaming output (real-time display)
- Efficient prompt handling
- Smart caching

---

## 🔌 Ollama Management

### Start Ollama
```bash
ollama serve
```
(Run in a separate terminal)

### Check Status
```bash
ollama list              # Show models
curl localhost:11434/api/tags  # API check
```

### Download Additional Models
```bash
ollama pull qwen2.5-coder:7b    # Standard version
ollama pull mistral              # Alternative
```

---

## 🚀 Integration with Backend

```python
from run_ollama_qwen import OllamaQwenRunner

runner = OllamaQwenRunner()

# In your RAG pipeline
prompt = f"""Answer based on context:
{retrieved_context}

Question: {user_query}

Answer:"""

response = runner.generate(prompt)
```

---

## 📊 Performance Benchmarks

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| qwen2.5-coder | 4.7GB | Medium | High | Coding & Logic ⭐ |
| qwen3 | 5.2GB | Medium | Good | General |
| claude-opus-4-5 | 4.7GB | Medium | Good | Legacy Tasks |

---

## 🆘 Troubleshooting

**"Ollama not running"**
```bash
# Terminal 1:
ollama serve

# Terminal 2:
python3 run_ollama_qwen.py --interactive
```

**"Timeout errors"**
- Use shorter prompts
- Reduce `num_thread` to 2

**"Slow responses"**
- Reduce prompt length
- Check Mac memory usage

**"Mac getting hot"**
- Close other apps
- Reduce `num_thread`

---

## 🎯 Next Steps

1. ✅ Test with `--demo`
2. ✅ Try `--interactive` mode
3. ✅ Run `--backend` for RAG integration
4. ✅ Integrate into your Chat-Bot pipeline
5. ✅ Monitor performance and adjust settings

---

## 📝 Example: Backend Integration

```python
# In backend/app/services/llm/response_generator.py

from run_ollama_qwen import OllamaQwenRunner

class ResponseGenerator:
    def __init__(self, use_ollama=True):
        if use_ollama:
            self.ollama = OllamaQwenRunner()
    
    def generate(self, query, chunks):
        context = "\n".join([c[0] for c in chunks])
        prompt = f"Context: {context}\n\nQ: {query}\nA:"
        return self.ollama.generate(prompt)
```

---

**Happy Qwen-ing! 🎉**

