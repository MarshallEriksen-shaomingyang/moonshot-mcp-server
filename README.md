# 🚀 Moonshot MCP Server Gateway
## 📝✨ Description
Moonshot MCP Server Gateway is a lightweight gateway server with the following main features:

- Provides a unified connection entry point, allowing clients to access multiple MCP servers by connecting to this server
- Simplifies the connection and management process of MCP servers
- Supports multiple protocols, including Network Transports, Local Transports, etc. For specific protocols, please refer to the [MCP Protocol Documentation](https://gofastmcp.com/clients/transports#in-memory-transports)

## ⌨️🚀 Quick Start
```bash
git clone https://github.com/MarshallEriksen-shaomingyang/moonshot-mcp-server.git
cp .env.example .env
cp moonshot_config.example.toml moonshot_config.toml
# Create virtual environment
uv venv
# Activate virtual environment
source .venv/bin/activate
# Start the project
uv run server.py --mode http or uv run server.py --mode sse
```

## ⚙️📋 MCP Configuration Details (moonshot_config.toml)

### 📑 Configuration File Structure

#### 1️⃣ Server Basic Configuration [server]

| Config Item | Description | Required |
|-------------|-------------|----------|
| name | Server name | Yes |
| version | Server version | Yes |
| port | Listening port | Yes |
| host | Listening address | Yes |

#### 2️⃣ MCP Sub-server Configuration [mcpServers]

MCP supports multiple types of server configurations. Each sub-server configuration needs to specify a unique name (e.g., `[mcpServers.server_name]`) and a required `prefix` field for API routing.

##### ⚙️ Process Server (type = "process")

| Config Item | Description | Required |
|-------------|-------------|----------|
| command | Interpreter command | Yes |
| script_path | Script path | Yes |
| args | Startup parameters | No |
| prefix | API routing prefix | Yes |
| exclude | Commands to exclude | No |
| cwd | Working directory | No |
| env | Environment variables | No |

##### 🌐 HTTP/HTTPS Server (type = "http"/"https")

| Config Item | Description | Required |
|-------------|-------------|----------|
| url | Server URL | Yes |
| prefix | API routing prefix | Yes |
| headers | Request headers | No |

##### 🔌 WebSocket Server (type = "websocket")

| Config Item | Description | Required |
|-------------|-------------|----------|
| url | WebSocket server address | Yes |
| prefix | API routing prefix | Yes |

##### 📦 NPX Server (type = "npx")

| Config Item | Description | Required |
|-------------|-------------|----------|
| package | NPM package name | Yes |
| args | Startup parameters | No |
| prefix | API routing prefix | Yes |
| env | Environment variables | No |
| project_directory | Project directory | No |
| use_package_lock | Whether to use package-lock.json | No |

##### 🐍 UVX Server (type = "uvx")

| Config Item | Description | Required |
|-------------|-------------|----------|
| tool_name | Tool name | Yes |
| from_package | Package name | No |
| with_packages | Dependency package list | No |
| args | Tool parameters | No |
| prefix | API routing prefix | Yes |
| env | Environment variables | No |
| project_directory | Project directory | No |
| python_version | Python version | No |

### 🧩 Configuration Example

```toml
# Basic server configuration
[server]
name = "AlphaCore Server"
version = "1.0.0"
port = 8090
host = "0.0.0.0"

# Process server example
[mcpServers.python_server]
type = "process"
command = "python3"
script_path = "server.py"
prefix = "py"
cwd = "/data/moonshot_tools"

# HTTP server example
[mcpServers.http_server]
type = "https"
url = "https://api.example.com/mcp"
prefix = "api"

# For more configuration examples, please refer to moonshot_config.example.toml
```

## 🔗 MCP Tool List:

- [Awesome MCP Server List](https://github.com/punkpeye/awesome-mcp-servers)
- [mcp.so](https://mcp.so/)
- [glama](https://glama.ai/mcp/servers)

