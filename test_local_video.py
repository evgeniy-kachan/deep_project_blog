#!/usr/bin/env python3
"""
Simple test script for local video processing.
Upload video via scp first, then run this script.
"""
import sys
sys.path.insert(0, '/opt/youtube-shorts-generator')

from pathlib import Path
from backend.services.transcription import TranscriptionService
from backend.services.highlight_analyzer import HighlightAnalyzer
from backend.services.translation import Translator

# Video filename in temp/
VIDEO_FILENAME = "test_video.mp4"

print("="*80)
print("🎬 YouTube Shorts Generator - Local Video Test")
print("="*80)

video_path = Path("temp") / VIDEO_FILENAME

if not video_path.exists():
    print(f"\n❌ Видео не найдено: {video_path}")
    print("\nДоступные файлы:")
    for f in Path("temp").glob("*.mp4"):
        print(f"  - {f.name}")
    sys.exit(1)

print(f"\n✅ Видео: {video_path.name}")
print(f"   Размер: {video_path.stat().st_size / 1024 / 1024:.1f} MB")

# Transcription
print("\n🎙️ Транскрипция (DeepSeek)...")
print("⏳ Отправляем аудио в облако DeepSeek...")
transcription = TranscriptionService()
result = transcription.transcribe_audio_from_video(str(video_path))
segments = result["segments"]
print(f"✅ Найдено {len(segments)} сегментов транскрипции")

# Analysis
print("\n🤖 Анализ интересных моментов (LLM)...")
analyzer = HighlightAnalyzer()
highlights = analyzer.analyze_segments(segments, 20, 180)
print(f"✅ Найдено {len(highlights)} интересных моментов")

if not highlights:
    print("\n⚠️  Интересные моменты не найдены!")
    print("Возможные причины:")
    print("  - Видео с музыкой (нужна речь)")
    print("  - Видео не на английском")
    print("  - Недостаточно информативный контент")
    sys.exit(0)

# Translation
print("\n🌐 Перевод и субтитры (DeepSeek)...")
translator = Translator()
translations = translator.translate_batch([h['text'] for h in highlights])
for h, data in zip(highlights, translations):
    h['text_ru'] = data.get('screen_text', h['text'])
    h['text_ru_tts'] = data.get('tts_markup', h['text_ru'])
print("✅ Перевод завершен")

# Results
print("\n" + "="*80)
print("📊 РЕЗУЛЬТАТЫ АНАЛИЗА")
print("="*80)

for i, h in enumerate(highlights[:10], 1):
    print(f"\n🎯 Сегмент #{i}")
    print(f"⏱️  Время: {h['start_time']:.1f}s - {h['end_time']:.1f}s ({h['duration']:.1f}s)")
    print(f"⭐ Score: {h['highlight_score']:.2f}")
    print(f"📝 EN: {h['text'][:120]}{'...' if len(h['text']) > 120 else ''}")
    print(f"🇷🇺 RU: {h['text_ru'][:120]}{'...' if len(h['text_ru']) > 120 else ''}")

print("\n" + "="*80)
print(f"🎉 Найдено {len(highlights)} интересных моментов!")
print("="*80)
print("\nТеперь можно обработать через API:")
print(f"video_id: {video_path.stem}")
print(f"segment_ids: {[h['id'] for h in highlights[:3]]}")

