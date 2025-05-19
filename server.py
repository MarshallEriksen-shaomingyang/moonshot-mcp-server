"""Moonshot MCP Server."""

import asyncio
import logging
import signal
import sys
from typing import Any

from src.libs.i18n import i18n
from src.libs.mcp_config_loader import MCPConfigLoader
from src.libs.mcp_server import McpServer
from src.models.config_model import Config
from src.utils.custom_log import create_logger


async def shutdown(
    server: McpServer,
    signal: signal.Signals | None = None,
    logger: logging.Logger | None = None,
) -> None:
    if signal:
        logger.info("Received signal %s...", signal.name)
    logger.info(i18n.gettext("Closing MCP server..."))

    # 设置关闭标志
    server.is_shutting_down = True

    try:
        # 停止服务器并等待所有任务完成
        await asyncio.shield(server.stop())
        logger.info(i18n.gettext("MCP server closed successfully"))
    except asyncio.CancelledError:
        # 忽略取消异常继续关闭流程
        logger.info("Shutdown was cancelled, continuing shutdown process")
        # Still try to stop the server
        try:
            await server.stop()
        except Exception:
            logger.exception("Failed to stop server after cancellation")
    except Exception:
        logger.exception("Close MCP server failed")


async def setup_config() -> tuple[logging.Logger, dict, MCPConfigLoader]:
    """Set up configuration and logger."""
    logger = await create_logger("mcp_server")
    main_config = MCPConfigLoader("moonshot_config.toml")
    await main_config.load_config()
    config = await main_config.get_config()

    try:
        validated_config = Config(**config)
        logger.info("Validated config successfully")
        config = validated_config.model_dump()
    except Exception:
        logger.exception("Config validation error")
        raise

    return logger, config, main_config


async def setup_server(
    server_config: dict,
    proxy_config: dict,
    logger: logging.Logger,
) -> McpServer:
    """Create and set up the MCP server."""
    server = await McpServer.create(server_config, proxy_config, logger)

    # Set up signal handlers
    loop = asyncio.get_running_loop()
    signals = (signal.SIGTERM, signal.SIGINT)
    for sig in signals:
        loop.add_signal_handler(
            sig,
            lambda s=sig: asyncio.create_task(
                shutdown(server, signal=s, logger=logger),
            ),
        )

    # Add a custom exception handler to handle CancelledError more gracefully
    def custom_exception_handler(
        loop: asyncio.AbstractEventLoop,
        context: dict[str, Any],
    ) -> None:
        exception = context.get("exception")
        if isinstance(exception, asyncio.CancelledError):
            # Just log it without propagating
            logger.info("Task was cancelled during shutdown")
        else:
            # For other exceptions use the default handler
            loop.default_exception_handler(context)

    loop.set_exception_handler(custom_exception_handler)

    return server


async def main() -> None:
    """运行 MCP 服务器."""
    logger, config, main_config = await setup_config()
    server = None  # Initialize server variable

    async def reload_server() -> None:
        """Reload the server when the config file changes."""
        nonlocal server
        logger.info("Config file changed, restarting server...")

        # 停止当前服务器
        if server is not None:
            await server.stop()
            server = None  # 确保服务器被完全停止和清理

        # 重新加载配置
        await main_config.load_config()
        new_config = await main_config.get_config()

        try:
            # 验证新配置
            validated_config = Config(**new_config)
            logger.info("Validated new config successfully")
            new_config = validated_config.model_dump()

            # 获取新的服务器配置
            new_server_config = new_config["server"]
            new_proxy_config = new_config["mcpServers"]

            # 创建新的服务器实例
            server = await McpServer.create(new_server_config, new_proxy_config, logger)

            if server and server.main_server:
                logger.info("Configuration updated successfully. Please restart the server manually to apply changes.")
                # 不尝试启动HTTP服务器,因为这会导致端口冲突
                # 相反,我们只创建代理
                await server.create_proxies()
            else:
                logger.error("Failed to create server during reload: main_server is None")
        except Exception:
            logger.exception("Error reloading server with new configuration")

    await main_config.start_watching(reload_server)

    server_config = config["server"]
    proxy_config = config["mcpServers"]

    try:
        # 创建服务器实例
        server = await setup_server(server_config, proxy_config, logger)

        if not server or not server.main_server:
            logger.error("Failed to create server: main_server is None")
            return

        logger.info(i18n.gettext("MCP server is running,press Ctrl+C stop"))

        # 创建代理并运行服务器
        await server.create_proxies()

        # 运行HTTP服务器
        await server.main_server.run_http_async()

    except Exception:
        logger.exception("Error starting MCP server")
        if server is not None:
            await shutdown(server, logger=logger)
    finally:
        # 确保资源被正确释放
        if server is not None:
            await server.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger = logging.getLogger("mcp_server")
        logger.info("KeyboardInterrupt, stopping server...")
        sys.exit(0)
    except asyncio.CancelledError:
        # This is expected during shutdown, so exit gracefully
        sys.exit(0)
    except Exception as e:
        msg = f"Unhandled exception: {e}"
        raise RuntimeError(msg) from e
