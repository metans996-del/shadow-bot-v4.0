"""Конфигурация проекта."""
import json
import os
from pathlib import Path
from typing import Dict, Any


class Config:
    """Класс для загрузки и хранения конфигурации."""

    def __init__(self, config_path: str = None):
        """Инициализация конфигурации."""
        if config_path is None:
            config_path = Path(__file__).parent / "config.json"

        with open(config_path, "r", encoding="utf-8") as f:
            self._data = json.load(f)

    def get(self, key: str, default: Any = None) -> Any:
        """Получить значение по ключу с поддержкой вложенных ключей."""
        keys = key.split(".")
        value = self._data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def __getitem__(self, key: str) -> Any:
        """Получить значение по ключу."""
        return self.get(key)

    @property
    def openrouter_api_key(self) -> str:
        """API ключ OpenRouter."""
        return self.get("openrouter.api_key")

    @property
    def openrouter_models(self) -> Dict[str, str]:
        """Модели OpenRouter."""
        return self.get("openrouter.models", {})

    @property
    def vk_token(self) -> str:
        """VK access token."""
        return self.get("vk.access_token")

    @property
    def vk_group_id(self) -> str:
        """VK group ID."""
        return self.get("vk.group_id")


# Глобальный экземпляр конфигурации
_config = None


def load_config(config_path: str = None) -> Config:
    """Загрузить конфигурацию."""
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config

