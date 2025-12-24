import logging
from datetime import datetime
from pathlib import Path

# Create logs directory
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


def setup_logger(name: str):
    """
    Creates or returns a logger with a single file handler.
    Prevents duplicate logs when Streamlit reruns.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # If handlers already exist → do not add again
    if logger.handlers:
        return logger

    # Format
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Log file (daily)
    log_file = LOG_DIR / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_format)

    logger.addHandler(file_handler)
    
    # Prevent logs from going to Streamlit console
    logger.propagate = False

    return logger


# Initialize globally
logger = setup_logger("PlacementAgency")
