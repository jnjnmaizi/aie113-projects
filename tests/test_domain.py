import pytest
from bean_vision.domain import decide
from bean_vision.settings import Settings


@pytest.mark.parametrize(
    "scores,unsure", [([0.1, 0.8, 0.1], False), ([0.1, 0.799, 0.101], True), ([0, 1, 0], False)]
)
def test_threshold(scores, unsure):
    answer = decide(scores, 0.8)
    assert answer.not_sure is unsure
    assert answer.decision == ("not_sure" if unsure else "bean_rust")


@pytest.mark.parametrize("scores", [[], [0.5, 0.5], [-1, 1, 1], [float("nan"), 0, 1], [0.1, 0.1, 0.1]])
def test_invalid_scores(scores):
    with pytest.raises(ValueError):
        decide(scores, 0.8)


def test_settings_reject_bad_threshold():
    with pytest.raises(ValueError):
        Settings(not_sure_below=1.5)


def test_secret_not_printed():
    secret = "practice-only-not-a-real-token"
    settings = Settings(hf_token=secret)
    assert secret not in str(settings)
    assert secret not in settings.model_dump_json()
