"""Coordinate a diagnosis through an interchangeable model interface."""

from typing import Protocol
from bean_vision.domain import Diagnosis, decide


class ModelPort(Protocol):
    def predict(self, photo: bytes) -> list[float]: ...
    def explain(self, photo: bytes) -> bytes: ...


class VisionService:
    def __init__(self, model: ModelPort, threshold: float):
        self.model = model
        self.threshold = threshold

    def diagnose(self, photo: bytes) -> Diagnosis:
        return decide(self.model.predict(photo), self.threshold)

    def explain(self, photo: bytes) -> bytes:
        return self.model.explain(photo)
