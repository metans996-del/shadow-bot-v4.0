"""Анализ текста комментариев."""
import json
import logging
import re
from typing import Dict, Any, Optional

from ..services.llm import OpenRouterClient
from ..utils.text import clean_text

logger = logging.getLogger(__name__)


class TextPerception:
    """Анализатор текста."""

    def __init__(self, llm_client: OpenRouterClient):
        """Инициализация анализатора."""
        self.llm = llm_client

    def analyze(self, text: str) -> Dict[str, Any]:
        """Проанализировать текст комментария."""
        if not text:
            return {
                "content": "",
                "sentiment": "neutral",
                "themes": [],
                "pressure": 0.0,
                "word_count": 0,
                "char_count": 0
            }

        cleaned = clean_text(text)

        # Базовая статистика
        word_count = len(cleaned.split())
        char_count = len(cleaned)

        # LLM анализ текста
        analysis_result = self._analyze_with_llm(cleaned)

        # Объединяем базовую информацию с результатами LLM анализа
        result = {
            "content": cleaned,
            "word_count": word_count,
            "char_count": char_count,
            "sentiment": analysis_result.get("sentiment", "neutral"),
            "themes": analysis_result.get("themes", []),
            "pressure": analysis_result.get("pressure", 0.0)
        }

        return result

    def _analyze_with_llm(self, text: str) -> Dict[str, Any]:
        """Выполнить глубокий анализ текста через LLM."""
        prompt = f"""Проанализируй текст:
- эмоциональный тон
- ключевые темы
- степень агрессии или давления
Ответ в JSON.

Текст: {text}

Верни JSON в формате:
{{
  "sentiment": "negative" | "neutral" | "positive",
  "themes": ["тема1", "тема2"],
  "pressure": 0.0-1.0
}}"""

        response = None
        try:
            response = self.llm.think(prompt)

            if not response:
                logger.warning("LLM text analysis failed, using defaults")
                return {"sentiment": "neutral", "themes": [], "pressure": 0.0}

            # Извлечь JSON из ответа
            json_str = self._extract_json(response)

            if not json_str:
                logger.warning(f"Could not extract JSON from LLM response. Response: {response[:200]}")
                return {"sentiment": "neutral", "themes": [], "pressure": 0.0}

            # Парсим JSON
            data = json.loads(json_str)

            # Валидация и нормализация данных
            sentiment = data.get("sentiment", "neutral")
            if sentiment not in ["negative", "neutral", "positive"]:
                sentiment = "neutral"

            themes = data.get("themes", [])
            if not isinstance(themes, list):
                themes = []

            pressure = float(data.get("pressure", 0.0))
            # Ограничить давление до [0.0, 1.0]
            pressure = max(0.0, min(1.0, pressure))

            return {
                "sentiment": sentiment,
                "themes": themes,
                "pressure": pressure
            }

        except json.JSONDecodeError as e:
            response_preview = response[:200] if response else "No response"
            logger.warning(f"Failed to parse JSON from LLM response: {e}. Response: {response_preview}")
            return {"sentiment": "neutral", "themes": [], "pressure": 0.0}
        except Exception as e:
            logger.error(f"Error in LLM text analysis: {e}", exc_info=True)
            return {"sentiment": "neutral", "themes": [], "pressure": 0.0}

    def _extract_json(self, text: str) -> Optional[str]:
        """Извлечь JSON из текста ответа LLM."""
        # Сначала попробовать найти JSON в markdown блоке
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()

        # Попробовать найти JSON объект
        start_idx = text.find('{')
        if start_idx == -1:
            return None

        # Подсчитываем скобки для правильного извлечения вложенных объектов
        brace_count = 0
        end_idx = start_idx

        for i in range(start_idx, len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i + 1
                    break

        if brace_count == 0:
            return text[start_idx:end_idx].strip()

        return None

