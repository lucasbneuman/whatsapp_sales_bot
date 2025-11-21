"""Configuration manager for loading and saving application settings."""

from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from database import crud
from utils.logging_config import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """Manager for application configuration."""

    DEFAULT_CONFIG = {
        # IMPORTANTE: Estos son valores VACÍOS por defecto
        # El bot NO debe responder hasta que se configure correctamente
        "system_prompt": "",
        "welcome_message": "",
        "payment_link": "",
        "response_delay_minutes": 0.5,  # Delay en minutos
        "text_audio_ratio": 0,
        "use_emojis": True,
        "tts_voice": "nova",
        "multi_part_messages": False,  # Enviar mensajes en múltiples partes
        "max_words_per_response": 100,  # Límite de palabras por respuesta
        # Producto/Servicio
        "product_name": "",
        "product_description": "",
        "product_features": "",
        "product_benefits": "",
        "product_price": "",
        "product_target_audience": "",
        # Prompts editables
        "welcome_prompt": "",
        "intent_prompt": "",
        "sentiment_prompt": "",
        "data_extraction_prompt": "",
        "closing_prompt": "",
    }

    def __init__(self):
        """Initialize configuration manager."""
        self._cache: Dict[str, Any] = {}
        logger.info("Config manager initialized")

    async def load_config(self, db: AsyncSession, key: str, default: Any = None) -> Any:
        """
        Load a configuration value.

        Args:
            db: Database session
            key: Configuration key
            default: Default value if not found

        Returns:
            Configuration value
        """
        # Check cache first
        if key in self._cache:
            return self._cache[key]

        # Load from database
        value = await crud.get_config(db, key)

        if value is None:
            # Use default or fall back to DEFAULT_CONFIG
            value = default if default is not None else self.DEFAULT_CONFIG.get(key)
            logger.info(f"Config '{key}' not found, using default: {value}")
        else:
            logger.info(f"Loaded config '{key}': {value}")

        # Cache it
        self._cache[key] = value
        return value

    async def save_config(self, db: AsyncSession, key: str, value: Any) -> None:
        """
        Save a configuration value.

        Args:
            db: Database session
            key: Configuration key
            value: Configuration value
        """
        await crud.set_config(db, key, value)
        self._cache[key] = value
        logger.info(f"Saved config '{key}': {value}")

    async def load_all_configs(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Load all configuration values.

        Args:
            db: Database session

        Returns:
            Dict of all configurations
        """
        configs = await crud.get_all_configs(db)

        # Merge with defaults (defaults for missing keys)
        for key, value in self.DEFAULT_CONFIG.items():
            if key not in configs:
                configs[key] = value

        # Update cache
        self._cache = configs.copy()

        logger.info(f"Loaded {len(configs)} configurations")
        return configs

    async def save_all_configs(self, db: AsyncSession, configs: Dict[str, Any]) -> None:
        """
        Save multiple configurations.

        Args:
            db: Database session
            configs: Dict of configurations to save
        """
        for key, value in configs.items():
            await self.save_config(db, key, value)

        logger.info(f"Saved {len(configs)} configurations")

    def get_cached(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value from cache.

        Args:
            key: Configuration key
            default: Default value if not in cache

        Returns:
            Cached value or default
        """
        return self._cache.get(key, default)

    def clear_cache(self) -> None:
        """Clear the configuration cache."""
        self._cache.clear()
        logger.info("Config cache cleared")

    async def initialize_defaults(self, db: AsyncSession) -> None:
        """
        Initialize default configurations in database if they don't exist.

        Args:
            db: Database session
        """
        for key, value in self.DEFAULT_CONFIG.items():
            existing = await crud.get_config(db, key)
            if existing is None:
                await crud.set_config(db, key, value)
                logger.info(f"Initialized default config '{key}': {value}")

        # Load all into cache
        await self.load_all_configs(db)


# Global instance (will be initialized in app.py)
config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global config manager instance."""
    global config_manager
    if config_manager is None:
        config_manager = ConfigManager()
    return config_manager
