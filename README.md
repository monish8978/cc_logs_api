# CC Logs API — Production Deployment

A high-concurrency logging and management API designed for scalability and speed. Built with **FastAPI**, **Celery**, **Redis**, and **Elasticsearch**.

## 🚀 Architecture Overview

- **FastAPI**: Handles high-speed API requests asynchronously.
- **Celery + Redis**: Processes log insertions in the background to ensure sub-millisecond response times for client applications.
- **Elasticsearch**: Dedicated log storage for advanced searching and filtering.
- **MySQL**: Persistent storage for administrative metadata (clients, apps, status).
- **Docker**: Containerized environment for consistent deployment across environments.

## 🛠 Tech Stack

- **Framework**: FastAPI (Python 3.12)
- **Task Queue**: Celery 5.x
- **Message Broker**: Redis 7 (Alpine)
- **Database**: MySQL (Host-based)
- **Search Engine**: Elasticsearch (Host-based)
- **Deployment**: Docker & Docker Compose

## 📦 Getting Started

### 1. Prerequisites
- Docker & Docker Compose installed.
- MySQL and Elasticsearch running on the host machine.

### 2. Host Configuration (Important)
Since the app runs in Docker, ensure your host MySQL allows connections from the Docker network:
```sql
CREATE USER 'root'@'%' IDENTIFIED BY 'sqladmin';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;
```

### 3. Environment Setup
Create a `.env` file in the root directory (already provided in this repo):
```env
DB_HOST=host.docker.internal
DB_USER=root
DB_PASS=sqladmin
DB_NAME=cc_app_db
ES_API=http://host.docker.internal:9200
REDIS_URL=redis://redis:6379/0
```

### 4. Deployment Commands
```bash
# Start all services in the background
docker compose up --build -d

# Check service status
docker compose ps

# View real-time logs
docker compose logs -f api
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API Health Check |
| GET | `/docs` | Interactive Swagger Documentation |
| POST | `/push-log/` | Insert logs (Background Processed) |
| POST | `/admin/create-client` | Create new client metadata |
| POST | `/admin/rotate-key` | Rotate client access key |
| POST | `/admin/disable-client` | Suspend client access |
| POST | `/admin/upload-version` | Upload new app version package |
| POST | `/check-version` | Check for available updates |
| POST | `/validate-key` | Validate key and get download URL |
| GET | `/get-logs/` | Fetch logs from Elasticsearch |
| GET | `/search-logs/` | Search logs with filters in ES |

## 📁 Project Structure
- `/db`: Database connection pooling (aiomysql).
- `/services`: Core services like Elasticsearch client.
- `/utils`: Helper functions and response formatters.
- `main.py`: FastAPI application and routes.
- `worker.py`: Celery worker definition and background tasks.
- `config.py`: Environment-aware configuration loader.

---
**Developed by Antigravity AI**
