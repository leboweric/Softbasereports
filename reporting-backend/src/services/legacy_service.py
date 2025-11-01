"""
Legacy Service
Platform service implementation for Softbase Legacy.
This is a stub that will be implemented in Phase 2.
"""

import logging
from typing import List, Dict, Any, Optional
from .base_platform_service import BasePlatformService

logger = logging.getLogger(__name__)

class LegacyService(BasePlatformService):
    """
    Platform service implementation for Softbase Legacy.
    Currently a stub - will be implemented in Phase 2.
    """
    
    def __init__(self, organization):
        super().__init__(organization)
        logger.warning(f"LegacyService initialized for {organization.name} - NOT YET IMPLEMENTED")
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        raise NotImplementedError("Legacy platform support coming in Phase 2")
    
    def get_monthly_sales(self, months: int = 12) -> List[Dict[str, Any]]:
        raise NotImplementedError("Legacy platform support coming in Phase 2")
    
    def get_service_monthly_revenue(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("Legacy platform support coming in Phase 2")
    
    def get_parts_monthly_revenue(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("Legacy platform support coming in Phase 2")
    
    def get_rental_monthly_revenue(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("Legacy platform support coming in Phase 2")
    
    def get_equipment_list(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        raise NotImplementedError("Legacy platform support coming in Phase 2")
    
    def get_work_orders(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        raise NotImplementedError("Legacy platform support coming in Phase 2")
    
    def get_customers(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        raise NotImplementedError("Legacy platform support coming in Phase 2")