"""Главный оркестратор бота."""
import logging
import uuid
from datetime import datetime
from typing import Optional

from ..config.loader import load_config
from ..services.llm import OpenRouterClient
from ..services.vk import VKClient
from ..storage.database import Database
from ..storage.models import Comment
from ..perception.text import TextPerception
from ..perception.image import ImagePerception
from ..perception.video import VideoPerception
from ..interpretation.classifier import CommentClassifier
from ..interpretation.intrusion import IntrusionEvaluator
from ..logic.monologue import MonologueGenerator
from ..logic.response import ResponseGenerator
from ..logic.revelation import ManifestGenerator
from .state import StateManager

logger = logging.getLogger(__name__)


class SolipsistBot:
    """Главный класс бота."""

    def __init__(self):
        """Инициализация бота."""
        self.config = load_config()

        # Инициализация сервисов
        self.llm = OpenRouterClient()
        self.vk = VKClient()
        self.db = Database(self.config.get("database.path", "memory/solipsist.db"))

        # Инициализация менеджера состояний
        self.state = StateManager(self.db)

        # Инициализация модулей восприятия
        self.text_perception = TextPerception(self.llm)
        self.image_perception = ImagePerception(self.llm)
        self.video_perception = VideoPerception(self.llm)

        # Инициализация интерпретации
        self.classifier = CommentClassifier(self.llm, self.db)
        self.intrusion_evaluator = IntrusionEvaluator()

        # Инициализация логики
        self.monologue_generator = MonologueGenerator(self.llm, self.state)
        self.response_generator = ResponseGenerator(self.llm, self.state)
        self.manifest_generator = ManifestGenerator(self.llm, self.vk, self.db, self.state)

        logger.info("SolipsistBot initialized")

    def process_comment(self, comment_data: dict) -> Optional[str]:
        """Обработать комментарий через полный пайплайн."""
        try:
            # Создать объект комментария
            # Использовать timestamp из данных, если есть, иначе текущее время
            comment_timestamp = comment_data.get("timestamp")
            if isinstance(comment_timestamp, datetime):
                timestamp = comment_timestamp
            elif isinstance(comment_timestamp, (int, float)):
                timestamp = datetime.fromtimestamp(comment_timestamp)
            else:
                timestamp = datetime.now()

            comment = Comment(
                comment_id=str(comment_data.get("id", uuid.uuid4())),
                post_id=str(comment_data.get("post_id", "")),
                author_id=str(comment_data.get("author_id", "")),
                text=comment_data.get("text"),
                image_url=comment_data.get("image_url"),
                video_url=comment_data.get("video_url"),
                timestamp=timestamp
            )

            logger.info(f"Processing comment {comment.comment_id}")

            # Перцепция
            perception_data = {}
            if comment.text:
                perception_data["text"] = self.text_perception.analyze(comment.text)

            if comment.image_url:
                perception_data["image"] = self.image_perception.analyze(comment.image_url)

            if comment.video_url:
                perception_data["video"] = self.video_perception.analyze(comment.video_url)

            # Интерпретация
            classified_as = self.classifier.classify(comment.text or "", perception_data.get("text", {}))
            comment.classified_as = classified_as

            intrusion_score = self.intrusion_evaluator.evaluate(
                classified_as,
                perception_data.get("text", {}),
                has_image=bool(comment.image_url),
                has_video=bool(comment.video_url)
            )
            comment.intrusion_score = intrusion_score

            # Обновление состояния
            self.state.update_after_comment(intrusion_score, classified_as)

            # Решение об ответе
            response_text = self.response_generator.generate(comment)

            if response_text:
                comment.responded = True
                comment.response_text = response_text
                logger.info(f"Generated response for comment {comment.comment_id}")
            else:
                logger.info(f"Decided not to respond to comment {comment.comment_id}")

            # Сохранить комментарий (всегда, даже без ответа)
            self.db.save_comment(comment)

            return response_text

        except Exception as e:
            logger.error(f"Error processing comment: {e}", exc_info=True)
            return None

    def generate_monologue(self) -> bool:
        """Сгенерировать внутренний монолог."""
        try:
            logger.info("Generating monologue")
            monologue = self.monologue_generator.generate(count=3)
            self.db.save_monologue(monologue)
            self.state.update_after_monologue()
            logger.info(f"Generated monologue {monologue.monologue_id}")
            return True
        except Exception as e:
            logger.error(f"Error generating monologue: {e}", exc_info=True)
            return False

    def publish_manifest(self) -> bool:
        """Опубликовать манифест из накопленных монологов."""
        try:
            logger.info("Publishing manifest")
            # Получить последние монологи для манифеста
            monologues = self.db.get_recent_monologues(limit=5)

            if not monologues:
                logger.warning("No monologues available for manifest")
                return False

            # Сгенерировать манифест
            manifest = self.manifest_generator.generate_from_monologues(monologues)

            if not manifest:
                logger.error("Failed to generate manifest")
                return False

            # Опубликовать
            success = self.manifest_generator.publish_next()
            return success

        except Exception as e:
            logger.error(f"Error publishing manifest: {e}", exc_info=True)
            return False

    def run_comment_check(self):
        """Проверить новые комментарии и обработать их."""
        try:
            comments = self.vk.get_new_comments(count=20)

            for comment_data in comments:
                comment_id = str(comment_data.get("id", ""))
                author_id = comment_data.get("author_id", "")

                # Проверить, не обработан ли уже комментарий
                existing_comment = self.db.get_comment(comment_id)
                if existing_comment:
                    logger.debug(f"Comment {comment_id} already processed, skipping")
                    continue

                # ЗАЩИТА ОТ БЕСКОНЕЧНОГО ЦИКЛА: пропускаем собственные комментарии сообщества
                # В VK API from_id комментария от группы = -abs(group_id)
                try:
                    group_id_raw = self.config.get("vk.group_id")
                    if group_id_raw:
                        group_id_value = int(group_id_raw) if isinstance(group_id_raw, (int, str)) else 0
                        # Нормализуем: group_id всегда отрицательный для сравнения с from_id
                        expected_from_id = -abs(group_id_value)
                        author_id_int = int(author_id) if author_id else 0
                        if author_id_int == expected_from_id:
                            logger.info(f"Skipping bot's own comment {comment_id} (from_id={author_id})")
                            continue
                except (ValueError, TypeError) as e:
                    logger.debug(f"Error comparing group_id: {e}")
                    pass

                # Логируем комментарий от создателя, но обрабатываем его как обычный
                creator_user_id = self.config.get("vk.creator_user_id")
                if creator_user_id:
                    try:
                        if author_id and abs(int(author_id)) == abs(int(creator_user_id)):
                            logger.info(f"Creator comment detected (author_id={author_id})")
                    except (ValueError, TypeError):
                        pass

                self.process_comment(comment_data)

        except Exception as e:
            logger.error(f"Error in comment check: {e}", exc_info=True)

