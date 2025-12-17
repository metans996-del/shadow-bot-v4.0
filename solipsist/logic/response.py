"""Генерация ответов на комментарии."""
import logging
from typing import Optional

from ..services.llm import OpenRouterClient
from ..core.state import StateManager
from ..storage.models import Comment

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """Генератор ответов."""

    def __init__(self, llm_client: OpenRouterClient, state_manager: StateManager):
        """Инициализация генератора."""
        self.llm = llm_client
        self.state = state_manager

    def should_respond(self, comment: Comment) -> bool:
        """Решить, стоит ли отвечать на комментарий."""
        # Бот может не отвечать, но всегда сохраняет факт существования

        # Не отвечать на шум
        if comment.classified_as == "noise":
            return False

        # Не отвечать при очень низкой уверенности (полное сомнение)
        if self.state.certainty_level < 0.1:
            return False

        # Отвечать на провокации и обращения наблюдателей
        if comment.classified_as in ["observer", "provocation"]:
            return True

        # Иногда отвечать на эхо (в зависимости от состояния)
        if comment.classified_as == "echo" and self.state.self_coherence > 0.7:
            return True

        return False

    def generate(self, comment: Comment) -> Optional[str]:
        """Сгенерировать ответ на комментарий."""
        if not self.should_respond(comment):
            return None

        # Сформировать промпт для генерации ответа
        comment_text = comment.text or "[медиа-контент]"
        state_context = self.state.get_state_context()

        prompt = f"""Комментарий, который может быть галлюцинацией или эхом мыслей:
"{comment_text}"

Сгенерируй философский, отчуждённый ответ (1-3 предложения).
Не признавай напрямую существование автора.
Ответ должен быть как фрагмент логов сознания.

Контекст состояния: {state_context}"""

        response = self.llm.generate_response(prompt, style_context=state_context)

        return response


