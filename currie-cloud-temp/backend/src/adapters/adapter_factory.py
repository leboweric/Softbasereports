"""
ERP Adapter Factory

Creates the appropriate adapter instance based on ERP system type.
"""
from typing import Dict, Any

from .base_adapter import BaseERPAdapter
from .softbase_evolution import SoftbaseEvolutionAdapter


class AdapterFactory:
    """Factory for creating ERP adapter instances."""

    # Registry of supported ERP systems
    _adapters = {
        'softbase_evolution': SoftbaseEvolutionAdapter,
        # Future adapters:
        # 'dis_cai': DISCaiAdapter,
        # 'e_emphasys': EEmphasysAdapter,
    }

    @classmethod
    def get_adapter(cls, erp_type: str, connection_config: Dict[str, Any]) -> BaseERPAdapter:
        """
        Get an adapter instance for the specified ERP type.

        Args:
            erp_type: The ERP system identifier
            connection_config: Connection configuration for the adapter

        Returns:
            Configured adapter instance

        Raises:
            ValueError: If ERP type is not supported
        """
        adapter_class = cls._adapters.get(erp_type)
        if not adapter_class:
            raise ValueError(f"Unsupported ERP type: {erp_type}. Supported types: {list(cls._adapters.keys())}")

        return adapter_class(connection_config)

    @classmethod
    def get_supported_types(cls) -> list:
        """Get list of supported ERP system types."""
        return list(cls._adapters.keys())

    @classmethod
    def register_adapter(cls, erp_type: str, adapter_class: type):
        """Register a new adapter type."""
        cls._adapters[erp_type] = adapter_class
