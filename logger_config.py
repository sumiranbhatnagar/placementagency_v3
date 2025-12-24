import logging
import streamlit as st
from datetime import datetime

def setup_logger(name: str):
    """
    Creates or returns a logger that works on Streamlit Cloud.
    Uses StreamHandler instead of FileHandler (no disk writes).
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
    
    # ✅ Use StreamHandler instead of FileHandler (works on cloud)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(log_format)
    logger.addHandler(stream_handler)
    
    # Prevent logs from propagating
    logger.propagate = False
    
    return logger

# Initialize globally
logger = setup_logger("PlacementAgency")
