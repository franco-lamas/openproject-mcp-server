---
description: Interacción con OpenProject mediante el servidor MCP Docker
---

Este workflow permite a Antigravity gestionar proyectos y tareas en OpenProject usando el servidor MCP disponible.

### Comandos base
Para ejecutar cualquier herramienta, se debe usar el script puente:
`python3 /tmp/op_bridge.py <herramienta> '<argumentos_json>'`

### Herramientas disponibles:
1. **list_projects**: `python3 /tmp/op_bridge.py list_projects`
2. **get_project_details**: `python3 /tmp/op_bridge.py get_project_details '{"project_id_or_identifier": "ID"}'`
3. **create_work_package**: `python3 /tmp/op_bridge.py create_work_package '{"project_id": "ID", "subject": "Titulo", "description": "...", "work_package_type": "Task"}'`
4. **list_work_packages**: `python3 /tmp/op_bridge.py list_work_packages '{"project_id": "ID"}'`
5. **search_global**: `python3 /tmp/op_bridge.py search_global '{"query": "termino"}'`

### Notas de configuración:
- El servidor corre en Docker con la imagen `openproject-mcp-server`.
- Requiere el archivo `.env` en la raíz del proyecto.
- Usa `--network=host` para conectar con el OpenProject local en el puerto 8080.
