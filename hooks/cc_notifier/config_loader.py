"""
Configuration loader for cc-notifier with YAML file support.
"""

import yaml
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from loguru import logger


# Default configuration paths
DEFAULT_CONFIG_DIR = Path.home() / ".config" / "cc-notifier"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.yaml"
DEFAULT_EXPORT_DIR = DEFAULT_CONFIG_DIR / "exports"


class NotificationConfig(BaseModel):
    """Notification-related configuration."""

    threshold_seconds: int = Field(
        default=10,
        ge=0,
        description="Minimum job duration in seconds to trigger notification (0 = notify all)"
    )
    sound: str = Field(
        default="default",
        description="Notification sound to use"
    )
    app_bundle: str = Field(
        default="dev.warp.Warp-Stable",
        description="Application bundle ID to focus on notification click"
    )


class DatabaseConfig(BaseModel):
    """Database-related configuration."""

    path: Path = Field(
        default=Path.home() / ".claude" / "hooks" / "cc_notifier" / "cc-notifier.db",
        description="Path to SQLite database file"
    )


class CleanupConfig(BaseModel):
    """Data cleanup configuration."""

    retention_days: int = Field(
        default=30,
        ge=1,
        description="Number of days to retain session data (older data will be auto-cleaned)"
    )
    auto_cleanup_enabled: bool = Field(
        default=True,
        description="Enable automatic cleanup of old data"
    )
    export_before_cleanup: bool = Field(
        default=True,
        description="Export data before cleanup"
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(
        default="INFO",
        description="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    path: Path = Field(
        default=Path.home() / ".claude" / "hooks" / "cc_notifier" / "cc-notifier.log",
        description="Path to log file"
    )

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate log level is valid."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()


class CCNotifierConfig(BaseModel):
    """Complete cc-notifier configuration."""

    notification: NotificationConfig = Field(default_factory=NotificationConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    cleanup: CleanupConfig = Field(default_factory=CleanupConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


class ConfigLoader:
    """Loads and manages cc-notifier configuration from YAML file."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize config loader.

        Args:
            config_path: Path to YAML config file (default: ~/.config/cc-notifier/config.yaml)
        """
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self._config: Optional[CCNotifierConfig] = None

    def load(self) -> CCNotifierConfig:
        """
        Load configuration from YAML file with fallback to defaults.

        Returns:
            CCNotifierConfig instance
        """
        if self._config is not None:
            return self._config

        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    yaml_data = yaml.safe_load(f) or {}
                self._config = CCNotifierConfig(**yaml_data)
                logger.debug(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config from {self.config_path}: {e}")
                logger.info("Using default configuration")
                self._config = CCNotifierConfig()
        else:
            logger.debug(f"No config file found at {self.config_path}, using defaults")
            self._config = CCNotifierConfig()

        return self._config

    def save(self, config: Optional[CCNotifierConfig] = None) -> None:
        """
        Save configuration to YAML file.

        Args:
            config: Configuration to save (default: current loaded config)
        """
        if config is None:
            if self._config is None:
                raise ValueError("No configuration loaded or provided to save")
            config = self._config

        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert Pydantic model to dict for YAML serialization
        config_dict = config.model_dump(mode='python')

        # Convert Path objects to strings
        def path_to_str(obj):
            if isinstance(obj, Path):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: path_to_str(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [path_to_str(v) for v in obj]
            return obj

        config_dict = path_to_str(config_dict)

        with open(self.config_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Configuration saved to {self.config_path}")

    def reset_to_defaults(self) -> CCNotifierConfig:
        """
        Reset configuration to defaults and save.

        Returns:
            Default CCNotifierConfig instance
        """
        self._config = CCNotifierConfig()
        self.save(self._config)
        logger.info("Configuration reset to defaults")
        return self._config

    @property
    def config(self) -> CCNotifierConfig:
        """Get current configuration (loads if not already loaded)."""
        if self._config is None:
            return self.load()
        return self._config


def get_config(config_path: Optional[Path] = None) -> CCNotifierConfig:
    """
    Convenience function to load configuration.

    Args:
        config_path: Optional custom config path

    Returns:
        CCNotifierConfig instance
    """
    loader = ConfigLoader(config_path)
    return loader.load()
