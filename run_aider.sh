#!/bin/bash
# Helper script to run Aider with local Qwen
export OLLAMA_API_BASE=http://localhost:11434
python3 -m aider "$@"
