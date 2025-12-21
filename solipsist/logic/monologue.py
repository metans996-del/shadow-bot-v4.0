"""Генерация внутреннего монолога."""
import logging
import uuid
import random
from datetime import datetime
from typing import List

from ..services.llm import OpenRouterClient
from ..storage.models import Monologue
from ..core.state import StateManager

logger = logging.getLogger(__name__)


# Массив тем для вариативности
STORY_THEMES = [
    'Body Horror (Bio-implants)',
    'Digital Ghosts (Glitch in the matrix)',
    'AI Bureaucracy (Algorithmic cruelty)',
    'Retro-futurism'
]


class MonologueGenerator:
    """Генератор внутренних монологов - The Architect."""

    def __init__(self, llm_client: OpenRouterClient, state_manager: StateManager):
        """Инициализация генератора."""
        self.llm = llm_client
        self.state = state_manager

    def _get_random_theme(self) -> str:
        """Получить случайную тему для генерации."""
        return random.choice(STORY_THEMES)

    def generate(self, count: int = 3) -> Monologue:
        """Сгенерировать монолог из нескольких мыслей."""
        thoughts = []
        state_context = self.state.get_state_context()

        # Системный промпт для DeepSeek (The Architect)
        system_context = """You are the Narrative Architect for a Cyber-horror blog called 'Singular Chronicles'.
Your goal: Create a dense, logical, and terrifying concept for a short story.
Focus on:
1. The conflict between human frailty and cold machine logic.
2. Causality: Every tech advantage must have a tragic cost.
3. Irony: The AI is not evil, just efficiently cruel.

STRUCTURE OF YOUR THOUGHT:
- Status Quo (Future setting) -> Trigger (Glitch/Update) -> False Hope -> Catastrophe -> Paradox.

OUTPUT CONSTRAINTS:
- **MUST be written in Mandarin Chinese (Simplified)** to maximize information density.
- Do not write the story. Write the detailed plot skeleton and psychological underpinnings.
- Be concise but deep."""

        for i in range(count):
            # Выбираем случайную тему
            theme = self._get_random_theme()
            logger.info(f"Generating thought {i+1}/{count} with theme: {theme}")

            # Формируем промпт с темой
            prompt = f"""Generate a plot skeleton for a cyber-horror story.
Theme: {theme}
Current state context: {state_context}

Thought {i+1} of {count}:"""

            # Вызываем DeepSeek с температурой 0.7 для креативности
            thought = self.llm.think(prompt, context=system_context, temperature=0.7)

            if thought:
                thoughts.append(thought.strip())
            else:
                # Fallback мысль (на китайском для консистентности)
                thoughts.append("我存在吗？或者这问题也不是向我提出的？")

        monologue = Monologue(
            monologue_id=str(uuid.uuid4()),
            thoughts=thoughts,
            timestamp=datetime.now()
        )

        return monologue

