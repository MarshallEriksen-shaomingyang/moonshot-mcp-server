from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator


class ErrorMessages:
    TYPE_ERROR = "type must be one of 'process', 'http', 'https', 'websocket', 'uvx', 'npx'"
    PREFIX_ERROR = "prefix must be set"
    URL_ERROR = "url must be set when type is 'http', 'https', 'websocket'"
    COMMAND_ERROR = "command must be set when type is 'process'"


class ServerConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = "8000"
    name: str
    version: str = "1.0.0"


class ProxyConfig(BaseModel):
    # 可选值: "process", "http", "https", "websocket", "uvx", "npx"
    type: str = Field(..., alias="type")
    prefix: str = Field(..., alias="prefix")
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

    @model_validator(mode="after")
    def validate_config(self) -> "ProxyConfig":
        # 验证type字段
        if self.type not in ["process", "http", "https", "websocket", "uvx", "npx"]:
            raise ValueError(ErrorMessages.TYPE_ERROR)

        # 验证prefix字段
        if not self.prefix:
            raise ValueError(ErrorMessages.PREFIX_ERROR)

        # 根据type验证相关字段
        if self.type in ["http", "https", "websocket"] and not self.url:
            raise ValueError(ErrorMessages.URL_ERROR)

        if self.type == "process" and not self.command:
            raise ValueError(ErrorMessages.COMMAND_ERROR)

        return self


class Config(BaseModel):
    server: ServerConfig
    mcpServers: dict[str, ProxyConfig] = {}  # noqa: N815
