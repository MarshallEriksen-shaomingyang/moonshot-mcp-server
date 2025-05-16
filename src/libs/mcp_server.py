import asyncio
from typing import Any

from fastapi import FastAPI
from fastmcp import Client, FastMCP
from fastmcp.client.transports import (
    NodeStdioTransport,
    NpxStdioTransport,
    PythonStdioTransport,
    SSETransport,
    UvxStdioTransport,
    WSTransport,
)

from src.models.config_model import ProxyConfig, ServerConfig
from src.utils.custom_log import create_logger


class McpServer:
    """MCP server aggregator class."""

    def __init__(self, server_config: ServerConfig, proxy_config: ProxyConfig):
        self.server_config: ServerConfig = server_config
        self.proxy_config: ProxyConfig = proxy_config
        self.main_server: FastMCP | None = None
        self.clients: list[Client] = []
        self._tasks: list[asyncio.Task] = []
        self._logger = None

    @classmethod
    async def create(cls, server_config: ServerConfig, proxy_config: ProxyConfig):
        instance = cls(server_config, proxy_config)
        instance._logger = await create_logger("mcp_server")
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
        except Exception as e:
            self._logger.error(f"Failed to stop server: {str(e)}")

    async def _create_proxies(self) -> None:
        """Create proxy servers based on configuration."""
        if not self.proxy_config:
            self._logger.info("No proxy configurations found, skipping proxy creation")
            return
        for name, config in self.proxy_config.items():
            self._logger.info(f"name: {name}, config: {config}")
            try:
                client = await self._create_proxy(name, config)
                proxy_route = FastMCP.from_client(client, name=name)
                if client:
                    await self.main_server.import_server(
                        server=proxy_route, prefix=config.get("prefix", "")
                    )
                    self.clients.append(client)
            except Exception as e:
                import traceback

                traceback.print_exc()
                self._logger.error(f"Failed to create proxy {name}: {str(e)}")

    async def _create_proxy(self, name: str, config: dict[str, Any]) -> Client | None:
        """Create a single proxy server."""
        mcp_type = config.get("type")
        if not mcp_type:
            self._logger.error(f"{name}: Proxy type not specified")
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
            self._logger.error(f"Unknown proxy type: {mcp_type}")
            return None

        transport = await creator(name, config)
        if not transport:
            return None

        return await self._setup_proxy(name, config, transport)

    async def _setup_proxy(
        self, name: str, config: dict[str, Any], transport: Any
    ) -> Client | None:
        """Set up a proxy server with retry mechanism."""
        retry_count = config.get("retry", 1)
        # roots = config.get("whiteLists", [])

        for attempt in range(retry_count):
            try:
                client = Client(transport=transport)
                self._logger.info(f"Connected server '{name}' successfully")
                return client
            except TimeoutError:
                self._logger.warning("Timeout connecting server '{name}' (try {}/{})").format(
                    name, attempt + 1, retry_count
                )

            except Exception as e:
                self._logger.error(f"Failed to connect server '{name}': {str(e)}")

        return None

    async def _create_process_transport(
        self, name: str, config: dict[str, Any]
    ) -> PythonStdioTransport | NodeStdioTransport | None:
        """Create process transport for Python or Node.js scripts."""
        script_path = config.get("script_path")
        if not script_path:
            self._logger.error(f"{name}: Script path not found")
            return None

        is_python = script_path.endswith(".py")
        is_js = script_path.endswith(".js")
        if not (is_python or is_js):
            self._logger.error(f"{name}: Unsupported script type")
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
            else:
                return NodeStdioTransport(
                    node_cmd=config.get("command", ""),
                    script_path=script_path,
                    args=config.get("args", []),
                    env=config.get("env"),
                    cwd=config.get("cwd"),
                )
        except Exception as e:
            self._logger.error(f"Error creating process transport for '{name}': {str(e)}")

            return None

    async def _create_sse_transport(self, name: str, config: dict[str, Any]) -> SSETransport | None:
        """Create SSE transport."""
        url = config.get("url")
        if not url:
            self._logger.error(f"{name}: URL not found")
            return None
        return SSETransport(url, headers=config.get("headers", {}))

    async def _create_ws_transport(self, name: str, config: dict[str, Any]) -> WSTransport | None:
        """Create WebSocket transport."""
        url = config.get("url")
        if not url:
            self._logger.error(f"{name}: URL not found")
            return None
        return WSTransport(url)

    async def _create_uvx_transport(
        self, name: str, config: dict[str, Any]
    ) -> UvxStdioTransport | None:
        """Create UVX transport."""
        tool_name = config.get("tool_name")
        if not tool_name:
            self._logger.error(f"{name}: Tool name not found")
            return None
        return UvxStdioTransport(
            tool_name=tool_name,
            from_package=config.get("from_package", ""),
            with_packages=config.get("with_packages", []),
            tool_args=config.get("args", []),
            env_vars=config.get("env", None),
            project_directory=config.get("project_directory", None),
            python_version=config.get("python_version", None),
        )

    async def _create_npx_transport(
        self, name: str, config: dict[str, Any]
    ) -> NpxStdioTransport | None:
        """Create NPX transport."""
        package = config.get("package")
        if not package:
            self._logger.error(f"{name}: Package not found")
            return None
        return NpxStdioTransport(
            package=package,
            args=config.get("args", []),
            project_directory=config.get("project_directory", None),
            env_vars=config.get("env", None),
            use_package_lock=config.get("use_package_lock", True),
        )
