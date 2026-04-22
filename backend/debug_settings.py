import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

try:
    from app.config import get_settings
    settings = get_settings()
    print(f"App Name: {settings.app_name}")
    print(f"Port: {settings.port}")
    print("Settings loaded successfully")
except Exception as e:
    print(f"Error: {e}")
