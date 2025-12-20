"""Анализ видео (через превью/кадры)."""
import logging
from typing import Dict, Any, Optional

from ..services.llm import OpenRouterClient

logger = logging.getLogger(__name__)


class VideoPerception:
    """Анализатор видео."""

    def __init__(self, llm_client: OpenRouterClient):
        """Инициализация анализатора."""
        self.llm = llm_client

    def analyze(self, video_url: str, preview_url: Optional[str] = None) -> Dict[str, Any]:
        """Проанализировать видео через превью."""
        # TODO: Реализовать извлечение кадра/превью из видео
        # Пока используем preview_url если доступен

        if preview_url:
            prompt = """Опиши этот кадр из видео кратко (2-3 предложения).
            Что на нём происходит? Какое настроение оно передаёт?"""

            description = self.llm.analyze_image(preview_url, prompt)

            if description:
                return {
                    "description": description,
                    "has_content": True,
                    "analysis_type": "preview"
                }

        return {
            "description": "Видео требует анализа кадров",
            "has_content": False,
            "analysis_type": "none"
        }



