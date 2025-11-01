"""
Base Platform Service
Abstract base class defining the interface that all platform services must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BasePlatformService(ABC):
    """
    Abstract base class for platform-specific services.
    All platform implementations (Evolution, Legacy) must implement these methods.
    """
    
    def __init__(self, organization):
        """
        Initialize the platform service with organization-specific configuration.
        
        Args:
            organization: Organization model instance containing connection details
        """
        self.organization = organization
        self.platform_type = organization.platform_type
    
    # ==================== Dashboard Methods ====================
    
    @abstractmethod
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        Get dashboard summary data including KPIs and metrics.
        
        Returns:
            Dictionary containing dashboard summary data
        """
        pass
    
    @abstractmethod
    def get_monthly_sales(self, months: int = 12) -> List[Dict[str, Any]]:
        """
        Get monthly sales data.
        
        Args:
            months: Number of months to retrieve (default: 12)
            
        Returns:
            List of dictionaries with month and sales data
        """
        pass
    
    # ==================== Department Methods ====================
    
    @abstractmethod
    def get_service_monthly_revenue(self) -> List[Dict[str, Any]]:
        """
        Get monthly service department revenue.
        
        Returns:
            List of dictionaries with month and revenue data
        """
        pass
    
    @abstractmethod
    def get_parts_monthly_revenue(self) -> List[Dict[str, Any]]:
        """
        Get monthly parts department revenue.
        
        Returns:
            List of dictionaries with month and revenue data
        """
        pass
    
    @abstractmethod
    def get_rental_monthly_revenue(self) -> List[Dict[str, Any]]:
        """
        Get monthly rental department revenue.
        
        Returns:
            List of dictionaries with month and revenue data
        """
        pass
    
    # ==================== Equipment Methods ====================
    
    @abstractmethod
    def get_equipment_list(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get list of equipment with optional filters.
        
        Args:
            filters: Optional dictionary of filter criteria
            
        Returns:
            List of equipment records
        """
        pass
    
    # ==================== Work Order Methods ====================
    
    @abstractmethod
    def get_work_orders(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get list of work orders with optional filters.
        
        Args:
            filters: Optional dictionary of filter criteria
            
        Returns:
            List of work order records
        """
        pass
    
    # ==================== Customer Methods ====================
    
    @abstractmethod
    def get_customers(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get list of customers with optional filters.
        
        Args:
            filters: Optional dictionary of filter criteria
            
        Returns:
            List of customer records
        """
        pass
    
    # ==================== Helper Methods ====================
    
    def get_platform_info(self) -> Dict[str, str]:
        """
        Get information about the platform.
        
        Returns:
            Dictionary with platform type and version info
        """
        return {
            'platform_type': self.platform_type,
            'organization_id': self.organization.id,
            'organization_name': self.organization.name
        }