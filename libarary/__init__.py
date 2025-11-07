from pathlib import Path

# Ensure logs directory exists before Django initializes logging
LOGS_DIR = Path(__file__).resolve().parent.parent / 'logs'
LOGS_DIR.mkdir(parents=True, exist_ok=True)
