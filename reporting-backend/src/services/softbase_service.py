import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from .azure_sql_service import AzureSQLService
import logging

logger = logging.getLogger(__name__)

class SoftbaseService:
    """Service to interact with Softbase Evolution database via Azure SQL"""
    
    def __init__(self, organization):
        self.organization = organization
        self.db_service = AzureSQLService()
        
    def get_data(self, query_type: str, filters: Dict, date_range: Dict, organization_id: int) -> Dict:
        """Get data based on query type and filters from Azure SQL database"""
        
        try:
            # First, let's explore what tables are available
            if query_type == 'tables':
                tables = self.db_service.get_tables()
                return {
                    'data': [{'table_name': t} for t in tables],
                    'total_count': len(tables)
                }
            
            # Map query types to potential table names (we'll need to adjust based on actual tables)
            # These are common patterns - actual table names may differ
            query_map = {
                'sales': """
                    SELECT TOP 100 * FROM Sales 
                    WHERE 1=1
                """,
                'inventory': """
                    SELECT TOP 100 * FROM Inventory 
                    WHERE 1=1
                """,
                'customers': """
                    SELECT TOP 100 * FROM Customers 
                    WHERE 1=1
                """,
                'service': """
                    SELECT TOP 100 * FROM ServiceRecords 
                    WHERE 1=1
                """,
                'parts': """
                    SELECT TOP 100 * FROM Parts 
                    WHERE 1=1
                """
            }
            
            # Start with base query
            base_query = query_map.get(query_type, "SELECT TOP 10 TABLE_NAME FROM INFORMATION_SCHEMA.TABLES")
            
            # Add date filters if provided
            if date_range.get('start_date') and 'WHERE' in base_query:
                base_query += f" AND Date >= '{date_range['start_date']}'"
            if date_range.get('end_date') and 'WHERE' in base_query:
                base_query += f" AND Date <= '{date_range['end_date']}'"
            
            # Execute query
            results = self.db_service.execute_query(base_query)
            
            return {
                'data': results,
                'total_count': len(results),
                'query_used': base_query  # For debugging
            }
            
        except Exception as e:
            logger.error(f"Database query failed: {str(e)}")
            # Fall back to mock data if real query fails
            return self._get_mock_data(query_type, filters)
    
    def _get_mock_data(self, query_type: str, filters: Dict) -> Dict:
        """Return mock data for development/testing when database is not available"""
        
        if query_type == 'sales':
            return {
                'data': [
                    {
                        'id': 1,
                        'date': '2024-01-15',
                        'customer_name': 'ABC Warehouse',
                        'product': 'Toyota 8FBE15U',
                        'quantity': 2,
                        'unit_price': 25000.00,
                        'total_amount': 50000.00,
                        'salesperson': 'John Smith'
                    },
                    {
                        'id': 2,
                        'date': '2024-01-16',
                        'customer_name': 'XYZ Logistics',
                        'product': 'Hyster H50FT',
                        'quantity': 1,
                        'unit_price': 35000.00,
                        'total_amount': 35000.00,
                        'salesperson': 'Jane Doe'
                    }
                ],
                'total_count': 2
            }
        
        elif query_type == 'inventory':
            return {
                'data': [
                    {
                        'id': 1,
                        'model': 'Toyota 8FBE15U',
                        'serial_number': 'TY123456',
                        'status': 'Available',
                        'location': 'Warehouse A',
                        'cost': 22000.00,
                        'retail_price': 25000.00
                    }
                ],
                'total_count': 1
            }
        
        elif query_type == 'customers':
            return {
                'data': [
                    {
                        'id': 1,
                        'name': 'ABC Warehouse',
                        'contact_person': 'Robert Wilson',
                        'email': 'robert@abcwarehouse.com',
                        'phone': '555-0123',
                        'total_purchases': 125000.00,
                        'last_purchase_date': '2024-01-15'
                    }
                ],
                'total_count': 1
            }
        
        else:
            return {'data': [], 'total_count': 0}
    
    def get_available_tables(self) -> List[str]:
        """Get list of all available tables in the database"""
        try:
            return self.db_service.get_tables()
        except Exception as e:
            logger.error(f"Failed to get tables: {str(e)}")
            return []
    
    def get_table_info(self, table_name: str) -> List[Dict[str, str]]:
        """Get column information for a specific table"""
        try:
            return self.db_service.get_table_columns(table_name)
        except Exception as e:
            logger.error(f"Failed to get table info: {str(e)}")
            return []
    
    def execute_custom_query(self, query: str) -> Dict:
        """Execute a custom SQL query (with safety checks)"""
        try:
            # Basic safety check - only allow SELECT queries
            if not query.strip().upper().startswith('SELECT'):
                raise ValueError("Only SELECT queries are allowed")
            
            results = self.db_service.execute_query(query)
            return {
                'data': results,
                'total_count': len(results),
                'success': True
            }
        except Exception as e:
            logger.error(f"Custom query failed: {str(e)}")
            return {
                'data': [],
                'total_count': 0,
                'success': False,
                'error': str(e)
            }
    
    def get_summary_metric(self, metric_type: str, organization_id: int) -> Any:
        """Get summary metrics for dashboard"""
        
        try:
            if metric_type == 'total_sales':
                # Try to get real sales data from database
                query = """
                    SELECT SUM(TotalAmount) as total 
                    FROM Sales 
                    WHERE Date >= DATEADD(month, DATEDIFF(month, 0, GETDATE()), 0)
                """
                result = self.db_service.execute_query(query)
                if result and result[0].get('total'):
                    return float(result[0]['total'])
            
            elif metric_type == 'inventory_count':
                query = "SELECT COUNT(*) as count FROM Inventory WHERE Status = 'Available'"
                result = self.db_service.execute_query(query)
                if result and result[0].get('count'):
                    return int(result[0]['count'])
            
            elif metric_type == 'active_customers':
                query = """
                    SELECT COUNT(DISTINCT CustomerID) as count 
                    FROM Sales 
                    WHERE Date >= DATEADD(day, -90, GETDATE())
                """
                result = self.db_service.execute_query(query)
                if result and result[0].get('count'):
                    return int(result[0]['count'])
            
        except Exception as e:
            logger.error(f"Failed to get metric {metric_type}: {str(e)}")
        
        # Return mock data if real query fails
        mock_values = {
            'total_sales': 125000,
            'inventory_count': 45,
            'active_customers': 23
        }
        return mock_values.get(metric_type, 0)
    
    def get_recent_activity(self, organization_id: int) -> List[Dict]:
        """Get recent activity for dashboard"""
        try:
            query = """
                SELECT TOP 5 
                    'sale' as type,
                    'Sale to ' + CustomerName + ' - ' + ProductName as description,
                    TotalAmount as amount,
                    Date as date
                FROM Sales
                ORDER BY Date DESC
            """
            results = self.db_service.execute_query(query)
            return results
        except Exception as e:
            logger.error(f"Failed to get recent activity: {str(e)}")
            # Return mock data if query fails
            return [
                {
                    'type': 'sale',
                    'description': 'Sale to ABC Warehouse - Toyota Forklift',
                    'amount': 25000,
                    'date': datetime.now().strftime('%Y-%m-%d')
                }
            ]
    
    def test_connection(self) -> Dict:
        """Test connection to Azure SQL Database"""
        try:
            if self.db_service.test_connection():
                tables = self.db_service.get_tables()
                return {
                    'status': 'connected', 
                    'message': f'Connected to Azure SQL. Found {len(tables)} tables.',
                    'tables': tables[:10]  # Show first 10 tables
                }
            else:
                return {'status': 'error', 'message': 'Failed to connect to Azure SQL'}
        except Exception as e:
            return {'status': 'error', 'message': f'Connection failed: {str(e)}'}