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
            
            -- Mid-month snapshot flag (15th of month official forecast)
            is_mid_month_snapshot BOOLEAN DEFAULT FALSE,
            
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

                    # Create QBR tables
                    cursor.execute(self._get_qbr_tables_sql())
                    logger.info("QBR tables created/verified successfully")

                    # Create Sales Rep Compensation tables
                    cursor.execute(self._get_sales_rep_comp_tables_sql())
                    logger.info("Sales rep compensation tables created/verified successfully")

                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Failed to create tables: {str(e)}")
            return False

    def _get_qbr_tables_sql(self):
        """SQL to create QBR-related tables"""
        return """
        -- QBR Sessions table
        CREATE TABLE IF NOT EXISTS qbr_sessions (
            qbr_id VARCHAR(50) PRIMARY KEY,
            customer_number VARCHAR(50) NOT NULL,
            customer_name VARCHAR(255) NOT NULL,
            quarter VARCHAR(10) NOT NULL,
            fiscal_year INT NOT NULL,
            meeting_date DATE,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(100),
            last_modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_modified_by VARCHAR(100),
            status VARCHAR(20) DEFAULT 'draft',
            notes TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_qbr_customer ON qbr_sessions(customer_number);
        CREATE INDEX IF NOT EXISTS idx_qbr_quarter ON qbr_sessions(quarter, fiscal_year);
        CREATE INDEX IF NOT EXISTS idx_qbr_status ON qbr_sessions(status);

        -- QBR Business Priorities table
        CREATE TABLE IF NOT EXISTS qbr_business_priorities (
            priority_id SERIAL PRIMARY KEY,
            qbr_id VARCHAR(50) NOT NULL REFERENCES qbr_sessions(qbr_id) ON DELETE CASCADE,
            priority_number INT NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_priority_qbr ON qbr_business_priorities(qbr_id);

        -- QBR Recommendations table
        CREATE TABLE IF NOT EXISTS qbr_recommendations (
            recommendation_id SERIAL PRIMARY KEY,
            qbr_id VARCHAR(50) NOT NULL REFERENCES qbr_sessions(qbr_id) ON DELETE CASCADE,
            category VARCHAR(50) NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            estimated_impact VARCHAR(255),
            is_auto_generated BOOLEAN DEFAULT FALSE,
            status VARCHAR(20) DEFAULT 'proposed',
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_recommendation_qbr ON qbr_recommendations(qbr_id);
        CREATE INDEX IF NOT EXISTS idx_recommendation_category ON qbr_recommendations(category);

        -- QBR Action Items table
        CREATE TABLE IF NOT EXISTS qbr_action_items (
            action_id SERIAL PRIMARY KEY,
            qbr_id VARCHAR(50) NOT NULL REFERENCES qbr_sessions(qbr_id) ON DELETE CASCADE,
            party VARCHAR(20) NOT NULL,
            description VARCHAR(500) NOT NULL,
            owner_name VARCHAR(100),
            due_date DATE,
            completed BOOLEAN DEFAULT FALSE,
            completed_date DATE,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_action_qbr ON qbr_action_items(qbr_id);
        CREATE INDEX IF NOT EXISTS idx_action_duedate ON qbr_action_items(due_date);

        -- Equipment Condition History table (for fleet health tracking)
        CREATE TABLE IF NOT EXISTS equipment_condition_history (
            condition_id SERIAL PRIMARY KEY,
            unit_no VARCHAR(50) NOT NULL,
            customer_number VARCHAR(50) NOT NULL,
            assessment_date DATE NOT NULL,
            condition_status VARCHAR(20) NOT NULL,
            age_years DECIMAL(5,2),
            annual_maintenance_cost DECIMAL(12,2),
            notes TEXT,
            assessed_by VARCHAR(100),
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_condition_unitno ON equipment_condition_history(unit_no);
        CREATE INDEX IF NOT EXISTS idx_condition_customer ON equipment_condition_history(customer_number);
        CREATE INDEX IF NOT EXISTS idx_condition_date ON equipment_condition_history(assessment_date);
        CREATE INDEX IF NOT EXISTS idx_condition_status ON equipment_condition_history(condition_status);
        """

    def _get_sales_rep_comp_tables_sql(self):
        """SQL to create Sales Rep Compensation tables"""
        return """
        -- Sales Rep Compensation Settings table
        -- Stores each rep's compensation plan configuration
        CREATE TABLE IF NOT EXISTS sales_rep_comp_settings (
            id SERIAL PRIMARY KEY,
            salesman_name VARCHAR(100) NOT NULL UNIQUE,
            salesman_code VARCHAR(20),
            monthly_draw NUMERIC(12,2) NOT NULL DEFAULT 0,
            start_date DATE NOT NULL,
            starting_balance NUMERIC(12,2) NOT NULL DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(100),
            updated_at TIMESTAMP,
            updated_by VARCHAR(100)
        );

        CREATE INDEX IF NOT EXISTS idx_rep_comp_salesman ON sales_rep_comp_settings(salesman_name);
        CREATE INDEX IF NOT EXISTS idx_rep_comp_active ON sales_rep_comp_settings(is_active);

        -- Sales Rep Monthly Transactions table
        -- Tracks each month's commission activity and draw decisions
        CREATE TABLE IF NOT EXISTS sales_rep_monthly_transactions (
            id SERIAL PRIMARY KEY,
            salesman_name VARCHAR(100) NOT NULL,
            year_month VARCHAR(7) NOT NULL,  -- Format: YYYY-MM

            -- Commission values (calculated from verified invoices)
            gross_commissions NUMERIC(12,2) DEFAULT 0,

            -- Draw decisions
            draw_amount NUMERIC(12,2) DEFAULT 0,  -- Amount actually taken (can be 0 if banking)
            draw_taken BOOLEAN DEFAULT FALSE,      -- Whether they took their draw this month

            -- Running balance (positive = rep owes, negative = company owes rep)
            opening_balance NUMERIC(12,2) DEFAULT 0,
            closing_balance NUMERIC(12,2) DEFAULT 0,

            -- Status tracking
            is_locked BOOLEAN DEFAULT FALSE,       -- Lock after month is finalized
            locked_at TIMESTAMP,
            locked_by VARCHAR(100),

            -- Metadata
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            updated_by VARCHAR(100),

            UNIQUE(salesman_name, year_month)
        );

        CREATE INDEX IF NOT EXISTS idx_rep_trans_salesman ON sales_rep_monthly_transactions(salesman_name);
        CREATE INDEX IF NOT EXISTS idx_rep_trans_month ON sales_rep_monthly_transactions(year_month);
        CREATE INDEX IF NOT EXISTS idx_rep_trans_locked ON sales_rep_monthly_transactions(is_locked);
        """

# Singleton instance
def get_postgres_db():
    """Get the PostgreSQL service instance"""
    return PostgreSQLService()