"""Конфигурация проекта."""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


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
        """VK access token (deprecated, use vk_group_access_token)."""
        # Обратная совместимость
        return self.get("vk.access_token") or self.get("vk.group_access_token")

    @property
    def vk_group_id(self) -> str:
        """VK group ID."""
        group_id = self.get("vk.group_id")
        # Если group_id отрицательный, убираем минус для строки
        if isinstance(group_id, int) and group_id < 0:
            return str(abs(group_id))
        return str(group_id) if group_id else None

    @property
    def vk_group_access_token(self) -> str:
        """VK group access token (для публикаций от имени сообщества)."""
        return self.get("vk.group_access_token") or self.get("vk.access_token")

    @property
    def vk_user_access_token(self) -> str:
        """VK user access token (опционально, для чтения)."""
        return self.get("vk.user_access_token")

    @property
    def vk_creator_user_id(self) -> Optional[int]:
        """ID создателя группы (владельца)."""
        return self.get("vk.creator_user_id")


# Глобальный экземпляр конфигурации
_config = None


def load_config(config_path: str = None) -> Config:
    """Загрузить конфигурацию."""
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config

