"""Translation + subtitle adaptation service using DeepSeek chat API."""
from __future__ import annotations

import logging
from typing import Dict, List

from backend.services.deepseek_client import DeepSeekClient

logger = logging.getLogger(__name__)


class Translator:
    """
    Delegates translation, cultural adaptation, and subtitle markup to DeepSeek.
    Returns both clean Russian text (for UI/video subtitles) and an annotated
    variant tuned for Silero TTS (pauses, emphasis, intonation hints).
    """

    def __init__(self):
        self.client = DeepSeekClient()

    def translate(self, text: str) -> Dict[str, List[str] | str]:
        """Convenience wrapper for single segment translation."""
        result = self.translate_batch([text])
        return result[0] if result else {"screen_text": text, "tts_markup": text, "subtitle_lines": [text]}

    def translate_batch(self, texts: List[str]) -> List[Dict[str, List[str] | str]]:
        """Translate and adapt many segments at once."""
        if not texts:
            return []

        prompt_lines = []
        for idx, text in enumerate(texts):
            normalized = " ".join((text or "").strip().split())
            prompt_lines.append(f"{idx}: {normalized}")

        system_prompt = (
            "Ты профессиональный редактор коротких видео. "
            "Переводи английские реплики на естественный разговорный русский, "
            "поддерживая эмоциональный стиль. Кроме перевода, подготовь:\n"
            "- screen_text: чистый текст без разметки, удобный для субтитров на видео;\n"
            "- tts_markup: тот же текст, но с обозначением пауз с помощью '...', "
            "а также подчёркиванием _важных слов_ и пометками эмоций в скобках для Silero TTS;\n"
            "- subtitle_lines: массив из 2-4 коротких строк (до 6 слов) для показа на экране.\n"
            "Не добавляй новых фактов. Сохраняй юмор и тон."
        )

        user_prompt = (
            "Верни JSON вида "
            '{"segments":[{"index":0,"screen_text":"",'
            '"tts_markup":"","subtitle_lines":["",""]}, ...]}. '
            "Вот реплики:\n" + "\n".join(prompt_lines)
        )

        try:
            response = self.client.chat_json(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.35,
            )
        except Exception as exc:
            logger.error("DeepSeek translation failed: %s", exc, exc_info=True)
            return [
                {
                    "screen_text": text,
                    "tts_markup": text,
                    "subtitle_lines": [" ".join(text.split())] if text else [""],
                }
                for text in texts
            ]

        segment_map = {}
        for item in response.get("segments", []):
            try:
                index = int(item.get("index"))
            except (TypeError, ValueError):
                continue
            segment_map[index] = item

        results: List[Dict[str, List[str] | str]] = []
        for idx, text in enumerate(texts):
            fallback = " ".join((text or "").split())
            data = segment_map.get(idx, {})
            screen_text = (data.get("screen_text") or fallback or "").strip()
            tts_markup = (data.get("tts_markup") or screen_text).strip()
            subtitle_lines = data.get("subtitle_lines") or [screen_text]
            cleaned_lines = [line.strip() for line in subtitle_lines if line and line.strip()]
            if not cleaned_lines:
                cleaned_lines = [screen_text]

            results.append(
                {
                    "screen_text": screen_text,
                    "tts_markup": tts_markup,
                    "subtitle_lines": cleaned_lines,
                }
            )

        return results