# OpenProject MCP Server 🚀

A generic [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that provides a seamless interface to **OpenProject API v3**. This server allows AI agents (like Claude) to interact with your OpenProject instances to manage projects, work packages, and roadmaps.

## ✨ Features

- **Project Management**: List all projects, subprojects, and get detailed metadata.
- **Work Package Operations**: Create, update, and search for tasks, bugs, and milestones.
- **Roadmap Access**: Query project versions and milestones.
- **Hierarchical Support**: Navigate complex project structures (like parent-child relationships).
- **Docker-Ready**: Easy deployment using Docker or Docker Compose.
- **Security**: Environment variable configuration for sensitive API tokens.

## 🛠️ Configuration

The server requires the following environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENPROJECT_HOST` | Your OpenProject instance URL | `http://localhost:8080` |
| `OPENPROJECT_API_KEY` | Your API Token (Access Token) | `apikey:your_token_here` |
| `OPENPROJECT_TLS_VERIFY` | Verify SSL certificates (True/False) | `True` |

## 🚀 Quick Start (Docker)

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/openproject-mcp-server.git
   cd openproject-mcp-server
   ```
2. Configure your environment:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```
3. Run with Docker:
   ```bash
   docker build -t openproject-mcp-server .
   docker run -i --rm --env-file .env openproject-mcp-server
   ```

## 🤖 Usage with Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "openproject": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--env-file",
        "/path/to/your/openproject-mcp-server/.env",
        "openproject-mcp-server"
      ]
    }
  }
}
```

## 📄 License
MIT License.
