from io import BytesIO
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from bean_vision.api import create_app
from bean_vision.settings import Settings


class FakeModel:
    def predict(self, photo):
        return [0.05, 0.90, 0.05]

    def explain(self, photo):
        return photo


@pytest.fixture
def photo():
    stream = BytesIO()
    Image.new("RGB", (32, 32), "green").save(stream, format="PNG")
    return stream.getvalue()


@pytest.fixture
def client():
    with TestClient(create_app(Settings(), FakeModel)) as client:
        yield client
