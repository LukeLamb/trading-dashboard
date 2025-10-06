"""
Database Connection Module
Handles PostgreSQL connections using SQLAlchemy
"""

import os
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import QueuePool
import logging

logger = logging.getLogger(__name__)

# Base class for SQLAlchemy models
Base = declarative_base()

class DatabaseConfig:
    """Database configuration from environment variables"""

    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = os.getenv("DB_PORT", "5432")
        self.database = os.getenv("DB_NAME", "trading_game")
        self.user = os.getenv("DB_USER", "postgres")
        self.password = os.getenv("DB_PASSWORD", "")
        self.pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "20"))
        self.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        self.echo = os.getenv("DB_ECHO", "false").lower() == "true"

    @property
    def database_url(self) -> str:
        """Generate database URL for SQLAlchemy"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class DatabaseConnection:
    """Manages database connection and session lifecycle"""

    _engine = None
    _session_factory = None

    @classmethod
    def initialize(cls, config: DatabaseConfig = None):
        """Initialize database engine and session factory"""
        if cls._engine is not None:
            logger.warning("Database already initialized, skipping")
            return

        if config is None:
            config = DatabaseConfig()

        logger.info(f"Initializing database connection to {config.host}:{config.port}/{config.database}")

        # Create engine with connection pooling
        cls._engine = create_engine(
            config.database_url,
            poolclass=QueuePool,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            pool_timeout=config.pool_timeout,
            pool_pre_ping=True,  # Verify connections before using
            echo=config.echo,
        )

        # Add event listener for connection tracking
        @event.listens_for(cls._engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            logger.debug("New database connection established")

        @event.listens_for(cls._engine, "close")
        def receive_close(dbapi_conn, connection_record):
            logger.debug("Database connection closed")

        # Create session factory
        cls._session_factory = sessionmaker(
            bind=cls._engine,
            autocommit=False,
            autoflush=False,
        )

        logger.info("Database connection initialized successfully")

    @classmethod
    def get_engine(cls):
        """Get SQLAlchemy engine instance"""
        if cls._engine is None:
            cls.initialize()
        return cls._engine

    @classmethod
    def get_session(cls) -> Session:
        """Get new database session"""
        if cls._session_factory is None:
            cls.initialize()
        return cls._session_factory()

    @classmethod
    def close(cls):
        """Close all database connections"""
        if cls._engine is not None:
            logger.info("Closing database connections")
            cls._engine.dispose()
            cls._engine = None
            cls._session_factory = None


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to get database session

    Usage in FastAPI:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = DatabaseConnection.get_session()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Initialize database tables (create all tables defined in Base)"""
    logger.info("Creating database tables from models")
    Base.metadata.create_all(bind=DatabaseConnection.get_engine())
    logger.info("Database tables created successfully")


def drop_db():
    """Drop all database tables (USE WITH CAUTION)"""
    logger.warning("Dropping all database tables")
    Base.metadata.drop_all(bind=DatabaseConnection.get_engine())
    logger.info("Database tables dropped")


# Context manager for database sessions
class db_session:
    """
    Context manager for database sessions

    Usage:
        with db_session() as db:
            user = db.query(User).filter_by(username="john").first()
    """

    def __enter__(self) -> Session:
        self.db = DatabaseConnection.get_session()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(f"Database session error: {exc_val}")
            self.db.rollback()
        else:
            self.db.commit()
        self.db.close()


# Health check function
def check_database_health() -> dict:
    """
    Check database connection health

    Returns:
        dict: Health status with connection info
    """
    try:
        with db_session() as db:
            # Execute simple query to test connection
            db.execute("SELECT 1")

        return {
            "status": "healthy",
            "database": "connected",
            "message": "Database connection successful"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


if __name__ == "__main__":
    # Test database connection
    logging.basicConfig(level=logging.INFO)

    print("Testing database connection...")
    health = check_database_health()
    print(f"Health check: {health}")

    if health["status"] == "healthy":
        print("✅ Database connection successful!")
    else:
        print("❌ Database connection failed!")
        print(f"Error: {health.get('error')}")
