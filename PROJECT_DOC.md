# youtube-shorts-generator – Project Documentation

## 1. Overview

AI-пайплайн, который из исходного ролика (локального файла или YouTube) автоматически строит клипы формата Shorts/Reels:

1. Загружает или скачивает видео.
2. Отправляет аудиодорожку в DeepSeek Speech для транскрибации.
3. Находит интересные отрезки через DeepSeek LLM.
4. Переводит/адаптирует текст на русский через DeepSeek.
5. Возвращает разметку пауз/интонаций для Silero TTS и чистые субтитры.
6. Синтезирует озвучку Silero TTS (голос Eugene).
7. Генерирует вертикальное видео (FFmpeg + кастомный рендер).
8. Выдаёт клипы для скачивания через UI.

## 2. Repo / Services

```
backend/             FastAPI сервер (uvicorn)
├─ routers/video.py  API / пайплайн
├─ services          DeepSeek API клиенты, TTS, subtitles, рендер
├─ utils             хелперы
frontend/            React + Tailwind (Nginx)
docker-compose.yml   backend + frontend + ollama
Dockerfile           CUDA образ для backend
Dockerfile.nginx     сборка фронта
nginx.conf           прокси + статический фронт
PROJECT_DOC.md       текущий документ
```

### Backend key services

| Service              | File                                     | Notes                                    |
| -------------------- | ---------------------------------------- | ---------------------------------------- |
| TranscriptionService | `backend/services/transcription.py`      | DeepSeek Speech API                      |
| HighlightAnalyzer    | `backend/services/highlight_analyzer.py` | DeepSeek Chat (JSON scoring)             |
| Translator           | `backend/services/translation.py`        | DeepSeek Chat (перевод + субтитры + TTS) |
| TTSService           | `backend/services/tts.py`                | Silero (`language=ru`, `speaker=eugene`) |
| VideoProcessor       | `backend/services/video_processor.py`    | FFmpeg пайплайн, субтитры CapCut         |

## 3. Configuration

Управляется через `backend/config.py` + `.env`:

| Variable                                                         | Description                   |
| ---------------------------------------------------------------- | ----------------------------- |
| `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`                          | доступ к облаку DeepSeek      |
| `DEEPSEEK_CHAT_MODEL`, `DEEPSEEK_TRANSCRIBE_MODEL`               | выбор моделей DeepSeek        |
| `HIGHLIGHT_CONCURRENT_REQUESTS`                                  | параллелизм анализа           |
| `SILERO_LANGUAGE`, `SILERO_SPEAKER`, `SILERO_MODEL_VERSION`      | Silero TTS                    |
| `VERTICAL_CONVERSION_METHOD`                                     | default метод рендера         |
| `TEMP_DIR`, `OUTPUT_DIR`                                         | каталоги данных               |

## 4. Workflow

1. **Upload/Analyze**  
   UI: пользователь загружает MP4 → `/api/video/upload-video`.  
   Затем `/api/video/analyze-local?filename=...` запускает фоновый таск.

2. **Analysis Pipeline** (`_run_analysis_pipeline`):

   - DeepSeek Speech -> сегменты (англ. текст + слова)
   - HighlightAnalyzer -> кандидатные окна (30–180 сек), оценка DeepSeek LLM
   - `_filter_overlapping_segments` -> убираем дубликаты
   - Translator -> `text_ru`, `text_ru_tts`, `subtitle_lines`
   - Результаты кешируются (`analysis_results_cache`), статус таска — `completed`

3. **Processing** (`/api/video/process`):

   - Тянем кешированный `video_id`
   - Для выбранных `segment_ids`:
     - TTS по `text_ru_tts`
     - VideoProcessor: вырезать отрезок, сделать вертикальный кадр (blur/center/smart), нарисовать субтитры (CapCut стиль)
   - Возвращаем `output_videos` (относительные пути)

4. **Download**
   - `/api/video/download/{video_id}/{segment_id}` → `FileResponse`

## 5. Frontend UX

- **VideoInput**: загрузка файла (только `.mp4`), прогресс.
- **ProgressBar**: отображение статуса анализа/рендера (данные из `/api/video/task/{task_id}`).
- **SegmentsList**:
  - Чекбоксы для сегментов, быстрые фильтры (выбрать/снять все).
  - Карточки выбора vertical метода.
  - Кнопка "Создать клипы" запускает `/api/video/process`.
- **DownloadList**:
  - Показывает список готовых клипов, кнопки `Скачать`/`Скачать все`.
  - Кнопка “Назад к выбору моментов” возвращает на экран сегментов (без повторного анализа).
  - “Обработать новое видео” — полный сброс.

## 6. Subtitles & TTS

- Субтитры: `VideoProcessor._create_stylized_subtitles` + CapCut стиль (`Montserrat`, fontsize 86, позиция `\pos(540,1250)`, мягкая тень).
- Анимация по словам: `\t` + fade, каждое слово появляется независимо, строка не подпрыгивает.
- TTS markup:
  - DeepSeek возвращает `_акценты_`, `...` для пауз и эмоций.
  - Silero голос — `eugene`. Можно сменить через env или `config.SILERO_SPEAKER`.

## 7. Commands

```bash
# локальная разработка
uvicorn backend.main:app --reload
cd frontend && npm start

# docker / gpu
docker compose up --build

# на сервере (из README/UPDATE_SERVER.md):
git pull origin main
docker compose build --no-cache backend frontend
docker compose up -d --force-recreate backend frontend
```

## 8. Future ideas

- UI для настройки субтитров (шрифт/позиция drag&drop).
- Расширенный `smart_crop` (детекция лица/объекта с OpenCV).
- Личный пресет стилей (хранить в backend + UI-переключатель).
- Поддержка SSML или другого TTS для эмоциональной озвучки.
- Экспорт метаданных (json) для передачи в соцсети.
