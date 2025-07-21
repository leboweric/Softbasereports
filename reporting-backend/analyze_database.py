"""
Comprehensive database analysis tool
Run this to learn everything about the Softbase database structure
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from src.services.azure_sql_service import AzureSQLService
import json
from datetime import datetime
import pandas as pd

class DatabaseAnalyzer:
    def __init__(self):
        self.db = AzureSQLService()
        self.analysis = {
            'timestamp': datetime.now().isoformat(),
            'tables': {},
            'key_patterns': {},
            'data_quality': {},
            'business_insights': {}
        }
    
    def analyze_all(self):
        """Run complete database analysis"""
        print("Starting comprehensive database analysis...")
        
        # 1. Get all tables
        self.get_all_tables()
        
        # 2. Analyze key business tables
        self.analyze_invoices()
        self.analyze_work_orders()
        self.analyze_customers()
        self.analyze_equipment()
        self.analyze_parts()
        
        # 3. Find data patterns
        self.find_sale_codes()
        self.analyze_date_ranges()
        self.find_missing_data()
        
        # 4. Save results
        self.save_analysis()
    
    def get_all_tables(self):
        """Get list of all tables with row counts"""
        query = """
        SELECT 
            t.TABLE_SCHEMA,
            t.TABLE_NAME,
            p.rows AS ROW_COUNT
        FROM INFORMATION_SCHEMA.TABLES t
        LEFT JOIN sys.partitions p ON p.object_id = OBJECT_ID(t.TABLE_SCHEMA + '.' + t.TABLE_NAME)
        WHERE t.TABLE_TYPE = 'BASE TABLE'
        AND t.TABLE_SCHEMA = 'ben002'
        AND p.index_id IN (0,1)
        ORDER BY p.rows DESC
        """
        
        tables = self.db.execute_query(query)
        print(f"\nFound {len(tables)} tables in ben002 schema")
        
        for table in tables[:20]:  # Show top 20 by row count
            print(f"  {table['TABLE_NAME']}: {table.get('ROW_COUNT', 0):,} rows")
        
        self.analysis['tables'] = tables
    
    def analyze_invoices(self):
        """Analyze InvoiceReg table structure and data"""
        print("\nAnalyzing InvoiceReg table...")
        
        # Get all columns
        columns_query = """
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'ben002' AND TABLE_NAME = 'InvoiceReg'
        ORDER BY ORDINAL_POSITION
        """
        columns = self.db.execute_query(columns_query)
        
        # Get date range
        date_range_query = """
        SELECT 
            MIN(InvoiceDate) as earliest_invoice,
            MAX(InvoiceDate) as latest_invoice,
            COUNT(DISTINCT InvoiceNo) as total_invoices,
            COUNT(DISTINCT CustomerNo) as unique_customers,
            SUM(GrandTotal) as total_revenue
        FROM ben002.InvoiceReg
        """
        date_info = self.db.execute_query(date_range_query)
        
        # Get SaleCode distribution
        salecode_query = """
        SELECT 
            SaleCode,
            COUNT(*) as invoice_count,
            SUM(GrandTotal) as total_amount
        FROM ben002.InvoiceReg
        WHERE InvoiceDate >= DATEADD(month, -3, GETDATE())
        GROUP BY SaleCode
        ORDER BY total_amount DESC
        """
        salecodes = self.db.execute_query(salecode_query)
        
        self.analysis['business_insights']['invoices'] = {
            'columns': columns,
            'date_range': date_info[0] if date_info else {},
            'sale_codes': salecodes[:20]  # Top 20
        }
        
        print(f"  Invoice date range: {date_info[0]['earliest_invoice']} to {date_info[0]['latest_invoice']}")
        print(f"  Total invoices: {date_info[0]['total_invoices']:,}")
        print(f"  Unique customers: {date_info[0]['unique_customers']:,}")
    
    def analyze_work_orders(self):
        """Analyze WO table structure"""
        print("\nAnalyzing WO (Work Orders) table...")
        
        # Get work order types
        wo_types_query = """
        SELECT 
            Type,
            SaleCode,
            COUNT(*) as count
        FROM ben002.WO
        WHERE OpenDate >= DATEADD(month, -3, GETDATE())
        GROUP BY Type, SaleCode
        ORDER BY count DESC
        """
        wo_types = self.db.execute_query(wo_types_query)
        
        # Get status distribution
        status_query = """
        SELECT 
            CASE 
                WHEN ClosedDate IS NULL AND CompletedDate IS NULL THEN 'Open'
                WHEN ClosedDate IS NULL AND CompletedDate IS NOT NULL THEN 'Completed'
                WHEN ClosedDate IS NOT NULL THEN 'Closed'
                ELSE 'Other'
            END as Status,
            COUNT(*) as count
        FROM ben002.WO
        GROUP BY 
            CASE 
                WHEN ClosedDate IS NULL AND CompletedDate IS NULL THEN 'Open'
                WHEN ClosedDate IS NULL AND CompletedDate IS NOT NULL THEN 'Completed'
                WHEN ClosedDate IS NOT NULL THEN 'Closed'
                ELSE 'Other'
            END
        """
        statuses = self.db.execute_query(status_query)
        
        self.analysis['business_insights']['work_orders'] = {
            'types_and_codes': wo_types[:20],
            'status_distribution': statuses
        }
    
    def analyze_customers(self):
        """Analyze Customer table"""
        print("\nAnalyzing Customer table...")
        
        customer_query = """
        SELECT 
            COUNT(*) as total_customers,
            COUNT(CASE WHEN Balance > 0 THEN 1 END) as customers_with_balance,
            SUM(Balance) as total_receivables,
            AVG(Balance) as avg_balance
        FROM ben002.Customer
        """
        customer_stats = self.db.execute_query(customer_query)
        
        self.analysis['business_insights']['customers'] = customer_stats[0] if customer_stats else {}
    
    def analyze_equipment(self):
        """Analyze Equipment table"""
        print("\nAnalyzing Equipment table...")
        
        equipment_query = """
        SELECT 
            RentalStatus,
            COUNT(*) as count,
            COUNT(DISTINCT Make) as unique_makes,
            COUNT(DISTINCT Model) as unique_models
        FROM ben002.Equipment
        GROUP BY RentalStatus
        """
        equipment_stats = self.db.execute_query(equipment_query)
        
        self.analysis['business_insights']['equipment'] = equipment_stats
    
    def analyze_parts(self):
        """Analyze parts-related tables"""
        print("\nAnalyzing parts tables...")
        
        # Check which parts tables exist
        parts_tables_query = """
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'ben002'
        AND TABLE_NAME LIKE '%Part%'
        """
        parts_tables = self.db.execute_query(parts_tables_query)
        
        self.analysis['business_insights']['parts_tables'] = [t['TABLE_NAME'] for t in parts_tables]
    
    def find_sale_codes(self):
        """Find all unique SaleCodes across tables"""
        print("\nFinding all SaleCodes...")
        
        # Get from InvoiceReg
        invoice_codes_query = """
        SELECT DISTINCT 'InvoiceReg' as source_table, SaleCode
        FROM ben002.InvoiceReg
        WHERE SaleCode IS NOT NULL
        """
        
        # Get from WO
        wo_codes_query = """
        SELECT DISTINCT 'WO' as source_table, SaleCode
        FROM ben002.WO
        WHERE SaleCode IS NOT NULL
        """
        
        invoice_codes = self.db.execute_query(invoice_codes_query)
        wo_codes = self.db.execute_query(wo_codes_query)
        
        all_codes = invoice_codes + wo_codes
        unique_codes = list(set([c['SaleCode'] for c in all_codes]))
        
        self.analysis['key_patterns']['sale_codes'] = {
            'unique_count': len(unique_codes),
            'codes': sorted(unique_codes)
        }
        
        print(f"  Found {len(unique_codes)} unique SaleCodes")
    
    def analyze_date_ranges(self):
        """Analyze date ranges in key tables"""
        print("\nAnalyzing date ranges...")
        
        date_queries = {
            'InvoiceReg': "SELECT MIN(InvoiceDate) as min_date, MAX(InvoiceDate) as max_date FROM ben002.InvoiceReg",
            'WO': "SELECT MIN(OpenDate) as min_date, MAX(OpenDate) as max_date FROM ben002.WO WHERE OpenDate IS NOT NULL",
            'Equipment': "SELECT MIN(PurchaseDate) as min_date, MAX(PurchaseDate) as max_date FROM ben002.Equipment WHERE PurchaseDate IS NOT NULL"
        }
        
        date_ranges = {}
        for table, query in date_queries.items():
            try:
                result = self.db.execute_query(query)
                if result:
                    date_ranges[table] = result[0]
            except:
                pass
        
        self.analysis['data_quality']['date_ranges'] = date_ranges
    
    def find_missing_data(self):
        """Check for missing critical data"""
        print("\nChecking data quality...")
        
        quality_checks = {
            'invoices_without_customer': """
                SELECT COUNT(*) as count 
                FROM ben002.InvoiceReg 
                WHERE CustomerNo IS NULL OR CustomerNo = ''
            """,
            'work_orders_without_salecode': """
                SELECT COUNT(*) as count 
                FROM ben002.WO 
                WHERE SaleCode IS NULL OR SaleCode = ''
            """,
            'equipment_without_status': """
                SELECT COUNT(*) as count 
                FROM ben002.Equipment 
                WHERE RentalStatus IS NULL OR RentalStatus = ''
            """
        }
        
        quality_results = {}
        for check_name, query in quality_checks.items():
            try:
                result = self.db.execute_query(query)
                if result:
                    quality_results[check_name] = result[0]['count']
            except:
                quality_results[check_name] = 'Error'
        
        self.analysis['data_quality']['missing_data'] = quality_results
    
    def save_analysis(self):
        """Save analysis results"""
        # Save JSON
        json_filename = f"database_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_filename, 'w') as f:
            json.dump(self.analysis, f, indent=2, default=str)
        
        # Save readable report
        report_filename = f"database_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_filename, 'w') as f:
            f.write("# Softbase Database Analysis Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Database Overview\n\n")
            f.write(f"Total tables: {len(self.analysis['tables'])}\n\n")
            
            f.write("### Top Tables by Row Count:\n")
            for table in self.analysis['tables'][:15]:
                f.write(f"- **{table['TABLE_NAME']}**: {table.get('ROW_COUNT', 0):,} rows\n")
            
            f.write("\n## Key Business Insights\n\n")
            
            if 'invoices' in self.analysis['business_insights']:
                inv = self.analysis['business_insights']['invoices']['date_range']
                f.write("### Invoice Data\n")
                f.write(f"- Date Range: {inv.get('earliest_invoice')} to {inv.get('latest_invoice')}\n")
                f.write(f"- Total Invoices: {inv.get('total_invoices', 0):,}\n")
                f.write(f"- Unique Customers: {inv.get('unique_customers', 0):,}\n")
                f.write(f"- Total Revenue: ${inv.get('total_revenue', 0):,.2f}\n\n")
            
            f.write("### Sale Codes\n")
            if 'sale_codes' in self.analysis['key_patterns']:
                codes = self.analysis['key_patterns']['sale_codes']['codes']
                f.write(f"Found {len(codes)} unique SaleCodes\n\n")
                f.write("Common codes: " + ", ".join(codes[:20]) + "...\n\n")
        
        print(f"\n✅ Analysis complete!")
        print(f"   JSON data: {json_filename}")
        print(f"   Report: {report_filename}")

if __name__ == "__main__":
    analyzer = DatabaseAnalyzer()
    analyzer.analyze_all()