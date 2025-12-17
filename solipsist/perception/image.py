"""Анализ изображений."""
import logging
from typing import Dict, Any, Optional

from ..services.llm import OpenRouterClient

logger = logging.getLogger(__name__)


class ImagePerception:
    """Анализатор изображений."""

    def __init__(self, llm_client: OpenRouterClient):
        """Инициализация анализатора."""
        self.llm = llm_client

    def analyze(self, image_url: str) -> Dict[str, Any]:
        """Проанализировать изображение."""
        prompt = """Опиши это изображение кратко (2-3 предложения).
        Что на нём изображено? Какое настроение оно передаёт?"""

        description = self.llm.analyze_image(image_url, prompt)

        if description:
            return {
                "description": description,
                "has_content": True
            }
        else:
            return {
                "description": "Не удалось проанализировать изображение",
                "has_content": False
            }


