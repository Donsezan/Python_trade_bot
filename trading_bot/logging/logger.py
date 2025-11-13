import logging
import yaml
import os

def setup_logger():
    """Set up the logger to write to a file and the console."""
    # Go up two levels from the current file to get to the project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, '..', 'config.yaml')

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    log_config = config.get('logging', {})
    log_file = log_config.get('log_file', 'bot.log')
    log_level = log_config.get('log_level', 'INFO')

    logger = logging.getLogger('trading_bot')
    logger.setLevel(log_level)

    # Create handlers
    log_file_path = os.path.join(project_root,'..', log_file)
    file_handler = logging.FileHandler(log_file_path)
    console_handler = logging.StreamHandler()

    # Create formatters and add it to handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

logger = setup_logger()
