import aiomysql
from config import *
from logger import log

# Connection pool instance
_pool = None

async def init_db_pool():
    """
    Initialize MySQL connection pool for async operations
    """
    global _pool
    try:
        if _pool is None:
            _pool = await aiomysql.create_pool(
                host=DB_HOST,
                port=3306,
                user=DB_USER,
                password=DB_PASS,
                db=DB_NAME,
                autocommit=True,
                minsize=5,
                maxsize=20,
                cursorclass=aiomysql.DictCursor
            )
            log.info("✅ Database connection pool initialized")
            await init_tables()
    except Exception as e:
        log.error(f"❌ Database pool initialization failed: {str(e)}", exc_info=True)
        raise Exception("Unable to connect to database pool")

async def init_tables():
    """
    Create necessary tables if they don't exist
    """
    queries = [
        """
        CREATE TABLE IF NOT EXISTS clients (
            id INT AUTO_INCREMENT PRIMARY KEY,
            client_id VARCHAR(100) UNIQUE NOT NULL,
            access_key VARCHAR(255) NOT NULL,
            expiry_date DATETIME NOT NULL,
            status ENUM('0', '1') DEFAULT '1',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
        """,
        """
        CREATE TABLE IF NOT EXISTS versions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            version VARCHAR(50) NOT NULL,
            client_id VARCHAR(100) NOT NULL,
            release_notes TEXT,
            mandatory TINYINT(1) DEFAULT 0,
            file_path VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
        ) ENGINE=InnoDB;
        """,
        """
        CREATE TABLE IF NOT EXISTS logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            client_id VARCHAR(100),
            version VARCHAR(50),
            ip VARCHAR(45),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
        """
    ]
    
    async with _pool.acquire() as conn:
        async with conn.cursor() as cursor:
            for query in queries:
                await cursor.execute(query)
    log.info("✅ Database tables checked/initialized")

async def close_db_pool():
    """
    Close database connection pool
    """
    global _pool
    if _pool:
        _pool.close()
        await _pool.wait_closed()
        log.info("Database connection pool closed")

async def get_db_conn():
    """
    Dependency to get a database connection from the pool
    """
    global _pool
    if _pool is None:
        await init_db_pool()
    
    async with _pool.acquire() as conn:
        yield conn