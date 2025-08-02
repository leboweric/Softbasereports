from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService

expense_search_diagnostic_bp = Blueprint('expense_search_diagnostic', __name__)

@expense_search_diagnostic_bp.route('/api/diagnostics/expense-search', methods=['GET'])
@jwt_required()
def search_for_expenses():
    """Search for G&A expenses across various tables"""
    try:
        db = AzureSQLService()
        results = {
            'invoice_expenses': {},
            'wo_expenses': {},
            'potential_expense_fields': [],
            'recommendations': []
        }
        
        # Search InvoiceReg for expense-related fields
        query = """
        SELECT TOP 100
            InvoiceNo,
            InvoiceDate,
            SaleDept,
            SaleCode,
            PartsTaxable,
            PartsNonTax,
            LaborTaxable,
            LaborNonTax,
            MiscTaxable,
            MiscNonTax,
            RentalTaxable,
            RentalNonTax,
            EquipmentTaxable,
            EquipmentNonTax,
            GrandTotal,
            -- Check for any other numeric fields that might be expenses
            COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'ben002' 
        AND TABLE_NAME = 'InvoiceReg'
        AND DATA_TYPE IN ('decimal', 'money', 'float', 'numeric')
        """
        
        # Get all numeric columns from InvoiceReg
        numeric_cols_query = """
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'ben002' 
        AND TABLE_NAME = 'InvoiceReg'
        AND DATA_TYPE IN ('decimal', 'money', 'float', 'numeric', 'int')
        ORDER BY ORDINAL_POSITION
        """
        
        numeric_columns = db.execute_query(numeric_cols_query)
        
        results['potential_expense_fields'] = [
            {
                'column': col['COLUMN_NAME'],
                'data_type': col['DATA_TYPE']
            }
            for col in numeric_columns
        ]
        
        # Sample data from InvoiceReg to look for patterns
        sample_query = """
        SELECT TOP 10 *
        FROM ben002.InvoiceReg
        WHERE InvoiceDate >= DATEADD(MONTH, -1, GETDATE())
        ORDER BY InvoiceDate DESC
        """
        
        sample_invoices = db.execute_query(sample_query)
        
        # Check for expense patterns in SaleDept or SaleCode
        dept_analysis_query = """
        SELECT DISTINCT
            SaleDept,
            SaleCode,
            COUNT(*) as record_count
        FROM ben002.InvoiceReg
        WHERE InvoiceDate >= DATEADD(MONTH, -6, GETDATE())
        GROUP BY SaleDept, SaleCode
        ORDER BY SaleDept, SaleCode
        """
        
        dept_patterns = db.execute_query(dept_analysis_query)
        
        results['invoice_expenses']['sample_records'] = [
            {
                'invoice_no': inv.get('InvoiceNo'),
                'date': str(inv.get('InvoiceDate', '')),
                'department': inv.get('SaleDept'),
                'sale_code': inv.get('SaleCode'),
                'total': float(inv.get('GrandTotal', 0))
            }
            for inv in sample_invoices[:5]
        ]
        
        results['invoice_expenses']['department_patterns'] = [
            {
                'department': d['SaleDept'],
                'sale_code': d['SaleCode'],
                'count': d['record_count']
            }
            for d in dept_patterns
        ]
        
        # Search for expense-related data in WO table
        wo_expense_query = """
        SELECT TOP 10
            WONo,
            Type,
            SaleCode,
            Customer,
            BillTo
        FROM ben002.WO
        WHERE Type NOT IN ('S', 'R')  -- Not Service or Rental
        ORDER BY WONo DESC
        """
        
        wo_expenses = db.execute_query(wo_expense_query)
        
        results['wo_expenses']['sample_records'] = [
            {
                'wo_no': wo.get('WONo'),
                'type': wo.get('Type'),
                'sale_code': wo.get('SaleCode'),
                'customer': wo.get('Customer'),
                'bill_to': wo.get('BillTo')
            }
            for wo in wo_expenses
        ]
        
        # Check if there are any populated GL tables in other schemas
        gl_schema_check = """
        SELECT DISTINCT
            TABLE_SCHEMA,
            TABLE_NAME,
            COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME LIKE '%GL%'
        OR TABLE_NAME LIKE '%Expense%'
        OR TABLE_NAME LIKE '%Account%'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
        """
        
        gl_tables = db.execute_query(gl_schema_check)
        
        # Group by schema
        schemas = {}
        for row in gl_tables:
            schema = row['TABLE_SCHEMA']
            if schema not in schemas:
                schemas[schema] = []
            schemas[schema].append(f"{row['TABLE_NAME']}.{row['COLUMN_NAME']}")
        
        results['other_schemas'] = schemas
        
        # Generate recommendations
        if len(results['invoice_expenses']['department_patterns']) > 0:
            results['recommendations'].append(
                "InvoiceReg table has Department and SaleCode fields that might categorize expenses"
            )
        
        if len(numeric_columns) > 15:
            results['recommendations'].append(
                f"InvoiceReg has {len(numeric_columns)} numeric fields - some might track specific expense types"
            )
        
        if len(schemas) > 1:
            results['recommendations'].append(
                f"Found potential GL/Account tables in {len(schemas)} schemas - check with DBA"
            )
        
        results['recommendations'].append(
            "Consider that G&A expenses might be tracked as negative invoices or specific department codes"
        )
        
        return jsonify(results), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Diagnostic query failed: {str(e)}',
            'details': {
                'error_type': type(e).__name__
            }
        }), 500