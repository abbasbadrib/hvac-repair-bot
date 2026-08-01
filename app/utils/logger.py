"""
Logging configuration.
"""

import logging
import sys
from app.config import Config

def setup_logger():
    """Setup logging configuration."""
    log_level = Config.get_log_level()
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('app.log')
        ]
    )
    
    # Set specific log levels
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.INFO)
    
    return logging.getLogger(__name__)
