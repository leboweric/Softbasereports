"""
GL Account Mapping Tables Migration Script
Creates tables for storing auto-discovered GL account mappings per tenant
"""
import os
import sys
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Run the GL mapping tables migration"""
    try:
        from services.postgres_service import PostgreSQLService
        
        pg = PostgreSQLService()
        
        migration_file = os.path.join(os.path.dirname(__file__), 'create_gl_mapping_tables.sql')
        
        with open(migration_file, 'r') as f:
            sql_content = f.read()
        
        logger.info("Starting GL mapping tables migration...")
        
        with pg.get_connection() as conn:
            if not conn:
                logger.error("Failed to get database connection")
                return False
            
            try:
                with conn.cursor() as cursor:
                    cursor.execute(sql_content)
                    logger.info("Migration SQL executed successfully")
                
                conn.commit()
                logger.info("Migration committed successfully")
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Migration failed: {str(e)}")
                raise
        
        # Verify tables
        verify_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('tenant_gl_accounts', 'tenant_departments', 'tenant_expense_categories', 'gl_discovery_log')
        ORDER BY table_name
        """
        results = pg.execute_query(verify_query)
        created = [r['table_name'] for r in results]
        
        expected = ['gl_discovery_log', 'tenant_departments', 'tenant_expense_categories', 'tenant_gl_accounts']
        for table in expected:
            status = "✓" if table in created else "✗"
            logger.info(f"  {status} {table}")
        
        logger.info("GL mapping tables migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Migration error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("=" * 50)
    print("GL Account Mapping Tables Migration")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 50)
    
    success = run_migration()
    sys.exit(0 if success else 1)
