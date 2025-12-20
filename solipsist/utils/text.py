"""Утилиты для работы с текстом."""
import re
from typing import List


def clean_text(text: str) -> str:
    """Очистить текст от лишних символов."""
    if not text:
        return ""

    # Удалить множественные пробелы
    text = re.sub(r'\s+', ' ', text)
    # Удалить пробелы в начале и конце
    text = text.strip()

    return text


def split_sentences(text: str) -> List[str]:
    """Разделить текст на предложения."""
    # Простое разделение по точкам, восклицательным и вопросительным знакам
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences


def truncate_text(text: str, max_length: int = 500) -> str:
    """Обрезать текст до максимальной длины."""
    if len(text) <= max_length:
        return text

    # Обрезать до последнего пробела
    truncated = text[:max_length].rsplit(' ', 1)[0]
    return truncated + "..."


def count_words(text: str) -> int:
    """Подсчитать количество слов в тексте."""
    if not text:
        return 0
    return len(text.split())



