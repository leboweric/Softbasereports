from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
import os
import logging
import traceback
from src.services.openai_service import OpenAIQueryService
from src.services.softbase_service import SoftbaseService
from src.models.user import User
from datetime import datetime, timedelta
import calendar

logger = logging.getLogger(__name__)
ai_query_bp = Blueprint('ai_query', __name__)

# Version indicator for deployment verification
DEPLOYMENT_VERSION = "v5-error-handling"

def parse_time_period(intent):
    """Parse time period from intent"""
    if 'last month' in intent:
        return 'last_month'
    elif 'this month' in intent:
        return 'this_month'
    elif 'last week' in intent:
        return 'last_week'
    elif 'today' in intent:
        return 'today'
    elif 'this year' in intent or 'year' in intent:
        return 'this_year'
    elif 'last year' in intent:
        return 'last_year'
    else:
        return 'last_30_days'

def get_date_filter(period, date_column='InvoiceDate'):
    """Get SQL date filter for period"""
    today = datetime.now()
    
    if period == 'last_month':
        first_day_of_month = today.replace(day=1)
        last_month_end = first_day_of_month - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        return f"{date_column} >= '{last_month_start.strftime('%Y-%m-%d')}' AND {date_column} < '{first_day_of_month.strftime('%Y-%m-%d')}'"
    elif period == 'this_month':
        first_day_of_month = today.replace(day=1)
        return f"{date_column} >= '{first_day_of_month.strftime('%Y-%m-%d')}'"
    elif period == 'last_week':
        last_week = today - timedelta(days=7)
        return f"{date_column} >= '{last_week.strftime('%Y-%m-%d')}'"
    elif period == 'today':
        return f"{date_column} >= '{today.strftime('%Y-%m-%d')}'"
    elif period == 'this_year':
        year_start = today.replace(month=1, day=1)
        return f"{date_column} >= '{year_start.strftime('%Y-%m-%d')}'"
    elif period == 'last_year':
        last_year_start = today.replace(year=today.year-1, month=1, day=1)
        this_year_start = today.replace(month=1, day=1)
        return f"{date_column} >= '{last_year_start.strftime('%Y-%m-%d')}' AND {date_column} < '{this_year_start.strftime('%Y-%m-%d')}'"
    else:
        thirty_days_ago = today - timedelta(days=30)
        return f"{date_column} >= '{thirty_days_ago.strftime('%Y-%m-%d')}'"

