import litellm
import os

os.environ["OLLAMA_API_BASE"] = "http://localhost:11434"

model = "ollama/qwen2.5-coder:7b-instruct-q4_K_M"
print(f"Checking model: {model}")

try:
    # We just want to check if the model is recognized/mapped
    # LiteLLM.completion has a 'dry_run' or similar? 
    # Or just check if it's in the mapped models.
    # Actually, let's just try to get the model info.
    
    # Simple check for model support
    from litellm import model_cost
    if model in model_cost:
        print(f"Model {model} found in model_cost")
    else:
        print(f"Model {model} NOT found in model_cost (this is common for local models)")

    # Try a minimal completion with a very short timeout
    response = litellm.completion(
        model=model,
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=1
    )
    print("Success!")
    print(response)
except Exception as e:
    print(f"Error: {e}")
