import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class PostgreSQLService:
    """Service for managing PostgreSQL connections for user-generated content"""
    
    _instance = None
    _connection_pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PostgreSQLService, cls).__new__(cls)
            cls._instance._initialize_pool()
        return cls._instance
    
    def _initialize_pool(self):
        """Initialize the connection pool"""
        try:
            # Get PostgreSQL connection string from environment - Railway uses various names
            database_url = (
                os.environ.get('POSTGRES_URL') or 
                os.environ.get('DATABASE_URL') or
                os.environ.get('DATABASE_PRIVATE_URL') or
                os.environ.get('POSTGRES_PRIVATE_URL')
            )
            
            if not database_url:
                logger.warning("PostgreSQL URL not found in environment variables (checked POSTGRES_URL, DATABASE_URL, DATABASE_PRIVATE_URL, POSTGRES_PRIVATE_URL)")
                return
            
            # Parse the connection string for psycopg2
            # Railway provides postgresql:// but psycopg2 prefers postgres://
            if database_url.startswith('postgresql://'):
                database_url = database_url.replace('postgresql://', 'postgres://', 1)
            
            self._connection_pool = psycopg2.pool.ThreadedConnectionPool(
                1,  # Min connections
                20,  # Max connections
                database_url,
                cursor_factory=RealDictCursor
            )
            logger.info("PostgreSQL connection pool initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL connection pool: {str(e)}")
            self._connection_pool = None
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        if not self._connection_pool:
            logger.error("PostgreSQL connection pool not initialized")
            yield None
            return
            
        conn = None
        try:
            conn = self._connection_pool.getconn()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"PostgreSQL connection error: {str(e)}")
            raise
        finally:
            if conn:
                self._connection_pool.putconn(conn)
    
    def execute_query(self, query, params=None):
        """Execute a SELECT query and return results"""
        with self.get_connection() as conn:
            if not conn:
                return []
            
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, params or ())
                    return cursor.fetchall()
            except Exception as e:
                logger.error(f"Query execution failed: {str(e)}")
                raise
    
    def execute_update(self, query, params=None):
        """Execute an INSERT/UPDATE/DELETE query"""
        with self.get_connection() as conn:
            if not conn:
                return None
            
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, params or ())
                    return cursor.rowcount
            except Exception as e:
                logger.error(f"Update execution failed: {str(e)}")
                raise
    
    def execute_insert_returning(self, query, params=None):
        """Execute an INSERT query with RETURNING clause"""
        with self.get_connection() as conn:
            if not conn:
                return None
            
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, params or ())
                    return cursor.fetchone()
            except Exception as e:
                logger.error(f"Insert execution failed: {str(e)}")
                raise
    
    def create_tables(self):
        """Create necessary tables if they don't exist"""
        create_notes_table = """
        CREATE TABLE IF NOT EXISTS work_order_notes (
            id SERIAL PRIMARY KEY,
            wo_number VARCHAR(50) NOT NULL,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(100),
            updated_by VARCHAR(100)
        );
        
        CREATE INDEX IF NOT EXISTS idx_wo_number ON work_order_notes(wo_number);
        """
        
        try:
            with self.get_connection() as conn:
                if not conn:
                    logger.error("Cannot create tables - no PostgreSQL connection")
                    return False
                
                with conn.cursor() as cursor:
                    cursor.execute(create_notes_table)
                    conn.commit()
                    logger.info("Work order notes table created/verified successfully")
                    return True
        except Exception as e:
            logger.error(f"Failed to create tables: {str(e)}")
            return False

# Singleton instance
def get_postgres_db():
    """Get the PostgreSQL service instance"""
    return PostgreSQLService()