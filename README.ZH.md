# 🚀 Moonshot MCP Server Gateway
## 📝✨ 描述
Moonshot MCP Server Gateway 是一个轻量级的网关服务器，主要功能包括：

- 提供统一的连接入口，客户端只需连接该服务器即可访问多个MCP服务器
- 简化了MCP服务器的连接和管理流程
- 支持多种协议，包括 Network Transports、Local Transports等 具体协议请参考[MCP协议文档](协议请参考[MCP协议文档](https://gofastmcp.com/clients/transports#in-memory-transports))


## ⌨️🚀 快速开始
```bash
git clone https://github.com/MarshallEriksen-shaomingyang/moonshot-mcp-server.git
cp .env.example .env
cp moonshot_config.example.toml moonshot_config.toml
# 创建虚拟环境
uv venv
# 激活虚拟环境
source .venv/bin/activate
# 启动项目
uv run server.py
```

## ⚙️📋 MCP 配置详情 (moonshot_config.toml)

### 📑 配置文件结构说明

#### 1️⃣ 服务器基础配置 [server]

| 配置项 | 说明 | 必填 |
|--------|------|------|
| name | 服务器名称 | 是 |
| version | 服务器版本号 | 是 |
| port | 监听端口 | 是 |
| host | 监听地址 | 是 |

#### 2️⃣ MCP子服务器配置 [mcpServers]

MCP支持多种类型的服务器配置，每个子服务器配置都需要指定唯一的名称（如 `[mcpServers.server_name]`）和必填的 `prefix` 字段用于API路由。

##### ⚙️ 进程型服务器 (type = "process")

| 配置项 | 说明 | 必填 |
|--------|------|------|
| command | 解释器命令 | 是 |
| script_path | 脚本路径 | 是 |
| args | 启动参数 | 否 |
| prefix | API路由前缀 | 是 |
| exclude | 需要排除的命令 | 否 |
| cwd | 工作目录 | 否 |
| env | 环境变量配置 | 否 |

##### 🌐 HTTP/HTTPS服务器 (type = "http"/"https")

| 配置项 | 说明 | 必填 |
|--------|------|------|
| url | 服务器URL | 是 |
| prefix | API路由前缀 | 是 |
| headers | 请求头配置 | 否 |

##### 🔌 WebSocket服务器 (type = "websocket")

| 配置项 | 说明 | 必填 |
|--------|------|------|
| url | WebSocket服务器地址 | 是 |
| prefix | API路由前缀 | 是 |

##### 📦 NPX服务器 (type = "npx")

| 配置项 | 说明 | 必填 |
|--------|------|------|
| package | NPM包名 | 是 |
| args | 启动参数 | 否 |
| prefix | API路由前缀 | 是 |
| env | 环境变量 | 否 |
| project_directory | 项目目录 | 否 |
| use_package_lock | 是否使用 package-lock.json | 否 |

##### 🐍 UVX服务器 (type = "uvx")

| 配置项 | 说明 | 必填 |
|--------|------|------|
| tool_name | 工具名称 | 是 |
| from_package | 包名称 | 是 |
| with_packages | 依赖包列表 | 否 |
| args | 工具参数 | 否 |
| prefix | API路由前缀 | 是 |
| env | 环境变量 | 否 |
| project_directory | 项目目录 | 否 |
| python_version | python 版本 | 否 |

### 🧩 配置示例

```toml
# 基础服务器配置
[server]
name = "AlphaCore Server"
version = "1.0.0"
port = 8090
host = "0.0.0.0"

# 进程型服务器示例
[mcpServers.python_server]
type = "process"
command = "python3"
script_path = "server.py"
prefix = "py"
cwd = "/data/moonshot_tools"

# HTTP服务器示例
[mcpServers.http_server]
type = "https"
url = "https://api.example.com/mcp"
prefix = "api"

# 更多配置示例请参考 moonshot_config.example.toml
```
## 🔗 mcp 工具列表：

- [Awesome MCP Server List](https://github.com/punkpeye/awesome-mcp-servers)
- [mcp.so](https://mcp.so/)
- [glama](https://glama.ai/mcp/servers)