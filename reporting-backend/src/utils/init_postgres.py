#!/usr/bin/env python
"""
Initialize PostgreSQL database tables for user-generated content
Run this script to create the necessary tables in PostgreSQL
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.postgres_service import get_postgres_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize the PostgreSQL database with required tables"""
    try:
        logger.info("Initializing PostgreSQL database...")
        
        db = get_postgres_db()
        
        # Create tables
        if db.create_tables():
            logger.info("Database initialization completed successfully")
            
            # Verify the table was created
            result = db.execute_query("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'work_order_notes'
                ORDER BY ordinal_position
            """)
            
            if result:
                logger.info("Work order notes table columns:")
                for col in result:
                    logger.info(f"  - {col['column_name']}: {col['data_type']}")
            else:
                logger.warning("Could not verify table creation")
        else:
            logger.error("Database initialization failed")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False

if __name__ == "__main__":
    if init_database():
        print("✅ Database initialized successfully")
        sys.exit(0)
    else:
        print("❌ Database initialization failed")
        sys.exit(1)