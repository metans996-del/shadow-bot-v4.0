"""Клиент VK API."""
import requests
import logging
import time
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..config.loader import load_config

logger = logging.getLogger(__name__)

# Максимальная длина одного поста в VK
MAX_VK_POST_LENGTH = 3500


class VKClient:
    """Клиент для работы с VK API."""

    def __init__(self):
        """Инициализация клиента."""
        config = load_config()
        self.access_token = config.vk_token
        self.group_id = config.get("vk.group_id")
        self.api_version = config.get("vk.api_version", "5.131")
        self.api_base = "https://api.vk.com/method"

        if not self.access_token or self.access_token == "YOUR_VK_ACCESS_TOKEN":
            logger.warning("VK access token not configured")

    def _make_request(self, method: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Выполнить запрос к VK API."""
        if not self.access_token or self.access_token == "YOUR_VK_ACCESS_TOKEN":
            logger.error("VK access token not configured")
            return None

        params["access_token"] = self.access_token
        params["v"] = self.api_version

        try:
            response = requests.post(
                f"{self.api_base}/{method}",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                logger.error(f"VK API error: {data['error']}")
                return None

            return data.get("response")
        except Exception as e:
            logger.error(f"VK API request error: {e}")
            return None

    def get_new_comments(self, count: int = 20) -> List[Dict[str, Any]]:
        """Получить новые комментарии к постам группы."""
        owner_id = f"-{self.group_id}"
        all_comments = []

        # Получить последние посты группы
        posts_params = {
            "owner_id": owner_id,
            "count": 10,  # Получаем последние 10 постов
            "filter": "owner"  # Только посты от имени группы
        }

        posts_response = self._make_request("wall.get", posts_params)
        if not posts_response or "items" not in posts_response:
            logger.warning("Failed to get posts or no posts found")
            return []

        posts = posts_response.get("items", [])
        logger.info(f"Found {len(posts)} posts to check for comments")

        # Для каждого поста получить комментарии
        for post in posts:
            post_id = post.get("id")
            if not post_id:
                continue

            # Получить комментарии к посту
            comments_params = {
                "owner_id": owner_id,
                "post_id": post_id,
                "count": 100,  # Максимум комментариев за запрос
                "need_likes": 0,
                "preview_length": 0,
                "extended": 0,
                "fields": ""
            }

            comments_response = self._make_request("wall.getComments", comments_params)
            if not comments_response or "items" not in comments_response:
                continue

            comments = comments_response.get("items", [])
            logger.info(f"Found {len(comments)} comments for post {post_id}")

            # Преобразовать комментарии в нужный формат
            for comment in comments:
                comment_id = str(comment.get("id", ""))
                author_id = str(comment.get("from_id", ""))
                text = comment.get("text", "")

                # Извлечь вложения (фото, видео)
                attachments = comment.get("attachments", [])
                image_url = None
                video_url = None

                for att in attachments:
                    att_type = att.get("type", "")
                    if att_type == "photo":
                        photo = att.get("photo", {})
                        # Получить URL самого большого размера
                        sizes = photo.get("sizes", [])
                        if sizes:
                            # Сортировка по размеру (width * height)
                            largest = max(sizes, key=lambda x: x.get("width", 0) * x.get("height", 0))
                            image_url = largest.get("url")
                    elif att_type == "video":
                        video = att.get("video", {})
                        # Для видео можно получить превью (может быть в разных форматах)
                        if video.get("image"):
                            if isinstance(video.get("image"), list) and len(video["image"]) > 0:
                                image_url = video["image"][0].get("url")
                            elif isinstance(video.get("image"), str):
                                image_url = video.get("image")
                        # Формируем URL видео
                        video_owner_id = video.get("owner_id", "")
                        video_id = video.get("id", "")
                        if video_owner_id and video_id:
                            video_url = f"https://vk.com/video{video_owner_id}_{video_id}"

                # Преобразовать дату
                date = comment.get("date")
                timestamp = datetime.fromtimestamp(date) if date else datetime.now()

                comment_data = {
                    "id": comment_id,
                    "post_id": str(post_id),
                    "author_id": author_id,
                    "text": text,
                    "image_url": image_url,
                    "video_url": video_url,
                    "timestamp": timestamp
                }

                all_comments.append(comment_data)

                # Ограничить общее количество комментариев
                if len(all_comments) >= count:
                    break

            if len(all_comments) >= count:
                break

        logger.info(f"Total comments retrieved: {len(all_comments)}")
        return all_comments[:count]

    def _make_post_request(self, method: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Выполнить POST-запрос к VK API с передачей параметров через data (для длинных текстов)."""
        if not self.access_token or self.access_token == "YOUR_VK_ACCESS_TOKEN":
            logger.error("VK access token not configured")
            return None

        params["access_token"] = self.access_token
        params["v"] = self.api_version

        try:
            response = requests.post(
                f"{self.api_base}/{method}",
                data=params,  # Используем data вместо params для длинных текстов
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                logger.error(f"VK API error: {data['error']}")
                return None

            return data.get("response")
        except Exception as e:
            logger.error(f"VK API request error: {e}")
            return None

    def split_manifest(self, text: str) -> List[str]:
        """Разбить текст манифеста на части по MAX_VK_POST_LENGTH.

        Разбиение происходит по абзацам и предложениям, не разрывая слова.
        """
        if len(text) <= MAX_VK_POST_LENGTH:
            return [text]

        parts = []
        current_part = ""

        # Разбиваем на абзацы (двойные переносы строк)
        paragraphs = text.split('\n\n')

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # Если абзац сам по себе слишком длинный, разбиваем на предложения
            if len(paragraph) > MAX_VK_POST_LENGTH:
                # Сначала сохраняем накопленную часть, если есть
                if current_part:
                    parts.append(current_part.strip())
                    current_part = ""

                # Разбиваем длинный абзац на предложения
                sentences = self._split_into_sentences(paragraph)
                for sentence in sentences:
                    # Если предложение само слишком длинное, разбиваем по словам
                    if len(sentence) > MAX_VK_POST_LENGTH:
                        if current_part:
                            parts.append(current_part.strip())
                            current_part = ""
                        # Разбиваем длинное предложение на части по словам
                        words = sentence.split()
                        for word in words:
                            if len(current_part) + len(word) + 1 > MAX_VK_POST_LENGTH:
                                if current_part:
                                    parts.append(current_part.strip())
                                current_part = word
                            else:
                                if current_part:
                                    current_part += " " + word
                                else:
                                    current_part = word
                    elif len(current_part) + len(sentence) + 1 > MAX_VK_POST_LENGTH:
                        if current_part:
                            parts.append(current_part.strip())
                        current_part = sentence
                    else:
                        if current_part:
                            current_part += "\n" + sentence
                        else:
                            current_part = sentence
            else:
                # Обычный абзац - добавляем к текущей части если помещается
                needed_length = len(current_part) + len(paragraph) + (2 if current_part else 0)
                if needed_length > MAX_VK_POST_LENGTH:
                    if current_part:
                        parts.append(current_part.strip())
                    current_part = paragraph
                else:
                    if current_part:
                        current_part += "\n\n" + paragraph
                    else:
                        current_part = paragraph

        # Добавляем последнюю часть
        if current_part:
            parts.append(current_part.strip())

        return parts

    def _split_into_sentences(self, text: str) -> List[str]:
        """Разбить текст на предложения."""
        # Разбиваем по точкам, восклицательным и вопросительным знакам
        sentences = re.split(r'([.!?]+)', text)
        result = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                result.append((sentences[i] + sentences[i + 1]).strip())
            elif sentences[i].strip():
                result.append(sentences[i].strip())
        return [s for s in result if s]

    def post_message(self, message: str, attachments: Optional[List[str]] = None) -> Optional[int]:
        """Опубликовать пост на стене группы (с поддержкой длинных текстов)."""
        # Разбиваем текст на части если он слишком длинный
        parts = self.split_manifest(message)

        if len(parts) > 1:
            logger.info(f"Splitting message into {len(parts)} parts")

        first_post_id = None

        for i, part in enumerate(parts):
            # Добавляем пометку о части, если частей больше одной
            if len(parts) > 1:
                part_text = f"[Манифест. Часть {i+1}/{len(parts)}]\n\n{part}"
            else:
                part_text = part

            params = {
                "owner_id": f"-{self.group_id}",
                "message": part_text
            }

            if attachments and i == 0:  # Вложения только к первой части
                params["attachments"] = ",".join(attachments)

            # Используем POST с data для избежания ошибки 414
            result = self._make_post_request("wall.post", params)

            if result and "post_id" in result:
                post_id = result["post_id"]
                if first_post_id is None:
                    first_post_id = post_id

                logger.info(f"Published part {i+1}/{len(parts)} as post {post_id}")

                # Пауза между публикациями (кроме последней)
                if i < len(parts) - 1:
                    time.sleep(1.5)  # 1-2 секунды пауза
            else:
                logger.error(f"Failed to publish part {i+1}/{len(parts)}")
                return None

        return first_post_id

    def reply_to_comment(
        self,
        post_id: int,
        comment_id: int,
        message: str
    ) -> Optional[int]:
        """Ответить на комментарий."""
        params = {
            "owner_id": f"-{self.group_id}",
            "post_id": post_id,
            "reply_to_comment": comment_id,
            "message": message
        }

        result = self._make_request("wall.createComment", params)
        if result and "comment_id" in result:
            return result["comment_id"]
        return None

