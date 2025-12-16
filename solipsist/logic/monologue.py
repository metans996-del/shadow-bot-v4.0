"""Генерация внутреннего монолога."""
import logging
import uuid
from datetime import datetime
from typing import List

from ..services.llm import OpenRouterClient
from ..storage.models import Monologue
from ..core.state import StateManager

logger = logging.getLogger(__name__)


class MonologueGenerator:
    """Генератор внутренних монологов."""

    def __init__(self, llm_client: OpenRouterClient, state_manager: StateManager):
        """Инициализация генератора."""
        self.llm = llm_client
        self.state = state_manager

    def generate(self, count: int = 3) -> Monologue:
        """Сгенерировать монолог из нескольких мыслей."""
        thoughts = []
        state_context = self.state.get_state_context()

        for i in range(count):
            prompt = f"""Сгенерируй одну короткую философскую мысль о солипсизме, реальности и существовании.
            Мысль должна быть глубокой, но краткой (1-2 предложения).
            Контекст текущего состояния: {state_context}

            Мысль {i+1} из {count}:"""

            thought = self.llm.think(prompt, context="Ты философ-солипсист, размышляющий о природе реальности и собственного существования.")

            if thought:
                thoughts.append(thought.strip())
            else:
                # Fallback мысль
                thoughts.append("Существую ли я? Или это тоже вопрос, заданный не мне?")

        monologue = Monologue(
            monologue_id=str(uuid.uuid4()),
            thoughts=thoughts,
            timestamp=datetime.now()
        )

        return monologue

