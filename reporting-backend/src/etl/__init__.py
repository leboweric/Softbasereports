"""
AIOP ETL Package
Provides Extract, Transform, Load jobs for the Data Mart layer
"""

from .base_etl import BaseETL
from .etl_bennett_sales import BennettSalesETL, BennettCashFlowETL, run_bennett_etl
from .etl_customer_activity import CustomerActivityETL, run_customer_activity_etl
from .etl_vital import (
    VitalHubSpotContactsETL, 
    VitalHubSpotDealsETL,
    VitalZoomETL,
    VitalCaseDataETL,
    VitalQuickBooksETL,
    VitalAppAnalyticsETL,
    run_vital_etl
)
from .scheduler import run_all_etl, setup_scheduler, init_etl_scheduler, register_etl_routes

__all__ = [
    'BaseETL',
    'BennettSalesETL',
    'BennettCashFlowETL',
    'run_bennett_etl',
    'CustomerActivityETL',
    'run_customer_activity_etl',
    'VitalHubSpotContactsETL',
    'VitalHubSpotDealsETL',
    'VitalZoomETL',
    'VitalCaseDataETL',
    'VitalQuickBooksETL',
    'VitalAppAnalyticsETL',
    'run_vital_etl',
    'run_all_etl',
    'setup_scheduler',
    'init_etl_scheduler',
    'register_etl_routes'
]
