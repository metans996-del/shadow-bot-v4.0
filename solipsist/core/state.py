"""Система управления состояниями бота."""
import logging
from typing import Optional
from datetime import datetime

from ..storage.database import Database
from ..storage.models import SolipsistState

logger = logging.getLogger(__name__)


class StateManager:
    """Менеджер состояний бота."""

    def __init__(self, database: Database):
        """Инициализация менеджера состояний."""
        self.db = database
        self._current_state: Optional[SolipsistState] = None
        self._load_state()

    def _load_state(self):
        """Загрузить последнее состояние из БД."""
        state = self.db.get_latest_state()
        if state:
            self._current_state = state
        else:
            # Инициализировать начальное состояние
            from ..config.loader import load_config
            config = load_config()
            state_config = config.get("state", {})

            self._current_state = SolipsistState(
                certainty_level=state_config.get("initial_certainty", 0.3),
                intrusion_level=state_config.get("initial_intrusion", 0.1),
                self_coherence=state_config.get("initial_coherence", 0.9),
                timestamp=datetime.now()
            )
            self.save_state()

    @property
    def certainty_level(self) -> float:
        """Уровень уверенности в существовании реальности."""
        return self._current_state.certainty_level if self._current_state else 0.3

    @property
    def intrusion_level(self) -> float:
        """Уровень давления внешних сигналов."""
        return self._current_state.intrusion_level if self._current_state else 0.1

    @property
    def self_coherence(self) -> float:
        """Ощущение непрерывности собственного 'я'."""
        return self._current_state.self_coherence if self._current_state else 0.9

    def update_after_comment(
        self,
        intrusion_score: float,
        classified_as: str
    ):
        """Обновить состояние после обработки комментария."""
        if not self._current_state:
            self._load_state()

        # Увеличить уровень вторжения
        new_intrusion = min(1.0, self.intrusion_level + intrusion_score * 0.2)

        # В зависимости от классификации изменять certainty
        if classified_as == "observer":
            # Наблюдатель - снижает уверенность
            new_certainty = max(0.0, self.certainty_level - 0.1)
        elif classified_as == "provocation":
            # Провокация - может увеличить уверенность (как сопротивление)
            new_certainty = min(1.0, self.certainty_level + 0.05)
        else:
            # Эхо или шум - слабое влияние
            new_certainty = max(0.0, self.certainty_level - 0.02)

        # Coherence может снижаться при высоком intrusion
        if new_intrusion > 0.7:
            new_coherence = max(0.5, self.self_coherence - 0.1)
        else:
            # Медленное восстановление
            new_coherence = min(1.0, self.self_coherence + 0.01)

        self._current_state = SolipsistState(
            certainty_level=new_certainty,
            intrusion_level=new_intrusion,
            self_coherence=new_coherence,
            timestamp=datetime.now()
        )

        self.save_state()

    def update_after_monologue(self):
        """Обновить состояние после монолога."""
        if not self._current_state:
            self._load_state()

        # Монолог восстанавливает coherence
        new_coherence = min(1.0, self.self_coherence + 0.05)

        # Небольшое снижение intrusion (размышление помогает)
        new_intrusion = max(0.0, self.intrusion_level - 0.05)

        self._current_state = SolipsistState(
            certainty_level=self.certainty_level,
            intrusion_level=new_intrusion,
            self_coherence=new_coherence,
            timestamp=datetime.now()
        )

        self.save_state()

    def reset_after_publication(self):
        """Частично сбросить состояние после публикации."""
        if not self._current_state:
            self._load_state()

        from ..config.loader import load_config
        config = load_config()
        decay_rate = config.get("state.decay_rate", 0.02)

        # Частичный сброс intrusion
        new_intrusion = max(0.1, self.intrusion_level * (1 - decay_rate))

        self._current_state = SolipsistState(
            certainty_level=self.certainty_level,
            intrusion_level=new_intrusion,
            self_coherence=self.self_coherence,
            timestamp=datetime.now()
        )

        self.save_state()

    def save_state(self):
        """Сохранить текущее состояние в БД."""
        if self._current_state:
            self.db.save_state(self._current_state)

    def get_state_context(self) -> str:
        """Получить текстовое описание состояния для контекста."""
        return (
            f"Уверенность в реальности: {self.certainty_level:.2f}, "
            f"Уровень вторжения: {self.intrusion_level:.2f}, "
            f"Целостность 'я': {self.self_coherence:.2f}"
        )


