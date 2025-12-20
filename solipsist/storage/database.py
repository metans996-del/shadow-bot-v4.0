"""Работа с базой данных SQLite."""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from .models import SolipsistState, Comment, Monologue, Manifest


class Database:
    """Класс для работы с базой данных."""

    def __init__(self, db_path: str):
        """Инициализация подключения к БД."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Инициализировать таблицы БД."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Таблица состояний
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                certainty_level REAL NOT NULL,
                intrusion_level REAL NOT NULL,
                self_coherence REAL NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

        # Таблица комментариев
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                comment_id TEXT PRIMARY KEY,
                post_id TEXT NOT NULL,
                author_id TEXT NOT NULL,
                text TEXT,
                image_url TEXT,
                video_url TEXT,
                timestamp TEXT NOT NULL,
                classified_as TEXT,
                intrusion_score REAL,
                responded INTEGER DEFAULT 0,
                response_text TEXT
            )
        """)

        # Таблица монологов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monologues (
                monologue_id TEXT PRIMARY KEY,
                thoughts TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

        # Таблица манифестов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS manifests (
                manifest_id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                published INTEGER DEFAULT 0,
                published_at TEXT,
                timestamp TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def save_state(self, state: SolipsistState):
        """Сохранить состояние."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO states (certainty_level, intrusion_level, self_coherence, timestamp)
            VALUES (?, ?, ?, ?)
        """, (
            state.certainty_level,
            state.intrusion_level,
            state.self_coherence,
            state.timestamp.isoformat()
        ))

        conn.commit()
        conn.close()

    def get_latest_state(self) -> Optional[SolipsistState]:
        """Получить последнее состояние."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT certainty_level, intrusion_level, self_coherence, timestamp
            FROM states
            ORDER BY timestamp DESC
            LIMIT 1
        """)

        row = cursor.fetchone()
        conn.close()

        if row:
            return SolipsistState(
                certainty_level=row[0],
                intrusion_level=row[1],
                self_coherence=row[2],
                timestamp=datetime.fromisoformat(row[3])
            )
        return None

    def save_comment(self, comment: Comment):
        """Сохранить комментарий."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO comments
            (comment_id, post_id, author_id, text, image_url, video_url, timestamp,
             classified_as, intrusion_score, responded, response_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            comment.comment_id,
            comment.post_id,
            comment.author_id,
            comment.text,
            comment.image_url,
            comment.video_url,
            comment.timestamp.isoformat(),
            comment.classified_as,
            comment.intrusion_score,
            1 if comment.responded else 0,
            comment.response_text
        ))

        conn.commit()
        conn.close()

    def get_comment(self, comment_id: str) -> Optional[Comment]:
        """Получить комментарий по ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT comment_id, post_id, author_id, text, image_url, video_url,
                   timestamp, classified_as, intrusion_score, responded, response_text
            FROM comments
            WHERE comment_id = ?
        """, (comment_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return Comment(
                comment_id=row[0],
                post_id=row[1],
                author_id=row[2],
                text=row[3],
                image_url=row[4],
                video_url=row[5],
                timestamp=datetime.fromisoformat(row[6]) if row[6] else None,
                classified_as=row[7],
                intrusion_score=row[8],
                responded=bool(row[9]),
                response_text=row[10]
            )
        return None

    def save_monologue(self, monologue: Monologue):
        """Сохранить монолог."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO monologues (monologue_id, thoughts, timestamp)
            VALUES (?, ?, ?)
        """, (
            monologue.monologue_id,
            json.dumps(monologue.thoughts),
            monologue.timestamp.isoformat()
        ))

        conn.commit()
        conn.close()

    def get_recent_monologues(self, limit: int = 10) -> List[Monologue]:
        """Получить последние монологи."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT monologue_id, thoughts, timestamp
            FROM monologues
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        monologues = []
        for row in rows:
            monologues.append(Monologue(
                monologue_id=row[0],
                thoughts=json.loads(row[1]),
                timestamp=datetime.fromisoformat(row[2])
            ))
        return monologues

    def save_manifest(self, manifest: Manifest):
        """Сохранить манифест."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO manifests
            (manifest_id, content, published, published_at, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            manifest.manifest_id,
            manifest.content,
            1 if manifest.published else 0,
            manifest.published_at.isoformat() if manifest.published_at else None,
            manifest.timestamp.isoformat()
        ))

        conn.commit()
        conn.close()

    def get_unpublished_manifests(self) -> List[Manifest]:
        """Получить неопубликованные манифесты."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT manifest_id, content, published, published_at, timestamp
            FROM manifests
            WHERE published = 0
            ORDER BY timestamp ASC
        """)

        rows = cursor.fetchall()
        conn.close()

        manifests = []
        for row in rows:
            manifests.append(Manifest(
                manifest_id=row[0],
                content=row[1],
                published=bool(row[2]),
                published_at=datetime.fromisoformat(row[3]) if row[3] else None,
                timestamp=datetime.fromisoformat(row[4])
            ))
        return manifests