def generate_sql_from_analysis(analysis):
    """Generate SQL query from AI analysis"""
    query_type = analysis.get('query_type', 'list')
    tables = analysis.get('tables', [])
    filters = analysis.get('filters', {})
    intent = analysis.get('intent', '').lower()
    
    # Log the analysis for debugging
    logger.info(f"Query analysis: type={query_type}, tables={tables}, intent={intent}")
    logger.info(f"Full analysis object: {analysis}")
    
    # Parse time period from intent
    time_period = parse_time_period(intent)
    
    # IMPORTANT: Check for specific query patterns FIRST before generic ones
    
    # Handle top customers queries
    if ('top' in intent and 'customer' in intent) or ('best' in intent and 'customer' in intent):
        # Extract number if specified
        import re
        num_match = re.search(r'top\s+(\d+)', intent)
        limit = int(num_match.group(1)) if num_match else 10
        
        date_filter = get_date_filter(time_period)
        
        # Use a simpler query that groups by Customer ID from InvoiceReg
        return f"""
        SELECT TOP {limit}
            i.Customer as CustomerID,
            MAX(i.BillToName) as CustomerName,
            COUNT(DISTINCT i.InvoiceNo) as InvoiceCount,
            SUM(i.GrandTotal) as TotalRevenue,
            MAX(i.InvoiceDate) as LastPurchaseDate
        FROM ben002.InvoiceReg i
        WHERE {date_filter}
        GROUP BY i.Customer
        ORDER BY TotalRevenue DESC
        """
    
    # Handle net income/profit queries first (these need special handling)
    if 'net income' in intent or 'profit' in intent or 'net profit' in intent:
        # For net income, we need to return a message that we need cost data
        return """
        SELECT 
            'Net Income Calculation Not Available' as status,
            'Net income requires cost of goods sold and expense data which is not available in the current view' as message,
            'Try asking for total sales, revenue, or gross sales instead' as suggestion
        """
    
    # Handle gross margin queries
    elif 'gross margin' in intent or 'margin' in intent:
        return """
        SELECT 
            'Gross Margin Calculation Not Available' as status,
            'Gross margin requires cost data which is not available in the current view' as message,
            'Try asking for total sales or revenue instead' as suggestion
        """
    
    # Handle time-based sales/revenue queries (but only if not handled by specific patterns above)
    elif ('total sales' in intent or 'total revenue' in intent or 
          ('sales' in intent and not 'customer' in intent) or 
          ('revenue' in intent and not 'customer' in intent)):
        # Determine time period
        today = datetime.now()
        
        if 'last month' in intent:
            first_day_of_month = today.replace(day=1)
            last_month_end = first_day_of_month - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            date_filter = f"InvoiceDate >= '{last_month_start.strftime('%Y-%m-%d')}' AND InvoiceDate < '{first_day_of_month.strftime('%Y-%m-%d')}'"
            period_desc = "last month"
        elif 'this month' in intent:
            first_day_of_month = today.replace(day=1)
            date_filter = f"InvoiceDate >= '{first_day_of_month.strftime('%Y-%m-%d')}'"
            period_desc = "this month"
        elif 'last week' in intent:
            last_week = today - timedelta(days=7)
            date_filter = f"InvoiceDate >= '{last_week.strftime('%Y-%m-%d')}'"
            period_desc = "last week"
        elif 'today' in intent:
            date_filter = f"InvoiceDate >= '{today.strftime('%Y-%m-%d')}'"
            period_desc = "today"
        else:
            # Default to last 30 days
            thirty_days_ago = today - timedelta(days=30)
            date_filter = f"InvoiceDate >= '{thirty_days_ago.strftime('%Y-%m-%d')}'"
            period_desc = "last 30 days"
        
        if 'total' in intent or query_type == 'aggregation':
            return f"""
            SELECT 
                '{period_desc}' as period,
                COUNT(DISTINCT InvoiceNo) as invoice_count,
                COUNT(DISTINCT Customer) as unique_customers,
                SUM(GrandTotal) as total_sales,
                AVG(GrandTotal) as average_sale,
                MIN(InvoiceDate) as period_start,
                MAX(InvoiceDate) as period_end
            FROM ben002.InvoiceReg
            WHERE {date_filter}
            """
        else:
            return f"""
            SELECT TOP 100
                InvoiceNo,
                InvoiceDate,
                Customer,
                BillToName,
                GrandTotal
            FROM ben002.InvoiceReg
            WHERE {date_filter}
            ORDER BY InvoiceDate DESC
            """
    
    # Handle customer queries
    elif 'customer' in ' '.join(tables).lower():
        if query_type == 'aggregation':
            return """
            SELECT TOP 20
                ID as CustomerNo,
                Name,
                City,
                State,
                Balance,
                YTD as YTDSales
            FROM ben002.Customer
            ORDER BY YTD DESC
            """
        else:
            return """
            SELECT TOP 100
                ID as CustomerNo,
                Name,
                City,
                State,
                CreditLimit,
                Balance
            FROM ben002.Customer
            WHERE Balance > 0
            ORDER BY Balance DESC
            """
    
    # Handle equipment/inventory/forklift queries
    elif any(term in intent for term in ['equipment', 'inventory', 'forklift', 'stock', 'unit']) or \
         'equipment' in ' '.join(tables).lower() or 'inventory' in ' '.join(tables).lower():
        
        # Check for specific brand mentions
        brand_filter = ""
        brands = ['linde', 'toyota', 'crown', 'yale', 'hyster', 'clark', 'caterpillar']
        for brand in brands:
            if brand in intent:
                brand_filter = f" AND LOWER(Make) LIKE '%{brand}%'"
                break
        
        # Check what type of query
        if 'stock' in intent or 'in stock' in intent:
            # Query for in-stock items
            if brand_filter:
                return f"""
                SELECT 
                    Make,
                    Model,
                    COUNT(*) as quantity_in_stock,
                    COUNT(DISTINCT Model) as unique_models
                FROM ben002.Equipment
                WHERE RentalStatus = 'In Stock'{brand_filter}
                GROUP BY Make, Model
                ORDER BY quantity_in_stock DESC
                """
            else:
                return """
                SELECT 
                    Make,
                    COUNT(*) as quantity_in_stock,
                    COUNT(DISTINCT Model) as unique_models
                FROM ben002.Equipment
                WHERE RentalStatus = 'In Stock'
                GROUP BY Make
                ORDER BY quantity_in_stock DESC
                """
        
        elif 'how many' in intent or 'count' in intent or query_type == 'count':
            # Count query
            where_clause = "WHERE 1=1"
            if 'stock' in intent:
                where_clause += " AND RentalStatus = 'In Stock'"
            where_clause += brand_filter
            
            return f"""
            SELECT 
                COUNT(*) as total_count,
                COUNT(CASE WHEN RentalStatus = 'In Stock' THEN 1 END) as in_stock,
                COUNT(CASE WHEN RentalStatus = 'Rented' THEN 1 END) as rented,
                COUNT(CASE WHEN RentalStatus = 'Sold' THEN 1 END) as sold
            FROM ben002.Equipment
            {where_clause}
            """
        
        else:
            # General equipment listing
            where_clause = "WHERE 1=1"
            if brand_filter:
                where_clause += brand_filter
            
            return f"""
            SELECT TOP 100
                StockNo,
                SerialNo,
                Make,
                Model,
                ModelYear,
                RentalStatus,
                Location,
                Hours,
                SaleAmount
            FROM ben002.Equipment
            {where_clause}
            ORDER BY StockNo DESC
            """
    
    # Handle work order queries
    # Also check if WO table is mentioned or if the original query mentions work orders
    elif (any(term in intent for term in ['work order', 'workorder', 'wo ', 'work-order']) or
          'WO' in tables or 'wo' in ' '.join(tables).lower() or
          any(term in analysis.get('original_query', '').lower() for term in ['work order', 'workorder', 'work-order'])):
        date_filter = ""
        if 'last month' in intent:
            today = datetime.now()
            first_day_of_month = today.replace(day=1)
            last_month_end = first_day_of_month - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            date_filter = f" AND OpenDate >= '{last_month_start.strftime('%Y-%m-%d')}' AND OpenDate < '{first_day_of_month.strftime('%Y-%m-%d')}'"
        elif 'this month' in intent:
            today = datetime.now()
            first_day_of_month = today.replace(day=1)
            date_filter = f" AND OpenDate >= '{first_day_of_month.strftime('%Y-%m-%d')}'"
        elif 'today' in intent:
            today = datetime.now()
            date_filter = f" AND OpenDate >= '{today.strftime('%Y-%m-%d')}'"
        elif 'yesterday' in intent:
            yesterday = datetime.now() - timedelta(days=1)
            date_filter = f" AND OpenDate >= '{yesterday.strftime('%Y-%m-%d')}' AND OpenDate < '{datetime.now().strftime('%Y-%m-%d')}'"
        
        # Check if asking for count
        if 'how many' in intent or 'count' in intent:
            return f"""
            SELECT 
                COUNT(*) as total_work_orders,
                COUNT(CASE WHEN Type = 'S' THEN 1 END) as service_orders,
                COUNT(CASE WHEN Type = 'R' THEN 1 END) as rental_orders,
                COUNT(CASE WHEN Type = 'I' THEN 1 END) as internal_orders,
                COUNT(CASE WHEN ClosedDate IS NULL THEN 1 END) as open_orders,
                COUNT(CASE WHEN ClosedDate IS NOT NULL THEN 1 END) as closed_orders
            FROM ben002.WO
            WHERE 1=1{date_filter}
            """
        else:
            # List work orders
            return f"""
            SELECT TOP 100
                WONo,
                OpenDate,
                Type,
                Customer,
                BillTo,
                UnitNo,
                CompletedDate,
                ClosedDate
            FROM ben002.WO
            WHERE 1=1{date_filter}
            ORDER BY OpenDate DESC
            """
    
    # Handle service/repair queries
    elif any(term in intent for term in ['service', 'repair', 'claim', 'maintenance']):
        date_filter = ""
        if 'last month' in intent:
            today = datetime.now()
            first_day_of_month = today.replace(day=1)
            last_month_end = first_day_of_month - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            date_filter = f" AND OpenDate >= '{last_month_start.strftime('%Y-%m-%d')}' AND OpenDate < '{first_day_of_month.strftime('%Y-%m-%d')}'"
        
        return f"""
        SELECT 
            COUNT(*) as total_claims,
            COUNT(CASE WHEN CloseDate IS NULL THEN 1 END) as open_claims,
            COUNT(CASE WHEN CloseDate IS NOT NULL THEN 1 END) as closed_claims,
            SUM(TotalLabor + TotalParts) as total_service_cost,
            AVG(TotalLabor + TotalParts) as avg_service_cost
        FROM ben002.ServiceClaim
        WHERE 1=1{date_filter}
        """
    
    # Handle parts queries
    elif any(term in intent for term in ['part', 'parts']):
        if 'low stock' in intent or 'low inventory' in intent:
            return """
            SELECT TOP 20
                PartNo,
                Description,
                QtyOnHand,
                BinLocation,
                Cost,
                Price
            FROM ben002.NationalParts
            WHERE QtyOnHand < 10
            ORDER BY QtyOnHand ASC
            """
        else:
            return """
            SELECT TOP 100
                PartNo,
                Description,
                QtyOnHand,
                BinLocation,
                Supplier,
                Cost,
                Price
            FROM ben002.NationalParts
            WHERE QtyOnHand > 0
            ORDER BY QtyOnHand DESC
            """
    
    # Default query with more helpful message
    else:
        logger.warning(f"Could not generate SQL for intent: {intent}")
        return f"""
        SELECT 
            'Could not understand query: {intent[:100]}' as message,
            'Try asking about: customers, sales, equipment inventory, service claims, or parts' as suggestion,
            '{query_type}' as detected_type,
            '{', '.join(tables)}' as detected_tables
        """

