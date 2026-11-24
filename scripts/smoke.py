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
print(json.dumps({"ready": True, "prediction": answer}, indent=2))
