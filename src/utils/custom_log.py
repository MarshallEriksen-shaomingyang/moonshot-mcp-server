import logging
import os
import time

import colorlog

from src.libs import i18n
from src.settings import get_settings


async def create_log_path():
    """创建日志文件路径"""
    root_path = os.path.dirname(os.path.realpath(__file__))
    parent_path = os.path.dirname(root_path)
    logs_path = os.path.join(parent_path, "logs")
    if not os.path.exists(logs_path):
        os.makedirs(logs_path)
    current_date = time.strftime("%Y-%m-%d")
    date_path = os.path.join(logs_path, current_date)
    if not os.path.exists(date_path):
        os.makedirs(date_path)
    return date_path


def create_file_handler(log_file: str) -> logging.FileHandler:
    """创建文件处理器
    Args:
        log_file: 日志文件路径
    Returns:
        logging.FileHandler: 配置好的文件处理器
    """
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
        i18n.gettext.gettext("{} Log Assistant").format(settings.assistant_name)
    )
    logger.setLevel(logging.DEBUG)

    # 防止重复添加处理器
    if not logger.handlers:
        # 创建文件处理器（纯文本格式）
        log_path = await create_log_path()
        log_file = (
            os.path.join(log_path, f"{file_name}.log")
            if file_name
            else os.path.join(
                log_path, f"{settings.assistant_name}-{time.strftime('%Y-%m-%d_%H-%M-%S')}.log"
            )
        )
        file_handler = create_file_handler(log_file)

        # 创建控制台处理器（带颜色）
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
