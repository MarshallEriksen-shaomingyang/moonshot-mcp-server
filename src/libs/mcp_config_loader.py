import asyncio
import logging
from collections.abc import Callable
from pathlib import Path

import tomli
from watchdog.events import FileSystemEvent
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger("mcp_server")


class FileModifiedHandler(FileSystemEventHandler):
    """处理配置文件修改事件."""

    def __init__(self, loader: "MCPConfigLoader", debounce_interval: float = 1.0) -> None:
        """初始化FileModifiedHandler."""
        self.loader = loader
        self.debounce_interval = debounce_interval
        self.last_triggered = 0

    def on_modified(self, event: FileSystemEvent) -> None:
        """当配置文件被修改时触发."""
        # 将 event.src_path 转换为 Path 对象进行比较
        if str(event.src_path) != str(self.loader.config_path) or event.is_directory:
            return

        # 使用时间戳而不是事件循环的时间
        import time

        current_time = time.time()
        if current_time - self.last_triggered < self.debounce_interval:
            return  # 防抖: 忽略短时间内的重复修改

        self.last_triggered = current_time
        logger.info("Config file changed, scheduling reload...")

        if self.loader._loop and self.loader.callback:  # noqa: SLF001
            # 确保回调是异步的,调度到事件循环
            coro = self.loader.callback()
            if asyncio.iscoroutine(coro):
                asyncio.run_coroutine_threadsafe(coro, self.loader._loop)  # noqa: SLF001
            else:
                self.loader._loop.call_soon_threadsafe(self.loader.callback)  # noqa: SLF001


class MCPConfigLoader:
    def __init__(self, config_path: str) -> None:
        """初始化MCPConfigLoader."""
        self.config_path = Path(config_path).resolve()
        self.callback: Callable | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._observer = None
        self._config: dict | None = None

    async def load_config(self) -> None:
        """加载配置文件."""
        if not self.config_path.exists():
            config_not_found = "Config file not found"
            raise FileNotFoundError(config_not_found)

        try:
            with self.config_path.open("rb") as f:
                self._config = tomli.load(f)
        except tomli.TOMLDecodeError as e:
            msg = "Config file load failed"
            raise ValueError(msg) from e
        except Exception as e:
            msg = f"Config file load failed: {e}"
            raise ValueError(msg) from e

    async def get_config(self) -> dict | None:
        """获取当前配置."""
        if self._config is None:
            await self.load_config()
        return self._config

    async def start_watching(self, callback: Callable) -> None:
        """启动配置文件监控."""
        if not self.config_path.exists():
            msg = "Config file not found"
            raise FileNotFoundError(msg)

        self.callback = callback
        self._loop = asyncio.get_running_loop()

        event_handler = FileModifiedHandler(self, debounce_interval=1.0)
        self._observer = Observer()
        self._observer.schedule(
            event_handler,
            path=self.config_path.parent,
            recursive=False,
        )
        self._observer.start()
        logger.info("Started watching config file: '%s'", self.config_path)

    async def stop_watching(self) -> None:
        """停止配置文件监控."""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            logger.info("Stopped watching config file: %s", self.config_path)
