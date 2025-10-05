#!/usr/bin/env python3
"""
Find depreciation-related fields in the Azure SQL database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.services.azure_sql_service import AzureSQLService

def main():
    try:
        print("Connecting to Azure SQL database...")
        sql_service = AzureSQLService()
        
        # Find tables with depreciation in the name
        print("=" * 50)
        print("TABLES WITH DEPRECIATION-RELATED NAMES")
        print("=" * 50)
        query1 = """
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE (TABLE_NAME LIKE '%deprec%' OR TABLE_NAME LIKE '%depr%'
               OR TABLE_NAME LIKE '%asset%' OR TABLE_NAME LIKE '%book%')
        AND TABLE_SCHEMA = 'ben002'
        ORDER BY TABLE_NAME
        """
        try:
            result1 = sql_service.execute_query(query1)
            if result1:
                for row in result1:
                    print(f"  - {row['TABLE_NAME']}")
            else:
                print("  No tables found with depreciation-related names")
        except Exception as e:
            print(f"  Error: {e}")

        # Find columns with depreciation, book value, accumulated depreciation
        print("\\n" + "=" * 50)
        print("COLUMNS WITH DEPRECIATION/BOOK VALUE KEYWORDS")
        print("=" * 50)
        query2 = """
        SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE (COLUMN_NAME LIKE '%deprec%' OR COLUMN_NAME LIKE '%depr%' 
               OR COLUMN_NAME LIKE '%book%' OR COLUMN_NAME LIKE '%accum%'
               OR COLUMN_NAME LIKE '%asset%' OR COLUMN_NAME LIKE '%value%'
               OR COLUMN_NAME LIKE '%cost%' OR COLUMN_NAME LIKE '%basis%'
               OR COLUMN_NAME LIKE '%original%' OR COLUMN_NAME LIKE '%purchase%')
        AND TABLE_SCHEMA = 'ben002'
        ORDER BY TABLE_NAME, COLUMN_NAME
        """
        try:
            result2 = sql_service.execute_query(query2)
            if result2:
                current_table = None
                for row in result2:
                    if current_table != row['TABLE_NAME']:
                        current_table = row['TABLE_NAME']
                        print(f"\\n{current_table}:")
                    
                    nullable = "NULL" if row['IS_NULLABLE'] == 'YES' else "NOT NULL"
                    max_len = f"({row['CHARACTER_MAXIMUM_LENGTH']})" if row['CHARACTER_MAXIMUM_LENGTH'] else ""
                    print(f"  - {row['COLUMN_NAME']:<25} {row['DATA_TYPE']}{max_len:<15} {nullable}")
            else:
                print("  No columns found with depreciation-related keywords")
        except Exception as e:
            print(f"  Error: {e}")

        # Get ALL Equipment table columns for complete analysis
        print("\\n" + "=" * 50)
        print("ALL EQUIPMENT TABLE COLUMNS")
        print("=" * 50)
        query3 = """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH,
               COLUMN_DEFAULT, NUMERIC_PRECISION, NUMERIC_SCALE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'Equipment' AND TABLE_SCHEMA = 'ben002'
        ORDER BY ORDINAL_POSITION
        """
        try:
            result3 = sql_service.execute_query(query3)
            if result3:
                for row in result3:
                    nullable = "NULL" if row['IS_NULLABLE'] == 'YES' else "NOT NULL"
                    max_len = f"({row['CHARACTER_MAXIMUM_LENGTH']})" if row['CHARACTER_MAXIMUM_LENGTH'] else ""
                    precision = f"({row['NUMERIC_PRECISION']},{row['NUMERIC_SCALE']})" if row['NUMERIC_PRECISION'] else ""
                    default = f" DEFAULT: {row['COLUMN_DEFAULT']}" if row['COLUMN_DEFAULT'] else ""
                    print(f"  {row['COLUMN_NAME']:<25} {row['DATA_TYPE']}{max_len}{precision:<15} {nullable}{default}")
            else:
                print("  Equipment table not found or no columns returned")
        except Exception as e:
            print(f"  Error: {e}")

        # Sample equipment data to see what's actually populated
        print("\\n" + "=" * 50)
        print("SAMPLE EQUIPMENT FINANCIAL DATA")
        print("=" * 50)
        query4 = """
        SELECT TOP 5 
            SerialNo,
            Make,
            Model,
            Cost,
            Sell,
            Retail,
            -- Add any other potential financial fields we find
            CASE WHEN Cost IS NOT NULL THEN Cost ELSE 0 END as CostValue,
            CASE WHEN Sell IS NOT NULL THEN Sell ELSE 0 END as SellValue
        FROM ben002.Equipment 
        WHERE SerialNo IS NOT NULL
        AND (Cost IS NOT NULL OR Sell IS NOT NULL)
        ORDER BY Cost DESC
        """
        try:
            result4 = sql_service.execute_query(query4)
            if result4:
                print("Sample records with financial data:")
                for row in result4:
                    print(f"  Serial: {row['SerialNo']:<15} Make: {row['Make']:<10} Cost: ${row['Cost'] or 0:<10} Sell: ${row['Sell'] or 0}")
            else:
                print("  No equipment records found with financial data")
        except Exception as e:
            print(f"  Error: {e}")

        # Check for any tables that might contain asset or depreciation data
        print("\\n" + "=" * 50)
        print("ALL TABLES IN DATABASE (looking for asset-related)")
        print("=" * 50)
        query5 = """
        SELECT TABLE_NAME, 
               (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = t.TABLE_NAME AND TABLE_SCHEMA = 'ben002') as COLUMN_COUNT
        FROM INFORMATION_SCHEMA.TABLES t
        WHERE TABLE_SCHEMA = 'ben002'
        AND TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
        """
        try:
            result5 = sql_service.execute_query(query5)
            if result5:
                print("All tables (highlighting potential asset/financial tables):")
                for row in result5:
                    table_name = row['TABLE_NAME']
                    is_financial = any(keyword in table_name.lower() for keyword in 
                                     ['asset', 'deprec', 'book', 'cost', 'value', 'financial', 'account'])
                    marker = " *** POTENTIAL FINANCIAL TABLE ***" if is_financial else ""
                    print(f"  {table_name:<30} ({row['COLUMN_COUNT']} columns){marker}")
            else:
                print("  No tables found")
        except Exception as e:
            print(f"  Error: {e}")

        # Check for any views that might contain depreciation calculations
        print("\\n" + "=" * 50)
        print("DATABASE VIEWS (might contain calculated depreciation)")
        print("=" * 50)
        query6 = """
        SELECT TABLE_NAME as VIEW_NAME
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = 'ben002'
        AND TABLE_TYPE = 'VIEW'
        ORDER BY TABLE_NAME
        """
        try:
            result6 = sql_service.execute_query(query6)
            if result6:
                print("Database views:")
                for row in result6:
                    print(f"  - {row['VIEW_NAME']}")
            else:
                print("  No views found")
        except Exception as e:
            print(f"  Error: {e}")

        print("\\n" + "=" * 50)
        print("DEPRECIATION INVESTIGATION COMPLETE")
        print("=" * 50)

    except Exception as e:
        print(f"Script failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()