"""
Evolution Service
Platform service implementation for Softbase Evolution.
Wraps the existing AzureSQLService to provide the standard platform interface.
"""

import logging
from typing import List, Dict, Any, Optional
from .base_platform_service import BasePlatformService
from .azure_sql_service import AzureSQLService
from .credential_manager import get_credential_manager

logger = logging.getLogger(__name__)

class EvolutionService(BasePlatformService):
    """
    Platform service implementation for Softbase Evolution.
    Uses Azure SQL Server as the backend database.
    """
    
    def __init__(self, organization):
        """
        Initialize the Evolution service with organization-specific configuration.
        
        Args:
            organization: Organization model instance
        """
        super().__init__(organization)
        
        # Create tenant-specific Azure SQL connection
        self.sql_service = self._create_sql_service()
        
        logger.info(f"EvolutionService initialized for organization: {organization.name}")
    
    def _create_sql_service(self) -> AzureSQLService:
        """
        Create an AzureSQLService instance with tenant-specific credentials.
        
        Returns:
            Configured AzureSQLService instance
        """
        # If organization has custom database credentials, use them
        if self.organization.db_server and self.organization.db_password_encrypted:
            credential_manager = get_credential_manager()
            decrypted_password = credential_manager.decrypt_password(
                self.organization.db_password_encrypted
            )
            
            # Create a custom AzureSQLService with tenant credentials
            service = AzureSQLService()
            service.server = self.organization.db_server
            service.database = self.organization.db_name
            service.username = self.organization.db_username
            service.password = decrypted_password
            
            logger.info(f"Using custom database credentials for {self.organization.name}")
            return service
        else:
            # Fall back to default credentials from environment variables
            logger.info(f"Using default database credentials for {self.organization.name}")
            return AzureSQLService()
    
    # ==================== Dashboard Methods ====================
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get dashboard summary data."""
        # This will be implemented by calling existing dashboard queries
        # For now, return a placeholder
        logger.info("Getting dashboard summary")
        return {
            "status": "success",
            "message": "Dashboard summary (Evolution platform)"
        }
    
    def get_monthly_sales(self, months: int = 12) -> List[Dict[str, Any]]:
        """Get monthly sales data."""
        query = """
        SELECT 
            FORMAT(InvoiceDate, 'MMM') as month,
            SUM(LaborTaxable + LaborNonTax + PartsTaxable + PartsNonTax + MiscTaxable + MiscNonTax) as total_sales
        FROM InvoiceReg
        WHERE InvoiceDate >= DATEADD(month, -@months, GETDATE())
        GROUP BY FORMAT(InvoiceDate, 'MMM'), MONTH(InvoiceDate)
        ORDER BY MONTH(InvoiceDate)
        """
        
        results = self.sql_service.execute_query(query, {'months': months})
        return results
    
    # ==================== Department Methods ====================
    
    def get_service_monthly_revenue(self) -> List[Dict[str, Any]]:
        """Get monthly service department revenue."""
        query = """
        SELECT 
            FORMAT(InvoiceDate, 'MMM') as month,
            SUM(LaborTaxable + LaborNonTax) as revenue
        FROM InvoiceReg
        WHERE SaleCode = 'S'
            AND InvoiceDate >= DATEADD(month, -12, GETDATE())
        GROUP BY FORMAT(InvoiceDate, 'MMM'), MONTH(InvoiceDate)
        ORDER BY MONTH(InvoiceDate)
        """
        
        results = self.sql_service.execute_query(query)
        return results
    
    def get_parts_monthly_revenue(self) -> List[Dict[str, Any]]:
        """Get monthly parts department revenue."""
        query = """
        SELECT 
            FORMAT(InvoiceDate, 'MMM') as month,
            SUM(PartsTaxable + PartsNonTax) as revenue
        FROM InvoiceReg
        WHERE SaleCode = 'P'
            AND InvoiceDate >= DATEADD(month, -12, GETDATE())
        GROUP BY FORMAT(InvoiceDate, 'MMM'), MONTH(InvoiceDate)
        ORDER BY MONTH(InvoiceDate)
        """
        
        results = self.sql_service.execute_query(query)
        return results
    
    def get_rental_monthly_revenue(self) -> List[Dict[str, Any]]:
        """Get monthly rental department revenue."""
        query = """
        SELECT 
            FORMAT(InvoiceDate, 'MMM') as month,
            SUM(LaborTaxable + LaborNonTax + PartsTaxable + PartsNonTax) as revenue
        FROM InvoiceReg
        WHERE SaleCode = 'R'
            AND InvoiceDate >= DATEADD(month, -12, GETDATE())
        GROUP BY FORMAT(InvoiceDate, 'MMM'), MONTH(InvoiceDate)
        ORDER BY MONTH(InvoiceDate)
        """
        
        results = self.sql_service.execute_query(query)
        return results
    
    # ==================== Equipment Methods ====================
    
    def get_equipment_list(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get list of equipment."""
        query = "SELECT * FROM Equipment"
        
        # Add filters if provided
        if filters:
            # TODO: Implement filter logic
            pass
        
        results = self.sql_service.execute_query(query)
        return results
    
    # ==================== Work Order Methods ====================
    
    def get_work_orders(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get list of work orders."""
        query = "SELECT * FROM WO"
        
        # Add filters if provided
        if filters:
            # TODO: Implement filter logic
            pass
        
        results = self.sql_service.execute_query(query)
        return results
    
    # ==================== Customer Methods ====================
    
    def get_customers(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get list of customers."""
        query = "SELECT * FROM Customer"
        
        # Add filters if provided
        if filters:
            # TODO: Implement filter logic
            pass
        
        results = self.sql_service.execute_query(query)
        return results