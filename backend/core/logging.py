"""
Logging configuration for Talktor backend
Supports both console and file logging with structured output
"""
import logging
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


def setup_logging(
    level: str = "INFO", 
    enable_file_logging: bool = True,
    log_directory: str = "logs",
    service_name: Optional[str] = None
) -> None:
    """
    Setup logging configuration for the application
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_file_logging: Whether to enable file logging
        log_directory: Directory to store log files
        service_name: Name of the service for log file naming
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatters
    console_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Create file handler if enabled
    if enable_file_logging:
        log_dir = Path(log_directory)
        log_dir.mkdir(exist_ok=True)
        
        # Generate timestamp for log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Determine service name
        if service_name is None:
            # Try to detect service from main module
            main_module = sys.modules.get('__main__')
            if main_module and hasattr(main_module, '__file__'):
                service_name = Path(main_module.__file__).stem
            else:
                service_name = "talktor"
        
        # Create log file path
        log_filename = f"{timestamp}_{service_name}.log"
        log_filepath = log_dir / log_filename
        
        # Create file handler
        file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # Log the log file location
        root_logger.info(f"📁 Log file created: {log_filepath}")
    
    # Set specific logger levels
    logger_levels = {
        'websocket': logging.WARNING,  # Reduce websocket noise
        'urllib3': logging.WARNING,    # Reduce HTTP noise
        'asyncio': logging.WARNING,    # Reduce asyncio noise
        'websockets': logging.WARNING, # Reduce websockets noise
    }
    
    for logger_name, logger_level in logger_levels.items():
        logging.getLogger(logger_name).setLevel(logger_level)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
