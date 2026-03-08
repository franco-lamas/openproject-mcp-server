import pytest
from httpx import AsyncClient
from main import app, op_client
import json

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_list_projects(client, mocker):
    # Mocking the op_client request
    mock_response = {
        "_embedded": {
            "elements": [
                {"name": "Project A", "identifier": "proj-a"},
                {"name": "Project B", "identifier": "proj-b"}
            ]
        }
    }
    mocker.patch.object(op_client, 'request', return_value=mock_response)
    
    response = await client.get("/projects")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Project A"

@pytest.mark.asyncio
async def test_create_work_package(client, mocker):
    mock_response = {"id": 123, "subject": "Test Task"}
    mocker.patch.object(op_client, 'request', return_value=mock_response)
    # Mock cache
    op_client.type_cache = {"task": "/api/v3/types/1"}
    op_client.priority_cache = {"normal": "/api/v3/priorities/1"}

    payload = {
        "project_id": "demo",
        "subject": "Test Task",
        "description": "Desc",
        "work_package_type": "Task",
        "priority": "Normal"
    }
    response = await client.post("/work_packages", json=payload)
    assert response.status_code == 200
    assert response.json()["id"] == 123

@pytest.mark.asyncio
async def test_wiki_tools(client, mocker):
    mock_wiki_list = {
        "_embedded": {
            "elements": [{"id": 1, "title": "Wiki Home"}]
        }
    }
    mocker.patch.object(op_client, 'request', return_value=mock_wiki_list)
    
    response = await client.get("/projects/demo/wiki_pages")
    assert response.status_code == 200
    assert response.json()[0]["title"] == "Wiki Home"

@pytest.mark.asyncio
async def test_get_wiki_page(client, mocker):
    mock_wiki_page = {
        "id": 1,
        "title": "Wiki Home",
        "text": {"raw": "Welcome to the wiki!"},
        "lockVersion": 5,
        "_links": {"project": {"title": "Demo Project"}}
    }
    mocker.patch.object(op_client, 'request', return_value=mock_wiki_page)
    
    response = await client.get("/wiki_pages/1")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Wiki Home"
    assert "Welcome" in data["content"]
