import logging
from logging.handlers import TimedRotatingFileHandler
import os

from config import LOG_DIR, LOG_FILENAME

# =========================================================
# CREATE LOG DIRECTORY
# =========================================================
os.makedirs(LOG_DIR, exist_ok=True)

# =========================================================
# LOG FILE PATH
# =========================================================
LOG_FILE = os.path.join(
    LOG_DIR,
    LOG_FILENAME
)

# =========================================================
# LOGGER
# =========================================================
log = logging.getLogger("cc_logs_api")

log.setLevel(logging.INFO)

# =========================================================
# FORMATTER
# =========================================================
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(lineno)d | %(message)s"
)

# =========================================================
# FILE HANDLER
# =========================================================
file_handler = TimedRotatingFileHandler(
    filename=LOG_FILE,
    when="midnight",
    interval=1,
    backupCount=7,
    encoding="utf-8"
)

file_handler.setFormatter(formatter)

# =========================================================
# CONSOLE HANDLER
# =========================================================
console_handler = logging.StreamHandler()

console_handler.setFormatter(formatter)

# =========================================================
# ATTACH HANDLERS
# =========================================================
if not log.handlers:

    log.addHandler(file_handler)
    log.addHandler(console_handler)