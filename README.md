# OpenProject MCP Server 🚀

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Model Context Protocol](https://img.shields.io/badge/MCP-1.0.0-orange.svg)](https://modelcontextprotocol.io/)

A professional [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that provides a robust interface to **OpenProject API v3**. Manage your projects, work packages, and activities directly through AI agents like Claude.

## ✨ Features

- 🛠️ **Full Work Package Lifecycle**: Create, list, search, and **update** work packages.
- 💬 **Activity Support**: List activities and add comments to any work package.
- 🏢 **Multi-Project Management**: Explore project hierarchies and subprojects.
- 🚀 **Dual Interface**: Seamlessly switch between **MCP (stdio)** and **FastAPI (REST)** modes.
- 🔒 **Secure**: Environment-based configuration with TLS verification support.

## 🛠️ MCP Tools Available

| Tool | Description |
|------|-------------|
| `list_projects` | List projects and subprojects. |
| `get_project_details` | Fetch full project metadata. |
| `list_work_packages` | List tasks/packages in a project with status filters. |
| `get_work_package_details` | Get detailed information including `lockVersion`. |
| `create_work_package` | Create new work packages (Tasks, Milestones, etc). |
| `update_work_package` | Update subject, description, or priority. |
| `search_global` | Global search across all work packages. |
| `add_work_package_comment` | Add a comment to a work package. |
| `list_work_package_activities` | View full history and comments of a task. |

## 🚀 Quick Start

### 🐳 Docker (Recommended)

1. Build the image:
   ```bash
   docker build -t openproject-mcp .
   ```
2. Run as API:
   ```bash
   docker run -d -p 8000:8000 --env-file .env openproject-mcp
   ```

### 🤖 Integration with Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "openproject": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm", "--network=host",
        "--env-file", "/absolute/path/to/.env",
        "openproject-mcp", "mcp"
      ]
    }
  }
}
```

## ⚙️ Configuration

Create a `.env` file based on `.env.example`:
- `OPENPROJECT_HOST`: Your instance URL (e.g., `https://myproject.openproject.com`)
- `OPENPROJECT_API_KEY`: Your API key (v3)
- `OPENPROJECT_TLS_VERIFY`: Set to `False` for self-signed certs.

## 📄 License
MIT License.
