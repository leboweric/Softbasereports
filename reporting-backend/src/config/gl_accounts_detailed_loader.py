# GL Accounts Detailed Loader - Tenant-aware routing for P&L Excel export configs
#
# This module provides get_detailed_gl_config(schema) which returns the appropriate
# DEPARTMENT_CONFIG, OVERHEAD_EXPENSE_ACCOUNTS, and OTHER_INCOME_EXPENSE_ACCOUNTS
# for the given tenant schema. This replaces the direct import from
# gl_accounts_detailed.py (Bennett-only) in pl_report_detailed.py.
#
# Pattern mirrors gl_accounts_loader.py's TENANT_GL_CONFIGS approach.

import logging

from src.config.gl_accounts_detailed import (
    DEPARTMENT_CONFIG as DEPARTMENT_CONFIG_BENNETT,
    OVERHEAD_EXPENSE_ACCOUNTS as OVERHEAD_EXPENSE_ACCOUNTS_BENNETT,
    OTHER_INCOME_EXPENSE_ACCOUNTS as OTHER_INCOME_EXPENSE_ACCOUNTS_BENNETT,
)
from src.config.gl_accounts_detailed_ips import (
    DEPARTMENT_CONFIG_IPS,
    OVERHEAD_EXPENSE_ACCOUNTS_IPS,
    OTHER_INCOME_EXPENSE_ACCOUNTS_IPS,
)

logger = logging.getLogger(__name__)

# Mapping of schema to detailed GL configuration
TENANT_DETAILED_CONFIGS = {
    'ben002': {
        'department_config': DEPARTMENT_CONFIG_BENNETT,
        'overhead_expense_accounts': OVERHEAD_EXPENSE_ACCOUNTS_BENNETT,
        'other_income_expense_accounts': OTHER_INCOME_EXPENSE_ACCOUNTS_BENNETT,
        # Department order for Excel tabs (Bennett)
        'dept_order': [
            'new_equipment', 'used_equipment', 'parts', 'service',
            'rental', 'transportation', 'in_house'
        ],
        # Department code for the "In House / Administrative" tab
        'inhouse_dept_key': 'in_house',
        'inhouse_dept_code': 90,
        'inhouse_tab_name': 'P&L In House',
    },
    'ind004': {
        'department_config': DEPARTMENT_CONFIG_IPS,
        'overhead_expense_accounts': OVERHEAD_EXPENSE_ACCOUNTS_IPS,
        'other_income_expense_accounts': OTHER_INCOME_EXPENSE_ACCOUNTS_IPS,
        # Department order for Excel tabs (IPS)
        # IPS has different departments: allied, demo, ami, lease, miscellaneous
        'dept_order': [
            'new_equipment', 'allied', 'used_equipment', 'service',
            'parts', 'rental', 'lease', 'demo', 'ami', 'miscellaneous'
        ],
        # IPS uses 'miscellaneous' as its administrative/catch-all department
        'inhouse_dept_key': 'miscellaneous',
        'inhouse_dept_code': 80,
        'inhouse_tab_name': 'P&L Misc',
    },
}


def get_detailed_gl_config(schema: str) -> dict:
    """
    Get the complete detailed GL configuration for a specific tenant.

    Args:
        schema: The tenant's database schema (e.g., 'ben002', 'ind004')

    Returns:
        Dictionary with keys:
            - department_config: DEPARTMENT_CONFIG dict
            - overhead_expense_accounts: OVERHEAD_EXPENSE_ACCOUNTS dict
            - other_income_expense_accounts: OTHER_INCOME_EXPENSE_ACCOUNTS dict
            - dept_order: List of department keys in Excel tab order
            - inhouse_dept_key: Key for the admin/in-house department
            - inhouse_dept_code: Department code for admin tab
            - inhouse_tab_name: Tab name for admin worksheet
    """
    config = TENANT_DETAILED_CONFIGS.get(schema)
    if config is None:
        logger.warning(
            f"No detailed GL config for schema '{schema}' - falling back to ben002. "
            f"Add this tenant to TENANT_DETAILED_CONFIGS!"
        )
        config = TENANT_DETAILED_CONFIGS['ben002']
    return config


def get_department_config(schema: str) -> dict:
    """
    Get the DEPARTMENT_CONFIG for a specific tenant.

    Args:
        schema: The tenant's database schema

    Returns:
        Dictionary of department configurations with (account_no, description) tuples
    """
    return get_detailed_gl_config(schema)['department_config']


def get_overhead_expense_config(schema: str) -> dict:
    """
    Get the OVERHEAD_EXPENSE_ACCOUNTS for a specific tenant.

    Args:
        schema: The tenant's database schema

    Returns:
        Dictionary of overhead expense categories with (account_no, description) tuples
    """
    return get_detailed_gl_config(schema)['overhead_expense_accounts']


def get_other_income_expense_config(schema: str) -> dict:
    """
    Get the OTHER_INCOME_EXPENSE_ACCOUNTS for a specific tenant.

    Args:
        schema: The tenant's database schema

    Returns:
        Dictionary of other income/expense categories with (account_no, description) tuples
    """
    return get_detailed_gl_config(schema)['other_income_expense_accounts']


def get_dept_order(schema: str) -> list:
    """
    Get the department order for Excel tab generation.

    Args:
        schema: The tenant's database schema

    Returns:
        List of department keys in the order they should appear as Excel tabs
    """
    return get_detailed_gl_config(schema)['dept_order']


def get_inhouse_config(schema: str) -> dict:
    """
    Get the in-house/administrative department configuration.

    Args:
        schema: The tenant's database schema

    Returns:
        Dictionary with inhouse_dept_key, inhouse_dept_code, inhouse_tab_name
    """
    config = get_detailed_gl_config(schema)
    return {
        'dept_key': config['inhouse_dept_key'],
        'dept_code': config['inhouse_dept_code'],
        'tab_name': config['inhouse_tab_name'],
    }
