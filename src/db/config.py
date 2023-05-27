import os


LOCAL_DATABASE_URL = "sqlite+aiosqlite:///./local.db"
"""Used for testing purposes"""

DB_NAME = os.environ.get("POSTGRES_DB")
DB_USER = os.environ.get("POSTGRES_USER")
DB_PASS = os.environ.get("POSTGRES_PASSWORD")

# set automatically by kubernetes
# resolves to postgres service's host/port
DB_HOST = os.environ.get("POSTGRES_SERVICE_HOST")
DB_PORT = os.environ.get("POSTGRES_SERVICE_PORT")

REMOTE_DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
"""Production database URL"""

SQLALCHEMY_DATABASE_URL = (
    LOCAL_DATABASE_URL if DB_NAME is None else REMOTE_DATABASE_URL
)
