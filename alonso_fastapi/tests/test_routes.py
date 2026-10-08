from starlette.testclient import TestClient  # Import TestClient
from app.main import app

client = TestClient(app)

def test_submit_job():
    """Test the /submit-job/ route."""
    response = client.post("/submit-job/", json={"college_name": "Test College"})
    assert response.status_code == 200
    assert response.json()["status"] == "Job submitted"
