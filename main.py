import os
import json
import logging
import httpx
from typing import Optional, List, Dict, Any, Union
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()
OPENPROJECT_HOST = os.getenv("OPENPROJECT_HOST", "http://localhost:8080").rstrip("/")
OPENPROJECT_API_KEY = os.getenv("OPENPROJECT_API_KEY", "")
VERIFY_SSL = os.getenv("OPENPROJECT_TLS_VERIFY", "True").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger("openproject-mcp")

# --- Server Initialization ---
mcp = FastMCP("OpenProject")

class OpenProjectClient:
    """Optimized client for OpenProject API v3 with connection pooling and caching."""
    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self.type_cache: Dict[str, str] = {}
        self.status_cache: Dict[str, str] = {}
        self.priority_cache: Dict[str, str] = {}

    async def _ensure_client(self):
        """Lazy initialization of the persistent connection pool."""
        if self.client:
            return
            
        api_token = OPENPROJECT_API_KEY.replace("apikey:", "")
        self.client = httpx.AsyncClient(
            base_url=f"{OPENPROJECT_HOST}/api/v3",
            auth=("apikey", api_token),
            verify=VERIFY_SSL,
            timeout=30.0,
            headers={"Content-Type": "application/json"}
        )
        logger.info(f"Connected to OpenProject at {OPENPROJECT_HOST}")
        
        # Lazy metadata caching
        try:
            await self._refresh_metadata_cache()
        except Exception as e:
            logger.warning(f"Could not fetch metadata: {e}")

    async def _refresh_metadata_cache(self):
        """Cache common resource HREFs to minimize future API calls."""
        # Cache Work Package Types
        resp = await self.client.get("types")
        if resp.status_code == 200:
            for t in resp.json().get("_embedded", {}).get("elements", []):
                self.type_cache[t["name"].lower()] = t["_links"]["self"]["href"]
        
        # Cache Priorities
        resp = await self.client.get("priorities")
        if resp.status_code == 200:
            for p in resp.json().get("_embedded", {}).get("elements", []):
                self.priority_cache[p["name"].lower()] = p["_links"]["self"]["href"]

    async def request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Wrapper for httpx requests with error handling."""
        await self._ensure_client()
        
        response = await self.client.request(method, path, **kwargs)
        if response.status_code >= 400:
            logger.error(f"API Error ({response.status_code}): {response.text}")
            response.raise_for_status()
        return response.json()

# Global client instance
op_client = OpenProjectClient()

# --- Tools ---

@mcp.tool()
async def list_projects(parent_id: Optional[str] = None) -> str:
    """
    Lists projects. If parent_id is provided, lists subprojects.
    Returns a formatted list of Project names, IDs, and identifiers.
    """
    params = {}
    if parent_id:
        params["filters"] = json.dumps([{"parent": {"operator": "=", "values": [parent_id]}}])
    
    try:
        data = await op_client.request("GET", "projects", params=params)
        elements = data.get("_embedded", {}).get("elements", [])
        if not elements:
            return "No projects found."
        
        lines = []
        for p in elements:
            lines.append(f"• {p['name']} (ID: {p['id']}, Identifier: {p['identifier']})")
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing projects: {str(e)}"

@mcp.tool()
async def get_project_details(project_id_or_identifier: str) -> str:
    """Fetches full details of a project, including description and status."""
    try:
        data = await op_client.request("GET", f"projects/{project_id_or_identifier}")
        # Clean up for LLM readability
        details = {
            "name": data.get("name"),
            "identifier": data.get("identifier"),
            "description": data.get("description", {}).get("raw", ""),
            "active": data.get("active"),
            "parent": data.get("_links", {}).get("parent", {}).get("title", "None")
        }
        return json.dumps(details, indent=2)
    except Exception as e:
        return f"Error getting project details: {str(e)}"

@mcp.tool()
async def create_work_package(
    project_id: str,
    subject: str,
    description: str = "",
    work_package_type: str = "Task",
    priority: str = "Normal"
) -> str:
    """
    Creates a new work package (Task, Milestone, Bug, etc.) in a specific project.
    """
    try:
        # Resolve Type and Priority from cache or fallback
        type_href = op_client.type_cache.get(work_package_type.lower(), "/api/v3/types/1")
        priority_href = op_client.priority_cache.get(priority.lower(), "/api/v3/priorities/1")

        payload = {
            "subject": subject,
            "description": {"raw": description},
            "_links": {
                "project": {"href": f"/api/v3/projects/{project_id}"},
                "type": {"href": type_href},
                "priority": {"href": priority_href}
            }
        }
        
        result = await op_client.request("POST", "work_packages", json_data=payload)
        return f"✅ Success! Created {work_package_type} '{subject}' with ID #{result['id']}."
    except Exception as e:
        return f"Error creating work package: {str(e)}"

@mcp.tool()
async def list_work_packages(project_id: str, status: Optional[str] = None) -> str:
    """Lists work packages for a specific project, optionally filtered by status name."""
    try:
        filters = [{"project": {"operator": "=", "values": [project_id]}}]
        if status:
            filters.append({"status": {"operator": "=", "values": [status]}})
        
        params = {"filters": json.dumps(filters)}
        data = await op_client.request("GET", "work_packages", params=params)
        elements = data.get("_embedded", {}).get("elements", [])
        
        if not elements:
            return f"No work packages found for project {project_id}."
        
        lines = [f"Work Packages for Project {project_id}:"]
        for wp in elements:
            lines.append(f"  #{wp['id']} [{wp['_links']['type']['title']}] {wp['subject']} (Status: {wp['_links']['status']['title']})")
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing work packages: {str(e)}"

@mcp.tool()
async def search_global(query: str) -> str:
    """Searches for work packages matching a query string across all projects."""
    try:
        # Using the native search filter
        filters = [{"subject": {"operator": "~", "values": [query]}}]
        params = {"filters": json.dumps(filters)}
        data = await op_client.request("GET", "work_packages", params=params)
        elements = data.get("_embedded", {}).get("elements", [])
        
        if not elements:
            return f"No matches found for '{query}'."
        
        lines = [f"Search results for '{query}':"]
        for wp in elements:
            proj = wp['_links']['project']['title']
            lines.append(f"  #{wp['id']} {wp['subject']} (Project: {proj})")
        return "\n".join(lines)
    except Exception as e:
        return f"Error during search: {str(e)}"

if __name__ == "__main__":
    mcp.run()
