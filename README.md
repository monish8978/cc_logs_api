# CC Logs API

Enterprise-grade FastAPI application for:

- Desktop application logging
- Elasticsearch log storage
- Client access-key management
- Version management
- S3 file distribution
- JWT authentication
- Centralized logging system

---

# Features

- FastAPI REST APIs
- Elasticsearch integration
- AWS S3 integration
- MySQL database support
- Daily rotating logs
- Client license validation
- Version update system
- Secure presigned download URLs
- Production-ready structure

---

# Project Structure

```bash
cc_logs_api/
│
├── main.py
├── config.py
├── logger.py
├── requirements.txt
├── README.md
│
├── services/
│   └── elastic.py
│
├── db/
│   └── db.py
│
├── utils/
│   └── response.py
│
├── logs/
│
└── venv/
