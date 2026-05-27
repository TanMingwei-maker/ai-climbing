from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / 'data'
UPLOAD_DIR = DATA_DIR / 'uploads'
FRAME_DIR = DATA_DIR / 'frames'
ANNOTATION_DIR = DATA_DIR / 'annotations'
OUTPUT_DIR = DATA_DIR / 'outputs'
DB_PATH = DATA_DIR / 'app.db'

for directory in (UPLOAD_DIR, FRAME_DIR, ANNOTATION_DIR, OUTPUT_DIR):
    directory.mkdir(parents=True, exist_ok=True)