@ai_query_bp.route('/version', methods=['GET'])
def get_version():
    """Get deployment version for debugging"""
    return jsonify({
        'version': DEPLOYMENT_VERSION,
        'api_key_configured': bool(os.getenv('OPENAI_API_KEY') and os.getenv('OPENAI_API_KEY') != 'your-openai-api-key-here'),
        'timestamp': datetime.now().isoformat()
    })

@ai_query_bp.route('/test-date-ranges', methods=['GET'])
def test_date_ranges():
    """Test different date ranges to find the correct total"""
    try:
        from src.services.azure_sql_service import AzureSQLService
        db = AzureSQLService()
        
        results = {}
        
        # Test 1: Current fiscal year (Nov 1, 2024 - Oct 31, 2025)
        query1 = """
        SELECT 
            '2024-11-01 to present' as period,
            COUNT(DISTINCT InvoiceNo) as invoice_count,
            SUM(GrandTotal) as total_sales
        FROM ben002.InvoiceReg
        WHERE InvoiceDate >= '2024-11-01'
        """
        results['current_fiscal'] = db.execute_query(query1)
        
        # Test 2: Previous fiscal year (Nov 1, 2023 - Oct 31, 2024)  
        query2 = """
        SELECT 
            '2023-11-01 to 2024-10-31' as period,
            COUNT(DISTINCT InvoiceNo) as invoice_count,
            SUM(GrandTotal) as total_sales
        FROM ben002.InvoiceReg
        WHERE InvoiceDate >= '2023-11-01' AND InvoiceDate <= '2024-10-31'
        """
        results['previous_fiscal'] = db.execute_query(query2)
        
        # Test 3: Both fiscal years combined
        query3 = """
        SELECT 
            '2023-11-01 to present' as period,
            COUNT(DISTINCT InvoiceNo) as invoice_count,
            SUM(GrandTotal) as total_sales
        FROM ben002.InvoiceReg
        WHERE InvoiceDate >= '2023-11-01'
        """
        results['both_fiscal_years'] = db.execute_query(query3)
        
        # Test 4: Calendar year 2024
        query4 = """
        SELECT 
            '2024-01-01 to 2024-12-31' as period,
            COUNT(DISTINCT InvoiceNo) as invoice_count,
            SUM(GrandTotal) as total_sales
        FROM ben002.InvoiceReg
        WHERE InvoiceDate >= '2024-01-01' AND InvoiceDate <= '2024-12-31'
        """
        results['calendar_2024'] = db.execute_query(query4)
        
        # Test 5: All time total
        query5 = """
        SELECT 
            'All time' as period,
            COUNT(DISTINCT InvoiceNo) as invoice_count,
            SUM(GrandTotal) as total_sales,
            MIN(InvoiceDate) as first_invoice,
            MAX(InvoiceDate) as last_invoice
        FROM ben002.InvoiceReg
        """
        results['all_time'] = db.execute_query(query5)
        
        # Test 6: Last 12 months
        query6 = """
        SELECT 
            'Last 12 months' as period,
            COUNT(DISTINCT InvoiceNo) as invoice_count,
            SUM(GrandTotal) as total_sales
        FROM ben002.InvoiceReg
        WHERE InvoiceDate >= DATEADD(month, -12, GETDATE())
        """
        results['last_12_months'] = db.execute_query(query6)
        
        return jsonify({
            'success': True,
            'target_amount': 11998467.41,
            'date_range_tests': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_query_bp.route('/test-sql', methods=['GET'])
def test_sql():
    """Test SQL execution directly"""
    try:
        from src.services.azure_sql_service import AzureSQLService
        db = AzureSQLService()
        
        # Test 1: Check if Customer table has data
        test1 = "SELECT TOP 5 ID, Name FROM ben002.Customer ORDER BY ID"
        results1 = db.execute_query(test1)
        
        # Test 2: Check if InvoiceReg has data
        test2 = "SELECT TOP 5 InvoiceNo, Customer, GrandTotal FROM ben002.InvoiceReg ORDER BY InvoiceDate DESC"
        results2 = db.execute_query(test2)
        
        # Test 3: Try simple join
        test3 = """
        SELECT TOP 5
            c.ID,
            c.Name,
            i.InvoiceNo,
            i.Customer as InvoiceCustomerID,
            i.GrandTotal
        FROM ben002.Customer c
        INNER JOIN ben002.InvoiceReg i ON c.ID = i.Customer
        """
        results3 = db.execute_query(test3)
        
        # Test 4: Check data types
        test4 = """
        SELECT TOP 1
            c.ID as CustomerID,
            SQL_VARIANT_PROPERTY(c.ID, 'BaseType') as CustomerIDType,
            i.Customer as InvoiceCustomer,
            SQL_VARIANT_PROPERTY(i.Customer, 'BaseType') as InvoiceCustomerType
        FROM ben002.Customer c, ben002.InvoiceReg i
        """
        results4 = db.execute_query(test4)
        
        return jsonify({
            'success': True,
            'customers': {'query': test1, 'results': results1, 'count': len(results1) if results1 else 0},
            'invoices': {'query': test2, 'results': results2, 'count': len(results2) if results2 else 0},
            'join_test': {'query': test3, 'results': results3, 'count': len(results3) if results3 else 0},
            'data_types': {'query': test4, 'results': results4}
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

@ai_query_bp.route('/inspect-invoice-columns', methods=['GET'])
def inspect_invoice_columns():
    """Inspect InvoiceReg table columns to find the correct customer ID column"""
    try:
        from src.services.azure_sql_service import AzureSQLService
        db = AzureSQLService()
        
        # Test 1: Get all columns from InvoiceReg table with their data types
        test1 = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE,
            COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'ben002' 
        AND TABLE_NAME = 'InvoiceReg'
        ORDER BY ORDINAL_POSITION
        """
        columns_info = db.execute_query(test1)
        
        # Test 2: Look for columns that might contain customer IDs
        customer_related_columns = []
        for col in columns_info:
            col_name = col.get('COLUMN_NAME', '').lower()
            if any(term in col_name for term in ['customer', 'cust', 'client', 'buyer', 'billto', 'shipto']):
                customer_related_columns.append(col.get('COLUMN_NAME'))
        
        # Test 3: Get sample data from potential customer ID columns
        sample_data = {}
        if customer_related_columns:
            for col_name in customer_related_columns[:10]:  # Limit to first 10 to avoid too many queries
                try:
                    # Get distinct values and counts
                    query = f"""
                    SELECT TOP 10
                        [{col_name}] as value,
                        COUNT(*) as count
                    FROM ben002.InvoiceReg
                    WHERE [{col_name}] IS NOT NULL
                    GROUP BY [{col_name}]
                    ORDER BY COUNT(*) DESC
                    """
                    results = db.execute_query(query)
                    sample_data[col_name] = {
                        'sample_values': results,
                        'query': query
                    }
                except Exception as e:
                    sample_data[col_name] = {
                        'error': str(e),
                        'query': query
                    }
        
        # Test 4: Check if any of these columns can join with Customer.ID
        join_tests = {}
        for col_name in customer_related_columns[:5]:  # Test first 5 columns
            try:
                # Skip if it's the boolean Customer column we already know about
                if col_name.lower() == 'customer':
                    # Check if it's actually a bit/boolean type
                    col_info = next((c for c in columns_info if c['COLUMN_NAME'] == col_name), None)
                    if col_info and col_info.get('DATA_TYPE') == 'bit':
                        join_tests[col_name] = {
                            'result': 'Skipped - Customer column is bit (boolean) type',
                            'success': False
                        }
                        continue
                
                query = f"""
                SELECT TOP 5
                    c.ID as CustomerID,
                    c.Name as CustomerName,
                    i.InvoiceNo,
                    i.[{col_name}] as InvoiceCustomerValue,
                    i.GrandTotal
                FROM ben002.Customer c
                INNER JOIN ben002.InvoiceReg i ON c.ID = i.[{col_name}]
                """
                results = db.execute_query(query)
                join_tests[col_name] = {
                    'success': True,
                    'row_count': len(results) if results else 0,
                    'sample_results': results[:2] if results else [],
                    'query': query
                }
            except Exception as e:
                join_tests[col_name] = {
                    'success': False,
                    'error': str(e),
                    'query': query
                }
        
        # Test 5: Get a sample of InvoiceReg data to visually inspect
        test5 = """
        SELECT TOP 5 *
        FROM ben002.InvoiceReg
        ORDER BY InvoiceDate DESC
        """
        sample_invoice_data = db.execute_query(test5)
        
        return jsonify({
            'success': True,
            'all_columns': columns_info,
            'customer_related_columns': customer_related_columns,
            'column_sample_data': sample_data,
            'join_test_results': join_tests,
            'sample_invoice_records': sample_invoice_data,
            'recommendations': [
                "Look for columns with integer/varchar data types that match Customer.ID format",
                "Check join_test_results to see which columns successfully join with Customer table",
                "Review sample_invoice_records to identify the pattern of customer identifiers"
            ]
        })
        
    except Exception as e:
        logger.error(f"Error inspecting invoice columns: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

@ai_query_bp.route('/query', methods=['POST'])
@jwt_required()
def natural_language_query():
    """
    Process natural language queries and return structured results
    """
    try:
        # Get user identity and claims
        current_user_id = get_jwt_identity()  # This is the user ID as a string
        jwt_claims = get_jwt()  # This contains additional claims
        
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'Query text is required'}), 400
        
        query_text = data['query']
        
        # Get organization_id from JWT claims or from database
        organization_id = jwt_claims.get('organization_id')
        if not organization_id:
            # Fallback: get from database
            user = User.query.get(current_user_id)
            if user:
                organization_id = user.organization_id
            else:
                return jsonify({'error': 'User not found'}), 404
        
        # Initialize OpenAI service
        try:
            logger.info(f"Initializing OpenAI service for query: {query_text[:50]}...")
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if not openai_api_key or openai_api_key == 'your-openai-api-key-here':
                logger.error("OpenAI API key not properly configured")
                return jsonify({'error': 'OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.'}), 500
            
            openai_service = OpenAIQueryService()
            logger.info("OpenAI service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI service: {str(e)}", exc_info=True)
            return jsonify({'error': f'Failed to initialize OpenAI service: {str(e)}'}), 500
        
        # Process the natural language query
        try:
            logger.info("Processing natural language query...")
            # Add the original query to the context for fallback processing
            context = {'organization_id': organization_id, 'original_query': query_text}
            result = openai_service.process_natural_language_query(query_text, context)
            logger.info(f"Query processing result: {result.get('success', False)}")
            
            # If AI processing succeeded, add the original query to the analysis for fallback
            if result.get('success') and result.get('query_analysis'):
                result['query_analysis']['original_query'] = query_text
        except Exception as e:
            logger.error(f"Error during query processing: {str(e)}", exc_info=True)
            return jsonify({'error': f'Error processing query: {str(e)}'}), 500
        
        if not result['success']:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to process query')
            }), 400
        
        query_analysis = result['query_analysis']
        
        # Generate SQL based on the query analysis
        try:
            sql_query = generate_sql_from_analysis(query_analysis)
            logger.info(f"Generated SQL: {sql_query}")
            
            # Execute the SQL query
            from src.services.azure_sql_service import AzureSQLService
            db = AzureSQLService()
            
            logger.info("Executing SQL query...")
            results = db.execute_query(sql_query)
            
            # Log results
            if results:
                logger.info(f"Query returned {len(results)} results")
                if len(results) > 0:
                    logger.info(f"First result columns: {list(results[0].keys())}")
            else:
                logger.warning("Query returned no results")
                results = []
            
            # Format explanation
            explanation = query_analysis.get('explanation', f"Query understood: {query_analysis.get('intent', 'Unknown intent')}")
            
        except Exception as e:
            logger.error(f"Error generating/executing SQL: {str(e)}", exc_info=True)
            sql_query = f"Error: {str(e)}"
            results = []
            explanation = f"Failed to execute query: {str(e)}"
            
            # Return error details in response
            return jsonify({
                'success': False,
                'query': query_text,
                'error': str(e),
                'sql_query': sql_query,
                'parsed_params': query_analysis,
                'version': DEPLOYMENT_VERSION
            }), 400
        
        return jsonify({
            'success': True,
            'query': query_text,
            'parsed_params': query_analysis,
            'sql_query': sql_query,
            'results': results if results else [],
            'explanation': explanation,
            'result_count': len(results) if results else 0,
            'version': DEPLOYMENT_VERSION,
            'debug_info': {
                'intent': query_analysis.get('intent', ''),
                'query_type': query_analysis.get('query_type', ''),
                'tables': query_analysis.get('tables', [])
            }
        })
        
    except Exception as e:
        logger.error(f"Unexpected error in endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': f'Query processing failed: {str(e)}'}), 500

@ai_query_bp.route('/suggestions', methods=['GET'])
@jwt_required()
def get_query_suggestions():
    """
    Get suggested natural language queries based on common use cases
    """
    suggestions = [
        {
            'category': 'Sales Analysis',
            'queries': [
                "What were our total sales last month?",
                "Who are our top 5 customers by revenue this year?",
                "Which salesperson had the highest sales last quarter?",
                "Show me all Toyota forklift sales from last week"
            ]
        },
        {
            'category': 'Inventory Management', 
            'queries': [
                "How many Linde forklifts do we have in stock?",
                "Which parts are running low on inventory?",
                "Show me all available forklifts under $20,000",
                "What equipment is currently in maintenance?"
            ]
        },
        {
            'category': 'Rental Operations',
            'queries': [
                "Which customers have active rentals?",
                "Show me overdue rental returns",
                "What's our total rental revenue this month?",
                "Which equipment is rented out to Polaris?"
            ]
        },
        {
            'category': 'Parts & Service',
            'queries': [
                "Which Linde parts were we not able to fill last week?",
                "Show me all service appointments for tomorrow",
                "What parts do we need to reorder?",
                "Which technician completed the most services this month?"
            ]
        },
        {
            'category': 'Customer Insights',
            'queries': [
                "Give me the serial numbers of all forklifts that Polaris rents from us",
                "Which customers haven't made a purchase in 6 months?",
                "Show me all customers with outstanding invoices",
                "What's the average order value by customer?"
            ]
        }
    ]
    
    return jsonify({
        'success': True,
        'suggestions': suggestions
    })

@ai_query_bp.route('/query-history', methods=['GET'])
@jwt_required()
def get_query_history():
    """
    Get user's query history (would be stored in database in production)
    """
    # This would typically fetch from a query_history table
    # For now, return mock data
    
    history = [
        {
            'id': 1,
            'query': "Which Linde parts were we not able to fill last week?",
            'timestamp': "2025-01-15T10:30:00Z",
            'result_count': 12
        },
        {
            'id': 2,
            'query': "Show me all Toyota forklift sales from last month",
            'timestamp': "2025-01-14T14:22:00Z", 
            'result_count': 8
        },
        {
            'id': 3,
            'query': "Give me the serial numbers of all forklifts that Polaris rents from us",
            'timestamp': "2025-01-13T09:15:00Z",
            'result_count': 5
        }
    ]
    
    return jsonify({
        'success': True,
        'history': history
    })

@ai_query_bp.route('/validate-query', methods=['POST'])
@jwt_required()
def validate_query():
    """
    Validate and preview what a natural language query would return
    """
    try:
        # Get user identity and claims
        current_user_id = get_jwt_identity()  # This is the user ID as a string
        jwt_claims = get_jwt()  # This contains additional claims
        
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'Query text is required'}), 400
        
        query_text = data['query']
        
        # Get organization_id from JWT claims or from database
        organization_id = jwt_claims.get('organization_id')
        if not organization_id:
            # Fallback: get from database
            user = User.query.get(current_user_id)
            if user:
                organization_id = user.organization_id
            else:
                return jsonify({'error': 'User not found'}), 404
        
        # Initialize OpenAI service
        try:
            logger.info(f"Initializing OpenAI service for query: {query_text[:50]}...")
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if not openai_api_key or openai_api_key == 'your-openai-api-key-here':
                logger.error("OpenAI API key not properly configured")
                return jsonify({'error': 'OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.'}), 500
            
            openai_service = OpenAIQueryService()
            logger.info("OpenAI service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI service: {str(e)}", exc_info=True)
            return jsonify({'error': f'Failed to initialize OpenAI service: {str(e)}'}), 500
        
        # Process the natural language query
        try:
            logger.info("Processing natural language query...")
            # Add the original query to the context for fallback processing
            context = {'organization_id': organization_id, 'original_query': query_text}
            result = openai_service.process_natural_language_query(query_text, context)
            logger.info(f"Query processing result: {result.get('success', False)}")
            
            # If AI processing succeeded, add the original query to the analysis for fallback
            if result.get('success') and result.get('query_analysis'):
                result['query_analysis']['original_query'] = query_text
        except Exception as e:
            logger.error(f"Error during query processing: {str(e)}", exc_info=True)
            return jsonify({'error': f'Error processing query: {str(e)}'}), 500
        
        if not result['success']:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to validate query')
            }), 400
        
        query_analysis = result['query_analysis']
        sql_query = 'SQL generation not yet implemented'
        
        return jsonify({
            'success': True,
            'query': query_text,
            'parsed_params': query_analysis,
            'sql_query': sql_query,
            'estimated_fields': query_analysis.get('fields', []),
            'query_type': query_analysis.get('query_type', 'unknown')
        })
        
    except Exception as e:
        return jsonify({'error': f'Query validation failed: {str(e)}'}), 500

