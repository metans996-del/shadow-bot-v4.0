"""Планировщик задач."""
import logging
import schedule
import time
from datetime import datetime
from typing import Callable, Optional
import pytz

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Планировщик задач для бота."""

    def __init__(self):
        """Инициализация планировщика."""
        self.timezone = pytz.timezone("Europe/Moscow")
        self._monologue_callback = None
        self._publication_callback = None

    def register_monologue_callback(self, callback: Callable):
        """Зарегистрировать callback для монолога."""
        self._monologue_callback = callback
        # Настроить расписание после регистрации callback
        schedule.every().hour.do(self._run_monologue_task)

    def register_publication_callback(self, callback: Callable):
        """Зарегистрировать callback для публикации."""
        self._publication_callback = callback
        # Настроить расписание после регистрации callback
        schedule.every().day.at("00:00").do(self._run_publication_task)
        schedule.every().day.at("12:00").do(self._run_publication_task)

    def _run_monologue_task(self):
        """Запустить задачу генерации монолога."""
        logger.info("Running scheduled monologue task")
        if self._monologue_callback:
            try:
                self._monologue_callback()
            except Exception as e:
                logger.error(f"Error in monologue task: {e}", exc_info=True)

    def _run_publication_task(self):
        """Запустить задачу публикации манифеста."""
        logger.info("Running scheduled publication task")
        if self._publication_callback:
            try:
                self._publication_callback()
            except Exception as e:
                logger.error(f"Error in publication task: {e}", exc_info=True)

    def run_pending(self):
        """Запустить ожидающие задачи."""
        schedule.run_pending()

    def run_continuously(self):
        """Запустить планировщик непрерывно."""
        logger.info("Starting scheduler")
        while True:
            self.run_pending()
            time.sleep(60)  # Проверка каждую минуту

