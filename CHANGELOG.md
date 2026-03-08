# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-03-08

### Added
- **Wiki Support**: Tools to list, read, create, and update project wiki pages.
- **Task Comments**: Capability to add comments and view the full activity history of work packages.
- **Status Updates**: Enhanced `update_work_package` to support status transitions by name (e.g., "Closed").
- **Optimistic Locking**: Support for `lockVersion` in both tasks and wiki updates.
- **Automated Testing**: Added a `pytest` suite with mocking for API calls.
- **GitHub Copilot Skill**: Added `SKILL.md` for better agent discovery and integration.
- **Professional README**: Added badges, detailed tool tables, and clearer setup instructions.

### Changed
- **Version Tracking**: Unified project version across `pyproject.toml`, `main.py`, and `SKILL.md`.

## [1.0.0] - 2026-03-07

### Added
- **Core MCP Functionality**: Initial tools for project and work package management.
- **Dual Mode**: Support for both FastMCP (stdio) and FastAPI (REST).
- **Dockerization**: Ready-to-run Dockerfile and `.env` configuration.
- **Metadata Caching**: Optimized resolution of types and priorities.

[1.1.0]: https://github.com/franco-lamas/openproject-mcp-server/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/franco-lamas/openproject-mcp-server/releases/tag/v1.0.0
