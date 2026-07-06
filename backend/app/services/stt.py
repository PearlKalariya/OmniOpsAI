"""Speech-to-text via faster-whisper (Audio Agent capability).

faster-whisper is the CTranslate2 port of OpenAI Whisper — ~4x faster on
CPU and a fraction of the RAM, same accuracy. Speaker diarization
(pyannote) is deferred: its models are gated behind a Hugging Face access
token, see ROADMAP.

Lazy singleton like embeddings/ocr/reranker. "small" model ~460MB on
first use; configurable via WHISPER_MODEL_SIZE.
"""

from app.core.config import settings

_model = None


def get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        _model = WhisperModel(settings.whisper_model_size, device="cpu", compute_type="int8")
    return _model


def transcribe(path: str) -> tuple[str, dict]:
    """Return (transcript, meta). Meta: language, duration_sec."""
    model = get_model()
    segments, info = model.transcribe(path, vad_filter=True)
    text = " ".join(segment.text.strip() for segment in segments).strip()
    return text, {
        "language": info.language,
        "duration_sec": round(info.duration, 1),
    }
