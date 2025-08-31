"""
Configuration management for Unified Honeypot
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """Manages configuration loading and validation"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._find_config_file()
        self.config: Dict[str, Any] = {}
        self.load_config()

    def _find_config_file(self) -> str:
        """Find configuration file in standard locations"""
        search_paths = [
            "config/default_config.yaml",
            "config/config.yaml",
            "../config/default_config.yaml",
            "../config/config.yaml"
        ]

        for path in search_paths:
            if os.path.exists(path):
                return path

        # Create default config if none exists
        return "config/default_config.yaml"

    def load_config(self) -> None:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"Configuration file not found: {self.config_path}")
            print("Creating default configuration...")
            self._create_default_config()
        except yaml.YAMLError as e:
            print(f"Error parsing configuration file: {e}")
            raise

    def _create_default_config(self) -> None:
        """Create default configuration file"""
        os.makedirs("config", exist_ok=True)
        default_config = {
            "global": {
                "hostname": "honeypot.local",
                "log_level": "INFO",
                "bind_address": "0.0.0.0",
                "max_connections": 1000,
                "connection_timeout": 300
            },
            "plugins": {},
            "logging": {
                "file": {
                    "enabled": True,
                    "path": "logs/honeypot.log"
                }
            }
        }

        with open(self.config_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)

        self.config = default_config

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated key"""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value by dot-separated key"""
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save_config(self) -> None:
        """Save current configuration to file"""
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)

    def get_enabled_plugins(self) -> Dict[str, Dict]:
        """Get all enabled plugins from configuration"""
        plugins = self.get('plugins', {})
        enabled_plugins = {}

        for plugin_name, plugin_config in plugins.items():
            if plugin_config.get('enabled', False):
                enabled_plugins[plugin_name] = plugin_config

        return enabled_plugins


# Global configuration instance
config_manager = ConfigManager()
