
import json
import os
from typing import Any, Optional

class ConfigManager:
    """Centralized configuration management using JSON"""
    
    _instance = None
    _config = {}
    _config_file = "config.json"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance
    
    def _load(self):
        """Load configuration from JSON file or create with defaults"""
        defaults = {
            "camera_source": "0",
            "model_path": "models/yolo11l.pt",
            "confidence_threshold": 0.5,
            "db_host": "localhost",
            "db_port": 5432,
            "db_name": "DroneDetectionDB",
            "db_user": "postgres",
            "db_password": ""
        }
        
        if os.path.exists(self._config_file):
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    defaults.update(loaded)
            except (json.JSONDecodeError, IOError):
                # If file is corrupted, use defaults and overwrite
                self._save(defaults)
        
        self._config = defaults
        self._build_connection_string()
    
    def _save(self, config: dict):
        """Save configuration to file"""
        with open(self._config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    
    def _build_connection_string(self):
        """Build PostgreSQL connection string from config"""
        self._config["db_connection_string"] = (
            f"postgresql://{self._config['db_user']}:{self._config['db_password']}"
            f"@{self._config['db_host']}:{self._config['db_port']}/{self._config['db_name']}"
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value and save"""
        self._config[key] = value
        if key in ["db_host", "db_port", "db_name", "db_user", "db_password"]:
            self._build_connection_string()
        self._save(self._config)
    
    def set_all(self, settings: dict):
        """Set multiple configuration values at once"""
        self._config.update(settings)
        self._build_connection_string()
        self._save(self._config)
    
    def reload(self):
        """Reload configuration from file"""
        self._load()
    
    @property
    def connection_string(self) -> str:
        """Get PostgreSQL connection string"""
        return self._config.get("db_connection_string", "")
    
    @property
    def camera_source(self) -> str:
        return str(self._config.get("camera_source", "0"))
    
    @property
    def model_path(self) -> str:
        return str(self._config.get("model_path", "yolo11l.pt"))
    
    @property
    def confidence_threshold(self) -> float:
        return float(self._config.get("confidence_threshold", 0.5))

# Global instance
config = ConfigManager()