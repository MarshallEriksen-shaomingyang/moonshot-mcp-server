import asyncio
import signal
import sys

from src.libs.i18n import i18n
from src.libs.mcp_config_loader import MCPConfigLoader
from src.libs.mcp_server import McpServer
from src.models.config_model import Config


async def shutdown(server, signal=None):
    """优雅关闭服务器"""
    if signal:
        print(f"receive signal {signal.name}...")
    print(i18n.gettext("Closing MCP server..."))

    # 设置关闭标志
    server.is_shutting_down = True

    try:
        # 停止服务器并等待所有任务完成
        await asyncio.shield(server.stop())
        print(i18n.gettext("MCP server closed successfully"))
    except asyncio.CancelledError:
        # 忽略取消异常，继续关闭流程
        pass
    except Exception as e:
        print(f"Close MCP server failed: {str(e)}")
    finally:
        # 停止事件循环
        loop = asyncio.get_running_loop()
        loop.stop()


async def main():
    """运行 MCP 服务器"""
    # 首先运行run.sh脚本
    main_config = MCPConfigLoader("moonshot_config.toml")
    # 加载配置文件
    await main_config.load_config()
    # 获取配置文件
    config = await main_config.get_config()
    config = Config(**config).model_dump()

    async def reload_server():
        print("Config changed, restarting server...")
        # 停止当前服务器
        await server.stop()  # noqa: F823
        # 重新加载配置并启动
        await main_config.load_config()
        config = await main_config.get_config()
        server = await McpServer.create(config["server"], config["mcpServers"])
        await server._create_proxies()
        await server.main_server.run_sse_async()

    await main_config.start_watching(reload_server)

    server_config = config["server"]
    proxy_config = config["mcpServers"]

    try:
        # 创建服务器实例
        server = await McpServer.create(server_config, proxy_config)

        # 设置信号处理
        loop = asyncio.get_running_loop()
        signals = (signal.SIGTERM, signal.SIGINT)
        for sig in signals:
            loop.add_signal_handler(
                sig, lambda s=sig: asyncio.create_task(shutdown(server, signal=s))
            )

        print(i18n.gettext("MCP server is running，press Ctrl+C stop"))

        # 创建代理并运行服务器
        await server._create_proxies()
        await server.main_server.run_sse_async()

    except Exception as e:
        print(f"Error starting MCP server: {str(e)}")
        await shutdown(server)
    finally:
        # 确保资源被正确释放
        if "server" in locals():
            await server.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("MCP server interrupt by user 👿")
    finally:
        sys.exit(0)
