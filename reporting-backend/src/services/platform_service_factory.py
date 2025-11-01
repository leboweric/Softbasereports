"""
Platform Service Factory
Factory class for creating the appropriate platform service based on organization configuration.
"""

import logging
from typing import List
from .base_platform_service import BasePlatformService
from .evolution_service import EvolutionService
from .legacy_service import LegacyService

logger = logging.getLogger(__name__)

class PlatformServiceFactory:
    """
    Factory for creating platform-specific service instances.
    Determines which service to use based on the organization's platform_type.
    """
    
    @staticmethod
    def get_service(organization) -> BasePlatformService:
        """
        Get the appropriate platform service for the given organization.
        
        Args:
            organization: Organization model instance
            
        Returns:
            Platform service instance (EvolutionService or LegacyService)
            
        Raises:
            ValueError: If platform type is unsupported or not configured
        """
        platform_type = organization.platform_type
        
        # Default to 'evolution' if not set (for backward compatibility)
        if not platform_type:
            logger.info(f"No platform_type set for {organization.name}, defaulting to 'evolution'")
            platform_type = 'evolution'
        
        if platform_type == 'evolution':
            logger.info(f"Creating EvolutionService for {organization.name}")
            return EvolutionService(organization)
        elif platform_type == 'legacy':
            logger.info(f"Creating LegacyService for {organization.name}")
            return LegacyService(organization)
        else:
            error_msg = f"Unsupported platform type: {platform_type} for organization {organization.name}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    @staticmethod
    def get_supported_platforms() -> List[str]:
        """
        Get list of supported platform types.
        
        Returns:
            List of supported platform type strings
        """
        return ['evolution', 'legacy']