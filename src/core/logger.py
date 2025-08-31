"""
Unified logging system for honeypot activities
"""

import os
import json
import logging
import logging.handlers
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from .config import config_manager


class HoneypotLogger:
    """Centralized logging system for honeypot activities"""

    def __init__(self):
        self.loggers: Dict[str, logging.Logger] = {}
        self._setup_loggers()

    def _setup_loggers(self) -> None:
        """Setup different loggers based on configuration"""
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)

        # Main logger
        main_logger = logging.getLogger('honeypot')
        main_logger.setLevel(getattr(logging, config_manager.get('global.log_level', 'INFO')))

        # File handler
        if config_manager.get('logging.file.enabled', True):
            log_path = config_manager.get('logging.file.path', 'logs/honeypot.log')
            file_handler = logging.handlers.RotatingFileHandler(
                log_path,
                maxBytes=self._parse_size(config_manager.get('logging.file.max_size', '100MB')),
                backupCount=config_manager.get('logging.file.backup_count', 5)
            )
            file_handler.setFormatter(logging.Formatter(
                config_manager.get('logging.file.format',
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ))
            main_logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        main_logger.addHandler(console_handler)

        self.loggers['main'] = main_logger

        # JSON logger for structured data
        if config_manager.get('logging.json.enabled', True):
            json_logger = logging.getLogger('honeypot_json')
            json_logger.setLevel(logging.INFO)

            json_path = config_manager.get('logging.json.path', 'logs/attacks.json')
            json_handler = logging.handlers.RotatingFileHandler(
                json_path, maxBytes=100*1024*1024, backupCount=5
            )
            json_handler.setFormatter(JSONFormatter())
            json_logger.addHandler(json_handler)

            self.loggers['json'] = json_logger

    def _parse_size(self, size_str: str) -> int:
        """Parse size string like '100MB' to bytes"""
        size_str = size_str.upper()
        if size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)

    def get_logger(self, name: str = 'main') -> logging.Logger:
        """Get logger instance"""
        return self.loggers.get(name, self.loggers['main'])

    def log_attack(self, attack_data: Dict[str, Any]) -> None:
        """Log attack information in structured format"""
        attack_data['timestamp'] = datetime.utcnow().isoformat()

        # Log to main logger
        main_logger = self.get_logger('main')
        main_logger.warning(f"Attack detected: {attack_data.get('service', 'unknown')} "
                          f"from {attack_data.get('source_ip', 'unknown')}")

        # Log structured data
        if 'json' in self.loggers:
            json_logger = self.get_logger('json')
            json_logger.info("Attack data", extra={'attack_data': attack_data})


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage()
        }

        # Add attack data if present
        if hasattr(record, 'attack_data'):
            log_data.update(record.attack_data)

        return json.dumps(log_data)


# Global logger instance
logger = HoneypotLogger()
