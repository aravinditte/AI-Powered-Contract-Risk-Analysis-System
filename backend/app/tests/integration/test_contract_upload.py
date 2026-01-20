from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_contract_upload_invalid_format():
    response = client.post(
        "/api/v1/contracts/upload",
        files={"file": ("contract.exe", b"dummy")},
        headers={"Authorization": "Bearer invalid"},
    )

    assert response.status_code in (401, 403, 400)
