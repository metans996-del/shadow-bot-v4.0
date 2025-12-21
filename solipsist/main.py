"""Точка входа в приложение."""
import logging
import threading
import time
from pathlib import Path

from .core.bot import SolipsistBot
from .core.scheduler import TaskScheduler
from .utils.logging import setup_logging, get_logger
from .config.loader import load_config


def main():
    """Главная функция."""
    # Настройка логирования
    setup_logging(log_level=logging.INFO)
    logger = get_logger(__name__)

    logger.info("Starting SolipsistBot v4.0")

    try:
        # Загрузка конфигурации
        config = load_config()

        # Инициализация бота
        bot = SolipsistBot()

        # Инициализация планировщика
        scheduler = TaskScheduler()

        # Регистрация callbacks
        scheduler.register_monologue_callback(bot.generate_monologue)
        scheduler.register_publication_callback(bot.publish_manifest)

        # Запуск планировщика в отдельном потоке
        scheduler_thread = threading.Thread(
            target=scheduler.run_continuously,
            daemon=True
        )
        scheduler_thread.start()
        logger.info("Scheduler started")

        # Основной цикл: проверка комментариев
        logger.info("Entering main loop - checking comments every 60 seconds")
        while True:
            try:
                bot.run_comment_check()
                time.sleep(60)  # Проверка каждую минуту
            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(60)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise

    logger.info("SolipsistBot stopped")


if __name__ == "__main__":
    main()

