#!/usr/bin/env python3
"""
Script to create the commission_settings table in PostgreSQL
Run this after deployment to set up the commission settings feature
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.services.postgres_service import PostgreSQLService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_commission_settings_table():
    """Create the commission_settings table if it doesn't exist"""
    try:
        pg_service = PostgreSQLService()
        with pg_service.get_connection() as conn:
            cursor = conn.cursor()
            
            logger.info("Creating commission_settings table...")
            
            # Create the table with all necessary columns and constraints
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS commission_settings (
                    id SERIAL PRIMARY KEY,
                    invoice_no INTEGER NOT NULL,
                    sale_code VARCHAR(50),
                    category VARCHAR(100),
                    is_commissionable BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by VARCHAR(100),
                    CONSTRAINT unique_invoice_line UNIQUE (invoice_no, sale_code, category)
                );
            """)
            
            # Create indexes for better performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_commission_invoice_no ON commission_settings(invoice_no);
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_commission_is_commissionable ON commission_settings(is_commissionable);
            """)
            
            # Add trigger for updated_at
            cursor.execute("""
                CREATE OR REPLACE FUNCTION update_commission_settings_timestamp()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """)
            
            cursor.execute("""
                DROP TRIGGER IF EXISTS update_commission_settings_timestamp ON commission_settings;
            """)
            
            cursor.execute("""
                CREATE TRIGGER update_commission_settings_timestamp
                BEFORE UPDATE ON commission_settings
                FOR EACH ROW
                EXECUTE FUNCTION update_commission_settings_timestamp();
            """)
            
            conn.commit()
            
            # Verify table was created
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'commission_settings'
                ORDER BY ordinal_position;
            """)
            
            columns = cursor.fetchall()
            
            logger.info("✅ Commission settings table created successfully!")
            logger.info(f"Table has {len(columns)} columns:")
            for col_name, col_type in columns:
                logger.info(f"  - {col_name}: {col_type}")
                
            return True
            
    except Exception as e:
        logger.error(f"❌ Error creating commission settings table: {str(e)}")
        return False

if __name__ == "__main__":
    # Check for PostgreSQL connection
    pg_url = os.environ.get('POSTGRES_URL') or \
             os.environ.get('DATABASE_URL') or \
             os.environ.get('DATABASE_PRIVATE_URL') or \
             os.environ.get('POSTGRES_PRIVATE_URL')
    
    if not pg_url:
        logger.error("❌ No PostgreSQL connection URL found in environment variables")
        logger.info("Please set one of: POSTGRES_URL, DATABASE_URL, DATABASE_PRIVATE_URL, or POSTGRES_PRIVATE_URL")
        sys.exit(1)
    
    logger.info("Starting commission settings table creation...")
    success = create_commission_settings_table()
    
    if success:
        logger.info("✅ Migration completed successfully!")
    else:
        logger.error("❌ Migration failed!")
        sys.exit(1)