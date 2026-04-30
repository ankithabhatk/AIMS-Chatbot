#!/usr/bin/env python3
"""
🚀 Ollama Qwen Runner - Mac-Optimized Local LLM Integration
Runs code with local Ollama models (Qwen 2.5 Coder)
Prevents Mac crashes with resource management
"""

import subprocess
import requests
import json
import sys
import os
import logging
import time
from typing import Optional, Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OllamaQwenRunner:
    """Efficient Ollama + Qwen integration for macOS"""
    
    def __init__(self, 
                 model: str = "qwen2.5-coder:7b-instruct-q4_K_M",
                 host: str = "http://localhost:11434",
                 temperature: float = 0.3,
                 num_thread: int = 4):
        self.model = model
        self.host = host
        self.temperature = temperature
        self.num_thread = num_thread
        self.api_url = f"{host}/api/generate"
        
    def check_ollama_running(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=2)
            if response.status_code == 200:
                logger.info("✅ Ollama server is running")
                return True
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Ollama not running at {self.host}")
            return False
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return False
    
    def list_models(self) -> list:
        """List available models"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [m['name'] for m in data.get('models', [])]
                for model in models:
                    logger.info(f"  • {model}")
                return models
        except Exception as e:
            logger.error(f"Error listing models: {e}")
        return []
    
    def generate(self, prompt: str, stream: bool = True) -> str:
        """Generate response using Ollama"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": self.temperature,
                "num_thread": self.num_thread,
                "top_k": 40,
                "top_p": 0.9,
            }
        }
        
        try:
            logger.info(f"📝 Using {self.model}...")
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=180
            )
            
            if response.status_code != 200:
                logger.error(f"API error: {response.status_code}")
                return ""
            
            if stream:
                return self._stream_response(response)
            else:
                data = response.json()
                return data.get("response", "")
                
        except requests.exceptions.Timeout:
            logger.error("Timeout - try shorter prompts")
            return ""
        except Exception as e:
            logger.error(f"Error: {e}")
            return ""
    
    def _stream_response(self, response) -> str:
        """Handle streaming response"""
        full_response = ""
        try:
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    chunk = data.get("response", "")
                    full_response += chunk
                    print(chunk, end='', flush=True)
        except Exception as e:
            logger.error(f"Streaming error: {e}")
        print("\n")
        return full_response


def demo_examples():
    """Run demo examples"""
    runner = OllamaQwenRunner()
    
    # Check connection
    if not runner.check_ollama_running():
        logger.error("Start Ollama: Run 'ollama serve' in another terminal")
        return
    
    # List available models
    logger.info("\n📦 Available Models:")
    runner.list_models()
    
    # Example 1: Code explanation
    logger.info("\n\n=== EXAMPLE 1: Code Explanation ===")
    prompt1 = """Explain this Python code in 2-3 sentences:

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

Response:"""
    
    response1 = runner.generate(prompt1)
    
    # Example 2: Question answering
    logger.info("\n\n=== EXAMPLE 2: Question Answering ===")
    prompt2 = """Q: What is RAG in machine learning?
Answer:"""
    
    response2 = runner.generate(prompt2)
    
    # Example 3: Code generation
    logger.info("\n\n=== EXAMPLE 3: Code Generation ===")
    prompt3 = """Write Python code to check if a number is prime.
Code:"""
    
    response3 = runner.generate(prompt3)
    
    logger.info("\n✅ Demo completed!")


def interactive_mode():
    """Interactive chat with Qwen"""
    runner = OllamaQwenRunner()
    
    if not runner.check_ollama_running():
        logger.error("Start Ollama: Run 'ollama serve' in another terminal")
        return
    
    logger.info("\n🤖 Qwen Interactive Mode (type 'exit' to quit)")
    logger.info(f"Using: {runner.model}\n")
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() == 'exit':
                logger.info("Goodbye!")
                break
            if not user_input:
                continue
            
            response = runner.generate(user_input)
            print(f"\nQwen: {response}")
        except KeyboardInterrupt:
            logger.info("\nInterrupted!")
            break
        except EOFError:
            logger.info("End of input")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            break


def run_with_backend():
    """Integrate with Chat-Bot backend"""
    logger.info("\n🔗 Integrating with Chat-Bot backend...")
    
    sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')
    
    try:
        from app.services.llm.response_generator import ResponseGenerator
        from app.services.retrieval.faiss_index import get_index
        
        logger.info("✅ Backend services imported")
        
        # Example RAG query
        runner = OllamaQwenRunner()
        if not runner.check_ollama_running():
            logger.error("Ollama not running")
            return
        
        query = "What is the admission process?"
        logger.info(f"\nQuery: {query}")
        
        # Get index and search
        try:
            index = get_index()
            results = index.search(query, top_k=3)
            
            if results:
                logger.info(f"Found {len(results)} results")
                context = "\n".join([f"• {r[0][:100]}" for r in results])
                
                # Generate with Ollama
                prompt = f"""Answer based on context:
Context:
{context}

Question: {query}

Answer:"""
                
                response = runner.generate(prompt)
                logger.info(f"\nAnswer:\n{response}")
            else:
                logger.warning("No results found")
        except Exception as e:
            logger.error(f"Backend error: {e}")
            
    except ImportError as e:
        logger.error(f"Cannot import backend: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Qwen with Ollama")
    parser.add_argument("--demo", action="store_true", help="Run demo examples")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--backend", action="store_true", help="Test with backend")
    parser.add_argument("--model", default="qwen2.5-coder:7b-instruct-q4_K_M", help="Ollama model to use")
    parser.add_argument("--text", type=str, help="Run single prompt")
    
    args = parser.parse_args()
    
    if args.demo:
        demo_examples()
    elif args.interactive:
        interactive_mode()
    elif args.backend:
        run_with_backend()
    elif args.text:
        runner = OllamaQwenRunner(model=args.model)
        if runner.check_ollama_running():
            response = runner.generate(args.text)
    else:
        logger.info("Qwen Ollama Runner - Options:")
        logger.info("  python run_ollama_qwen.py --demo          (Run examples)")
        logger.info("  python run_ollama_qwen.py --interactive   (Chat mode)")
        logger.info("  python run_ollama_qwen.py --backend       (Test with backend)")
        logger.info("  python run_ollama_qwen.py --text 'prompt' (Single query)")

