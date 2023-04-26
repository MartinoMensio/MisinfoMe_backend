from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)


def test_status():
    response = client.get("/misinfo/api/utils/status")
    assert response.status_code == 200
    # assert response['status'] == "ok"


def test_unshorten():
    response = client.get(
        "/misinfo/api/utils/unshorten",
        params={"url": "https://bit.ly/claimreview-example"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "afp.com" in data["url_full"]
