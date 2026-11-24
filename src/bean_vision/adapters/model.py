from io import BytesIO
from pathlib import Path
import numpy as np
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification
from bean_vision.domain import LABELS
from bean_vision.adapters.images import decode_image


class HuggingFaceModel:
    def __init__(self, directory: Path, max_pixels: int = 16_000_000, threads: int = 2):
        torch.set_num_threads(threads)
        self.max_pixels = max_pixels
        self.processor = AutoImageProcessor.from_pretrained(directory, local_files_only=True, use_fast=False)
        self.model = AutoModelForImageClassification.from_pretrained(directory, local_files_only=True).eval()
        if tuple(self.model.config.id2label[i] for i in range(3)) != LABELS:
            raise ValueError("Model label order does not match the contract")
        if self.processor.size != {"height": 224, "width": 224}:
            raise ValueError("Unexpected image size")

    def prepare(self, photo: bytes):
        image = decode_image(photo, self.max_pixels)
        return image, self.processor(images=image, return_tensors="pt")["pixel_values"]

    def predict(self, photo: bytes) -> list[float]:
        _, pixels = self.prepare(photo)
        with torch.inference_mode():
            return self.model(pixel_values=pixels).logits.softmax(dim=-1)[0].tolist()

    def explain(self, photo: bytes) -> bytes:
        image, pixels = self.prepare(photo)
        with torch.inference_mode():
            probs = self.model(pixel_values=pixels).logits.softmax(dim=-1)[0]
            label = int(probs.argmax())
            positions = [(y, x) for y in range(0, 193, 16) for x in range(0, 193, 16)]
            drops = []
            # Same 169 masks as the notebook, but allocate only 8 at a time.
            for start in range(0, len(positions), 8):
                batch = positions[start : start + 8]
                covered = pixels.repeat(len(batch), 1, 1, 1)
                for n, (y, x) in enumerate(batch):
                    covered[n, :, y : y + 32, x : x + 32] = 0.0
                covered_probs = self.model(pixel_values=covered).logits.softmax(dim=-1)[:, label]
                drops.extend((probs[label] - covered_probs).tolist())
        heat = np.zeros((224, 224))
        count = np.zeros((224, 224))
        for (y, x), drop in zip(positions, drops):
            heat[y : y + 32, x : x + 32] += drop
            count[y : y + 32, x : x + 32] += 1
        heat /= count
        alpha = 0.85 * np.clip(heat, 0, None) / max(float(heat.max()), 0.10)
        gray = np.array(image.resize((224, 224)).convert("L").convert("RGB"), dtype=float)
        blue = np.array([0.11, 0.36, 0.67]) * 255
        overlay = gray * (1 - alpha[..., None]) + blue * alpha[..., None]
        output = BytesIO()
        Image.fromarray(np.clip(overlay, 0, 255).astype("uint8")).save(output, format="PNG")
        return output.getvalue()
