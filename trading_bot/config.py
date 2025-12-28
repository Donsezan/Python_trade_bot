import yaml
import os
from typing import Dict, Any
from pathlib import Path

class Config:
    """A class to manage the application's configuration."""

    def __init__(self, config_path: str = None):
        if config_path is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.environ.get('CONFIG_PATH', os.path.join(project_root, 'config.yaml'))
        
        print(f"DEBUG: Loading config from {config_path}")

        try:
            cfg_path = Path(config_path)
            if not cfg_path.is_absolute():
                cfg_path = Path(__file__).resolve().parent / cfg_path
            with cfg_path.open('r') as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Warning: Configuration file not found at {config_path}. Using empty config.")
            self.config = {}
        except yaml.YAMLError as e:
            raise Exception(f"Error parsing YAML file: {e}")

    def get_llm_provider(self) -> str:
        """Get the configured LLM provider."""
        return self.config.get('llm_provider', 'native')

    def get_llm_config(self) -> Dict[str, Any]:
        """Get the configuration for the selected LLM provider."""
        provider = self.get_llm_provider()
        return self.config.get(provider, {})

    def get_binance_config(self) -> Dict[str, Any]:
        """Get the Binance API configuration."""
        return self.config.get('binance', {})

    def get_trading_config(self) -> Dict[str, Any]:
        """Get the trading parameters."""
        return self.config.get('trading', {})

    def get_database_config(self) -> Dict[str, Any]:
        """Get the database configuration."""
        return self.config.get('database', {})

    def get_news_config(self) -> Dict[str, Any]:
        """Get the news sources configuration."""
        return self.config.get('news', {})

    def get_risk_management_config(self) -> Dict[str, Any]:
        """Get the risk management settings."""
        return self.config.get('risk_management', {})

config = Config()
