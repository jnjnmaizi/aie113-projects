"""Download only the pinned public model, then store safe local weights."""

import json
import os
from pathlib import Path

os.environ["DISABLE_SAFETENSORS_CONVERSION"] = "1"
from transformers import AutoImageProcessor, AutoModelForImageClassification

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / "model_manifest.json").read_text())
target = root / "artifacts/model"
args = {"revision": manifest["revision"], "token": False}
processor = AutoImageProcessor.from_pretrained(manifest["model_id"], use_fast=False, **args)
model = AutoModelForImageClassification.from_pretrained(manifest["model_id"], use_safetensors=False, **args)
model.save_pretrained(target, safe_serialization=True)
processor.save_pretrained(target)
print("Pinned public model saved to artifacts/model")
