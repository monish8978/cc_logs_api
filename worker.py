from celery import Celery
from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND, ES_API, INDEX_NAME
from elasticsearch import Elasticsearch
from datetime import datetime
import logging

# Setup Celery
celery_app = Celery(
    "tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

# Setup Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("celery_worker")

# Setup Sync Elasticsearch for Worker (Celery is better with sync tasks)
es_client = Elasticsearch(ES_API)

@celery_app.task(name="tasks.insert_log_task")
def insert_log_task(data: dict):
    """
    Background task to insert log into Elasticsearch
    """
    try:
        # Basic sanitization (sync version)
        clean_data = {
            "timestamp": data.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "agentId": data.get("agentId", ""),
            "macAddress": data.get("macAddress", ""),
            "level": data.get("level", "INFO"),
            "thread": data.get("thread", "main"),
            "message": data.get("message", ""),
            "url": data.get("url", ""),
            "exception": {"type": "", "stack_trace": ""}
        }

        if isinstance(data.get("exception"), dict):
            clean_data["exception"]["type"] = data["exception"].get("type", "")
            stack = data["exception"].get("stack_trace", "")
            if isinstance(stack, list):
                stack = "\n".join(stack)
            clean_data["exception"]["stack_trace"] = stack

        # Insert into ES
        response = es_client.index(index=INDEX_NAME, document=clean_data)
        logger.info(f"Log inserted via worker => {response['_id']}")
        return {"status": "success", "id": response["_id"]}

    except Exception as e:
        logger.error(f"Worker log insertion failed: {str(e)}")
        return {"status": "error", "message": str(e)}
