"""Configuration settings for the application."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

# DeepSeek Cloud AI
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_CHAT_MODEL = os.getenv("DEEPSEEK_CHAT_MODEL", "deepseek-chat")
DEEPSEEK_TRANSCRIBE_MODEL = os.getenv("DEEPSEEK_TRANSCRIBE_MODEL", "deepseek-speech")
DEEPSEEK_TIMEOUT = float(os.getenv("DEEPSEEK_TIMEOUT", 120))
HIGHLIGHT_CONCURRENT_REQUESTS = int(os.getenv("HIGHLIGHT_CONCURRENT_REQUESTS", 5))

# Processing Configuration
MAX_VIDEO_DURATION = int(os.getenv("MAX_VIDEO_DURATION", 7200))  # 2 hours
MIN_SEGMENT_DURATION = 20  # seconds
MAX_SEGMENT_DURATION = 180  # 3 minutes

# Directories
BASE_DIR = Path(__file__).parent.parent
TEMP_DIR = BASE_DIR / "temp"
OUTPUT_DIR = BASE_DIR / "output"

# Create directories if they don't exist
TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# GPU Configuration
CUDA_VISIBLE_DEVICES = os.getenv("CUDA_VISIBLE_DEVICES", "0")

# TTS Configuration
SILERO_LANGUAGE = "ru"
SILERO_SPEAKER = "eugene"  # Russian voice (aidar, baya, kseniya, xenia, eugene, random)
SILERO_MODEL_VERSION = "v3_1_ru"  # Model version for torch.hub.load

# Video Processing Configuration
VERTICAL_CONVERSION_METHOD = "blur_background"  # blur_background, center_crop, smart_crop
TARGET_WIDTH = 1080  # Width for vertical video (9:16)
TARGET_HEIGHT = 1920  # Height for vertical video (9:16)

