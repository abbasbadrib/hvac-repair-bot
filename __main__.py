"""
Entry point for Railway deployment.
"""
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.main import main
    print("✅ Successfully imported app.main")
except ImportError as e:
    print(f"❌ Error importing app.main: {e}")
    print("Current Python path:", sys.path)
    print("Files in app directory:", os.listdir("app") if os.path.exists("app") else "app directory not found")
    raise

if __name__ == "__main__":
    main()
