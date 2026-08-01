"""
Main runner for full bot.
"""
import sys
import os
import logging

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        logger.info("🚀 Starting HVAC Repair Bot...")
        from app.main import main
        logger.info("✅ Import successful")
        main()
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.info("⏳ Trying alternative import...")
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("main", "app/main.py")
            main_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(main_module)
            logger.info("✅ Direct import successful")
            main_module.main()
        except Exception as e2:
            logger.error(f"❌ All imports failed: {e2}")
            raise
