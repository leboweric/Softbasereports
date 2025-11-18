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
        
        create_service_assistant_queries_table = """
        CREATE TABLE IF NOT EXISTS service_assistant_queries (
            id SERIAL PRIMARY KEY,
            query_text TEXT NOT NULL,
            keywords TEXT[],
            equipment_make VARCHAR(100),
            equipment_model VARCHAR(100),
            kb_results_count INTEGER DEFAULT 0,
            wo_results_count INTEGER DEFAULT 0,
            web_results_count INTEGER DEFAULT 0,
            response_text TEXT,
            user_email VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_sa_created ON service_assistant_queries(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_sa_make ON service_assistant_queries(equipment_make);
        CREATE INDEX IF NOT EXISTS idx_sa_keywords ON service_assistant_queries USING GIN(keywords);
        """
        
        create_knowledge_base_table = """
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            equipment_make VARCHAR(100),
            equipment_model VARCHAR(100),
            issue_category VARCHAR(100) NOT NULL,
            symptoms TEXT NOT NULL,
            root_cause TEXT NOT NULL,
            solution TEXT NOT NULL,
            related_wo_numbers VARCHAR(500),
            image_urls TEXT,
            created_by VARCHAR(100) NOT NULL,
            created_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_by VARCHAR(100),
            updated_date TIMESTAMP,
            view_count INTEGER DEFAULT 0
        );
        
        CREATE INDEX IF NOT EXISTS idx_kb_category ON knowledge_base(issue_category);
        CREATE INDEX IF NOT EXISTS idx_kb_make ON knowledge_base(equipment_make);
        CREATE INDEX IF NOT EXISTS idx_kb_created ON knowledge_base(created_date DESC);
        CREATE INDEX IF NOT EXISTS idx_kb_views ON knowledge_base(view_count DESC);
        """
        
        create_forecast_history_table = """
        CREATE TABLE IF NOT EXISTS forecast_history (
            id SERIAL PRIMARY KEY,
            
            -- When was this forecast made?
            forecast_date DATE NOT NULL,
            forecast_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            
            -- What period is being forecasted?
            target_year INTEGER NOT NULL,
            target_month INTEGER NOT NULL,
            days_into_month INTEGER NOT NULL,
            
            -- Forecast values
            projected_total NUMERIC(18,2) NOT NULL,
            forecast_low NUMERIC(18,2),
            forecast_high NUMERIC(18,2),
            confidence_level VARCHAR(10),
            
            -- Context at time of forecast
            mtd_sales NUMERIC(18,2),
            mtd_invoices INTEGER,
            month_progress_pct NUMERIC(5,2),
            days_remaining INTEGER,
            pipeline_value NUMERIC(18,2),
            avg_pct_complete NUMERIC(5,2),
            
            -- Actual outcome (filled in after month ends)
            actual_total NUMERIC(18,2) NULL,
            actual_invoices INTEGER NULL,
            accuracy_pct NUMERIC(5,2) NULL,
            absolute_error NUMERIC(18,2) NULL,
            within_range BOOLEAN NULL,
            
            -- Metadata
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NULL
        );
        
        CREATE INDEX IF NOT EXISTS idx_forecast_target ON forecast_history(target_year, target_month);
        CREATE INDEX IF NOT EXISTS idx_forecast_date ON forecast_history(forecast_date);
        """
        
        try:
            with self.get_connection() as conn:
                if not conn:
                    logger.error("Cannot create tables - no PostgreSQL connection")
                    return False
                
                with conn.cursor() as cursor:
                    cursor.execute(create_notes_table)
                    logger.info("Work order notes table created/verified successfully")
                    
                    cursor.execute(create_service_assistant_queries_table)
                    logger.info("Service assistant queries table created/verified successfully")
                    
                    cursor.execute(create_knowledge_base_table)
                    logger.info("Knowledge base table created/verified successfully")
                    
                    cursor.execute(create_forecast_history_table)
                    logger.info("Forecast history table created/verified successfully")
                    
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Failed to create tables: {str(e)}")
            return False

# Singleton instance
def get_postgres_db():
    """Get the PostgreSQL service instance"""
    return PostgreSQLService()