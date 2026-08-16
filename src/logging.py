import os
import logging
from pathlib import Path


def get_root_path(current_file_path: Path = Path(__file__)) -> Path:
    """
    Returns the project root path (parent of the src directory)
    """
    return current_file_path.parent.parent


def log_message(logger_name: str, log_file_name: str) -> logging.Logger:

    # Check if the "logs" directory exists
    log_dir = 'logs'
    os.makedirs(get_root_path() / log_dir, exist_ok=True)

    # logging configuration
    logger: logging.Logger = logging.getLogger(logger_name)
    logger.setLevel('DEBUG')

    console_handler = logging.StreamHandler()
    console_handler.setLevel('DEBUG')

    log_file_path: str = f'{get_root_path()}/{log_dir}/{log_file_name}'

    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel('DEBUG')

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger


# calling the logging function
logger: logging.Logger = log_message('lauki-telecom-agent', 'agent.log')
