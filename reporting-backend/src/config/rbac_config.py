"""
Centralized RBAC configuration
Maps roles to their allowed resources and actions
"""

# Resource definitions - what can be accessed
RESOURCES = {
    'dashboard': 'Main dashboard with company financials',
    'parts_work_orders': 'Parts work orders report',
    'parts_inventory': 'Parts inventory by location',
    'parts_stock_alerts': 'Parts stock alerts report',
    'parts_forecast': 'Parts forecast report',
    'parts_overview': 'Parts department overview',
    'parts_employee_performance': 'Parts employee performance',
    'parts_velocity': 'Parts velocity metrics',
    'parts_inventory_turns': 'Parts inventory turns analysis (5-turn matrix)',
    'service_work_orders': 'Service work orders',
    'service_overview': 'Service department overview',
    'rental_availability': 'Rental availability report',
    'rental_overview': 'Rental department overview',
    'accounting_overview': 'Accounting department overview',
    'accounting_ar': 'Accounts receivable reports',
    'accounting_ap': 'Accounts payable reports',
    'accounting_commissions': 'Sales commission reports',
    'accounting_control': 'Control number reports',
    'accounting_inventory': 'Year-end inventory report',
    'minitrac': 'Minitrac equipment database',
    'knowledge_base': 'Technical troubleshooting knowledge base',
    'currie': 'Currie Financial Model quarterly reporting',
    'financial': 'Financial reports including P&L and Currie',
    'database_explorer': 'Database query and exploration tool',
    'schema_explorer': 'Schema explorer for investigating database structure',
    'user_management': 'User and role management',
    'qbr': 'Quarterly Business Review dashboard and PowerPoint export',
    'my_commissions': 'Sales rep personal commission report (view own data only)',
    'manage_rep_comp': 'Manage sales rep compensation plans (admin only)',
    # VITAL Worklife resources
    'vital_case_data': 'VITAL Worklife case management data and analytics',
    'vital_financial': 'VITAL Worklife financial data from QuickBooks',
    'vital_marketing': 'VITAL Worklife marketing data from HubSpot',
    'vital_data_sources': 'VITAL Worklife data source configuration (admin only)',
    'vital_hubspot': 'VITAL Worklife HubSpot CRM dashboard and analytics',
}

# Action types
ACTIONS = ['view', 'create', 'edit', 'delete', 'export']

# Role-based access control matrix
ROLE_PERMISSIONS = {
    'Super Admin': {
        'resources': list(RESOURCES.keys()),  # All resources
        'actions': ACTIONS,  # All actions
    },
    'Sales Manager': {
        'resources': [
            'dashboard', 'accounting_commissions', 'my_commissions',
            'manage_rep_comp', 'minitrac', 'qbr'
        ],
        'actions': ['view', 'create', 'edit', 'export'],
    },
    'Leadership': {
        'resources': [
            'dashboard',
            'parts_overview', 'parts_employee_performance', 'parts_velocity',
            'service_overview',
            'rental_overview',
            'accounting_overview',
            'financial',
            'currie',
            'minitrac',
            'qbr',
        ],
        'actions': ['view', 'export'],
    },
    'Parts Manager': {
        'resources': [
            'parts_work_orders', 'parts_inventory', 'parts_stock_alerts',
            'parts_forecast', 'parts_overview', 'parts_employee_performance',
            'parts_velocity', 'parts_inventory_turns', 'minitrac'
        ],
        'actions': ['view', 'create', 'edit', 'export'],
    },
    'Parts User': {
        'resources': [
            'parts_work_orders', 'parts_inventory',
            'parts_stock_alerts', 'parts_forecast', 'parts_inventory_turns', 'minitrac'
        ],
        'actions': ['view', 'export'],
    },
    'Service Manager': {
        'resources': [
            'service_work_orders', 'service_overview', 'knowledge_base', 'minitrac', 'qbr'
        ],
        'actions': ['view', 'create', 'edit', 'export'],
    },
    'Service User': {
        'resources': [
            'service_work_orders', 'knowledge_base', 'minitrac'
        ],
        'actions': ['view'],
    },
    'Accounting User': {
        'resources': [
            'accounting_overview', 'accounting_ar', 'accounting_ap',
            'accounting_commissions', 'accounting_control', 'accounting_inventory',
            'financial',
            'currie',
            'minitrac'
        ],
        'actions': ['view', 'export'],
    },
    'Accounting Manager': {
        'resources': [
            'accounting_overview', 'accounting_ar', 'accounting_ap',
            'accounting_commissions', 'accounting_control', 'accounting_inventory',
            'financial',
            'currie',
            'minitrac'
        ],
        'actions': ['view', 'create', 'edit', 'export'],
    },
    'Rental Manager': {
        'resources': [
            'rental_overview', 'rental_availability', 'minitrac'
        ],
        'actions': ['view', 'create', 'edit', 'export'],
    },
    'Parts Staff': {
        'resources': [
            'parts_work_orders', 'parts_inventory', 'minitrac'
        ],
        'actions': ['view'],
    },
    'Service Tech': {
        'resources': [
            'service_work_orders', 'knowledge_base', 'minitrac'
        ],
        'actions': ['view', 'edit'],
    },
    'Sales Rep': {
        'resources': [
            'my_commissions'
        ],
        'actions': ['view'],
    },
    # VITAL Worklife roles
    'VITAL Admin': {
        'resources': [
            'dashboard', 'vital_case_data', 'vital_financial', 'vital_marketing',
            'vital_data_sources', 'vital_hubspot', 'user_management'
        ],
        'actions': ACTIONS,  # All actions
    },
    'VITAL User': {
        'resources': [
            'dashboard', 'vital_case_data', 'vital_financial', 'vital_marketing',
            'vital_hubspot'
        ],
        'actions': ['view', 'export'],
    },
    'Read Only': {
        'resources': [
            'dashboard', 'minitrac'
        ],
        'actions': ['view'],
    },
}

