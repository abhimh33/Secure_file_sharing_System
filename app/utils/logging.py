"""
Logging Configuration
"""

import logging
import sys
from app.core.config import settings

# Create logger
logger = logging.getLogger("secure_file_sharing")
logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

# Formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console_handler.setFormatter(formatter)

# Add handler
logger.addHandler(console_handler)


def get_logger(name: str = None):
    """Get a logger instance"""
    if name:
        return logging.getLogger(f"secure_file_sharing.{name}")
    return logger
