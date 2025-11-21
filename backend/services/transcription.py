"""Video transcription service powered by DeepSeek speech API."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

import ffmpeg

from backend.config import TEMP_DIR
from backend.services.deepseek_client import DeepSeekClient

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Send extracted audio to DeepSeek for transcription."""

    def __init__(self):
        self.client = DeepSeekClient()

    @staticmethod
    def _normalize_segments(payload: Dict) -> List[Dict]:
        """Ensure segments are in the expected internal format."""
        normalized: List[Dict] = []
        segments = payload.get("segments") or []

        for seg in segments:
            normalized.append(
                {
                    "start": float(seg.get("start", 0.0)),
                    "end": float(seg.get("end", 0.0)),
                    "text": (seg.get("text") or "").strip(),
                    "words": seg.get("words") or [],
                }
            )

        if not normalized:
            text = (payload.get("text") or "").strip()
            normalized.append(
                {
                    "start": 0.0,
                    "end": float(payload.get("duration") or 0.0),
                    "text": text,
                    "words": [],
                }
            )

        return normalized

    def transcribe_audio_from_video(self, video_path: str, language: str = "en") -> Dict:
        """
        Extract audio from a video file and transcribe via DeepSeek.

        Returns:
            Dict with segments list and full text.
        """
        temp_dir = Path(TEMP_DIR)
        temp_dir.mkdir(parents=True, exist_ok=True)
        audio_path = temp_dir / f"{Path(video_path).stem}_ds.wav"

        try:
            (
                ffmpeg.input(video_path)
                .output(str(audio_path), acodec="pcm_s16le", ac=1, ar="16000")
                .overwrite_output()
                .run(quiet=True, capture_stdout=True, capture_stderr=True)
            )

            logger.info("Sending audio (%s) to DeepSeek transcription", audio_path)
            payload = self.client.transcribe(str(audio_path), language=language)
            segments = self._normalize_segments(payload)
            full_text = payload.get("text") or " ".join(seg["text"] for seg in segments)

            logger.info("DeepSeek transcription complete: %d segments", len(segments))
            return {
                "segments": segments,
                "text": full_text.strip(),
            }

        except Exception as exc:
            logger.error("Error transcribing video %s: %s", video_path, exc, exc_info=True)
            raise
        finally:
            audio_path.unlink(missing_ok=True)

