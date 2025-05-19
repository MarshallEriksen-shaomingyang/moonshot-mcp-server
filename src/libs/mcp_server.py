import asyncio
import logging
from typing import Any

from fastapi import FastAPI
from fastmcp import Client
from fastmcp import FastMCP
from fastmcp.client.transports import NodeStdioTransport
from fastmcp.client.transports import NpxStdioTransport
from fastmcp.client.transports import PythonStdioTransport
from fastmcp.client.transports import SSETransport
from fastmcp.client.transports import UvxStdioTransport
from fastmcp.client.transports import WSTransport

from src.models.config_model import ProxyConfig
from src.models.config_model import ServerConfig


class McpServer:
    """MCP server aggregator class."""

    def __init__(self, server_config: ServerConfig, proxy_config: ProxyConfig) -> None:
        """Initialize the MCP server."""
        self.server_config: ServerConfig = server_config
        self.proxy_config: ProxyConfig = proxy_config
        self.main_server: FastMCP | None = None
        self.clients: list[Client] = []
        self._tasks: list[asyncio.Task] = []
        self._logger: logging.Logger | None = None
        self.is_shutting_down: bool = False

    @classmethod
    async def create(cls, server_config: ServerConfig, proxy_config: ProxyConfig, logger: logging.Logger) -> None:
        """Create a new instance of the MCP server."""
        instance = cls(server_config, proxy_config)
        instance._logger = logger
        app = FastAPI()
        instance.main_server = FastMCP.from_fastapi(
            app=app,
            name=server_config["name"],
            host=server_config.get("host", "127.0.0.1"),
            port=server_config.get("port", "8000"),
        )
        return instance

    async def stop(self) -> None:
        """Stop the MCP server and clean up resources."""
        if not self._logger:
            return

        self._logger.info("Stopping MCP server...")
        try:
            # Cancel all tasks
            for task in self._tasks:
                task.cancel()

            # Close all clients
            await asyncio.gather(
                *(client.__aexit__(None, None, None) for client in self.clients),
                return_exceptions=True,
            )

            # Clear resources
            self.clients.clear()
            self._tasks.clear()

            if self.main_server:
                self.main_server = None

            self._logger.info("MCP server stopped successfully")
        except Exception:
            self._logger.exception("Failed to stop server")

    async def create_proxies(self) -> None:
        """Create proxy servers based on configuration."""
        if not self.proxy_config:
            self._logger.info("No proxy configurations found, skipping proxy creation")
            return
        for name, config in self.proxy_config.items():
            if not config:
                self._logger.warning("Proxy configuration for %s is empty, skipping", name)
                continue
            if not config.get("prefix"):
                self._logger.error("Proxy configuration for %s is missing prefix, skipping", name)
                continue
            self._logger.info("name: %s, config: %s", name, str(config))
            try:
                client = await self._create_proxy(name, config)
                proxy_route = FastMCP.from_client(client, name=name)
                if client:
                    await self.main_server.import_server(
                        server=proxy_route,
                        prefix=config.get("prefix", ""),
                    )
                    self.clients.append(client)
            except Exception:
                import traceback

                traceback.print_exc()
                self._logger.exception("Failed to create proxy %s", name)

    async def _create_proxy(self, name: str, config: dict[str, Any]) -> Client | None:
        """Create a single proxy server."""
        mcp_type = config.get("type")
        if not mcp_type:
            self._logger.error("%s: Proxy type not specified", name)
            return None

        transport_creators = {
            "process": self._create_process_transport,
            "http": self._create_sse_transport,
            "https": self._create_sse_transport,
            "websocket": self._create_ws_transport,
            "uvx": self._create_uvx_transport,
            "npx": self._create_npx_transport,
        }

        creator = transport_creators.get(mcp_type)
        if not creator:
            self._logger.error("Unknown proxy type: %s", mcp_type)
            return None

        transport = await creator(name, config)
        if not transport:
            return None

        return await self._setup_proxy(name, config, transport)

    async def _setup_proxy(
        self,
        name: str,
        config: dict[str, Any],
        transport: Any,  # noqa: ANN401
    ) -> Client | None:
        """Set up a proxy server with retry mechanism."""
        retry_count = config.get("retry", 1)
        for attempt in range(retry_count):
            try:
                client = Client(transport=transport)
                self._logger.info("Connected server '%s' successfully", name)
            except TimeoutError:
                self._logger.warning("Timeout connecting server '%s' (try %d/%d)", name, attempt + 1, retry_count)

            except Exception:
                self._logger.exception("Failed to connect server '%s'", name)
            return client
        return None

    async def _create_process_transport(
        self,
        name: str,
        config: dict[str, Any],
    ) -> PythonStdioTransport | NodeStdioTransport | None:
        """Create process transport for Python or Node.js scripts."""
        script_path = config.get("script_path")
        if not script_path:
            self._logger.error("%s: Script path not found", name)
            return None

        is_python = script_path.endswith(".py")
        is_js = script_path.endswith(".js")
        if not (is_python or is_js):
            self._logger.error("%s: Unsupported script type", name)
            return None

        try:
            if is_python:
                return PythonStdioTransport(
                    python_cmd=config.get("command", ""),
                    script_path=script_path,
                    args=config.get("args", []),
                    env=config.get("env"),
                    cwd=config.get("cwd"),
                )
            return NodeStdioTransport(
                node_cmd=config.get("command", ""),
                script_path=script_path,
                args=config.get("args", []),
                env=config.get("env"),
                cwd=config.get("cwd"),
            )
        except Exception:
            self._logger.exception("Error creating process transport for '%s'", name)

            return None

    async def _create_sse_transport(self, name: str, config: dict[str, Any]) -> SSETransport | None:
        """Create SSE transport."""
        url = config.get("url")
        if not url:
            self._logger.error("%s: URL not found", name)
            return None
        return SSETransport(url, headers=config.get("headers", {}))

    async def _create_ws_transport(self, name: str, config: dict[str, Any]) -> WSTransport | None:
        """Create WebSocket transport."""
        url = config.get("url")
        if not url:
            self._logger.error("%s: URL not found", name)
            return None
        return WSTransport(url)

    async def _create_uvx_transport(
        self,
        name: str,
        config: dict[str, Any],
    ) -> UvxStdioTransport | None:
        """Create UVX transport."""
        tool_name = config.get("tool_name")
        if not tool_name:
            self._logger.error("%s: Tool name not found", name)
            return None
        return UvxStdioTransport(
            tool_name=tool_name,
            from_package=config.get("from_package", ""),
            with_packages=config.get("with_packages", []),
            tool_args=config.get("args", []),
            env_vars=config.get("env"),
            project_directory=config.get("project_directory"),
            python_version=config.get("python_version"),
        )

    async def _create_npx_transport(
        self,
        name: str,
        config: dict[str, Any],
    ) -> NpxStdioTransport | None:
        """Create NPX transport."""
        package = config.get("package")
        if not package:
            self._logger.error("%s: Package not found", name)
            return None
        return NpxStdioTransport(
            package=package,
            args=config.get("args", []),
            project_directory=config.get("project_directory"),
            env_vars=config.get("env"),
            use_package_lock=config.get("use_package_lock", True),
        )
