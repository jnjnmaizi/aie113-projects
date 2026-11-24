"""Use against the real server or container, never a fake model."""

import json
import sys
import time
from pathlib import Path
import httpx

url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
for attempt in range(60):
    try:
        response = httpx.get(url + "/ready", timeout=5)
        if response.status_code == 200:
            break
    except httpx.HTTPError:
        pass
    time.sleep(2)
else:
    raise SystemExit("Readiness failed")
fixture = Path(__file__).resolve().parents[1] / "tests/fixtures/leaf-0.png"
response = httpx.post(
    url + "/v1/predict", files={"file": ("leaf.png", fixture.read_bytes(), "image/png")}, timeout=60
)
response.raise_for_status()
answer = response.json()
assert len(answer["scores"]) == 3
assert answer["label"] == max(answer["scores"], key=answer["scores"].get)
assert httpx.get(url + "/docs").status_code == 200
golden = json.loads((fixture.parent / "golden.json").read_text())
for case in golden["cases"]:
    response = httpx.post(
        url + "/v1/predict",
        files={"file": (case["file"], (fixture.parent / case["file"]).read_bytes(), "image/png")},
        timeout=60,
    )
    response.raise_for_status()
    actual = response.json()["scores"]
    for label, expected in zip(("angular_leaf_spot", "bean_rust", "healthy"), case["scores"]):
        assert abs(actual[label] - expected) <= 1e-5, (case["index"], label)
print(
    json.dumps({"ready": True, "golden_cases_verified": len(golden["cases"]), "prediction": answer}, indent=2)
)
