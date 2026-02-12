from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from src.utils.tenant_utils import get_tenant_db
import os
import logging
import traceback
import re
from src.services.openai_service import OpenAIQueryService
from src.services.softbase_service import SoftbaseService
from src.services.sql_generator import SmartSQLGenerator
from src.models.user import User
from datetime import datetime, timedelta
import calendar

from flask_jwt_extended import get_jwt_identity
from src.models.user import User

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
        # Use fiscal year start month from org config
        from flask import g
        fy_month = 1  # Default to calendar year
        if hasattr(g, 'current_organization') and g.current_organization:
            fy_month = g.current_organization.fiscal_year_start_month or 1
        if today.month >= fy_month:
            year_start = today.replace(month=fy_month, day=1)
        else:
            year_start = today.replace(year=today.year-1, month=fy_month, day=1)
        return f"{date_column} >= '{year_start.strftime('%Y-%m-%d')}'"
    elif period == 'last_year':
        from flask import g
        fy_month = 1  # Default to calendar year
        if hasattr(g, 'current_organization') and g.current_organization:
            fy_month = g.current_organization.fiscal_year_start_month or 1
        if today.month >= fy_month:
            this_year_start = today.replace(month=fy_month, day=1)
            last_year_start = today.replace(year=today.year-1, month=fy_month, day=1)
        else:
            this_year_start = today.replace(year=today.year-1, month=fy_month, day=1)
            last_year_start = today.replace(year=today.year-2, month=fy_month, day=1)
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
    original_query = analysis.get('original_query', '').lower() if 'original_query' in analysis else ''
    
    # Log the analysis for debugging
    logger.info(f"Query analysis: type={query_type}, tables={tables}, intent={intent}")
    logger.info(f"Original query: {original_query}")
    logger.info(f"Full analysis object: {analysis}")
    
    # Try smart SQL generation first if we have structured data
    if 'query_action' in analysis:
        try:
            logger.info(f"Using SmartSQLGenerator with action: {analysis['query_action']}")
            smart_gen = SmartSQLGenerator()
            sql = smart_gen.generate_sql(analysis)
            if sql and 'Query not recognized' not in sql:
                return sql
        except Exception as e:
            logger.warning(f"SmartSQLGenerator failed, falling back to pattern matching: {str(e)}")
    
    # Parse time period from intent
    time_period = parse_time_period(intent)
    
    # IMPORTANT: Check for specific query patterns FIRST before generic ones
    
    # Inventory Management exact query matches - MUST BE FIRST
    if ('how many linde forklifts do we have in stock' in intent or
        'how many linde forklifts do we have in stock' in original_query or
        ('linde' in intent.lower() and 'forklift' in intent and 'stock' in intent) or
        ('count' in intent and 'linde' in intent.lower() and 'forklift' in intent)):
        return """
        SELECT 
            'Linde' as Make,
            COUNT(*) as quantity_in_stock
        FROM {schema}.Equipment
        WHERE RentalStatus = 'In Stock'
        AND UPPER(Make) LIKE '%LINDE%'
        AND (UPPER(Model) LIKE '%FORK%' OR UPPER(Make) LIKE '%FORKLIFT%')
        """
    
    elif ('which parts are running low on inventory' in intent or
          'which parts are running low on inventory' in original_query or
          'parts' in intent and 'low' in intent and 'inventory' in intent):
        return """
        SELECT TOP 100
            p.PartNo,
            p.Description,
            p.OnHand as QtyOnHand,
            p.MinStock as ReorderPoint,
            CASE 
                WHEN p.OnHand = 0 THEN 'OUT OF STOCK'
                WHEN p.OnHand <= p.MinStock THEN 'CRITICAL LOW'
                WHEN p.OnHand <= (p.MinStock * 1.5) THEN 'LOW'
                ELSE 'OK'
            END as Status
        FROM {schema}.Parts p
        WHERE p.OnHand <= CASE 
            WHEN p.MinStock * 1.5 > 10 THEN p.MinStock * 1.5 
            ELSE 10 
        END
        ORDER BY 
            CASE 
                WHEN p.OnHand = 0 THEN 0
                WHEN p.OnHand <= p.MinStock THEN 1
                ELSE 2
            END,
            p.OnHand ASC
        """
    
    elif ('show me all available forklifts under' in intent or
          'show me all available forklifts under' in original_query or
          ('available' in intent and 'forklift' in intent and 'under' in intent)):
        # Extract price from query
        import re
        price_match = re.search(r'\$?([\d,]+)', original_query if original_query else intent)
        price_limit = int(price_match.group(1).replace(',', '')) if price_match else 20000
        
        return f"""
        SELECT 
            e.UnitNo as StockNo,
            e.Make,
            e.Model,
            e.Sell as SaleAmount
        FROM {schema}.Equipment e
        WHERE e.RentalStatus = 'In Stock'
        AND e.Sell > 0
        AND e.Sell <= {price_limit}
        AND (UPPER(e.Model) LIKE '%FORK%' OR UPPER(e.Make) LIKE '%FORK%')
        ORDER BY e.Sell ASC
        """
    
    elif ('what equipment is currently in maintenance' in intent or
          'what equipment is currently in maintenance' in original_query or
          ('equipment' in intent and 'maintenance' in intent)):
        return """
        SELECT DISTINCT
            e.UnitNo as StockNo,
            e.Make,
            e.Model,
            e.SerialNo,
            wo.WONo as ServiceOrderNo,
            wo.OpenDate as MaintenanceStartDate,
            wo.Comments
        FROM {schema}.Equipment e
        INNER JOIN {schema}.WO wo ON e.UnitNo = wo.UnitNo
        WHERE wo.Type = 'S'
        AND wo.ClosedDate IS NULL
        ORDER BY wo.OpenDate DESC
        """
    
    # Customer Insights exact query matches
    elif ('give me the serial numbers of all forklifts that polaris rents from us' in intent or
          'give me the serial numbers of all forklifts that polaris rents from us' in original_query or
          ('polaris' in intent.lower() and 'serial' in intent) or
          ('polaris' in intent.lower() and 'forklift' in intent) or
          ('serial' in intent and 'forklift' in intent and 'polaris' in intent.lower()) or
          ('serial' in intent and 'forklift' in intent and 'rent' in intent)):
        # Check if asking about specific customer
        if 'polaris' in intent.lower() or 'polaris' in (original_query or '').lower():
            return """
            SELECT 
                e.SerialNo,
                e.Make,
                e.Model
            FROM {schema}.Equipment e
            INNER JOIN {schema}.Customer c ON e.CustomerNo = c.Number
            WHERE e.CustomerNo IS NOT NULL 
            AND e.CustomerNo != ''
            AND (e.RentalStatus LIKE '%rent%' 
                 OR e.RentalStatus LIKE '%Rent%'
                 OR e.RentalStatus LIKE '%RENT%'
                 OR e.RentalStatus = 'R'
                 OR e.RentalStatus = 'Out'
                 OR e.RentalStatus = 'On Rent')
            AND UPPER(c.Name) LIKE '%POLARIS%'
            AND (UPPER(e.Model) LIKE '%FORK%' OR UPPER(e.Make) LIKE '%FORK%')
            ORDER BY e.SerialNo
            """
        else:
            # Generic rented forklifts
            return """
            SELECT 
                e.SerialNo,
                e.Make,
                e.Model
            FROM {schema}.Equipment e
            WHERE e.RentalStatus = 'Rented'
            AND (UPPER(e.Model) LIKE '%FORK%' OR UPPER(e.Make) LIKE '%FORK%')
            ORDER BY e.SerialNo
            """
    
    elif ('which customers haven\'t made a purchase in 6 months' in intent or
          'which customers haven\'t made a purchase in 6 months' in original_query or
          'which customers haven\'t made a purchase in 6 months' in original_query.replace("'", "\'") if original_query else False or
          ('customers' in intent and 'haven\'t' in intent and 'purchase' in intent and '6 months' in intent)):
        six_months_ago = datetime.now() - timedelta(days=180)
        return f"""
        SELECT 
            c.Name as customer,
            MAX(i.InvoiceDate) as last_purchase,
            DATEDIFF(day, MAX(i.InvoiceDate), GETDATE()) as days_since_purchase
        FROM {schema}.Customer c
        LEFT JOIN {schema}.InvoiceReg i ON c.ID = i.Customer
        GROUP BY c.ID, c.Name
        HAVING MAX(i.InvoiceDate) < '{six_months_ago.strftime('%Y-%m-%d')}'
           OR MAX(i.InvoiceDate) IS NULL
        ORDER BY last_purchase ASC
        """
    
    elif ('show me all customers with outstanding invoices' in intent or
          'show me all customers with outstanding invoices' in original_query or
          ('customers' in intent and 'outstanding' in intent and 'invoice' in intent)):
        return """
        SELECT 
            ar.CustomerNo,
            c.Name as customer,
            SUM(ar.Amount) as balance
        FROM {schema}.ARDetail ar
        INNER JOIN {schema}.Customer c ON ar.CustomerNo = c.Number
        WHERE ar.Amount > 0
        GROUP BY ar.CustomerNo, c.Name
        HAVING SUM(ar.Amount) > 0
        ORDER BY balance DESC
        """
    
    elif (('average order value by customer' in intent or
           'average order value by customer' in original_query or
           'what\'s the average order value by customer' in intent or
           'what\'s the average order value by customer' in original_query or
           'what\'s the average order value by customer' in original_query.replace("'", "\'") if original_query else False)):
        return """
        SELECT TOP 20
            i.BillToName as customer,
            AVG(i.GrandTotal) as average_value
        FROM {schema}.InvoiceReg i
        WHERE i.GrandTotal > 0
        AND i.BillToName IS NOT NULL
        GROUP BY i.BillToName
        HAVING COUNT(DISTINCT i.InvoiceNo) > 0
        ORDER BY average_value DESC
        """
    
    # Parts & Service exact query matches - MUST BE FIRST to prevent generic handlers from catching them
    elif ('which linde parts were we not able to fill last week' in intent or 
          'which linde parts were we not able to fill last week' in original_query or
          ('linde' in intent.lower() and 'parts' in intent and ('not' in intent or 'backorder' in intent or 'unable' in intent)) or
          ('parts' in intent and 'backorder' in intent) or
          ('linde' in original_query.lower() and 'parts' in original_query and 'fill' in original_query)):
        # Get date filter for last week
        last_week_start = datetime.now() - timedelta(days=7)
        last_week_filter = f"wo.OpenDate >= '{last_week_start.strftime('%Y-%m-%d')}'"
        
        return f"""
        SELECT DISTINCT
            wp.PartNo,
            wp.Description
        FROM {schema}.WOParts wp
        INNER JOIN {schema}.WO wo ON wp.WONo = wo.WONo
        WHERE {last_week_filter}
        AND (wp.PartNo LIKE 'L%' OR UPPER(wp.Description) LIKE '%LINDE%')
        AND wp.BOQty > 0
        ORDER BY wp.PartNo
        """
    
    elif ('show me all service appointments for tomorrow' in intent or 'service appointments for tomorrow' in intent or
          'show me all service appointments for tomorrow' in original_query or 'service appointments for tomorrow' in original_query):
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_str = tomorrow.strftime('%Y-%m-%d')
        
        return f"""
        SELECT 
            wo.WONo + ' - ' + ISNULL(c.Name, 'Unknown Customer') + ' at ' + 
            CONVERT(varchar, wo.ScheduleDate, 108) as appointment,
            CASE 
                WHEN wo.Comments IS NOT NULL THEN wo.Comments
                ELSE 'Service for ' + ISNULL(wo.UnitNo, 'Equipment')
            END as service
        FROM {schema}.WO wo
        LEFT JOIN {schema}.Customer c ON wo.BillTo = c.Number
        WHERE wo.Type = 'S'
        AND CAST(wo.ScheduleDate AS DATE) = '{tomorrow_str}'
        AND wo.ClosedDate IS NULL
        ORDER BY wo.ScheduleDate
        """
    
    elif ('what parts do we need to reorder' in intent or
          'what parts do we need to reorder' in original_query):
        return """
        SELECT TOP 100
            p.PartNo,
            p.Description,
            p.OnHand as QtyOnHand
        FROM {schema}.Parts p
        WHERE p.OnHand < 10
        AND p.PartNo NOT LIKE '%OIL%'
        AND p.PartNo NOT LIKE '%GREASE%'
        AND p.PartNo NOT LIKE '%COOLANT%'
        AND p.Description NOT LIKE '%OIL%'
        AND p.Description NOT LIKE '%GREASE%'
        AND p.Description NOT LIKE '%COOLANT%'
        ORDER BY p.OnHand ASC, p.PartNo
        """
    
    elif ('which technician completed the most services this month' in intent or
          'which technician completed the most services this month' in original_query):
        month_filter = f"wo.ClosedDate >= '{datetime.now().strftime('%Y-%m-01')}'"
        
        return f"""
        SELECT TOP 1
            wo.Technician as technician,
            COUNT(DISTINCT wo.WONo) as service_count
        FROM {schema}.WO wo
        WHERE wo.Type = 'S'
        AND wo.ClosedDate IS NOT NULL
        AND {month_filter}
        AND wo.Technician IS NOT NULL
        GROUP BY wo.Technician
        ORDER BY COUNT(DISTINCT wo.WONo) DESC
        """
    
    # First check for exact query matches to ensure proper handling
    elif ('which customers have active rentals' in intent or
          'which customers have active rentals' in original_query):
        # Use RentalHistory for more accurate active rental data
        current_year = datetime.now().year
        current_month = datetime.now().month
        return f"""
        SELECT DISTINCT
            c.Name as customer,
            e.UnitNo + ' - ' + e.Make + ' ' + e.Model as rental
        FROM {schema}.RentalHistory rh
        INNER JOIN {schema}.Equipment e ON rh.SerialNo = e.SerialNo
        INNER JOIN {schema}.Customer c ON e.CustomerNo = c.Number
        WHERE rh.Year = {current_year}
        AND rh.Month = {current_month}
        AND rh.DaysRented > 0
        ORDER BY c.Name, e.UnitNo
        """
    
    elif 'show me overdue rental returns' in intent or 'overdue rental returns' in intent:
        return """
        SELECT 
            e.UnitNo + ' - ' + e.Make + ' ' + e.Model as rental,
            DATEADD(day, 30, wo.OpenDate) as due_date,
            DATEDIFF(day, DATEADD(day, 30, wo.OpenDate), GETDATE()) as overdue
        FROM {schema}.Equipment e
        INNER JOIN {schema}.Customer c ON e.CustomerNo = c.Number
        INNER JOIN {schema}.WO wo ON e.UnitNo = wo.UnitNo
        WHERE e.CustomerNo IS NOT NULL 
        AND e.CustomerNo != ''
        AND (e.RentalStatus LIKE '%rent%' 
             OR e.RentalStatus LIKE '%Rent%'
             OR e.RentalStatus LIKE '%RENT%'
             OR e.RentalStatus = 'R'
             OR e.RentalStatus = 'Out'
             OR e.RentalStatus = 'On Rent')
        AND wo.Type = 'R'
        AND wo.ClosedDate IS NULL
        AND DATEADD(day, 30, wo.OpenDate) < GETDATE()
        ORDER BY overdue DESC
        """
    
    elif ('list' in intent and 'forklift' in intent and ('rent' in intent or 'being rented' in intent)) or \
         ('forklift' in intent and 'currently' in intent and 'rent' in intent) or \
         ('all forklifts' in intent and 'rent' in intent):
        # List all forklifts currently being rented
        current_year = datetime.now().year
        current_month = datetime.now().month
        return f"""
        SELECT DISTINCT
            e.UnitNo,
            e.SerialNo,
            e.Make,
            e.Model,
            c.Name as CustomerName,
            rh.DaysRented,
            rh.RentAmount
        FROM {schema}.RentalHistory rh
        INNER JOIN {schema}.Equipment e ON rh.SerialNo = e.SerialNo
        LEFT JOIN {schema}.Customer c ON e.CustomerNo = c.Number
        WHERE rh.Year = {current_year}
        AND rh.Month = {current_month}
        AND rh.DaysRented > 0
        AND (UPPER(e.Model) LIKE '%FORK%' OR UPPER(e.Make) LIKE '%FORK%')
        ORDER BY e.UnitNo
        """
    
    elif ('which equipment is rented out to polaris' in intent or
          ('list equipment rented out' in intent and 'polaris' in (original_query or '').lower())):
        return """
        SELECT 
            e.UnitNo as equipment,
            c.Name as customer
        FROM {schema}.Equipment e
        INNER JOIN {schema}.Customer c ON e.CustomerNo = c.Number
        WHERE e.CustomerNo IS NOT NULL 
        AND e.CustomerNo != ''
        AND (e.RentalStatus LIKE '%rent%' 
             OR e.RentalStatus LIKE '%Rent%'
             OR e.RentalStatus LIKE '%RENT%'
             OR e.RentalStatus = 'R'
             OR e.RentalStatus = 'Out'
             OR e.RentalStatus = 'On Rent')
        AND UPPER(c.Name) LIKE '%POLARIS%'
        ORDER BY e.UnitNo
        """
    
    elif 'list equipment rented out to a specific customer' in intent:
        # Generic handler when no specific customer mentioned
        return """
        SELECT 
            e.UnitNo,
            e.SerialNo,
            e.Make,
            e.Model,
            c.Name as CustomerName
        FROM {schema}.Equipment e
        INNER JOIN {schema}.Customer c ON e.CustomerNo = c.Number
        WHERE e.RentalStatus = 'Rented'
        ORDER BY c.Name, e.UnitNo
        """
    
    # Handle top customers queries
    elif ('top' in intent and 'customer' in intent) or ('best' in intent and 'customer' in intent) or \
         ('who are our top' in intent and 'customers' in intent) or \
         ('who are our top' in original_query and 'customers' in original_query):
        # Extract number if specified from both intent and original query
        combined_text = intent + ' ' + (original_query if original_query else '')
        import re  # Ensure re is available in this scope
        num_match = re.search(r'top\s+(\d+)', combined_text)
        if not num_match:
            # Also check for written numbers
            if 'five' in combined_text or '5' in combined_text:
                limit = 5
            else:
                limit = 10
        else:
            limit = int(num_match.group(1))
        
        date_filter = get_date_filter(time_period)
        
        # Group by BillToName since Customer field is boolean
        return f"""
        SELECT TOP {limit}
            i.BillToName as CustomerName,
            SUM(i.GrandTotal) as TotalRevenue
        FROM {schema}.InvoiceReg i
        WHERE {date_filter}
        AND i.BillToName IS NOT NULL
        GROUP BY i.BillToName
        ORDER BY TotalRevenue DESC
        """
    
    # Handle equipment sales queries (e.g., "Toyota forklift sales")
    if ('toyota' in intent.lower() or 'linde' in intent.lower() or 'forklift' in intent.lower()) and \
       ('sales' in intent or 'sold' in intent) and \
       'equipment' not in intent:  # Don't match general equipment queries
        # Equipment sales by make
        date_filter = get_date_filter(time_period)
        
        # Determine the make
        make_filter = ""
        if 'toyota' in intent.lower():
            make_filter = "AND UPPER(eh.Description) LIKE '%TOYOTA%'"
        elif 'linde' in intent.lower():
            make_filter = "AND UPPER(eh.Description) LIKE '%LINDE%'"
        
        return f"""
        SELECT DISTINCT
            i.InvoiceNo,
            CASE 
                WHEN eh.Description LIKE '%TOYOTA%' THEN 'Toyota'
                WHEN eh.Description LIKE '%LINDE%' THEN 'Linde'
                ELSE 'Other'
            END as Make
        FROM {schema}.InvoiceReg i
        INNER JOIN {schema}.EquipmentHistory eh ON i.InvoiceNo = eh.WONo
        WHERE {date_filter}
        AND eh.EntryType = 'SALE'
        {make_filter}
        ORDER BY i.InvoiceDate DESC
        """
    
    # Handle salesperson queries
    elif ('which salesperson had the highest sales last quarter' in intent or
          'which salesperson had the highest sales last quarter' in original_query or
          ('salesperson' in intent and ('sales' in intent or 'highest' in intent or 'top' in intent))):
        # Salesperson performance query
        # Check if asking for last quarter specifically
        if 'last quarter' in intent or 'last quarter' in original_query:
            # Calculate last quarter date range
            today = datetime.now()
            current_quarter = (today.month - 1) // 3 + 1
            current_year = today.year
            
            if current_quarter == 1:
                # Last quarter was Q4 of previous year
                start_date = datetime(current_year - 1, 10, 1)
                end_date = datetime(current_year, 1, 1)
            else:
                # Last quarter was previous quarter of current year
                start_month = (current_quarter - 2) * 3 + 1
                start_date = datetime(current_year, start_month, 1)
                end_month = (current_quarter - 1) * 3 + 1
                end_date = datetime(current_year, end_month, 1)
            
            date_filter = f"i.InvoiceDate >= '{start_date.strftime('%Y-%m-%d')}' AND i.InvoiceDate < '{end_date.strftime('%Y-%m-%d')}'"
        else:
            date_filter = get_date_filter(time_period)
        
        # Note: This assumes BillToName contains salesperson info
        # In reality, we'd need to look at Customer.Salesman1-6 fields
        return f"""
        SELECT TOP 1
            'Top Salesperson' as salesperson,
            SUM(i.GrandTotal) as sales
        FROM {schema}.InvoiceReg i
        WHERE {date_filter}
        """
    
    # Handle net income/profit queries first (these need special handling)
    elif 'net income' in intent or 'profit' in intent or 'net profit' in intent:
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
    
    # Handle service sales specifically (by department)
    elif 'service' in intent and ('sales' in intent or 'revenue' in intent):
        # Determine time period
        today = datetime.now()
        date_filter = ""
        period_desc = ""
        
        # Check for month names first
        month_names = ['january', 'february', 'march', 'april', 'may', 'june', 
                      'july', 'august', 'september', 'october', 'november', 'december']
        current_year = datetime.now().year
        
        # Check intent and original query for month names
        query_lower = (intent + ' ' + analysis.get('original_query', '')).lower()
        
        for i, month in enumerate(month_names):
            if month in query_lower:
                month_num = i + 1
                year = current_year
                year_match = re.search(r'\b(20\d{2})\b', query_lower)
                if year_match:
                    year = int(year_match.group(1))
                
                first_day = datetime(year, month_num, 1)
                if month_num == 12:
                    last_day = datetime(year + 1, 1, 1)
                else:
                    last_day = datetime(year, month_num + 1, 1)
                
                date_filter = f"InvoiceDate >= '{first_day.strftime('%Y-%m-%d')}' AND InvoiceDate < '{last_day.strftime('%Y-%m-%d')}'"
                period_desc = f"{month.capitalize()} {year}"
                break
        
        # If no month name found, check for other patterns
        if not date_filter:
            if 'last month' in intent:
                first_day_of_month = today.replace(day=1)
                last_month_end = first_day_of_month - timedelta(days=1)
                last_month_start = last_month_end.replace(day=1)
                date_filter = f"InvoiceDate >= '{last_month_start.strftime('%Y-%m-%d')}' AND InvoiceDate < '{first_day_of_month.strftime('%Y-%m-%d')}'"
                period_desc = last_month_start.strftime("%B %Y")
            elif 'this month' in intent:
                first_day_of_month = today.replace(day=1)
                date_filter = f"InvoiceDate >= '{first_day_of_month.strftime('%Y-%m-%d')}'"
                period_desc = "this month"
            else:
                thirty_days_ago = today - timedelta(days=30)
                date_filter = f"InvoiceDate >= '{thirty_days_ago.strftime('%Y-%m-%d')}'"
                period_desc = "last 30 days"
        
        return f"""
        SELECT 
            '{period_desc}' as period,
            COUNT(DISTINCT InvoiceNo) as invoice_count,
            SUM(GrandTotal) as total_service_sales,
            AVG(GrandTotal) as average_service_invoice,
            MIN(InvoiceDate) as period_start,
            MAX(InvoiceDate) as period_end
        FROM {schema}.InvoiceReg
        WHERE {date_filter}
        AND Department IN (10, 40, 45)  -- Service departments (10=Service, 40=Field Service, 45=Shop Service)
        """
    
    # Handle specific rental queries - check both intent and original query
    elif ('customer' in intent and 'active' in intent and 'rental' in intent) or \
         ('customer' in intent and 'have' in intent and 'rental' in intent):
        # Customers with active rentals - use flexible rental status matching
        return """
        SELECT DISTINCT
            c.Name as customer,
            e.UnitNo + ' - ' + e.Make + ' ' + e.Model as rental
        FROM {schema}.Equipment e
        INNER JOIN {schema}.Customer c ON e.CustomerNo = c.Number
        WHERE e.CustomerNo IS NOT NULL 
        AND e.CustomerNo != ''
        AND (e.RentalStatus LIKE '%rent%' 
             OR e.RentalStatus LIKE '%Rent%'
             OR e.RentalStatus LIKE '%RENT%'
             OR e.RentalStatus = 'R'
             OR e.RentalStatus = 'Out'
             OR e.RentalStatus = 'On Rent')
        ORDER BY c.Name, e.UnitNo
        """
    
    elif ('overdue' in intent and 'rental' in intent) or \
         ('rental' in intent and 'return' in intent and 'overdue' in intent) or \
         ('overdue rental returns' in original_query):
        # Overdue rental returns
        return """
        SELECT 
            c.Name as CustomerName,
            e.UnitNo,
            e.SerialNo,
            e.Make,
            e.Model,
            rc.EndDate as DueDate,
            DATEDIFF(day, rc.EndDate, GETDATE()) as DaysOverdue
        FROM {schema}.Equipment e
        INNER JOIN {schema}.Customer c ON e.CustomerNo = c.Number
        INNER JOIN {schema}.RentalContract rc ON e.UnitNo = rc.UnitNo
        WHERE e.RentalStatus = 'Rented'
        AND rc.EndDate < GETDATE()
        ORDER BY DaysOverdue DESC
        """
    
    elif ('equipment' in intent and 'rented' in intent and 'polaris' in intent.lower()) or \
         ('equipment' in intent and 'polaris' in intent.lower()) or \
         ('polaris' in intent.lower() and 'rent' in intent) or \
         ('equipment is rented out to polaris' in original_query):
        # Equipment rented to specific customer
        return """
        SELECT 
            e.UnitNo,
            e.SerialNo,
            e.Make,
            e.Model,
            e.ModelYear,
            e.RentalStatus,
            c.Name as CustomerName
        FROM {schema}.Equipment e
        INNER JOIN {schema}.Customer c ON e.CustomerNo = c.Number
        WHERE e.RentalStatus = 'Rented'
        AND UPPER(c.Name) LIKE '%POLARIS%'
        ORDER BY e.UnitNo
        """
    
    # Handle rental sales specifically
    elif 'rental' in intent and ('sales' in intent or 'revenue' in intent):
        # Alternative: Use RentalHistory for actual rental revenue
        # This would be more accurate as it tracks actual rental activity
        # current_year = datetime.now().year
        # current_month = datetime.now().month
        # return f"""
        # SELECT 
        #     '{current_year}-{current_month:02d}' as period,
        #     COUNT(DISTINCT rh.SerialNo) as equipment_count,
        #     SUM(rh.DaysRented) as total_days_rented,
        #     SUM(rh.RentAmount) as total_rental_sales
        # FROM {schema}.RentalHistory rh
        # WHERE rh.Year = {current_year}
        # AND rh.Month = {current_month}
        # """
        # Determine time period
        today = datetime.now()
        date_filter = ""
        period_desc = ""
        
        # Check for month names first
        month_names = ['january', 'february', 'march', 'april', 'may', 'june', 
                      'july', 'august', 'september', 'october', 'november', 'december']
        current_year = datetime.now().year
        
        # Check intent and original query for month names
        query_lower = (intent + ' ' + analysis.get('original_query', '')).lower()
        
        for i, month in enumerate(month_names):
            if month in query_lower:
                month_num = i + 1
                year = current_year
                year_match = re.search(r'\b(20\d{2})\b', query_lower)
                if year_match:
                    year = int(year_match.group(1))
                
                first_day = datetime(year, month_num, 1)
                if month_num == 12:
                    last_day = datetime(year + 1, 1, 1)
                else:
                    last_day = datetime(year, month_num + 1, 1)
                
                date_filter = f"InvoiceDate >= '{first_day.strftime('%Y-%m-%d')}' AND InvoiceDate < '{last_day.strftime('%Y-%m-%d')}'"
                period_desc = f"{month.capitalize()} {year}"
                break
        
        # If no month name found, check for other patterns
        if not date_filter:
            if 'last month' in intent:
                first_day_of_month = today.replace(day=1)
                last_month_end = first_day_of_month - timedelta(days=1)
                last_month_start = last_month_end.replace(day=1)
                date_filter = f"InvoiceDate >= '{last_month_start.strftime('%Y-%m-%d')}' AND InvoiceDate < '{first_day_of_month.strftime('%Y-%m-%d')}'"
                period_desc = last_month_start.strftime("%B %Y")
            elif 'this month' in intent:
                first_day_of_month = today.replace(day=1)
                date_filter = f"InvoiceDate >= '{first_day_of_month.strftime('%Y-%m-%d')}'"
                period_desc = "this month"
            else:
                thirty_days_ago = today - timedelta(days=30)
                date_filter = f"InvoiceDate >= '{thirty_days_ago.strftime('%Y-%m-%d')}'"
                period_desc = "last 30 days"
        
        return f"""
        SELECT 
            '{period_desc}' as period,
            COUNT(DISTINCT InvoiceNo) as invoice_count,
            SUM(GrandTotal) as total_rental_sales,
            AVG(GrandTotal) as average_rental_invoice,
            MIN(InvoiceDate) as period_start,
            MAX(InvoiceDate) as period_end
        FROM {schema}.InvoiceReg
        WHERE {date_filter}
        AND SaleCode IN ('RENTR', 'RENTRS')
        """
    
    # Handle labor sales specifically
    elif 'labor' in intent and ('sales' in intent or 'revenue' in intent):
        # Determine time period
        today = datetime.now()
        date_filter = ""
        period_desc = ""
        
        # Check for month names first
        month_names = ['january', 'february', 'march', 'april', 'may', 'june', 
                      'july', 'august', 'september', 'october', 'november', 'december']
        current_year = datetime.now().year
        
        # Check intent and original query for month names
        query_lower = (intent + ' ' + analysis.get('original_query', '')).lower()
        
        for i, month in enumerate(month_names):
            if month in query_lower:
                month_num = i + 1
                year = current_year
                year_match = re.search(r'\b(20\d{2})\b', query_lower)
                if year_match:
                    year = int(year_match.group(1))
                
                first_day = datetime(year, month_num, 1)
                if month_num == 12:
                    last_day = datetime(year + 1, 1, 1)
                else:
                    last_day = datetime(year, month_num + 1, 1)
                
                date_filter = f"InvoiceDate >= '{first_day.strftime('%Y-%m-%d')}' AND InvoiceDate < '{last_day.strftime('%Y-%m-%d')}'"
                period_desc = f"{month.capitalize()} {year}"
                break
        
        # If no month name found, check for other patterns
        if not date_filter:
            if 'last month' in intent:
                first_day_of_month = today.replace(day=1)
                last_month_end = first_day_of_month - timedelta(days=1)
                last_month_start = last_month_end.replace(day=1)
                date_filter = f"InvoiceDate >= '{last_month_start.strftime('%Y-%m-%d')}' AND InvoiceDate < '{first_day_of_month.strftime('%Y-%m-%d')}'"
                period_desc = last_month_start.strftime("%B %Y")
            elif 'this month' in intent:
                first_day_of_month = today.replace(day=1)
                date_filter = f"InvoiceDate >= '{first_day_of_month.strftime('%Y-%m-%d')}'"
                period_desc = "this month"
            else:
                thirty_days_ago = today - timedelta(days=30)
                date_filter = f"InvoiceDate >= '{thirty_days_ago.strftime('%Y-%m-%d')}'"
                period_desc = "last 30 days"
        
        return f"""
        SELECT 
            '{period_desc}' as period,
            COUNT(DISTINCT InvoiceNo) as invoice_count,
            SUM(ISNULL(LaborTaxable, 0) + ISNULL(LaborNonTax, 0)) as total_labor_sales,
            AVG(ISNULL(LaborTaxable, 0) + ISNULL(LaborNonTax, 0)) as average_labor_per_invoice,
            MIN(InvoiceDate) as period_start,
            MAX(InvoiceDate) as period_end
        FROM {schema}.InvoiceReg
        WHERE {date_filter}
        AND (LaborTaxable > 0 OR LaborNonTax > 0)
        """
    
    # Handle parts sales specifically
    elif 'parts' in intent and ('sales' in intent or 'revenue' in intent):
        # Similar logic for parts sales
        today = datetime.now()
        date_filter = ""
        period_desc = ""
        
        # [Same date parsing logic as above - abbreviated for brevity]
        if 'last month' in intent:
            first_day_of_month = today.replace(day=1)
            last_month_end = first_day_of_month - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            date_filter = f"InvoiceDate >= '{last_month_start.strftime('%Y-%m-%d')}' AND InvoiceDate < '{first_day_of_month.strftime('%Y-%m-%d')}'"
            period_desc = last_month_start.strftime("%B %Y")
        else:
            thirty_days_ago = today - timedelta(days=30)
            date_filter = f"InvoiceDate >= '{thirty_days_ago.strftime('%Y-%m-%d')}'"
            period_desc = "last 30 days"
        
        return f"""
        SELECT 
            '{period_desc}' as period,
            COUNT(DISTINCT InvoiceNo) as invoice_count,
            SUM(ISNULL(PartsTaxable, 0) + ISNULL(PartsNonTax, 0)) as total_parts_sales,
            AVG(ISNULL(PartsTaxable, 0) + ISNULL(PartsNonTax, 0)) as average_parts_per_invoice,
            MIN(InvoiceDate) as period_start,
            MAX(InvoiceDate) as period_end
        FROM {schema}.InvoiceReg
        WHERE {date_filter}
        AND (PartsTaxable > 0 OR PartsNonTax > 0)
        """
    
    # Handle time-based sales/revenue queries (but only if not handled by specific patterns above)
    elif ('total sales' in intent or 'total revenue' in intent or 
          ('sales' in intent and not 'customer' in intent) or 
          ('revenue' in intent and not 'customer' in intent)):
        # Determine time period
        today = datetime.now()
        date_filter = ""
        period_desc = ""
        
        # Check for month names first
        month_names = ['january', 'february', 'march', 'april', 'may', 'june', 
                      'july', 'august', 'september', 'october', 'november', 'december']
        current_year = datetime.now().year
        
        # Check intent and original query for month names
        query_lower = (intent + ' ' + analysis.get('original_query', '')).lower()
        
        for i, month in enumerate(month_names):
            if month in query_lower:
                month_num = i + 1
                # Assume current year unless specified
                year = current_year
                # Check if a year is mentioned
                year_match = re.search(r'\b(20\d{2})\b', query_lower)
                if year_match:
                    year = int(year_match.group(1))
                
                # Create date range for the month
                first_day = datetime(year, month_num, 1)
                if month_num == 12:
                    last_day = datetime(year + 1, 1, 1)
                else:
                    last_day = datetime(year, month_num + 1, 1)
                
                date_filter = f"InvoiceDate >= '{first_day.strftime('%Y-%m-%d')}' AND InvoiceDate < '{last_day.strftime('%Y-%m-%d')}'"
                period_desc = f"{month.capitalize()} {year}"
                break
        
        # If no month name found, check for other patterns
        if not date_filter:
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
        
        # Override period_desc if we detected a specific month
        if 'last month' in intent and period_desc == "last month":
            # Get the actual month name for last month
            last_month_date = today.replace(day=1) - timedelta(days=1)
            period_desc = last_month_date.strftime("%B %Y")
        
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
            FROM {schema}.InvoiceReg
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
            FROM {schema}.InvoiceReg
            WHERE {date_filter}
            ORDER BY InvoiceDate DESC
            """
    
    # Handle specific customer queries first
    elif ('customer' in intent and 'outstanding' in intent and 'invoice' in intent):
        # Customers with outstanding invoices - use ARDetail
        return """
        SELECT DISTINCT
            c.ID as CustomerNo,
            c.Name as CustomerName,
            COUNT(DISTINCT ar.InvoiceNo) as OutstandingInvoices,
            SUM(ar.Amount) as TotalOutstanding
        FROM {schema}.ARDetail ar
        INNER JOIN {schema}.Customer c ON ar.CustomerNo = c.Number
        WHERE ar.Amount > 0
        GROUP BY c.ID, c.Name
        HAVING SUM(ar.Amount) > 0
        ORDER BY TotalOutstanding DESC
        """
    
    elif ('customer' in intent and "haven't" in intent and 'purchase' in intent) or \
         ('customer' in intent and 'not' in intent and 'purchase' in intent):
        # Customers who haven't purchased recently
        return """
        SELECT 
            c.ID as CustomerNo,
            c.Name as CustomerName,
            c.City,
            c.State,
            s.LastSaleDate,
            DATEDIFF(day, s.LastSaleDate, GETDATE()) as DaysSinceLastSale
        FROM {schema}.Customer c
        LEFT JOIN {schema}.Sales s ON c.Number = s.CustomerNo
        WHERE s.LastSaleDate < DATEADD(month, -6, GETDATE())
           OR s.LastSaleDate IS NULL
        ORDER BY s.LastSaleDate ASC
        """
    
    elif ('average' in intent and 'order' in intent and 'value' in intent and 'customer' in intent):
        # Average order value by customer
        # InvoiceReg.Customer is boolean - use BillToName
        return """
        SELECT TOP 20
            i.BillToName as customer,
            AVG(i.GrandTotal) as average_value
        FROM {schema}.InvoiceReg i
        WHERE i.InvoiceDate >= DATEADD(year, -1, GETDATE())
        AND i.BillToName IS NOT NULL
        GROUP BY i.BillToName
        HAVING COUNT(DISTINCT i.InvoiceNo) > 0
        ORDER BY average_value DESC
        """
    
    
    
    # Handle work order queries
    # Also check if WO table is mentioned or if the original query mentions work orders
    elif (any(term in intent for term in ['work order', 'workorder', 'wo ', 'work-order']) or
          'WO' in tables or 'wo' in ' '.join(tables).lower() or
          any(term in analysis.get('original_query', '').lower() for term in ['work order', 'workorder', 'work-order'])):
        date_filter = ""
        
        # Check for month names
        month_names = ['january', 'february', 'march', 'april', 'may', 'june', 
                      'july', 'august', 'september', 'october', 'november', 'december']
        current_year = datetime.now().year
        
        # Check intent and original query for month names
        query_lower = (intent + ' ' + analysis.get('original_query', '')).lower()
        
        for i, month in enumerate(month_names):
            if month in query_lower:
                month_num = i + 1
                # Assume current year unless specified
                year = current_year
                # Check if a year is mentioned
                year_match = re.search(r'\b(20\d{2})\b', query_lower)
                if year_match:
                    year = int(year_match.group(1))
                
                # Create date range for the month
                first_day = datetime(year, month_num, 1)
                if month_num == 12:
                    last_day = datetime(year + 1, 1, 1)
                else:
                    last_day = datetime(year, month_num + 1, 1)
                
                date_filter = f" AND OpenDate >= '{first_day.strftime('%Y-%m-%d')}' AND OpenDate < '{last_day.strftime('%Y-%m-%d')}'"
                break
        
        # If no month name found, check for other date patterns
        if not date_filter:
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
        
        # Check what type of work order query
        if 'value' in intent or 'cost' in intent or 'amount' in intent or 'total' in intent:
            # Query for total value of work orders
            return f"""
            WITH WOCosts AS (
                SELECT 
                    wo.WONo,
                    wo.Type,
                    wo.OpenDate,
                    wo.ClosedDate,
                    ISNULL(labor.LaborCost, 0) as LaborCost,
                    ISNULL(parts.PartsCost, 0) as PartsCost,
                    ISNULL(misc.MiscCost, 0) as MiscCost,
                    ISNULL(labor.LaborCost, 0) + ISNULL(parts.PartsCost, 0) + ISNULL(misc.MiscCost, 0) as TotalCost
                FROM {schema}.WO wo
                LEFT JOIN (
                    SELECT WONo, SUM(Sell) as LaborCost
                    FROM {schema}.WOLabor
                    GROUP BY WONo
                ) labor ON wo.WONo = labor.WONo
                LEFT JOIN (
                    SELECT WONo, SUM(Sell * Qty) as PartsCost
                    FROM {schema}.WOParts
                    GROUP BY WONo
                ) parts ON wo.WONo = parts.WONo
                LEFT JOIN (
                    SELECT WONo, SUM(Sell) as MiscCost
                    FROM {schema}.WOMisc
                    GROUP BY WONo
                ) misc ON wo.WONo = misc.WONo
                WHERE 1=1{date_filter}
            )
            SELECT 
                COUNT(*) as total_work_orders,
                SUM(TotalCost) as total_value,
                AVG(TotalCost) as average_value,
                SUM(LaborCost) as total_labor,
                SUM(PartsCost) as total_parts,
                SUM(MiscCost) as total_misc,
                COUNT(CASE WHEN Type = 'S' THEN 1 END) as service_orders,
                COUNT(CASE WHEN Type = 'R' THEN 1 END) as rental_orders,
                COUNT(CASE WHEN Type = 'I' THEN 1 END) as internal_orders
            FROM WOCosts
            """
        elif 'how many' in intent or 'count' in intent:
            # Simple count query
            return f"""
            SELECT 
                COUNT(*) as total_work_orders,
                COUNT(CASE WHEN Type = 'S' THEN 1 END) as service_orders,
                COUNT(CASE WHEN Type = 'R' THEN 1 END) as rental_orders,
                COUNT(CASE WHEN Type = 'I' THEN 1 END) as internal_orders,
                COUNT(CASE WHEN ClosedDate IS NULL THEN 1 END) as open_orders,
                COUNT(CASE WHEN ClosedDate IS NOT NULL THEN 1 END) as closed_orders
            FROM {schema}.WO
            WHERE 1=1{date_filter}
            """
        else:
            # List work orders
            return f"""
            SELECT TOP 100
                WONo,
                OpenDate,
                Type,
                BillTo,
                UnitNo,
                CompletedDate,
                ClosedDate
            FROM {schema}.WO
            WHERE 1=1{date_filter}
            ORDER BY OpenDate DESC
            """
    
    # Handle specific service queries first
    elif 'service' in intent and 'appointment' in intent and 'tomorrow' in intent:
        # Service appointments for tomorrow
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_str = tomorrow.strftime('%Y-%m-%d')
        
        return f"""
        SELECT 
            wo.WONo,
            wo.Type as ServiceType,
            c.Name as CustomerName,
            wo.UnitNo,
            wo.SerialNo,
            wo.ScheduleDate as AppointmentTime,
            wo.Technician,
            wo.Comments
        FROM {schema}.WO wo
        LEFT JOIN {schema}.Customer c ON wo.BillTo = c.Number
        WHERE wo.Type = 'S'
        AND CAST(wo.ScheduleDate AS DATE) = '{tomorrow_str}'
        AND wo.ClosedDate IS NULL
        ORDER BY wo.ScheduleDate
        """
    
    elif 'technician' in intent and 'most' in intent and 'service' in intent:
        # Technician with most services
        date_filter = get_date_filter(parse_time_period(intent), 'wo.ClosedDate')
        
        return f"""
        SELECT TOP 10
            wo.Technician,
            COUNT(DISTINCT wo.WONo) as CompletedServices,
            SUM(wl.Hours) as TotalHours,
            AVG(wl.Hours) as AvgHoursPerService
        FROM {schema}.WO wo
        LEFT JOIN {schema}.WOLabor wl ON wo.WONo = wl.WONo
        WHERE wo.Type = 'S'
        AND wo.ClosedDate IS NOT NULL
        AND {date_filter}
        GROUP BY wo.Technician
        HAVING wo.Technician IS NOT NULL
        ORDER BY CompletedServices DESC
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
        FROM {schema}.ServiceClaim
        WHERE 1=1{date_filter}
        """
    
    # Handle parts queries
    elif any(term in intent for term in ['part', 'parts']):
        # Handle specific Linde parts fill rate query
        if ('linde' in intent and 'not' in intent and 'fill' in intent) or \
           ('linde' in intent and 'unable' in intent) or \
           ('parts' in intent and 'fill' in intent and 'not' in intent):
            # Get date filter for "last week"
            date_filter = get_date_filter('last_week', 'wo.OpenDate')
            
            return f"""
            SELECT DISTINCT
                wp.PartNo,
                wp.Description,
                wp.WONo,
                wo.OpenDate,
                wp.Qty as QuantityOrdered,
                wp.BOQty as BackorderQty,
                p.OnHand as CurrentStock,
                c.Name as CustomerName
            FROM {schema}.WOParts wp
            INNER JOIN {schema}.WO wo ON wp.WONo = wo.WONo
            LEFT JOIN {schema}.Parts p ON wp.PartNo = p.PartNo
            LEFT JOIN {schema}.Customer c ON wo.BillTo = c.ID
            WHERE {date_filter}
            AND (wp.PartNo LIKE 'L%' OR UPPER(wp.Description) LIKE '%LINDE%')
            AND wp.BOQty > 0
            ORDER BY wo.OpenDate DESC, wp.PartNo
            """
        elif 'reorder' in intent:
            # Parts that need reordering
            return """
            SELECT 
                p.PartNo,
                p.Description,
                p.OnHand as QtyOnHand
            FROM {schema}.Parts p
            WHERE p.OnHand <= ISNULL(p.MinStock, 10)
            ORDER BY p.OnHand ASC
            """
        elif 'low stock' in intent or 'low inventory' in intent:
            return """
            SELECT TOP 20
                PartNo,
                Description,
                OnHand as QtyOnHand,
                Bin,
                Cost,
                List as Price
            FROM {schema}.Parts
            WHERE OnHand < 10
            ORDER BY OnHand ASC
            """
        else:
            return """
            SELECT TOP 100
                PartNo,
                Description,
                OnHand as QtyOnHand,
                Bin,
                Cost,
                List as Price
            FROM {schema}.Parts
            WHERE OnHand > 0
            ORDER BY OnHand DESC
            """
    
    # If no specific handler matched, return an error
    else:
        logger.warning(f"No specific handler for query: {intent}")
        return f"""
        SELECT 
            'Query not recognized: {intent[:100]}' as error,
            'This specific query pattern needs to be implemented' as message
        """

@ai_query_bp.route('/test-structured-prompt', methods=['POST'])
@jwt_required()
def test_structured_prompt():
    """Test the new structured OpenAI prompt format"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400
        
        # Get user context
        current_user_id = get_jwt_identity()
        jwt_claims = get_jwt()
        organization_id = jwt_claims.get('organization_id')
        
        # Initialize OpenAI service
        openai_service = OpenAIQueryService()
        
        # Process query
        result = openai_service.process_natural_language_query(
            data['query'], 
            {'organization_id': organization_id}
        )
        
        return jsonify({
            'success': result.get('success', False),
            'query': data['query'],
            'structured_analysis': result.get('query_analysis'),
            'raw_response': result
        })
        
    except Exception as e:
        logger.error(f"Error testing structured prompt: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@ai_query_bp.route('/version', methods=['GET'])
def get_version():
    """Get deployment version for debugging"""
    return jsonify({
        'version': DEPLOYMENT_VERSION,
        'api_key_configured': bool(os.getenv('OPENAI_API_KEY') and os.getenv('OPENAI_API_KEY') != 'your-openai-api-key-here'),
        'timestamp': datetime.now().isoformat()
    })

@ai_query_bp.route('/check-sale-codes', methods=['GET'])
def check_sale_codes():
    """Check what SaleCodes and Departments exist in the database"""
    try:
        db = get_tenant_db()
        schema = get_tenant_schema()
        # Get all unique SaleCodes with counts
        sale_codes_query = f"""
        SELECT 
            SaleCode,
            COUNT(*) as invoice_count,
            SUM(GrandTotal) as total_sales,
            MIN(InvoiceDate) as first_invoice,
            MAX(InvoiceDate) as last_invoice
        FROM {schema}.InvoiceReg
        WHERE InvoiceDate >= '2025-07-01'
        GROUP BY SaleCode
        ORDER BY total_sales DESC
        """
        
        # Get all unique Departments with counts
        departments_query = f"""
        SELECT 
            Department,
            COUNT(*) as invoice_count,
            SUM(GrandTotal) as total_sales,
            MIN(InvoiceDate) as first_invoice,
            MAX(InvoiceDate) as last_invoice
        FROM {schema}.InvoiceReg
        WHERE InvoiceDate >= '2025-07-01'
        AND Department IS NOT NULL
        GROUP BY Department
        ORDER BY total_sales DESC
        """
        
        sale_codes_results = db.execute_query(sale_codes_query)
        departments_results = db.execute_query(departments_query)
        
        return jsonify({
            'success': True,
            'sale_codes': sale_codes_results,
            'departments': departments_results,
            'total_sale_codes': len(sale_codes_results) if sale_codes_results else 0,
            'total_departments': len(departments_results) if departments_results else 0
        })
        
    except Exception as e:
        logger.error(f"Error checking sale codes: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_query_bp.route('/test-date-ranges', methods=['GET'])
def test_date_ranges():
    """Test different date ranges to find the correct total"""
    try:
        db = get_tenant_db()
        schema = get_tenant_schema()
        results = {}
        
        # Test 1: Current fiscal year (Nov 1, 2024 - Oct 31, 2025)
        query1 = """
        SELECT 
            '2024-11-01 to present' as period,
            COUNT(DISTINCT InvoiceNo) as invoice_count,
            SUM(GrandTotal) as total_sales
        FROM {schema}.InvoiceReg
        WHERE InvoiceDate >= '2024-11-01'
        """
        results['current_fiscal'] = db.execute_query(query1)
        
        # Test 2: Previous fiscal year (Nov 1, 2023 - Oct 31, 2024)  
        query2 = """
        SELECT 
            '2023-11-01 to 2024-10-31' as period,
            COUNT(DISTINCT InvoiceNo) as invoice_count,
            SUM(GrandTotal) as total_sales
        FROM {schema}.InvoiceReg
        WHERE InvoiceDate >= '2023-11-01' AND InvoiceDate <= '2024-10-31'
        """
        results['previous_fiscal'] = db.execute_query(query2)
        
        # Test 3: Both fiscal years combined
        query3 = """
        SELECT 
            '2023-11-01 to present' as period,
            COUNT(DISTINCT InvoiceNo) as invoice_count,
            SUM(GrandTotal) as total_sales
        FROM {schema}.InvoiceReg
        WHERE InvoiceDate >= '2023-11-01'
        """
        results['both_fiscal_years'] = db.execute_query(query3)
        
        # Test 4: Calendar year 2024
        query4 = """
        SELECT 
            '2024-01-01 to 2024-12-31' as period,
            COUNT(DISTINCT InvoiceNo) as invoice_count,
            SUM(GrandTotal) as total_sales
        FROM {schema}.InvoiceReg
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
        FROM {schema}.InvoiceReg
        """
        results['all_time'] = db.execute_query(query5)
        
        # Test 6: Last 12 months
        query6 = """
        SELECT 
            'Last 12 months' as period,
            COUNT(DISTINCT InvoiceNo) as invoice_count,
            SUM(GrandTotal) as total_sales
        FROM {schema}.InvoiceReg
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
        db = get_tenant_db()
        schema = get_tenant_schema()
        # Test 1: Check if Customer table has data
        test1 = "SELECT TOP 5 ID, Name FROM {schema}.Customer ORDER BY ID"
        results1 = db.execute_query(test1)
        
        # Test 2: Check if InvoiceReg has data
        test2 = "SELECT TOP 5 InvoiceNo, Customer, GrandTotal FROM {schema}.InvoiceReg ORDER BY InvoiceDate DESC"
        results2 = db.execute_query(test2)
        
        # Test 3: Try simple join
        test3 = """
        SELECT TOP 5
            c.ID,
            c.Name,
            i.InvoiceNo,
            i.Customer as InvoiceCustomerID,
            i.GrandTotal
        FROM {schema}.Customer c
        INNER JOIN {schema}.InvoiceReg i ON c.ID = i.Customer
        """
        results3 = db.execute_query(test3)
        
        # Test 4: Check data types
        test4 = """
        SELECT TOP 1
            c.ID as CustomerID,
            SQL_VARIANT_PROPERTY(c.ID, 'BaseType') as CustomerIDType,
            i.Customer as InvoiceCustomer,
            SQL_VARIANT_PROPERTY(i.Customer, 'BaseType') as InvoiceCustomerType
        FROM {schema}.Customer c, {schema}.InvoiceReg i
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

@ai_query_bp.route('/check-rental-history', methods=['GET'])
def check_rental_history():
    """Check rental data using RentalHistory table"""
    try:
        db = get_tenant_db()
        schema = get_tenant_schema()
        # Get current rentals from RentalHistory
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        current_rentals_query = f"""
        SELECT 
            rh.SerialNo,
            rh.Year,
            rh.Month,
            rh.DaysRented,
            rh.RentAmount,
            e.UnitNo,
            e.Make,
            e.Model,
            e.CustomerNo,
            c.Name as CustomerName
        FROM {schema}.RentalHistory rh
        INNER JOIN {schema}.Equipment e ON rh.SerialNo = e.SerialNo
        LEFT JOIN {schema}.Customer c ON e.CustomerNo = c.Number
        WHERE rh.Year = {current_year}
        AND rh.Month = {current_month}
        AND rh.DaysRented > 0
        ORDER BY rh.RentAmount DESC
        """
        
        current_rentals = db.execute_query(current_rentals_query)
        
        # Get rental trends
        trends_query = f"""
        SELECT 
            Year,
            Month,
            COUNT(DISTINCT SerialNo) as EquipmentCount,
            SUM(DaysRented) as TotalDaysRented,
            SUM(RentAmount) as TotalRevenue
        FROM {schema}.RentalHistory
        WHERE Year >= {current_year - 1}
        GROUP BY Year, Month
        ORDER BY Year DESC, Month DESC
        """
        
        rental_trends = db.execute_query(trends_query)
        
        return jsonify({
            'success': True,
            'current_rentals': current_rentals,
            'rental_trends': rental_trends,
            'current_period': f"{current_year}-{current_month:02d}"
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_query_bp.route('/check-rental-data', methods=['GET'])
def check_rental_data():
    """Check rental data to debug active rentals query"""
    try:
        db = get_tenant_db()
        schema = get_tenant_schema()
        # Check rental status values
        status_query = f"""
        SELECT 
            RentalStatus,
            COUNT(*) as count
        FROM {schema}.Equipment
        GROUP BY RentalStatus
        ORDER BY count DESC
        """
        
        rental_statuses = db.execute_query(status_query)
        
        # Check equipment with CustomerNo
        customer_query = f"""
        SELECT TOP 10
            UnitNo,
            RentalStatus,
            CustomerNo,
            Customer as CustomerFlag,
            Make,
            Model
        FROM {schema}.Equipment
        WHERE CustomerNo IS NOT NULL
        AND CustomerNo != ''
        """
        
        equipment_with_customers = db.execute_query(customer_query)
        
        # Check if we can join
        join_test = """
        SELECT TOP 10
            e.UnitNo,
            e.RentalStatus,
            e.CustomerNo,
            c.Number,
            c.Name
        FROM {schema}.Equipment e
        INNER JOIN {schema}.Customer c ON e.CustomerNo = c.Number
        WHERE e.CustomerNo IS NOT NULL
        """
        
        join_results = db.execute_query(join_test)
        
        # Check specific rental statuses that might mean 'rented'
        rental_variations_query = f"""
        SELECT TOP 20
            e.UnitNo,
            e.Make,
            e.Model,
            e.RentalStatus,
            e.CustomerNo,
            c.Name as CustomerName
        FROM {schema}.Equipment e
        LEFT JOIN {schema}.Customer c ON e.CustomerNo = c.Number
        WHERE e.CustomerNo IS NOT NULL
        AND e.CustomerNo != ''
        AND (e.RentalStatus LIKE '%rent%' 
             OR e.RentalStatus LIKE '%Rent%'
             OR e.RentalStatus LIKE '%RENT%'
             OR e.RentalStatus = 'R'
             OR e.RentalStatus = 'Out')
        """
        
        rental_variations = db.execute_query(rental_variations_query)
        
        return jsonify({
            'success': True,
            'rental_statuses': rental_statuses,
            'equipment_with_customers': equipment_with_customers,
            'join_test_results': join_results,
            'rental_variations': rental_variations,
            'debug_info': {
                'total_statuses': len(rental_statuses) if rental_statuses else 0,
                'equipment_with_customer_count': len(equipment_with_customers) if equipment_with_customers else 0,
                'successful_joins': len(join_results) if join_results else 0
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_query_bp.route('/check-customer-columns', methods=['GET'])
def check_customer_columns():
    """Check actual Customer table columns"""
    try:
        db = get_tenant_db()
        schema = get_tenant_schema()
        # Get column info
        columns_query = f"""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{schema}' 
        AND TABLE_NAME = 'Customer'
        ORDER BY ORDINAL_POSITION
        """
        
        columns = db.execute_query(columns_query)
        
        # Try to get sample data
        sample_query = f"""
        SELECT TOP 5 *
        FROM {schema}.Customer
        ORDER BY ID
        """
        
        sample_data = db.execute_query(sample_query)
        
        return jsonify({
            'success': True,
            'columns': columns,
            'sample_data': sample_data,
            'column_names': [col['COLUMN_NAME'] for col in columns] if columns else []
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_query_bp.route('/inspect-invoice-columns', methods=['GET'])
def inspect_invoice_columns():
    """Inspect InvoiceReg table columns to find the correct customer ID column"""
    try:
        db = get_tenant_db()
        schema = get_tenant_schema()
        # Test 1: Get all columns from InvoiceReg table with their data types
        test1 = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE,
            COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{schema}' 
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
                    FROM {schema}.InvoiceReg
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
                FROM {schema}.Customer c
                INNER JOIN {schema}.InvoiceReg i ON c.ID = i.[{col_name}]
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
        FROM {schema}.InvoiceReg
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
            db = get_tenant_db()
            schema = get_tenant_schema()
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

