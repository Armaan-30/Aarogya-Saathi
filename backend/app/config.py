import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / 'backend' / '.env')
API_KEY = os.getenv('GEMINI_API_KEY', '')
MODEL = os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite')
DEMO_MODE = os.getenv('DEMO_MODE', 'true').lower() == 'true'
FREE_TIER = os.getenv('FREE_TIER_CONFIRMED', 'false').lower() == 'true'
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
SESSION_TTL_HOURS = max(1, min(int(os.getenv('SESSION_TTL_HOURS', '12')), 72))
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{ROOT / "backend" / "aarogya.db"}')
