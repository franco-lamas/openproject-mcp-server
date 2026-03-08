---
name: openproject-mcp-manager
description: Use this skill to manage OpenProject resources including projects, work packages, comments, and wiki documentation through the OpenProject MCP server.
version: 1.2.0
---

# OpenProject MCP Skill 🚀

This skill enables interaction with an OpenProject instance via its MCP server. It supports full lifecycle management of tasks and documentation.

## 🛠️ Available Capabilities

### 🏢 Project Management
- **List Projects**: Use `list_projects` to explore hierarchies.
- **Project Details**: Use `get_project_details` for specific metadata.

### 📝 Work Packages (Tasks)
- **Lifecycle**: Create (`create_work_package`), search (`search_global`), and read (`list_work_packages`).
- **Updates**: Use `update_work_package` to change subject, description, priority, or **status** (e.g., "Closed", "In Progress").
- **Locking**: Always fetch `lockVersion` using `get_work_package_details` before performing updates.

### 💬 Collaboration
- **Comments**: Add notes with `add_work_package_comment`.
- **History**: View all activities with `list_work_package_activities`.

### 📖 Wiki & Documentation
- **Content**: Read (`get_wiki_page`) and list (`list_wiki_pages`) project documentation.
- **Authoring**: Create (`create_wiki_page`) or update (`update_wiki_page`) wiki entries.

## 🚦 Rules & Best Practices
1. **Optimistic Locking**: When updating work packages or wiki pages, you **must** provide the correct `lock_version`. Fetch the latest state before updating.
2. **Status Transitions**: You can update task status by name (e.g., "New", "Resolved", "Closed"). The server handles internal HREF resolution.
3. **Markdown Support**: All descriptions and wiki content support Markdown. Ensure raw strings are correctly escaped if necessary.
4. **Context Management**: When a user mentions a task ID, always verify its details first before suggesting or performing an update.

## 🔧 Setup Reference
The server runs by default on `http://localhost:8000` (FastAPI) or via stdio (MCP).
- **Environment**: Ensure `OPENPROJECT_HOST` and `OPENPROJECT_API_KEY` are configured.
