import openai
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from src.services.openai_service import OpenAIQueryService

class ReportCreator:
    """Service to create custom reports from natural language descriptions"""
    
    def __init__(self):
        self.openai_service = OpenAIQueryService()
        
    def create_report_from_description(self, description: str, organization_id: int) -> Dict[str, Any]:
        """
        Create a custom report based on natural language description
        
        Args:
            description: Natural language description of the desired report
            organization_id: ID of the organization requesting the report
            
        Returns:
            Dictionary containing report configuration and generated data
        """
        try:
            # Parse the description to extract report requirements
            report_config = self._parse_report_description(description)
            
            # Generate SQL query based on the requirements
            sql_query = self._generate_sql_query(report_config)
            
            # Generate mock data for now (will be replaced with real Softbase data)
            report_data = self._generate_report_data(report_config, organization_id)
            
            # Create report metadata
            report_metadata = {
                'title': report_config.get('title', 'Custom Report'),
                'description': description,
                'created_at': datetime.utcnow().isoformat(),
                'organization_id': organization_id,
                'columns': report_config.get('columns', []),
                'filters': report_config.get('filters', {}),
                'sql_query': sql_query,
                'data_count': len(report_data)
            }
            
            return {
                'success': True,
                'metadata': report_metadata,
                'data': report_data,
                'config': report_config
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to create report from description'
            }
    
    def _parse_report_description(self, description: str) -> Dict[str, Any]:
        """Parse natural language description to extract report requirements"""
        
        # Use OpenAI to parse the description
        prompt = f"""
        Parse this report request and extract the key components:
        "{description}"
        
        Return a JSON object with the following structure:
        {{
            "title": "Generated report title",
            "data_source": "primary table/entity (e.g., work_orders, invoices, customers)",
            "columns": ["list", "of", "columns", "to", "include"],
            "filters": {{
                "status": "filter conditions",
                "date_range": "time period if specified",
                "other_conditions": "additional filters"
            }},
            "aggregations": ["sum", "count", "avg", "etc"],
            "grouping": ["group by fields"],
            "sorting": ["sort by fields"]
        }}
        
        Focus on forklift dealership business entities like:
        - Work Orders (service, maintenance, repairs)
        - Invoices and Billing
        - Parts and Inventory
        - Customers and Accounts
        - Equipment and Fleet
        - Service Technicians
        - Sales and Revenue
        """
        
        try:
            # Make OpenAI request directly using the client
            response = self.openai_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a report configuration assistant. Generate JSON configurations for business reports."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            # Get the response content
            response_text = response.choices[0].message.content
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                config = json.loads(json_match.group())
                return config
            else:
                # Fallback parsing
                return self._fallback_parse(description)
                
        except Exception as e:
            print(f"OpenAI parsing failed: {e}")
            return self._fallback_parse(description)
    
    def _fallback_parse(self, description: str) -> Dict[str, Any]:
        """Fallback parsing when OpenAI is not available"""
        description_lower = description.lower()
        
        # Determine data source
        data_source = "work_orders"
        if "invoice" in description_lower:
            data_source = "invoices"
        elif "part" in description_lower:
            data_source = "parts"
        elif "customer" in description_lower:
            data_source = "customers"
        elif "equipment" in description_lower or "forklift" in description_lower:
            data_source = "equipment"
        
        # Extract filters
        filters = {}
        if "complete" in description_lower and "not" in description_lower and "invoice" in description_lower:
            filters["status"] = "complete"
            filters["invoiced"] = False
        elif "wip" in description_lower or "work in progress" in description_lower:
            filters["status"] = "in_progress"
        
        # Generate title
        title = f"Custom {data_source.replace('_', ' ').title()} Report"
        
        return {
            "title": title,
            "data_source": data_source,
            "columns": self._get_default_columns(data_source),
            "filters": filters,
            "aggregations": ["sum", "count"],
            "grouping": [],
            "sorting": ["created_date"]
        }
    
    def _get_default_columns(self, data_source: str) -> List[str]:
        """Get default columns for different data sources"""
        column_mapping = {
            "work_orders": ["wo_number", "customer", "equipment", "description", "status", "created_date", "completed_date", "total_amount", "invoiced"],
            "invoices": ["invoice_number", "customer", "amount", "date", "status", "work_order"],
            "parts": ["part_number", "description", "quantity", "cost", "supplier", "location"],
            "customers": ["customer_name", "contact", "phone", "email", "total_orders", "last_order_date"],
            "equipment": ["serial_number", "model", "customer", "rental_status", "last_service"]
        }
        return column_mapping.get(data_source, ["id", "name", "status", "created_date"])
    
    def _generate_sql_query(self, config: Dict[str, Any]) -> str:
        """Generate SQL query based on report configuration"""
        data_source = config.get('data_source', 'work_orders')
        columns = config.get('columns', ['*'])
        filters = config.get('filters', {})
        
        # Build SELECT clause
        select_clause = f"SELECT {', '.join(columns)}"
        
        # Build FROM clause
        from_clause = f"FROM {data_source}"
        
        # Build WHERE clause
        where_conditions = []
        for key, value in filters.items():
            if isinstance(value, bool):
                where_conditions.append(f"{key} = {str(value).lower()}")
            elif isinstance(value, str):
                where_conditions.append(f"{key} = '{value}'")
        
        where_clause = ""
        if where_conditions:
            where_clause = f"WHERE {' AND '.join(where_conditions)}"
        
        # Build ORDER BY clause
        sorting = config.get('sorting', [])
        order_clause = ""
        if sorting:
            order_clause = f"ORDER BY {', '.join(sorting)}"
        
        return f"{select_clause} {from_clause} {where_clause} {order_clause}".strip()
    
    def _generate_report_data(self, config: Dict[str, Any], organization_id: int) -> List[Dict[str, Any]]:
        """Generate mock data based on report configuration"""
        data_source = config.get('data_source', 'work_orders')
        filters = config.get('filters', {})
        
        if data_source == 'work_orders':
            return self._generate_work_order_data(filters)
        elif data_source == 'invoices':
            return self._generate_invoice_data(filters)
        elif data_source == 'parts':
            return self._generate_parts_data(filters)
        elif data_source == 'customers':
            return self._generate_customer_data(filters)
        elif data_source == 'equipment':
            return self._generate_equipment_data(filters)
        else:
            return []
    
    def _generate_work_order_data(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate mock work order data"""
        base_data = [
            {
                "wo_number": "WO-2024-001",
                "customer": "ABC Manufacturing",
                "equipment": "Linde H25T #001",
                "description": "Annual maintenance service",
                "status": "complete",
                "created_date": "2024-01-15",
                "completed_date": "2024-01-16",
                "total_amount": 450.00,
                "invoiced": False
            },
            {
                "wo_number": "WO-2024-002",
                "customer": "XYZ Logistics",
                "equipment": "Toyota 8FBE20 #002",
                "description": "Hydraulic system repair",
                "status": "complete",
                "created_date": "2024-01-18",
                "completed_date": "2024-01-20",
                "total_amount": 1250.00,
                "invoiced": False
            },
            {
                "wo_number": "WO-2024-003",
                "customer": "Industrial Supply Co",
                "equipment": "Crown FC5200 #003",
                "description": "Battery replacement",
                "status": "in_progress",
                "created_date": "2024-01-22",
                "completed_date": None,
                "total_amount": 800.00,
                "invoiced": False
            },
            {
                "wo_number": "WO-2024-004",
                "customer": "Warehouse Solutions Inc",
                "equipment": "Yale GLP050 #004",
                "description": "Brake system service",
                "status": "complete",
                "created_date": "2024-01-25",
                "completed_date": "2024-01-26",
                "total_amount": 320.00,
                "invoiced": True
            },
            {
                "wo_number": "WO-2024-005",
                "customer": "ABC Manufacturing",
                "equipment": "Hyster H2.5FT #005",
                "description": "Engine diagnostics and tune-up",
                "status": "in_progress",
                "created_date": "2024-01-28",
                "completed_date": None,
                "total_amount": 650.00,
                "invoiced": False
            }
        ]
        
        # Apply filters
        filtered_data = []
        for item in base_data:
            include = True
            
            if 'status' in filters and item['status'] != filters['status']:
                include = False
            
            if 'invoiced' in filters and item['invoiced'] != filters['invoiced']:
                include = False
            
            if include:
                filtered_data.append(item)
        
        return filtered_data
    
    def _generate_invoice_data(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate mock invoice data"""
        return [
            {
                "invoice_number": "INV-2024-001",
                "customer": "Warehouse Solutions Inc",
                "amount": 320.00,
                "date": "2024-01-27",
                "status": "paid",
                "work_order": "WO-2024-004"
            },
            {
                "invoice_number": "INV-2024-002",
                "customer": "Metro Distribution",
                "amount": 1850.00,
                "date": "2024-01-29",
                "status": "pending",
                "work_order": "WO-2024-006"
            }
        ]
    
    def _generate_parts_data(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate mock parts data"""
        base_data = [
            {
                "part_number": "LIN-HYD-001",
                "description": "Hydraulic pump assembly",
                "quantity": 5,
                "cost": 450.00,
                "supplier": "Linde Parts",
                "location": "Warehouse A",
                "status": "in_stock"
            },
            {
                "part_number": "TOY-BAT-002",
                "description": "48V Battery pack",
                "quantity": 0,
                "cost": 800.00,
                "supplier": "Toyota Parts",
                "location": "Warehouse B",
                "status": "out_of_stock"
            },
            {
                "part_number": "CRN-BRK-003",
                "description": "Brake pad set",
                "quantity": 12,
                "cost": 85.00,
                "supplier": "Crown Parts",
                "location": "Warehouse A",
                "status": "in_stock"
            }
        ]
        
        # Apply WIP filter if specified
        if filters.get('status') == 'in_progress':
            # For parts, WIP might mean parts on order or being processed
            for item in base_data:
                if item['quantity'] == 0:
                    item['status'] = 'on_order'
                    item['wip_value'] = item['cost'] * 3  # Estimated order quantity
        
        return base_data
    
    def _generate_customer_data(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate mock customer data"""
        return [
            {
                "customer_name": "ABC Manufacturing",
                "contact": "John Smith",
                "phone": "(555) 123-4567",
                "email": "john@abcmfg.com",
                "total_orders": 15,
                "last_order_date": "2024-01-28"
            },
            {
                "customer_name": "XYZ Logistics",
                "contact": "Sarah Johnson",
                "phone": "(555) 987-6543",
                "email": "sarah@xyzlogistics.com",
                "total_orders": 8,
                "last_order_date": "2024-01-20"
            }
        ]
    
    def _generate_equipment_data(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate mock equipment data"""
        return [
            {
                "serial_number": "LIN001",
                "model": "Linde H25T",
                "customer": "ABC Manufacturing",
                "rental_status": "active",
                "last_service": "2024-01-16"
            },
            {
                "serial_number": "TOY002",
                "model": "Toyota 8FBE20",
                "customer": "XYZ Logistics",
                "rental_status": "active",
                "last_service": "2024-01-20"
            }
        ]
    
    def save_custom_report(self, report_config: Dict[str, Any], organization_id: int) -> Dict[str, Any]:
        """Save a custom report configuration for future use"""
        # In a real implementation, this would save to the database
        # For now, return success with the configuration
        
        report_template = {
            'id': f"custom_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            'name': report_config.get('title', 'Custom Report'),
            'description': report_config.get('description', ''),
            'organization_id': organization_id,
            'config': report_config,
            'created_at': datetime.utcnow().isoformat(),
            'is_custom': True
        }
        
        return {
            'success': True,
            'template': report_template,
            'message': 'Custom report saved successfully'
        }

