"""Оценка степени вторжения реальности."""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class IntrusionEvaluator:
    """Оценщик вторжения."""

    def __init__(self):
        """Инициализация оценщика."""
        pass

    def evaluate(
        self,
        classified_as: str,
        perception_data: Dict[str, Any],
        has_image: bool = False,
        has_video: bool = False
    ) -> float:
        """Оценить степень вторжения (0.0 - 1.0)."""
        base_scores = {
            "observer": 0.7,      # Высокое вторжение - прямое обращение
            "provocation": 0.6,   # Средне-высокое - попытка взаимодействия
            "echo": 0.3,          # Низкое - возможно эхо собственных мыслей
            "noise": 0.1          # Минимальное - фоновый шум
        }

        base_score = base_scores.get(classified_as, 0.2)

        # Увеличение за медиа-контент
        if has_image:
            base_score += 0.2
        if has_video:
            base_score += 0.3

        # Ограничить до [0.0, 1.0]
        return min(1.0, max(0.0, base_score))

