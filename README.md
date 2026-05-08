# CC Logs API — Production Documentation

A high-performance logging and version management API system.

## 🚀 Quick Start

```bash
# 1. Sync code to deployment directory
cp -r /Czentrix/apps/cc_logs_api/* /root/cc_logs_api/

# 2. Start services
cd /root/cc_logs_api
docker compose up --build -d
```

## 🔌 API Endpoints Reference

### 🛡️ Admin Endpoints
Management tasks for clients and versions.

#### 1. Create Client
`POST /admin/create-client`
```json
{
    "client_id": "test_client",
    "access_key": "secret_key_123",
    "expiry_date": "2026-12-31 23:59:59",
    "status": true
}
```

#### 2. Rotate Access Key
`POST /admin/rotate-key`
```json
{
    "client_id": "test_client",
    "new_key": "new_secret_456"
}
```

#### 3. Disable Client
`POST /admin/disable-client`
```json
{
    "client_id": "test_client"
}
```

#### 4. Upload App Version
`POST /admin/upload-version` (Multipart/Form-Data)
- `version`: (string) e.g., "1.0.5"
- `client_id`: (string)
- `release_notes`: (string)
- `mandatory`: (boolean)
- `file`: (binary) The update package.

---

### 📝 Logging Endpoints
High-concurrency log ingestion.

#### 1. Push Log (Background)
`POST /push-log/`
Accepts any JSON structure. The log is offloaded to Celery/Redis immediately.
```json
{
    "agentId": "agent_001",
    "level": "ERROR",
    "message": "System failure detected"
}
```

#### 2. Fetch Logs
`GET /get-logs/?page=1&size=100`
Retrieves logs from Elasticsearch.

#### 3. Search Logs
`GET /search-logs/?agentId=xxx&level=ERROR&start_date=2024-01-01&end_date=2024-01-31`
Advanced search across Elasticsearch indices.

---

### 🔑 Validation & Updates
Client-side integration points.

#### 1. Validate Key
`POST /validate-key`
Validates the access key and returns a secure S3 download URL for the latest version.
```json
{
    "access_key": "secret_key_123"
}
```

#### 2. Check Version
`POST /check-version`
Checks if an update is available (uses Redis caching for speed).
```json
{
    "client_id": "test_client",
    "current_version": "1.0.0"
}
```

## 🛠 Tech Stack
- **API**: FastAPI (Python 3.12)
- **Background Tasks**: Celery & Redis
- **Storage**: Elasticsearch (Logs) & MySQL (Metadata)
- **Cloud**: AWS S3 (Version Hosting)
- **Environment**: Docker Compose

---
**Developed by Antigravity AI**
