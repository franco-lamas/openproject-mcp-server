import os
import json
import logging
import httpx
from typing import Optional, List, Dict, Any, Union
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

# --- Configuration ---
load_dotenv()
OPENPROJECT_HOST = os.getenv("OPENPROJECT_HOST", "http://localhost:8080").rstrip("/")
OPENPROJECT_API_KEY = os.getenv("OPENPROJECT_API_KEY", "")
VERIFY_SSL = os.getenv("OPENPROJECT_TLS_VERIFY", "True").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger("openproject-api")

# --- OpenProject Client ---
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

        # Cache Statuses
        resp = await self.client.get("statuses")
        if resp.status_code == 200:
            for s in resp.json().get("_embedded", {}).get("elements", []):
                self.status_cache[s["name"].lower()] = s["_links"]["self"]["href"]

    async def request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Wrapper for httpx requests with error handling."""
        await self._ensure_client()
        
        # Handle the case where json_data is passed (legacy from previous version)
        if "json_data" in kwargs:
            kwargs["json"] = kwargs.pop("json_data")

        response = await self.client.request(method, path, **kwargs)
        if response.status_code >= 400:
            logger.error(f"API Error ({response.status_code}): {response.text}")
            response.raise_for_status()
        return response.json()

# Global client instance
op_client = OpenProjectClient()

# --- FastAPI Setup ---
app = FastAPI(title="OpenProject API Wrapper", version="1.1.0")
mcp = FastMCP("OpenProject")

# --- Models ---
class WorkPackageCreate(BaseModel):
    project_id: str
    subject: str
    description: str = ""
    work_package_type: str = "Task"
    priority: str = "Normal"

class WorkPackageUpdate(BaseModel):
    subject: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    lock_version: int

class WikiPageCreate(BaseModel):
    project_id: str
    title: str
    content: str

class WikiPageUpdate(BaseModel):
    content: str
    lock_version: int

# --- Shared Logic / Tools ---

@mcp.tool()
@app.get("/work_packages/{wp_id}")
async def get_work_package_details(wp_id: str):
    """Fetches full details of a specific work package."""
    try:
        data = await op_client.request("GET", f"work_packages/{wp_id}")
        return {
            "id": data.get("id"),
            "lockVersion": data.get("lockVersion"),
            "subject": data.get("subject"),
            "description": data.get("description", {}).get("raw", ""),
            "status": data.get("_links", {}).get("status", {}).get("title"),
            "priority": data.get("_links", {}).get("priority", {}).get("title"),
            "type": data.get("_links", {}).get("type", {}).get("title")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@mcp.tool()
@app.patch("/work_packages/{wp_id}")
async def update_work_package(wp_id: str, wp: WorkPackageUpdate):
    """Updates an existing work package. Requires lock_version for optimistic locking."""
    try:
        payload = {"lockVersion": wp.lock_version}
        
        if wp.subject:
            payload["subject"] = wp.subject
        if wp.description:
            payload["description"] = {"raw": wp.description}
        
        # Links preparation
        links = {}
        
        # Priority resolution
        if wp.priority:
            priority_href = op_client.priority_cache.get(wp.priority.lower())
            if not priority_href:
                await op_client._refresh_metadata_cache()
                priority_href = op_client.priority_cache.get(wp.priority.lower())
            if priority_href:
                links["priority"] = {"href": priority_href}

        # Status resolution
        if wp.status:
            status_href = op_client.status_cache.get(wp.status.lower())
            if not status_href:
                await op_client._refresh_metadata_cache()
                status_href = op_client.status_cache.get(wp.status.lower())
            if status_href:
                links["status"] = {"href": status_href}
        
        if links:
            payload["_links"] = links

        result = await op_client.request("PATCH", f"work_packages/{wp_id}", json=payload)
        return {"message": "Updated successfully", "id": result['id'], "lockVersion": result['lockVersion']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@mcp.tool()
@app.get("/projects")
async def list_projects(parent_id: Optional[str] = None):
    """Lists projects. If parent_id is provided, lists subprojects."""
    params = {}
    if parent_id:
        params["filters"] = json.dumps([{"parent": {"operator": "=", "values": [parent_id]}}])
    
    try:
        data = await op_client.request("GET", "projects", params=params)
        return data.get("_embedded", {}).get("elements", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@mcp.tool()
@app.get("/projects/{project_id_or_identifier}")
async def get_project_details(project_id_or_identifier: str):
    """Fetches full details of a project."""
    try:
        data = await op_client.request("GET", f"projects/{project_id_or_identifier}")
        return {
            "name": data.get("name"),
            "identifier": data.get("identifier"),
            "description": data.get("description", {}).get("raw", ""),
            "active": data.get("active"),
            "parent": data.get("_links", {}).get("parent", {}).get("title", "None")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@mcp.tool()
@app.post("/work_packages")
async def create_work_package(wp: WorkPackageCreate):
    """Creates a new work package."""
    try:
        # Resolve Type and Priority from cache or fallback
        type_href = op_client.type_cache.get(wp.work_package_type.lower(), "/api/v3/types/1")
        priority_href = op_client.priority_cache.get(wp.priority.lower(), "/api/v3/priorities/1")

        payload = {
            "subject": wp.subject,
            "description": {"raw": wp.description},
            "_links": {
                "project": {"href": f"/api/v3/projects/{wp.project_id}"},
                "type": {"href": type_href},
                "priority": {"href": priority_href}
            }
        }
        
        result = await op_client.request("POST", "work_packages", json=payload)
        return {"message": "Success", "id": result['id'], "subject": wp.subject}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@mcp.tool()
@app.get("/work_packages")
async def list_work_packages(project_id: str, status: Optional[str] = None):
    """Lists work packages for a specific project."""
    try:
        filters = [{"project": {"operator": "=", "values": [project_id]}}]
        if status:
            filters.append({"status": {"operator": "=", "values": [status]}})
        
        params = {"filters": json.dumps(filters)}
        data = await op_client.request("GET", "work_packages", params=params)
        return data.get("_embedded", {}).get("elements", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@mcp.tool()
@app.get("/search")
async def search_global(query: str):
    """Searches for work packages matching a query string."""
    try:
        filters = [{"subject": {"operator": "~", "values": [query]}}]
        params = {"filters": json.dumps(filters)}
        data = await op_client.request("GET", "work_packages", params=params)
        return data.get("_embedded", {}).get("elements", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@mcp.tool()
@app.get("/work_packages/{wp_id}/activities")
async def list_work_package_activities(wp_id: str):
    """Fetches all activities (comments, changes) for a specific work package."""
    try:
        data = await op_client.request("GET", f"work_packages/{wp_id}/activities")
        activities = []
        for activity in data.get("_embedded", {}).get("elements", []):
            activities.append({
                "comment": activity.get("comment", {}).get("raw", ""),
                "author": activity.get("_links", {}).get("author", {}).get("title"),
                "createdAt": activity.get("createdAt")
            })
        return activities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@mcp.tool()
@app.post("/work_packages/{wp_id}/activities")
async def add_work_package_comment(wp_id: str, comment: str):
    """Adds a new comment (activity) to a specific work package."""
    try:
        payload = {"comment": {"raw": comment}}
        result = await op_client.request("POST", f"work_packages/{wp_id}/activities", json=payload)
        return {"message": "Comment added successfully", "id": result.get("id")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Wiki Tools ---

@mcp.tool()
@app.get("/projects/{project_id}/wiki_pages")
async def list_wiki_pages(project_id: str):
    """Lists all wiki pages for a specific project."""
    try:
        data = await op_client.request("GET", f"projects/{project_id}/wiki_pages")
        return data.get("_embedded", {}).get("elements", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@mcp.tool()
@app.get("/wiki_pages/{page_id}")
async def get_wiki_page(page_id: str):
    """Fetches details and content of a specific wiki page."""
    try:
        data = await op_client.request("GET", f"wiki_pages/{page_id}")
        return {
            "id": data.get("id"),
            "title": data.get("title"),
            "content": data.get("text", {}).get("raw", ""),
            "lockVersion": data.get("lockVersion"),
            "project": data.get("_links", {}).get("project", {}).get("title")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@mcp.tool()
@app.post("/projects/{project_id}/wiki_pages")
async def create_wiki_page(page: WikiPageCreate):
    """Creates a new wiki page in a project."""
    try:
        payload = {
            "title": page.title,
            "text": {"raw": page.content}
        }
        result = await op_client.request("POST", f"projects/{page.project_id}/wiki_pages", json=payload)
        return {"message": "Wiki page created", "id": result.get("id"), "title": result.get("title")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@mcp.tool()
@app.patch("/wiki_pages/{page_id}")
async def update_wiki_page(page_id: str, page: WikiPageUpdate):
    """Updates an existing wiki page. Requires lock_version."""
    try:
        payload = {
            "text": {"raw": page.content},
            "lockVersion": page.lock_version
        }
        result = await op_client.request("PATCH", f"wiki_pages/{page_id}", json=payload)
        return {"message": "Wiki page updated", "id": result.get("id"), "lockVersion": result.get("lockVersion")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Entry point differentiation
if __name__ == "__main__":
    import uvicorn
    import sys
    
    # If run with 'mcp-mode' or similar, we could run the MCP stdio
    # But for a standard 'python main.py', let's default to the web server
    if len(sys.argv) > 1 and sys.argv[1] == "mcp":
        mcp.run()
    else:
        uvicorn.run(app, host="0.0.0.0", port=8000)
