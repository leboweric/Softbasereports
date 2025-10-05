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
    'service_work_orders': 'Service work orders',
    'service_overview': 'Service department overview',
    'rental_availability': 'Rental availability report',
    'rental_overview': 'Rental department overview',
    'accounting_overview': 'Accounting department overview',
    'minitrac': 'Minitrac equipment database',
    'database_explorer': 'Database exploration tools',
    'ai_query': 'AI-powered query generation',
    'user_management': 'User and role management',
}

# Action types
ACTIONS = ['view', 'create', 'edit', 'delete', 'export']

# Role-based access control matrix
ROLE_PERMISSIONS = {
    'Super Admin': {
        'resources': list(RESOURCES.keys()),  # All resources
        'actions': ACTIONS,  # All actions
    },
    'Leadership': {
        'resources': [
            'dashboard',
            'parts_overview', 'parts_employee_performance', 'parts_velocity',
            'service_overview',
            'rental_overview',
            'accounting_overview',
        ],
        'actions': ['view', 'export'],
    },
    'Parts Manager': {
        'resources': [
            'parts_work_orders', 'parts_inventory', 'parts_stock_alerts',
            'parts_forecast', 'parts_overview', 'parts_employee_performance',
            'parts_velocity', 'minitrac'
        ],
        'actions': ['view', 'create', 'edit', 'export'],
    },
    'Parts User': {
        'resources': [
            'parts_work_orders', 'parts_inventory',
            'parts_stock_alerts', 'parts_forecast', 'minitrac'
        ],
        'actions': ['view', 'export'],
    },
    'Service Manager': {
        'resources': [
            'service_work_orders', 'service_overview', 'minitrac'
        ],
        'actions': ['view', 'create', 'edit', 'export'],
    },
    'Service User': {
        'resources': [
            'service_work_orders', 'minitrac'
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
    },
    'parts': {
        'label': 'Parts',
        'icon': 'Package',
        'path': 'parts',
        'tabs': {
            'overview': {'label': 'Overview', 'resource': 'parts_overview'},
            'work-orders': {'label': 'Work Orders', 'resource': 'parts_work_orders'},
            'inventory-location': {'label': 'Inventory by Location', 'resource': 'parts_inventory'},
            'stock-alerts': {'label': 'Stock Alerts', 'resource': 'parts_stock_alerts'},
            'forecast': {'label': 'Forecast', 'resource': 'parts_forecast'},
            'employee-performance': {'label': 'Employee Performance', 'resource': 'parts_employee_performance'},
            'velocity': {'label': 'Velocity', 'resource': 'parts_velocity'},
        }
    },
    'service': {
        'label': 'Service',
        'icon': 'Wrench',
        'path': 'service',
        'tabs': {
            'overview': {'label': 'Overview', 'resource': 'service_overview'},
            'work-orders': {'label': 'Work Orders', 'resource': 'service_work_orders'},
        }
    },
    'rental': {
        'label': 'Rental',
        'icon': 'Truck',
        'path': 'rental',
        'tabs': {
            'overview': {'label': 'Overview', 'resource': 'rental_overview'},
            'availability': {'label': 'Availability', 'resource': 'rental_availability'},
        }
    },
    'accounting': {
        'label': 'Accounting',
        'icon': 'DollarSign',
        'path': 'accounting',
        'required_resource': 'accounting_overview',
    },
    'minitrac': {
        'label': 'Minitrac',
        'icon': 'Search',
        'path': 'minitrac',
        'required_resource': 'minitrac',
    },
    'user-management': {
        'label': 'User Management',
        'icon': 'Users',
        'path': 'user-management',
        'required_resource': 'user_management',
    },
    'database-explorer': {
        'label': 'Database Explorer',
        'icon': 'Database',
        'path': 'database-explorer',
        'required_resource': 'database_explorer',
    },
    'ai-query': {
        'label': 'AI Query',
        'icon': 'Bot',
        'path': 'ai-query',
        'required_resource': 'ai_query',
    },
}