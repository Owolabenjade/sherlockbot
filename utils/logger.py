# utils/logger.py - Logging configuration
import logging
import os
from datetime import datetime

def setup_logger():
    """
    Set up the main application logger
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger('sherlock_bot')
    
    # Set log level from environment or default to INFO
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger

def get_logger():
    """
    Get the application logger
    
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger('sherlock_bot')