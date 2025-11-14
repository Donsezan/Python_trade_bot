import yaml
from typing import Dict, Any

class Config:
    """Loads and provides access to the application's configuration."""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the Config object.

        Args:
            config_path: The path to the configuration file.
        """
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load the configuration from a YAML file.

        Args:
            config_path: The path to the YAML configuration file.

        Returns:
            A dictionary containing the configuration.
        """
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise Exception(f"Configuration file not found at: {config_path}")
        except yaml.YAMLError as e:
            raise Exception(f"Error parsing configuration file: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.

        Args:
            key: The key to look up in the configuration.
            default: The default value to return if the key is not found.

        Returns:
            The configuration value.
        """
        return self.config.get(key, default)

    def get_binance_config(self) -> Dict[str, str]:
        """Get the Binance API configuration."""
        return self.get("binance", {})

    def get_llm_config(self) -> Dict[str, Dict[str, str]]:
        """Get the LLM API configurations."""
        return self.get("llms", {})

    def get_trading_config(self) -> Dict[str, Any]:
        """Get the trading parameters."""
        return self.get("trading", {})

    def get_database_config(self) -> Dict[str, str]:
        """Get the database settings."""
        return self.get("database", {})

    def get_news_config(self) -> Dict[str, Any]:
        """Get the news sources configuration."""
        return self.get("news", {})

    def get_risk_management_config(self) -> Dict[str, float]:
        """Get the risk management configuration."""
        return self.get("risk_management", {})

# Create a global config instance
config = Config()
