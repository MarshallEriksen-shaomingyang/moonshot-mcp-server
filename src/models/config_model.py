from pydantic import BaseModel


class ServerConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = "8000"
    name: str
    version: str = "1.0.0"


class ProxyConfig(BaseModel):
    type: str
    prefix: str
    url: str | None = None
    command: str | None = None
    script_path: str | None = None
    args: list[str] = []
    env: dict | None = None
    cwd: str | None = None
    retry: int = 1
    whiteLists: list[str] | None = None  # noqa: N815
    exclude: list[str] = []
    headers: dict = {}
    tool_name: str | None = None
    from_package: str = ""
    with_packages: list[str] = []
    package: str | None = None
    project_directory: str | None = None
    python_version: str | None = None


class Config(BaseModel):
    server: ServerConfig
    mcpServers: dict[str, ProxyConfig] = {}  # noqa: N815
