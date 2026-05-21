from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODEL_DIR = PROJECT_ROOT / "models"
DATA_DIR = PROJECT_ROOT / "data"
YOLOV5_DIR = PROJECT_ROOT / "yolov5"
EOWL_DIR = DATA_DIR / "EOWL-v1.1.2" / "LF Delimited Format"

OPENMOJI_DIR = DATA_DIR / "openmoji-72x72-color"
