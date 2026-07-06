"""Image captioning via BLIP (Vision Agent capability).

BLIP-base (~1GB) describes what an image shows; TrOCR (ocr.py) reads the
text in it. Together they make images searchable by content AND wording.
Blueprint lists BLIP-2/Florence-2/SAM/YOLO — BLIP-2 is ~15GB and the
rest need a detection pipeline, so v1 ships captioning and the heavier
models stay on the roadmap.

Lazy singleton like the other model services. Revision pinned
(supply-chain, see ocr.py).
"""

from PIL import Image

_processor = None
_model = None

MODEL_NAME = "Salesforce/blip-image-captioning-base"
MODEL_REVISION = "82a37760796d32b1411fe092ab5d4e227313294b"


def _load():
    global _processor, _model
    if _model is None:
        from transformers import BlipForConditionalGeneration, BlipProcessor

        _processor = BlipProcessor.from_pretrained(MODEL_NAME, revision=MODEL_REVISION)
        _model = BlipForConditionalGeneration.from_pretrained(MODEL_NAME, revision=MODEL_REVISION)
    return _processor, _model


def caption(path: str) -> str:
    processor, model = _load()
    image = Image.open(path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    output = model.generate(**inputs, max_new_tokens=40)
    return processor.decode(output[0], skip_special_tokens=True).strip()
