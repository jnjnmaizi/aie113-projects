from io import BytesIO
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageEnhance
import pytest
from bean_vision.adapters.model import HuggingFaceModel
from bean_vision.domain import decide

pytestmark = pytest.mark.real
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def model():
    # Missing model is a failure, never a silent skip.
    return HuggingFaceModel(ROOT / "artifacts/model")


def png(image):
    out = BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


def test_golden(model):
    golden = json.loads((ROOT / "tests/fixtures/golden.json").read_text())
    for case in golden["cases"]:
        actual = model.predict((ROOT / "tests/fixtures" / case["file"]).read_bytes())
        np.testing.assert_allclose(actual, case["scores"], atol=1e-5, rtol=1e-5)


def test_preprocessing(model):
    _, values = model.prepare(png(Image.new("RGB", (500, 500), (255, 0, 128))))
    assert tuple(values.shape) == (1, 3, 224, 224)
    np.testing.assert_allclose(values[0, :, 100, 100].numpy(), [1, -1, 128 / 127.5 - 1], atol=1e-5)


def test_repeatable(model):
    photo = (ROOT / "tests/fixtures/leaf-0.png").read_bytes()
    np.testing.assert_array_equal(model.predict(photo), model.predict(photo))


def test_gray_and_noise_not_sure(model):
    images = [
        Image.new("RGB", (224, 224), (128, 128, 128)),
        Image.fromarray(np.random.default_rng(42).integers(0, 256, (224, 224, 3), dtype=np.uint8)),
    ]
    for image in images:
        assert decide(model.predict(png(image)), 0.8).not_sure


def test_reference_quality_and_invariance(model):
    from datasets import load_dataset

    manifest = json.loads((ROOT / "model_manifest.json").read_text())
    url = f"hf://datasets/{manifest['dataset_id']}@{manifest['dataset_revision']}/data/test-00000-of-00001.parquet"
    data = load_dataset("parquet", data_files={"test": url}, split="test")
    assert len(data) == 128
    assert data.features["labels"].names == ["angular_leaf_spot", "bean_rust", "healthy"]
    counts = np.bincount(data["labels"], minlength=3)
    assert counts.tolist() == [43, 43, 42]
    correct = brighter = rotated = 0
    for row in data:
        image = row["image"].convert("RGB")
        assert image.size == (500, 500)
        pred = int(np.argmax(model.predict(png(image))))
        correct += pred == row["labels"]
        brighter += int(np.argmax(model.predict(png(ImageEnhance.Brightness(image).enhance(1.1))))) == pred
        rotated += int(np.argmax(model.predict(png(image.rotate(5))))) == pred
    metrics = {
        "n": 128,
        "correct": correct,
        "accuracy": correct / 128,
        "baseline": int(counts.max()) / 128,
        "brightness_agreement": brighter / 128,
        "rotation_agreement": rotated / 128,
        "thresholds_fixed_before_run": {
            "accuracy": 0.90,
            "brightness_agreement": 0.95,
            "rotation_agreement": 0.95,
        },
    }
    (ROOT / "evidence").mkdir(exist_ok=True)
    (ROOT / "evidence/behaviour.json").write_text(json.dumps(metrics, indent=2))
    assert metrics["accuracy"] >= 0.90
    assert metrics["accuracy"] > metrics["baseline"]
    assert metrics["brightness_agreement"] >= 0.95
    assert metrics["rotation_agreement"] >= 0.95


def test_real_explanation(model):
    photo = (ROOT / "tests/fixtures/leaf-50.png").read_bytes()
    result = model.explain(photo)
    with Image.open(BytesIO(result)) as image:
        assert image.format == "PNG"
        assert image.size == (224, 224)
        assert np.asarray(image).std() > 1
    (ROOT / "evidence/service-explanation.png").write_bytes(result)
