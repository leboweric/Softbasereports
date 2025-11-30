"""
Base ERP Adapter Interface

All ERP/DMS system adapters must implement this interface to ensure
consistent data extraction across different systems.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import date


class BaseERPAdapter(ABC):
    """
    Abstract base class for ERP/DMS system adapters.
    Each supported ERP system needs an adapter that implements these methods.
    """

    def __init__(self, connection_config: Dict[str, Any]):
        """
        Initialize adapter with connection configuration.

        Args:
            connection_config: Dictionary containing connection details
                - For direct DB: server, database, username, password
                - For API: endpoint, api_key
                - For SFTP: host, path, credentials
        """
        self.config = connection_config
        self.connected = False

    @property
    @abstractmethod
    def erp_type(self) -> str:
        """Return the ERP system type identifier (e.g., 'softbase_evolution')."""
        pass

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connectivity to the ERP system.

        Returns:
            Dict with 'success' boolean and 'message' string
        """
        pass

    @abstractmethod
    def get_department_financials(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Extract revenue, COGS, and gross profit by department.

        Args:
            start_date: Start of reporting period
            end_date: End of reporting period

        Returns:
            List of dictionaries with department financial data:
            [
                {
                    'department': 'new_equipment',
                    'gross_sales': 123456.78,
                    'discounts': 1234.56,
                    'cost_of_goods_sold': 98765.43,
                    'units_sold': 10
                },
                ...
            ]
        """
        pass

    @abstractmethod
    def get_expense_allocations(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Extract expense allocations by department and category.

        Args:
            start_date: Start of reporting period
            end_date: End of reporting period

        Returns:
            List of dictionaries with expense data:
            [
                {
                    'expense_category': 'personnel',
                    'department': 'service',
                    'amount': 45000.00,
                    'allocation_method': 'direct'
                },
                ...
            ]
        """
        pass

    @abstractmethod
    def get_operational_metrics(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Extract operational KPIs and metrics.

        Args:
            start_date: Start of reporting period
            end_date: End of reporting period

        Returns:
            List of dictionaries with metric data:
            [
                {
                    'metric_name': 'technician_count',
                    'metric_category': 'service',
                    'metric_value': 15,
                    'metric_unit': 'count'
                },
                ...
            ]
        """
        pass

    def get_full_report(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Get complete financial report for a period.
        Combines all data extraction methods.

        Args:
            start_date: Start of reporting period
            end_date: End of reporting period

        Returns:
            Complete report dictionary
        """
        return {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'department_financials': self.get_department_financials(start_date, end_date),
            'expense_allocations': self.get_expense_allocations(start_date, end_date),
            'operational_metrics': self.get_operational_metrics(start_date, end_date)
        }

    def close(self):
        """Clean up any open connections."""
        self.connected = False
