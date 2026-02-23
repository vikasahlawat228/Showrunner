import pytest
from fastapi.testclient import TestClient
from antigravity_tool.server.app import app
from antigravity_tool.services.job_service import JobService
from antigravity_tool.schemas.job import JobStatus

client = TestClient(app)

def test_jobs_api():
    # Initial list
    response = client.get("/api/v1/jobs/")
    assert response.status_code == 200

    # Create dummy job
    response = client.post("/api/v1/jobs/", json={"job_type": "unknown_test", "payload": {}})
    assert response.status_code == 201
    job_id = response.json()["job_id"]

    # Get job
    response = client.get(f"/api/v1/jobs/{job_id}")
    assert response.status_code == 200
    job = response.json()
    assert job["id"] == job_id
    assert job["job_type"] == "unknown_test"
    assert job["status"] == "failed"

    # List all
    response = client.get("/api/v1/jobs/?active_only=false")
    assert response.status_code == 200
    jobs = [j["id"] for j in response.json()]
    assert job_id in jobs

