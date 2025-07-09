"""
Mock service that simulates Softbase Evolution data structure
Use this while Azure SQL connection issues are resolved
"""
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

class SoftbaseMockService:
    """Provides realistic mock data matching Softbase Evolution structure"""
    
    def get_tables(self) -> List[str]:
        """Return list of tables that would be in Softbase Evolution"""
        return [
            # Customer tables
            'CustomerMaster', 'CustomerBranches', 'CustomerContacts', 'CustomerTypes',
            'CustomerCreditInfo', 'CustomerNotes',
            
            # Equipment/Inventory tables
            'EquipmentMaster', 'EquipmentInventory', 'EquipmentTypes', 
            'Manufacturers', 'Models', 'ModelSpecs', 'SerialNumbers',
            
            # Sales tables
            'SalesOrders', 'SalesOrderDetails', 'Quotes', 'QuoteDetails',
            'Invoices', 'InvoiceDetails', 'Contracts', 'ContractDetails',
            
            # Service tables
            'WorkOrders', 'WorkOrderDetails', 'ServiceHistory', 'ServiceContracts',
            'Technicians', 'TechnicianSchedule', 'ServiceCodes',
            
            # Parts tables
            'PartsMaster', 'PartsInventory', 'PartsOrders', 'PartsPricing',
            'PartsSuppliers', 'PartsCategories',
            
            # Financial tables
            'GeneralLedger', 'AccountsReceivable', 'AccountsPayable',
            'PaymentHistory', 'TaxRates', 'CommissionRates',
            
            # Other tables
            'Employees', 'Departments', 'Locations', 'SystemSettings'
        ]
    
    def get_customers_sample(self) -> List[Dict[str, Any]]:
        """Get sample customer data"""
        customers = []
        customer_names = [
            "ABC Warehouse Solutions", "XYZ Distribution Center", 
            "Global Logistics Inc", "Metro Storage Systems",
            "Industrial Equipment Co", "Prime Materials Handling"
        ]
        
        for i, name in enumerate(customer_names):
            customers.append({
                'CustomerID': f'CUST{1000 + i}',
                'CompanyName': name,
                'ContactName': f'Contact {i+1}',
                'Phone': f'555-{random.randint(1000, 9999)}',
                'Email': f'contact@{name.lower().replace(" ", "")}.com',
                'CreditLimit': random.randint(10000, 100000),
                'Balance': random.randint(0, 50000),
                'Status': 'Active',
                'CreatedDate': (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat()
            })
        
        return customers
    
    def get_equipment_sample(self) -> List[Dict[str, Any]]:
        """Get sample equipment/forklift data"""
        equipment = []
        makes = ['Toyota', 'Hyster', 'Yale', 'Crown', 'Raymond']
        types = ['Electric Rider', 'IC Cushion', 'IC Pneumatic', 'Reach Truck', 'Order Picker']
        
        for i in range(20):
            make = random.choice(makes)
            equipment.append({
                'EquipmentID': f'EQ{2000 + i}',
                'SerialNumber': f'SN{random.randint(100000, 999999)}',
                'Make': make,
                'Model': f'{make[:3].upper()}-{random.randint(20, 80)}',
                'Type': random.choice(types),
                'Capacity': f'{random.choice([3000, 4000, 5000, 6000, 8000])} lbs',
                'MastHeight': f'{random.randint(180, 240)}"',
                'YearManufactured': random.randint(2018, 2024),
                'Status': random.choice(['Available', 'Sold', 'On Rent', 'In Service']),
                'Location': random.choice(['Main Warehouse', 'Branch 1', 'Branch 2']),
                'PurchasePrice': random.randint(15000, 85000),
                'CurrentValue': random.randint(10000, 70000)
            })
        
        return equipment
    
    def get_service_history_sample(self) -> List[Dict[str, Any]]:
        """Get sample service history data"""
        services = []
        service_types = ['PM Service', 'Repair', 'Safety Inspection', 'Major Overhaul', 'Warranty Service']
        
        for i in range(50):
            service_date = datetime.now() - timedelta(days=random.randint(1, 365))
            services.append({
                'ServiceID': f'SVC{3000 + i}',
                'WorkOrderNumber': f'WO{random.randint(10000, 99999)}',
                'EquipmentID': f'EQ{random.randint(2000, 2019)}',
                'CustomerID': f'CUST{random.randint(1000, 1005)}',
                'ServiceType': random.choice(service_types),
                'ServiceDate': service_date.isoformat(),
                'TechnicianID': f'TECH{random.randint(1, 5)}',
                'LaborHours': round(random.uniform(1, 8), 1),
                'PartsTotal': round(random.uniform(0, 500), 2),
                'LaborTotal': round(random.uniform(100, 800), 2),
                'TotalCost': round(random.uniform(100, 1300), 2),
                'Status': 'Completed',
                'Notes': f'Service completed successfully'
            })
        
        return services
    
    def get_sales_data_sample(self) -> List[Dict[str, Any]]:
        """Get sample sales data"""
        sales = []
        
        for i in range(30):
            sale_date = datetime.now() - timedelta(days=random.randint(1, 180))
            sales.append({
                'SalesOrderID': f'SO{4000 + i}',
                'CustomerID': f'CUST{random.randint(1000, 1005)}',
                'OrderDate': sale_date.isoformat(),
                'EquipmentID': f'EQ{random.randint(2000, 2019)}',
                'SaleType': random.choice(['New', 'Used', 'Rental', 'Lease']),
                'SalePrice': round(random.uniform(15000, 75000), 2),
                'Discount': round(random.uniform(0, 5000), 2),
                'Tax': round(random.uniform(1000, 5000), 2),
                'TotalAmount': round(random.uniform(16000, 80000), 2),
                'PaymentTerms': random.choice(['Net 30', 'Net 60', 'COD', '50% Down']),
                'Status': random.choice(['Pending', 'Completed', 'Delivered']),
                'SalespersonID': f'EMP{random.randint(1, 3)}'
            })
        
        return sales
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a mock query and return appropriate sample data"""
        query_lower = query.lower()
        
        if 'customer' in query_lower:
            return self.get_customers_sample()
        elif 'equipment' in query_lower or 'forklift' in query_lower:
            return self.get_equipment_sample()
        elif 'service' in query_lower or 'work' in query_lower:
            return self.get_service_history_sample()
        elif 'sales' in query_lower or 'order' in query_lower:
            return self.get_sales_data_sample()
        elif 'select @@version' in query_lower:
            return [{'version': 'Microsoft SQL Server 2019 (RTM) - 15.0.2000.5 (Simulated)'}]
        else:
            # Return empty result for unrecognized queries
            return []
    
    def test_connection(self) -> bool:
        """Always returns True for mock service"""
        return True