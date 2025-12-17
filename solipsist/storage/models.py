"""Модели данных."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class SolipsistState:
    """Состояние бота."""
    certainty_level: float  # 0.0 - 1.0
    intrusion_level: float  # 0.0 - 1.0
    self_coherence: float   # 0.0 - 1.0
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь."""
        return {
            "certainty_level": self.certainty_level,
            "intrusion_level": self.intrusion_level,
            "self_coherence": self.self_coherence,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Comment:
    """Комментарий."""
    comment_id: str
    post_id: str
    author_id: str
    text: Optional[str]
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    timestamp: datetime = None
    classified_as: Optional[str] = None  # observer, echo, provocation, noise
    intrusion_score: Optional[float] = None
    responded: bool = False
    response_text: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь."""
        return {
            "comment_id": self.comment_id,
            "post_id": self.post_id,
            "author_id": self.author_id,
            "text": self.text,
            "image_url": self.image_url,
            "video_url": self.video_url,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "classified_as": self.classified_as,
            "intrusion_score": self.intrusion_score,
            "responded": self.responded,
            "response_text": self.response_text
        }


@dataclass
class Monologue:
    """Внутренний монолог."""
    monologue_id: str
    thoughts: List[str]
    timestamp: datetime

    def __post_init__(self):
        if not hasattr(self, 'timestamp') or self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь."""
        return {
            "monologue_id": self.monologue_id,
            "thoughts": self.thoughts,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Manifest:
    """Манифест (публикация)."""
    manifest_id: str
    content: str
    published: bool = False
    published_at: Optional[datetime] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь."""
        return {
            "manifest_id": self.manifest_id,
            "content": self.content,
            "published": self.published,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "timestamp": self.timestamp.isoformat()
        }


