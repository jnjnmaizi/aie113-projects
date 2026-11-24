from fastapi.testclient import TestClient
from bean_vision.api import create_app
from bean_vision.settings import Settings
from conftest import FakeModel


def test_success(client, photo):
    response = client.post("/v1/predict", files={"file": ("leaf.png", photo, "image/png")})
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "bean_rust"
    assert data["not_sure"] is False
    assert abs(sum(data["scores"].values()) - 1) < 1e-6
    assert data["model_version"] == "1.0.0"


def test_low_confidence(photo):
    class Unsure(FakeModel):
        def predict(self, photo):
            return [0.3, 0.3, 0.4]

    with TestClient(create_app(Settings(), Unsure)) as client:
        answer = client.post("/v1/predict", files={"file": ("leaf.png", photo, "image/png")}).json()
        assert answer["not_sure"] is True
        assert answer["decision"] == "not_sure"


def test_missing_file(client):
    response = client.post("/v1/predict")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"


def test_wrong_type(client):
    response = client.post("/v1/predict", files={"file": ("secret.txt", b"PRIVATE-VALUE", "text/plain")})
    assert response.status_code == 415
    assert "PRIVATE-VALUE" not in response.text
    assert "secret.txt" not in response.text


def test_fake_image(client):
    response = client.post("/v1/predict", files={"file": ("leaf.png", b"not-image", "image/png")})
    assert response.status_code == 422


def test_upload_size(photo):
    with TestClient(create_app(Settings(max_upload_bytes=1024), FakeModel)) as client:
        response = client.post("/v1/predict", files={"file": ("leaf.png", b"a" * 1025, "image/png")})
        assert response.status_code == 413
        response = client.post("/v1/predict", content=b"a" * 70000)
        assert response.status_code == 413


def test_huge_dimensions(photo):
    with TestClient(create_app(Settings(max_pixels=100), FakeModel)) as client:
        response = client.post("/v1/predict", files={"file": ("leaf.png", photo, "image/png")})
        assert response.status_code == 413


def test_health_readiness_and_docs(client):
    assert client.get("/health").json() == {"status": "alive"}
    assert client.get("/ready").status_code == 200
    assert client.get("/docs").status_code == 200
    assert "/v1/predict" in client.get("/openapi.json").json()["paths"]


def test_failed_startup_safe():
    def broken():
        raise RuntimeError("DO-NOT-LEAK-TOKEN")

    with TestClient(create_app(Settings(), broken)) as client:
        assert client.get("/health").status_code == 200
        response = client.get("/ready")
        assert response.status_code == 503
        assert "DO-NOT-LEAK" not in response.text


def test_model_loaded_once(photo):
    calls = []

    def factory():
        calls.append(1)
        return FakeModel()

    with TestClient(create_app(Settings(), factory)) as client:
        for _ in range(2):
            assert (
                client.post("/v1/predict", files={"file": ("leaf.png", photo, "image/png")}).status_code
                == 200
            )
    assert len(calls) == 1


def test_explanation(client, photo):
    response = client.post("/v1/explain", files={"file": ("leaf.png", photo, "image/png")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


def test_internal_error_safe(photo):
    class Broken(FakeModel):
        def predict(self, photo):
            raise RuntimeError("DO-NOT-LEAK")

    with TestClient(create_app(Settings(), Broken), raise_server_exceptions=False) as client:
        response = client.post("/v1/predict", files={"file": ("leaf.png", photo, "image/png")})
        assert response.status_code == 500
        assert "DO-NOT-LEAK" not in response.text
