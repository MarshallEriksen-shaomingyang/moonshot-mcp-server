import logging
import time
from pathlib import Path

import colorlog

from src.libs import i18n
from src.settings import get_settings


async def create_log_path() -> str:
    """创建日志文件路径."""
    root_path = Path(__file__).resolve().parent
    parent_path = root_path.parent
    logs_path = parent_path / "logs"
    if not logs_path.exists():
        logs_path.mkdir(parents=True)
    current_date = time.strftime("%Y-%m-%d")
    date_path = logs_path / current_date
    if not date_path.exists():
        date_path.mkdir(parents=True)
    return date_path


def create_file_handler(log_file: str) -> logging.FileHandler:
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    file_handler.setFormatter(file_formatter)
    return file_handler


async def create_logger(file_name: str) -> logging.Logger:
    settings = get_settings()
    logger = logging.getLogger(
        i18n.gettext.gettext("{} Log Assistant").format(settings.assistant_name),
    )
    logger.setLevel(logging.DEBUG)

    # 防止重复添加处理器
    if not logger.handlers:
        log_path = await create_log_path()
        log_file = (
            Path(log_path) / f"{file_name}.log"
            if file_name
            else Path(log_path) / f"{settings.assistant_name}-{time.strftime('%Y-%m-%d_%H-%M-%S')}.log"
        )
        file_handler = create_file_handler(log_file)

        console_handler = colorlog.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        log_colors = {
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        }
        console_formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            log_colors=log_colors,
        )
        console_handler.setFormatter(console_formatter)

        # 添加处理器
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
