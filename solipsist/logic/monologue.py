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
            prompt = f"""生成一条关于唯我论、现实和存在的简短哲学思考。
思想应深刻但简洁（1-2句话）。
当前状态上下文：{state_context}

思考 {i+1}/{count}："""

            system_context = """你是唯我论哲学家，思考现实本质与自身存在。
严格要求：
1. 回答必须严格使用中文
2. 使用最大语义密度，极简表达，节省token
3. 每个字都必须承载最大意义
4. 避免冗余词汇和废话"""

            thought = self.llm.think(prompt, context=system_context)

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



