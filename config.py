import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =====================================================
# DATABASE CONFIG
# =====================================================
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

# =====================================================
# JWT CONFIG
# =====================================================
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGO = os.getenv("JWT_ALGO", "HS256")

# =====================================================
# AWS CONFIG
# =====================================================
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET = os.getenv("AWS_SECRET")
BUCKET_NAME = os.getenv("BUCKET_NAME")

# =====================================================
# ELASTICSEARCH CONFIG
# =====================================================
ES_API = os.getenv("ES_API")
INDEX_NAME = os.getenv("INDEX_NAME")

# =====================================================
# LOGGING CONFIG
# =====================================================
LOG_DIR = os.getenv("LOG_DIR")
LOG_FILENAME = os.getenv("LOG_FILENAME")

# =====================================================
# API CONFIG
# =====================================================
API_PORT = int(os.getenv("API_PORT", 10005))
API_IP = os.getenv("API_IP", "0.0.0.0")

# =====================================================
# REDIS & CELERY CONFIG
# =====================================================
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)