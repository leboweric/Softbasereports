"""
AIOP ETL Package
Provides Extract, Transform, Load jobs for the Data Mart layer
"""

from .base_etl import BaseETL
from .etl_bennett_sales import SalesDailyETL, CashFlowETL, run_bennett_etl
from .etl_customer_activity import CustomerActivityETL, run_customer_activity_etl
from .etl_ceo_dashboard import CEODashboardETL, run_ceo_dashboard_etl
from .etl_department_metrics import DepartmentMetricsETL, run_department_metrics_etl
from .tenant_discovery import TenantInfo, discover_softbase_tenants, run_etl_for_all_tenants
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

# Backward compatibility aliases
BennettSalesETL = SalesDailyETL
BennettCashFlowETL = CashFlowETL

__all__ = [
    'BaseETL',
    'SalesDailyETL',
    'CashFlowETL',
    'BennettSalesETL',  # backward compat alias
    'BennettCashFlowETL',  # backward compat alias
    'run_bennett_etl',
    'CustomerActivityETL',
    'run_customer_activity_etl',
    'CEODashboardETL',
    'run_ceo_dashboard_etl',
    'DepartmentMetricsETL',
    'run_department_metrics_etl',
    'TenantInfo',
    'discover_softbase_tenants',
    'run_etl_for_all_tenants',
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