# Navigation menu configuration
NAVIGATION_CONFIG = {
    'dashboard': {
        'label': 'Dashboard',
        'icon': 'LayoutDashboard',
        'path': 'dashboard',
        'required_resource': 'dashboard',
        'order': 1,
    },
    'parts': {
        'label': 'Parts',
        'icon': 'Package',
        'path': 'parts',
        'order': 2,
        'tabs': {
            'overview': {'label': 'Overview', 'resource': 'parts_overview'},
            'work-orders': {'label': 'Work Orders', 'resource': 'parts_work_orders'},
            'inventory-location': {'label': 'Inventory by Location', 'resource': 'parts_inventory'},
            'stock-alerts': {'label': 'Stock Alerts', 'resource': 'parts_stock_alerts'},
            'forecast': {'label': 'Forecast', 'resource': 'parts_forecast'},
            'employee-performance': {'label': 'Parts Contest', 'resource': 'parts_employee_performance'},
            'velocity': {'label': 'Velocity', 'resource': 'parts_velocity'},
            'inventory-turns': {'label': 'Inventory Turns', 'resource': 'parts_inventory_turns'},
        }
    },
    'service': {
        'label': 'Service',
        'icon': 'Wrench',
        'path': 'service',
        'order': 3,
        'tabs': {
            'overview': {'label': 'Overview', 'resource': 'service_overview'},
            'work-orders': {'label': 'Work Orders', 'resource': 'service_work_orders'},
        }
    },
    'rental': {
        'label': 'Rental',
        'icon': 'Truck',
        'path': 'rental',
        'order': 4,
        'tabs': {
            'overview': {'label': 'Overview', 'resource': 'rental_overview'},
            'availability': {'label': 'Availability', 'resource': 'rental_availability'},
        }
    },
    'accounting': {
        'label': 'Accounting',
        'icon': 'DollarSign',
        'path': 'accounting',
        'order': 5,
        'tabs': {
            'overview': {'label': 'Overview', 'resource': 'accounting_overview'},
            'ar': {'label': 'Accounts Receivable', 'resource': 'accounting_ar'},
            'ap': {'label': 'Accounts Payable', 'resource': 'accounting_ap'},
            'commissions': {'label': 'Sales Commissions', 'resource': 'accounting_commissions'},
            'control': {'label': 'Control Numbers', 'resource': 'accounting_control'},
            'inventory': {'label': 'Inventory', 'resource': 'accounting_inventory'},
        }
    },
    'knowledge-base': {
        'label': 'Knowledge Base',
        'icon': 'Book',
        'path': 'knowledge-base',
        'required_resource': 'knowledge_base',
        'order': 6,
    },
    'financial': {
        'label': 'Financial',
        'icon': 'FileSpreadsheet',
        'path': 'financial',
        'required_resource': 'financial',
        'order': 7,
    },
    'minitrac': {
        'label': 'Minitrac',
        'icon': 'Search',
        'path': 'minitrac',
        'required_resource': 'minitrac',
        'order': 8,
    },
    'database-explorer': {
        'label': 'Database Explorer',
        'icon': 'Database',
        'path': 'database-explorer',
        'required_resource': 'database_explorer',
        'order': 9,
    },
    'schema-explorer': {
        'label': 'Schema Explorer',
        'icon': 'FileSearch',
        'path': 'schema-explorer',
        'required_resource': 'schema_explorer',
        'order': 9.5,
    },
    'user-management': {
        'label': 'User Management',
        'icon': 'Users',
        'path': 'user-management',
        'required_resource': 'user_management',
        'order': 99,
    },
    'qbr': {
        'label': 'QBR',
        'icon': 'FileBarChart',
        'path': 'qbr',
        'required_resource': 'qbr',
        'order': 10,
    },
    'my-commissions': {
        'label': 'My Commissions',
        'icon': 'TrendingUp',
        'path': 'my-commissions',
        'required_resource': 'my_commissions',
        'order': 11,
    },
    'rep-comp-admin': {
        'label': 'Rep Comp Admin',
        'icon': 'Settings',
        'path': 'rep-comp-admin',
        'required_resource': 'manage_rep_comp',
        'order': 12,
    },
    # VITAL Worklife navigation
    'vital-case-data': {
        'label': 'Case Data',
        'icon': 'ClipboardList',
        'path': 'vital-case-data',
        'required_resource': 'vital_case_data',
        'order': 20,
    },
    'vital-financial': {
        'label': 'Financial',
        'icon': 'DollarSign',
        'path': 'vital-financial',
        'required_resource': 'vital_financial',
        'order': 21,
    },
    'vital-marketing': {
        'label': 'Marketing',
        'icon': 'TrendingUp',
        'path': 'vital-marketing',
        'required_resource': 'vital_marketing',
        'order': 22,
    },
    'vital-data-sources': {
        'label': 'Data Sources',
        'icon': 'Database',
        'path': 'vital-data-sources',
        'required_resource': 'vital_data_sources',
        'order': 23,
    },
    'vital-hubspot': {
        'label': 'HubSpot CRM',
        'icon': 'Target',
        'path': 'vital-hubspot',
        'required_resource': 'vital_hubspot',
        'order': 24,
    },
}
