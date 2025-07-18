import os
import sys

# Set environment variables
os.environ['AZURE_SQL_SERVER'] = 'evo1-sql-replica.database.windows.net'
os.environ['AZURE_SQL_DATABASE'] = 'evo'
os.environ['AZURE_SQL_USERNAME'] = 'ben002user'
os.environ['AZURE_SQL_PASSWORD'] = 'g6O8CE5mT83mDYOW'

# Add the reporting-backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'reporting-backend'))

try:
    from src.services.azure_sql_service import AzureSQLService
    
    print("Testing Azure SQL connection...")
    db = AzureSQLService()
    
    # Test connection
    if db.test_connection():
        print("✓ Connection successful!")
        
        # Get tables
        print("\nFetching tables...")
        tables = db.get_tables()
        print(f"✓ Found {len(tables)} tables")
        
        # Show first 10 tables
        print("\nFirst 10 tables:")
        for table in tables[:10]:
            print(f"  - {table}")
        
        # Look for key tables
        print("\nKey tables found:")
        key_patterns = ['customer', 'equipment', 'forklift', 'invoice', 'order', 'service', 'part']
        for pattern in key_patterns:
            matching = [t for t in tables if pattern in t.lower()]
            if matching:
                print(f"  {pattern.title()}: {', '.join(matching[:3])}")
        
    else:
        print("✗ Connection failed")
        
except Exception as e:
    print(f"Error: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()