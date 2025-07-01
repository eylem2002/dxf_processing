from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_keywords_tree():
    response = client.get("/api/keywords/tree")
    assert response.status_code == 200
    assert "name" in response.json()
    assert "children" in response.json()
