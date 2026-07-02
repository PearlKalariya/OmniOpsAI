"""Image OCR via Microsoft TrOCR (blueprint model choice).

TrOCR is a line-level recognizer: it reads one line of printed text per
pass and has no built-in text detection, so full-page/multi-column scans
need a detection stage first (planned with the Vision Agent in Milestone 2).
For M1 this handles single-line and simple printed-text images.

Model is lazy-loaded (~250MB download on first use) and cached for the
process lifetime, mirroring the embeddings service.
"""

from PIL import Image

_processor = None
_model = None

MODEL_NAME = "microsoft/trocr-small-printed"


def _load():
    global _processor, _model
    if _model is None:
        from transformers import TrOCRProcessor, VisionEncoderDecoderModel

        _processor = TrOCRProcessor.from_pretrained(MODEL_NAME)
        _model = VisionEncoderDecoderModel.from_pretrained(MODEL_NAME)
    return _processor, _model


def image_to_text(path: str) -> str:
    processor, model = _load()
    image = Image.open(path).convert("RGB")
    pixel_values = processor(images=image, return_tensors="pt").pixel_values
    generated_ids = model.generate(pixel_values, max_new_tokens=256)
    text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return text.strip()
