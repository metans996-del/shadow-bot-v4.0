"""Система логирования."""
import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(log_dir: str = "logs", log_level: int = logging.INFO):
    """Настроить систему логирования."""
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Файловый handler
    log_file = log_path / f"solipsist_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # Консольный handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # Корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Получить логгер с указанным именем."""
    return logging.getLogger(name)



