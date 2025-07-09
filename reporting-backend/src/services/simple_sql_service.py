"""
Simple SQL service using requests to test Azure SQL connection
"""
import requests
import json
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SimpleSQLService:
    """Simplified service to get basic table information"""
    
    def __init__(self):
        # For now, return mock data since we can't directly query without a driver
        self.mock_tables = {
            'customers': [
                'CustomerMaster',
                'CustomerBranches', 
                'CustomerContacts',
                'CustomerTypes'
            ],
            'inventory': [
                'EquipmentMaster',
                'EquipmentInventory',
                'EquipmentTypes',
                'Manufacturers',
                'Models'
            ],
            'sales': [
                'SalesOrders',
                'SalesOrderDetails',
                'Invoices',
                'InvoiceDetails',
                'Quotes'
            ],
            'service': [
                'WorkOrders',
                'ServiceHistory',
                'ServiceContracts',
                'Technicians'
            ],
            'parts': [
                'PartsMaster',
                'PartsInventory',
                'PartsOrders',
                'PartsPricing'
            ]
        }
    
    def get_mock_schema(self) -> Dict[str, Any]:
        """Return mock schema that represents typical Softbase Evolution structure"""
        all_tables = []
        for category, tables in self.mock_tables.items():
            all_tables.extend(tables)
        
        return {
            'total_tables': len(all_tables),
            'categories': self.mock_tables,
            'status': 'mock',
            'message': 'Using estimated Softbase Evolution schema'
        }
    
    def get_sample_queries(self) -> Dict[str, str]:
        """Return sample SQL queries for common operations"""
        return {
            'recent_sales': """
                SELECT TOP 10 
                    SO.OrderNumber,
                    SO.OrderDate,
                    C.CustomerName,
                    SO.TotalAmount
                FROM SalesOrders SO
                JOIN CustomerMaster C ON SO.CustomerID = C.CustomerID
                ORDER BY SO.OrderDate DESC
            """,
            'equipment_inventory': """
                SELECT 
                    E.EquipmentID,
                    E.SerialNumber,
                    M.ManufacturerName,
                    MD.ModelName,
                    E.Status
                FROM EquipmentMaster E
                JOIN Manufacturers M ON E.ManufacturerID = M.ManufacturerID
                JOIN Models MD ON E.ModelID = MD.ModelID
                WHERE E.Status = 'Available'
            """,
            'service_due': """
                SELECT 
                    WO.WorkOrderNumber,
                    C.CustomerName,
                    E.SerialNumber,
                    WO.ScheduledDate,
                    WO.ServiceType
                FROM WorkOrders WO
                JOIN CustomerMaster C ON WO.CustomerID = C.CustomerID
                JOIN EquipmentMaster E ON WO.EquipmentID = E.EquipmentID
                WHERE WO.Status = 'Scheduled'
                AND WO.ScheduledDate >= GETDATE()
                ORDER BY WO.ScheduledDate
            """
        }