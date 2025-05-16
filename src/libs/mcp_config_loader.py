import asyncio
import logging
import os
from collections.abc import Callable

import tomli
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class FileModifiedHandler(FileSystemEventHandler):
    """处理配置文件修改事件"""

    def __init__(self, loader: "MCPConfigLoader", debounce_interval: float = 1.0):
        self.loader = loader
        self.debounce_interval = debounce_interval
        self.last_triggered = 0

    def on_modified(self, event):
        """当配置文件被修改时触发"""
        if event.src_path != self.loader.config_path or event.is_directory:
            return

        current_time = asyncio.get_event_loop().time()
        if current_time - self.last_triggered < self.debounce_interval:
            return  # 防抖：忽略短时间内的重复修改

        self.last_triggered = current_time
        logger.info("Config file changed, scheduling reload...")

        if self.loader._loop and self.loader.callback:
            # 确保回调是异步的，调度到事件循环
            coro = self.loader.callback()
            if asyncio.iscoroutine(coro):
                asyncio.run_coroutine_threadsafe(coro, self.loader._loop)
            else:
                self.loader._loop.call_soon_threadsafe(self.loader.callback)


class MCPConfigLoader:
    """
    配置文件加载器
    Args:
        config_path (str): 配置文件路径
    """

    def __init__(self, config_path: str):
        self.config_path = os.path.abspath(config_path)
        self.callback: Callable | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._observer = None
        self._config: dict | None = None

    async def load_config(self) -> None:
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            logger.error(f"Config file not found: {self.config_path}")
            raise FileNotFoundError("Config file not found")

        try:
            with open(self.config_path, "rb") as f:
                self._config = tomli.load(f)
            logger.info(f"Config file loaded successfully: {self.config_path}")
        except tomli.TOMLDecodeError as e:
            logger.error(f"Config file parse error: {str(e)}")
            raise ValueError("Config file load failed") from e
        except Exception as e:
            logger.error(f"Unexpected error loading config: {str(e)}")
            raise ValueError("Config file load failed") from e

    async def get_config(self) -> dict | None:
        """获取当前配置"""
        if self._config is None:
            await self.load_config()
        return self._config

    async def start_watching(self, callback: Callable) -> None:
        """启动配置文件监控"""
        if not os.path.exists(self.config_path):
            logger.error(f"Config file not found: {self.config_path}")
            raise FileNotFoundError("Config file not found")

        self.callback = callback
        self._loop = asyncio.get_running_loop()

        event_handler = FileModifiedHandler(self, debounce_interval=1.0)
        self._observer = Observer()
        self._observer.schedule(
            event_handler, path=os.path.dirname(self.config_path), recursive=False
        )
        self._observer.start()
        logger.info(f"Started watching config file: {self.config_path}")

    async def stop_watching(self) -> None:
        """停止配置文件监控"""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            logger.info(f"Stopped watching config file: {self.config_path}")
