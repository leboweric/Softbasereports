"""
Export database schema and sample data for local analysis
"""
import os
import json
from datetime import datetime
from src.services.azure_sql_service import AzureSQLService

def export_database_info():
    """Export comprehensive database information"""
    db = AzureSQLService()
    
    output = {
        'export_date': datetime.now().isoformat(),
        'tables': {},
        'relationships': [],
        'indexes': [],
        'stored_procedures': []
    }
    
    # Get all tables
    tables_query = """
    SELECT 
        t.TABLE_SCHEMA,
        t.TABLE_NAME,
        t.TABLE_TYPE
    FROM INFORMATION_SCHEMA.TABLES t
    WHERE t.TABLE_SCHEMA = 'ben002'
    ORDER BY t.TABLE_NAME
    """
    
    tables = db.execute_query(tables_query)
    print(f"Found {len(tables)} tables")
    
    for table in tables:
        schema = table['TABLE_SCHEMA']
        table_name = table['TABLE_NAME']
        full_name = f"{schema}.{table_name}"
        
        print(f"Analyzing table: {full_name}")
        
        # Get columns
        columns_query = f"""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE,
            COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{schema}'
        AND TABLE_NAME = '{table_name}'
        ORDER BY ORDINAL_POSITION
        """
        
        columns = db.execute_query(columns_query)
        
        # Get row count
        count_query = f"SELECT COUNT(*) as row_count FROM {full_name}"
        try:
            count_result = db.execute_query(count_query)
            row_count = count_result[0]['row_count'] if count_result else 0
        except:
            row_count = 'Error'
        
        # Get sample data (first 5 rows)
        sample_query = f"SELECT TOP 5 * FROM {full_name}"
        try:
            sample_data = db.execute_query(sample_query)
        except:
            sample_data = []
        
        # Get primary keys
        pk_query = f"""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE OBJECTPROPERTY(OBJECT_ID(CONSTRAINT_SCHEMA + '.' + CONSTRAINT_NAME), 'IsPrimaryKey') = 1
        AND TABLE_SCHEMA = '{schema}'
        AND TABLE_NAME = '{table_name}'
        """
        
        primary_keys = db.execute_query(pk_query)
        
        output['tables'][full_name] = {
            'columns': columns,
            'row_count': row_count,
            'sample_data': sample_data,
            'primary_keys': [pk['COLUMN_NAME'] for pk in primary_keys]
        }
    
    # Get foreign key relationships
    fk_query = """
    SELECT 
        fk.name AS FK_Name,
        tp.name AS Parent_Table,
        cp.name AS Parent_Column,
        tr.name AS Referenced_Table,
        cr.name AS Referenced_Column
    FROM sys.foreign_keys fk
    INNER JOIN sys.tables tp ON fk.parent_object_id = tp.object_id
    INNER JOIN sys.tables tr ON fk.referenced_object_id = tr.object_id
    INNER JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id = fk.object_id
    INNER JOIN sys.columns cp ON fkc.parent_column_id = cp.column_id AND fkc.parent_object_id = cp.object_id
    INNER JOIN sys.columns cr ON fkc.referenced_column_id = cr.column_id AND fkc.referenced_object_id = cr.object_id
    WHERE SCHEMA_NAME(tp.schema_id) = 'ben002'
    """
    
    relationships = db.execute_query(fk_query)
    output['relationships'] = relationships
    
    # Get indexes
    index_query = """
    SELECT 
        t.name AS Table_Name,
        i.name AS Index_Name,
        i.type_desc AS Index_Type,
        STRING_AGG(c.name, ', ') AS Columns
    FROM sys.indexes i
    INNER JOIN sys.tables t ON i.object_id = t.object_id
    INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
    INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
    WHERE SCHEMA_NAME(t.schema_id) = 'ben002'
    AND i.name IS NOT NULL
    GROUP BY t.name, i.name, i.type_desc
    ORDER BY t.name, i.name
    """
    
    try:
        indexes = db.execute_query(index_query)
        output['indexes'] = indexes
    except:
        print("Could not retrieve indexes")
    
    # Save to file
    filename = f"database_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\nExport complete! Saved to {filename}")
    print(f"Total tables: {len(output['tables'])}")
    print(f"Total relationships: {len(output['relationships'])}")
    print(f"Total indexes: {len(output['indexes'])}")
    
    # Create a summary report
    summary_filename = f"database_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(summary_filename, 'w') as f:
        f.write("DATABASE SUMMARY REPORT\n")
        f.write("=" * 50 + "\n\n")
        
        f.write("TABLES:\n")
        for table_name, info in output['tables'].items():
            f.write(f"\n{table_name}:\n")
            f.write(f"  Rows: {info['row_count']}\n")
            f.write(f"  Columns: {len(info['columns'])}\n")
            f.write(f"  Primary Keys: {', '.join(info['primary_keys'])}\n")
            
            # Show column details
            f.write("  Column Details:\n")
            for col in info['columns']:
                nullable = "NULL" if col['IS_NULLABLE'] == 'YES' else "NOT NULL"
                f.write(f"    - {col['COLUMN_NAME']} ({col['DATA_TYPE']}) {nullable}\n")
        
        f.write("\n\nRELATIONSHIPS:\n")
        for rel in output['relationships']:
            f.write(f"  {rel.get('Parent_Table')}.{rel.get('Parent_Column')} -> ")
            f.write(f"{rel.get('Referenced_Table')}.{rel.get('Referenced_Column')}\n")
    
    print(f"Summary report saved to {summary_filename}")

if __name__ == "__main__":
    export_database_info()