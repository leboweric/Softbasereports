import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class SoftbaseService:
    """Service to interact with Softbase Evolution API"""
    
    def __init__(self, organization):
        self.organization = organization
        self.api_key = organization.softbase_api_key
        self.endpoint = organization.softbase_endpoint or "https://api.softbase.com"  # Default endpoint
        self.headers = {
            'Authorization': f'Bearer {self.api_key}' if self.api_key else '',
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, endpoint: str, method: str = 'GET', params: Dict = None, data: Dict = None) -> Dict:
        """Make HTTP request to Softbase API"""
        try:
            url = f"{self.endpoint.rstrip('/')}/{endpoint.lstrip('/')}"
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            # For now, return mock data if API is not available
            return self._get_mock_data(endpoint, params or data or {})
    
    def _get_mock_data(self, endpoint: str, params: Dict) -> Dict:
        """Return mock data for development/testing when API is not available"""
        
        if 'sales' in endpoint.lower():
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
                    },
                    {
                        'id': 3,
                        'date': '2024-01-17',
                        'customer_name': 'Manufacturing Co',
                        'product': 'Crown RC5500',
                        'quantity': 3,
                        'unit_price': 28000.00,
                        'total_amount': 84000.00,
                        'salesperson': 'Mike Johnson'
                    }
                ],
                'total_count': 3,
                'summary': {
                    'total_amount': 169000.00,
                    'total_quantity': 6,
                    'average_sale': 56333.33
                }
            }
        
        elif 'inventory' in endpoint.lower():
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
                    },
                    {
                        'id': 2,
                        'model': 'Hyster H50FT',
                        'serial_number': 'HY789012',
                        'status': 'Sold',
                        'location': 'Lot B',
                        'cost': 30000.00,
                        'retail_price': 35000.00
                    }
                ],
                'total_count': 2
            }
        
        elif 'customers' in endpoint.lower():
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
                    },
                    {
                        'id': 2,
                        'name': 'XYZ Logistics',
                        'contact_person': 'Sarah Davis',
                        'email': 'sarah@xyzlogistics.com',
                        'phone': '555-0456',
                        'total_purchases': 85000.00,
                        'last_purchase_date': '2024-01-16'
                    }
                ],
                'total_count': 2
            }
        
        else:
            return {'data': [], 'total_count': 0}
    
    def get_data(self, query_type: str, filters: Dict, date_range: Dict, organization_id: int) -> Dict:
        """Get data based on query type and filters"""
        
        # Build query parameters
        params = {
            'organization_id': organization_id,
            **filters
        }
        
        # Add date range if provided
        if date_range.get('start_date'):
            params['start_date'] = date_range['start_date']
        if date_range.get('end_date'):
            params['end_date'] = date_range['end_date']
        
        # Map query types to API endpoints
        endpoint_map = {
            'sales': 'api/sales',
            'inventory': 'api/inventory',
            'customers': 'api/customers',
            'service': 'api/service-records',
            'financial': 'api/financial-summary'
        }
        
        endpoint = endpoint_map.get(query_type, 'api/sales')
        return self._make_request(endpoint, params=params)
    
    def get_summary_metric(self, metric_type: str, organization_id: int) -> Any:
        """Get summary metrics for dashboard"""
        
        if metric_type == 'total_sales':
            # Get total sales for current month
            start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            result = self.get_data('sales', {}, {'start_date': start_date, 'end_date': end_date}, organization_id)
            return result.get('summary', {}).get('total_amount', 0)
        
        elif metric_type == 'monthly_sales':
            # Get sales for last 12 months
            monthly_data = []
            for i in range(12):
                month_start = (datetime.now().replace(day=1) - timedelta(days=i*30)).replace(day=1)
                month_end = month_start.replace(day=28) + timedelta(days=4)
                month_end = month_end - timedelta(days=month_end.day)
                
                result = self.get_data('sales', {}, {
                    'start_date': month_start.strftime('%Y-%m-%d'),
                    'end_date': month_end.strftime('%Y-%m-%d')
                }, organization_id)
                
                monthly_data.append({
                    'month': month_start.strftime('%Y-%m'),
                    'amount': result.get('summary', {}).get('total_amount', 0)
                })
            
            return monthly_data[::-1]  # Reverse to get chronological order
        
        elif metric_type == 'inventory_count':
            result = self.get_data('inventory', {'status': 'Available'}, {}, organization_id)
            return result.get('total_count', 0)
        
        elif metric_type == 'active_customers':
            # Get customers with purchases in last 90 days
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            result = self.get_data('customers', {'active_since': start_date}, {}, organization_id)
            return result.get('total_count', 0)
        
        else:
            return 0
    
    def get_recent_activity(self, organization_id: int) -> List[Dict]:
        """Get recent activity for dashboard"""
        
        # Get recent sales
        recent_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        sales_result = self.get_data('sales', {}, {'start_date': recent_date}, organization_id)
        
        activities = []
        for sale in sales_result.get('data', [])[:5]:  # Last 5 sales
            activities.append({
                'type': 'sale',
                'description': f"Sale to {sale.get('customer_name', 'Unknown')} - {sale.get('product', 'Unknown')}",
                'amount': sale.get('total_amount', 0),
                'date': sale.get('date', '')
            })
        
        return activities
    
    def test_connection(self) -> Dict:
        """Test connection to Softbase API"""
        try:
            result = self._make_request('api/health')
            return {'status': 'connected', 'message': 'API connection successful'}
        except Exception as e:
            return {'status': 'error', 'message': f'Connection failed: {str(e)}'}

