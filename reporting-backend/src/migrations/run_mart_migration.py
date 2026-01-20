"""
AIOP Data Mart Migration Script
Runs the SQL migration to create all Mart tables in Railway PostgreSQL
"""

import os
import sys
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Run the Mart tables migration"""
    try:
        from services.postgres_service import PostgreSQLService
        
        pg = PostgreSQLService()
        
        # Read the SQL migration file
        migration_file = os.path.join(os.path.dirname(__file__), 'create_mart_tables.sql')
        
        with open(migration_file, 'r') as f:
            sql_content = f.read()
        
        # Split into individual statements (by semicolon, but be careful with strings)
        # For simplicity, we'll execute the whole file as one transaction
        
        logger.info("Starting Mart tables migration...")
        logger.info(f"Migration file: {migration_file}")
        
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
        
        # Verify tables were created
        verify_tables(pg)
        
        logger.info("=" * 50)
        logger.info("MIGRATION COMPLETED SUCCESSFULLY")
        logger.info("=" * 50)
        
        return True
        
    except Exception as e:
        logger.error(f"Migration error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def verify_tables(pg):
    """Verify all Mart tables were created"""
    expected_tables = [
        'mart_financial_metrics',
        'mart_crm_contacts',
        'mart_crm_deals',
        'mart_zoom_metrics',
        'mart_case_metrics',
        'mart_app_analytics',
        'mart_sales_daily',
        'mart_rental_fleet',
        'mart_cash_flow',
        'mart_etl_log'
    ]
    
    query = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name LIKE 'mart_%'
    ORDER BY table_name
    """
    
    results = pg.execute_query(query)
    created_tables = [r['table_name'] for r in results]
    
    logger.info("\nVerifying created tables:")
    logger.info("-" * 40)
    
    all_created = True
    for table in expected_tables:
        if table in created_tables:
            logger.info(f"  ✓ {table}")
        else:
            logger.warning(f"  ✗ {table} - NOT FOUND")
            all_created = False
    
    if all_created:
        logger.info("\nAll Mart tables verified successfully!")
    else:
        logger.warning("\nSome tables were not created!")
    
    return all_created


def show_table_info(pg):
    """Show information about created Mart tables"""
    query = """
    SELECT 
        t.table_name,
        COUNT(c.column_name) as column_count
    FROM information_schema.tables t
    JOIN information_schema.columns c ON t.table_name = c.table_name
    WHERE t.table_schema = 'public' 
    AND t.table_name LIKE 'mart_%'
    GROUP BY t.table_name
    ORDER BY t.table_name
    """
    
    results = pg.execute_query(query)
    
    logger.info("\nMart Table Summary:")
    logger.info("-" * 40)
    logger.info(f"{'Table Name':<30} {'Columns':<10}")
    logger.info("-" * 40)
    
    for row in results:
        logger.info(f"{row['table_name']:<30} {row['column_count']:<10}")


if __name__ == '__main__':
    print("=" * 50)
    print("AIOP Data Mart Migration")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 50)
    
    success = run_migration()
    
    if success:
        print("\n✓ Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n✗ Migration failed!")
        sys.exit(1)
