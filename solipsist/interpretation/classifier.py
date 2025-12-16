"""Классификация комментариев."""
import logging
from typing import Dict, Any, Optional

from ..services.llm import OpenRouterClient
from ..storage.database import Database

logger = logging.getLogger(__name__)


class CommentClassifier:
    """Классификатор комментариев."""

    CLASS_TYPES = ["observer", "echo", "provocation", "noise"]

    def __init__(self, llm_client: OpenRouterClient, database: Optional[Database] = None):
        """Инициализация классификатора."""
        self.llm = llm_client
        self.db = database

    def classify(
        self,
        text: str,
        perception_data: Dict[str, Any]
    ) -> str:
        """Классифицировать комментарий с помощью LLM."""
        if not text or not text.strip():
            return "noise"

        # Получить последние монологи для определения echo
        recent_monologues = []
        if self.db:
            try:
                recent_monologues = self.db.get_recent_monologues(limit=5)
            except Exception as e:
                logger.warning(f"Failed to get recent monologues: {e}")

        # Формируем промпт для классификации
        prompt = self._build_classification_prompt(text, recent_monologues)

        # Выполняем классификацию через LLM
        result = self.llm.think(prompt)

        if not result:
            logger.warning("LLM classification failed, falling back to noise")
            return "noise"

        # Извлекаем классификацию из ответа (должно быть одно слово)
        classification = result.strip().lower()

        # Очищаем ответ от лишних символов и берем первое слово
        words = classification.split()
        if words:
            classification = words[0].rstrip('.,!?;:')
        else:
            classification = "noise"

        # Валидация результата
        if classification not in self.CLASS_TYPES:
            logger.warning(f"Invalid classification '{classification}' (full response: '{result}'), defaulting to noise")
            return "noise"

        logger.info(f"Classified comment as: {classification}")
        return classification

    def _build_classification_prompt(self, text: str, monologues: list) -> str:
        """Построить промпт для классификации."""
        prompt = """Ты — модуль классификации сознания.
Классифицируй комментарий строго как один из вариантов:
observer — прямое обращение к субъекту
echo — повтор или развитие ранее опубликованных мыслей
provocation — сомнение в реальности или существовании субъекта
noise — бессвязный или нерелевантный шум

Ответь одним словом.
Комментарий: {comment_text}"""

        # Если есть монологи, добавляем их для определения echo
        if monologues:
            monologues_text = "\n\nРанее опубликованные мысли:\n"
            for monologue in monologues:
                thoughts = monologue.thoughts
                # Объединяем мысли монолога
                thoughts_text = " ".join(thoughts)
                monologues_text += f"- {thoughts_text}\n"

            prompt = prompt.replace(
                "Комментарий: {comment_text}",
                f"{monologues_text}\nКомментарий: {{comment_text}}"
            )

        prompt = prompt.format(comment_text=text)
        return prompt

