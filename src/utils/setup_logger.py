import os
import logging
from pathlib import Path

def setup_logger(logger_name: str, subfolder: str = None) -> logging.Logger:
    """
    Set up a logger with file and console handlers.
    
    Args:
        logger_name (str): Name of the logger (e.g., 'spell_scraper', 'item_scraper')
        subfolder (str, optional): Subfolder name in logs directory (e.g., 'data-extraction')
    
    Returns:
        logging.Logger: Configured logger instance
    
    Example:
        >>> logger = setup_logger('spell_scraper', 'data-extraction')
        >>> logger.info("Starting spell scraping...")
    """
    # Get the project root directory (3 levels up from this file)
    project_root = Path(__file__).parent.parent.parent
    logs_dir = project_root / 'logs'

    # Create main logs directory if it doesn't exist
    logs_dir.mkdir(exist_ok=True)

    # Create subfolder if specified
    if subfolder:
        logs_dir = logs_dir / subfolder
        logs_dir.mkdir(exist_ok=True)

    # Create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    # Prevent adding handlers multiple times
    if not logger.handlers:
        # Create file handler
        log_file = logs_dir / f"{logger_name}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Create formatters and add them to the handlers
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )

        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)

        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

def get_logger(logger_name: str) -> logging.Logger:
    """
    Get an existing logger by name. If it doesn't exist, returns a new logger.
    
    Args:
        logger_name (str): Name of the logger to retrieve
    
    Returns:
        logging.Logger: Requested logger instance
    """
    return logging.getLogger(logger_name)

