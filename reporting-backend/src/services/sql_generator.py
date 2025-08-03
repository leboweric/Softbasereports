"""
Smart SQL Generator that uses structured query analysis from OpenAI
"""
from datetime import datetime, timedelta
import logging
import re

logger = logging.getLogger(__name__)

class SmartSQLGenerator:
    """Generate SQL based on structured query analysis instead of pattern matching"""
    
    def __init__(self):
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
    
    def generate_sql(self, query_analysis):
        """Main entry point - routes to appropriate handler based on query_action"""
        query_action = query_analysis.get('query_action', '')
        
        # Add original intent to filters for context
        if 'filters' not in query_analysis:
            query_analysis['filters'] = {}
        query_analysis['filters']['original_intent'] = query_analysis.get('intent', '')
        query_analysis['filters']['query_type'] = query_analysis.get('query_type', 'list')
        
        # Route to appropriate handler
        handlers = {
            'list_equipment': self._handle_list_equipment,
            'list_rentals': self._handle_list_rentals,
            'count_equipment': self._handle_count_equipment,
            'count_rentals': self._handle_count_rentals,
            'show_sales': self._handle_show_sales,
            'show_inventory': self._handle_show_inventory,
            'service_status': self._handle_service_status,
            'parts_status': self._handle_parts_status,
            'customer_info': self._handle_customer_info,
            'financial_summary': self._handle_financial_summary
        }
        
        handler = handlers.get(query_action)
        if handler:
            return handler(query_analysis)
        else:
            # Fallback to intent-based generation for backward compatibility
            return self._fallback_generation(query_analysis)
    
    def _handle_list_equipment(self, analysis):
        """Handle equipment listing queries"""
        entity_subtype = analysis.get('entity_subtype', '').lower()
        filters = analysis.get('filters', {})
        status = filters.get('status', '')
        
        # Check if this is a rental query
        if status == 'rented' or analysis.get('use_rental_history') == 'true':
            return self._generate_rental_equipment_query(entity_subtype, filters)
        
        # Otherwise, general equipment query
        sql = "SELECT e.UnitNo, e.SerialNo, e.Make, e.Model"
        sql += ", e.RentalStatus, e.Location"
        sql += " FROM ben002.Equipment e"
        
        where_clauses = []
        
        # Add equipment type filter
        if entity_subtype == 'forklift':
            where_clauses.append("(UPPER(e.Model) LIKE '%FORK%' OR UPPER(e.Make) LIKE '%FORK%')")
        elif entity_subtype:
            where_clauses.append(f"UPPER(e.Model) LIKE '%{entity_subtype.upper()}%'")
        
        # Add status filter
        if status == 'available':
            where_clauses.append("e.RentalStatus = 'In Stock'")
        elif status == 'sold':
            where_clauses.append("e.RentalStatus = 'Sold'")
        
        # Add customer filter if specified
        if filters.get('customer'):
            sql += " INNER JOIN ben002.Customer c ON e.CustomerNo = c.Number"
            where_clauses.append(f"UPPER(c.Name) LIKE '%{filters['customer'].upper()}%'")
        
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        
        sql += " ORDER BY e.UnitNo"
        return sql
    
    def _generate_rental_equipment_query(self, equipment_type, filters):
        """Generate query for rental equipment using RentalHistory"""
        # Check if this is a count query
        query_type = filters.get('query_type', 'list')
        
        if query_type == 'count' or 'how many' in filters.get('original_intent', '').lower():
            # Count query
            sql = f"""
            SELECT COUNT(DISTINCT e.SerialNo) as count
            FROM ben002.RentalHistory rh
            INNER JOIN ben002.Equipment e ON rh.SerialNo = e.SerialNo
            WHERE rh.Year = {self.current_year}
            AND rh.Month = {self.current_month}
            AND rh.DaysRented > 0
            """
        else:
            # List query - Include all fields in SELECT that are used in ORDER BY
            sql = f"""
            SELECT DISTINCT
                e.UnitNo,
                e.SerialNo,
                e.Make,
                e.Model,
                c.Name as CustomerName,
                rh.DaysRented,
                rh.RentAmount
            FROM ben002.RentalHistory rh
            INNER JOIN ben002.Equipment e ON rh.SerialNo = e.SerialNo
            LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
            WHERE rh.Year = {self.current_year}
            AND rh.Month = {self.current_month}
            AND rh.DaysRented > 0
            """
        
        # Add equipment type filter
        if equipment_type == 'forklift':
            sql += " AND (UPPER(e.Model) LIKE '%FORK%' OR UPPER(e.Make) LIKE '%FORK%')"
        elif equipment_type:
            sql += f" AND UPPER(e.Model) LIKE '%{equipment_type.upper()}%'"
        
        # Add customer filter
        if filters.get('customer'):
            sql += f" AND UPPER(c.Name) LIKE '%{filters['customer'].upper()}%'"
        
        # Only add ORDER BY for list queries
        if query_type != 'count' and 'how many' not in filters.get('original_intent', '').lower():
            sql += " ORDER BY e.UnitNo"
            
        return sql
    
    def _handle_list_rentals(self, analysis):
        """Handle rental listing queries"""
        filters = analysis.get('filters', {})
        query_type = filters.get('query_type', 'list')
        entity_subtype = analysis.get('entity_subtype', '').lower()
        
        # Check if this is a count query
        if query_type == 'count' or 'how many' in filters.get('original_intent', '').lower():
            # This is asking for a count, not a list
            # If entity_subtype is forklift, count forklifts on rent
            if entity_subtype == 'forklift' or 'forklift' in filters.get('original_intent', '').lower():
                return self._generate_rental_equipment_query('forklift', filters)
            else:
                # Count all rentals
                sql = f"""
                SELECT COUNT(DISTINCT e.SerialNo) as count
                FROM ben002.RentalHistory rh
                INNER JOIN ben002.Equipment e ON rh.SerialNo = e.SerialNo
                WHERE rh.Year = {self.current_year}
                AND rh.Month = {self.current_month}
                AND rh.DaysRented > 0
                """
                return sql
        
        # For listing active rentals, use RentalHistory for accuracy
        # Note: When using DISTINCT with ORDER BY, all ORDER BY columns must be in SELECT
        sql = f"""
        SELECT DISTINCT
            c.Name as customer,
            e.UnitNo,
            e.Make,
            e.Model,
            e.UnitNo + ' - ' + e.Make + ' ' + e.Model as rental
        FROM ben002.RentalHistory rh
        INNER JOIN ben002.Equipment e ON rh.SerialNo = e.SerialNo
        INNER JOIN ben002.Customer c ON e.CustomerNo = c.Number
        WHERE rh.Year = {self.current_year}
        AND rh.Month = {self.current_month}
        AND rh.DaysRented > 0
        """
        
        # Add customer filter if specified
        if filters.get('customer'):
            sql += f" AND UPPER(c.Name) LIKE '%{filters['customer'].upper()}%'"
        
        sql += " ORDER BY c.Name, e.UnitNo"
        return sql
    
    def _handle_count_equipment(self, analysis):
        """Handle equipment counting queries"""
        entity_subtype = analysis.get('entity_subtype', '').lower()
        filters = analysis.get('filters', {})
        status = filters.get('status', '')
        
        # If counting rented equipment, use RentalHistory
        if status == 'rented' or 'rent' in filters.get('original_intent', '').lower():
            sql = f"""
            SELECT COUNT(DISTINCT e.SerialNo) as count
            FROM ben002.RentalHistory rh
            INNER JOIN ben002.Equipment e ON rh.SerialNo = e.SerialNo
            WHERE rh.Year = {self.current_year}
            AND rh.Month = {self.current_month}
            AND rh.DaysRented > 0
            """
            
            # Add equipment type filter
            if entity_subtype == 'forklift' or 'forklift' in filters.get('original_intent', '').lower():
                sql += " AND (UPPER(e.Model) LIKE '%FORK%' OR UPPER(e.Make) LIKE '%FORK%')"
            elif entity_subtype:
                sql += f" AND UPPER(e.Model) LIKE '%{entity_subtype.upper()}%'"
            
            return sql
        else:
            # Count equipment by status
            sql = "SELECT COUNT(*) as count FROM ben002.Equipment e WHERE 1=1"
            
            # Add equipment type filter
            if entity_subtype == 'forklift':
                sql += " AND (UPPER(e.Model) LIKE '%FORK%' OR UPPER(e.Make) LIKE '%FORK%')"
            elif entity_subtype:
                sql += f" AND UPPER(e.Model) LIKE '%{entity_subtype.upper()}%'"
            
            # Add status filter
            if status == 'available':
                sql += " AND e.RentalStatus = 'In Stock'"
            elif status == 'sold':
                sql += " AND e.RentalStatus = 'Sold'"
            
            return sql
    
    def _handle_count_rentals(self, analysis):
        """Handle rental counting queries"""
        filters = analysis.get('filters', {})
        
        sql = f"""
        SELECT COUNT(DISTINCT rh.SerialNo) as count
        FROM ben002.RentalHistory rh
        INNER JOIN ben002.Equipment e ON rh.SerialNo = e.SerialNo
        WHERE rh.Year = {self.current_year}
        AND rh.Month = {self.current_month}
        AND rh.DaysRented > 0
        """
        
        # Add customer filter if specified
        if filters.get('customer'):
            sql += " INNER JOIN ben002.Customer c ON e.CustomerNo = c.Number"
            sql += f" AND UPPER(c.Name) LIKE '%{filters['customer'].upper()}%'"
        
        return sql
    
    def _handle_show_sales(self, analysis):
        """Handle sales queries"""
        filters = analysis.get('filters', {})
        time_period = filters.get('time_period', 'last_30_days')
        query_type = analysis.get('query_type', 'aggregation')
        
        # Build date filter - pass analysis for month name parsing
        date_filter = self._build_date_filter(time_period, analysis=analysis)
        
        # Build period description
        period_desc = time_period
        if time_period == 'specific_date' and analysis:
            original_intent = filters.get('original_intent', '').lower()
            # Extract month name for display
            month_names = ['january', 'february', 'march', 'april', 'may', 'june', 
                          'july', 'august', 'september', 'october', 'november', 'december']
            for month in month_names:
                if month in original_intent:
                    year = datetime.now().year
                    year_match = re.search(r'\b(20\d{2})\b', original_intent)
                    if year_match:
                        year = int(year_match.group(1))
                    period_desc = f"{month.capitalize()} {year}"
                    break
        
        if query_type == 'aggregation':
            return f"""
            SELECT 
                '{period_desc}' as period,
                COUNT(DISTINCT InvoiceNo) as invoice_count,
                SUM(GrandTotal) as total_sales,
                AVG(GrandTotal) as average_sale
            FROM ben002.InvoiceReg
            WHERE {date_filter}
            """
        else:
            return f"""
            SELECT TOP 100
                InvoiceNo,
                InvoiceDate,
                BillToName as CustomerName,
                GrandTotal
            FROM ben002.InvoiceReg
            WHERE {date_filter}
            ORDER BY InvoiceDate DESC
            """
    
    def _handle_parts_status(self, analysis):
        """Handle parts inventory queries"""
        filters = analysis.get('filters', {})
        status = filters.get('status', '')
        
        if status == 'low' or 'reorder' in analysis.get('intent', ''):
            return """
            SELECT TOP 100
                p.PartNo,
                p.Description,
                p.OnHand as QtyOnHand
            FROM ben002.Parts p
            WHERE p.OnHand < COALESCE(p.MinStock, 10)
            ORDER BY p.OnHand ASC
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
            FROM ben002.Parts
            ORDER BY OnHand DESC
            """
    
    def _build_date_filter(self, time_period, date_column='InvoiceDate', analysis=None):
        """Build SQL date filter based on time period"""
        today = datetime.now()
        
        # Check if we need to parse month names from the original intent
        if time_period == 'specific_date' and analysis:
            original_intent = analysis.get('filters', {}).get('original_intent', '').lower()
            
            # Month names mapping
            month_names = {
                'january': 1, 'february': 2, 'march': 3, 'april': 4,
                'may': 5, 'june': 6, 'july': 7, 'august': 8,
                'september': 9, 'october': 10, 'november': 11, 'december': 12
            }
            
            # Try to find a month name in the intent
            for month_name, month_num in month_names.items():
                if month_name in original_intent:
                    # Default to current year unless a year is specified
                    year = today.year
                    
                    # Check if a year is mentioned
                    year_match = re.search(r'\b(20\d{2})\b', original_intent)
                    if year_match:
                        year = int(year_match.group(1))
                    
                    # Build date range for the month
                    first_day = datetime(year, month_num, 1)
                    if month_num == 12:
                        last_day = datetime(year + 1, 1, 1)
                    else:
                        last_day = datetime(year, month_num + 1, 1)
                    
                    return f"{date_column} >= '{first_day.strftime('%Y-%m-%d')}' AND {date_column} < '{last_day.strftime('%Y-%m-%d')}'"
        
        if time_period == 'current' or time_period == 'this_month':
            return f"{date_column} >= '{today.strftime('%Y-%m-01')}'"
        elif time_period == 'last_month':
            first_day = today.replace(day=1)
            last_month_end = first_day.replace(day=1) - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            return f"{date_column} >= '{last_month_start.strftime('%Y-%m-%d')}' AND {date_column} < '{first_day.strftime('%Y-%m-%d')}'"
        elif time_period == 'last_week':
            last_week = today - timedelta(days=7)
            return f"{date_column} >= '{last_week.strftime('%Y-%m-%d')}'"
        else:
            # Default to last 30 days
            thirty_days_ago = today - timedelta(days=30)
            return f"{date_column} >= '{thirty_days_ago.strftime('%Y-%m-%d')}'"
    
    def _handle_service_status(self, analysis):
        """Handle service-related queries"""
        # Implementation for service queries
        return "SELECT * FROM ben002.WO WHERE Type = 'S' AND ClosedDate IS NULL"
    
    def _handle_customer_info(self, analysis):
        """Handle customer information queries"""
        # Implementation for customer queries
        return "SELECT TOP 100 * FROM ben002.Customer"
    
    def _handle_financial_summary(self, analysis):
        """Handle financial summary queries"""
        # Implementation for financial queries
        return "SELECT SUM(GrandTotal) as total FROM ben002.InvoiceReg"
    
    def _handle_show_inventory(self, analysis):
        """Handle inventory queries"""
        # Implementation for inventory queries
        return "SELECT * FROM ben002.Equipment WHERE RentalStatus = 'In Stock'"
    
    def _fallback_generation(self, analysis):
        """Fallback to basic SQL generation"""
        # This would contain the current pattern matching logic as a fallback
        intent = analysis.get('intent', '').lower()
        return f"""
        SELECT 
            'Query not recognized: {intent[:100]}' as error,
            'This specific query pattern needs to be implemented' as message
        """