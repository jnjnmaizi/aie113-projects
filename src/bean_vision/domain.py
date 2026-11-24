"""Pure business rules: no web, image or machine-learning imports."""

from dataclasses import dataclass
from math import isclose, isfinite

LABELS = ("angular_leaf_spot", "bean_rust", "healthy")


@dataclass(frozen=True)
class Diagnosis:
    label: str
    confidence: float
    scores: dict[str, float]
    not_sure: bool
    decision: str


def decide(probabilities: list[float], threshold: float) -> Diagnosis:
    if not 0 <= threshold <= 1:
        raise ValueError("Threshold must be between zero and one")
    if len(probabilities) != 3 or any(not isfinite(p) or not 0 <= p <= 1 for p in probabilities):
        raise ValueError("Expected three finite probabilities")
    if not isclose(sum(probabilities), 1, abs_tol=1e-5):
        raise ValueError("Probabilities must sum to one")
    best = max(range(3), key=probabilities.__getitem__)
    unsure = probabilities[best] < threshold
    return Diagnosis(
        LABELS[best],
        probabilities[best],
        dict(zip(LABELS, probabilities)),
        unsure,
        "not_sure" if unsure else LABELS[best],
    )
