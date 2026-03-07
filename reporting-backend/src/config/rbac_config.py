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
    'parts_sold_by_customer': 'Parts sold by customer with GP analysis',
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
    'currie_service': 'Currie Service Department KPI metrics and benchmarks',
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
    'vital_quickbooks': 'VITAL Worklife QuickBooks financial dashboard',
    'vital_azure_sql': 'VITAL Worklife Azure SQL Case Data dashboard',
    'vital_zoom': 'VITAL Worklife Zoom call center analytics',
    'vital_high_fives': 'VITAL Worklife High Fives employee recognition tracking',
    'vital_anonymous_questions': 'VITAL Worklife Anonymous Questions for HR with AI trend analysis',
    'vital_finance': 'VITAL Worklife Finance billing management and revenue tracking',
    'vital_mobile_app': 'VITAL Worklife Mobile App analytics from GA4 BigQuery',
    'vital_claude_analytics': 'VITAL Worklife Claude AI-powered analytics (case data and sentiment analysis)',
    'customer_churn': 'Customer churn analysis with AI-powered insights',
    'eds_dashboard': "Ed's Dashboard - Sales GP Report by Branch and Department",
    'gl_mapping': 'GL Account Mapping - manage chart of accounts for tenant',
    'tenant_admin': 'Tenant/Organization administration - manage orgs, fiscal year settings',
    # Aloha Holdings resources (SAP multi-subsidiary holding company)
    'aloha_dashboard': 'Aloha Holdings executive dashboard - consolidated view across subsidiaries',
    'aloha_financials': 'Aloha Holdings consolidated financial reports from SAP',
    'aloha_inventory': 'Aloha Holdings consolidated inventory across SAP subsidiaries',
    'aloha_orders': 'Aloha Holdings consolidated orders across SAP subsidiaries',
    'aloha_data_sources': 'Aloha Holdings SAP data source configuration (admin only)',
}

# Action types
ACTIONS = ['view', 'create', 'edit', 'delete', 'export']

# Role-based access control matrix
ROLE_PERMISSIONS = {
    'Super Admin': {
        'resources': list(RESOURCES.keys()),  # All resources
        'actions': ACTIONS,  # All actions
    },
    'Owner': {
        'resources': [
            'dashboard',
            'parts_work_orders', 'parts_inventory', 'parts_stock_alerts',
            'parts_forecast', 'parts_overview', 'parts_employee_performance',
            'parts_velocity', 'parts_inventory_turns', 'parts_sold_by_customer',
            'service_work_orders', 'service_overview',
            'rental_availability', 'rental_overview',
            'accounting_overview', 'accounting_ar', 'accounting_ap',
            'accounting_commissions', 'accounting_control', 'accounting_inventory',
            'minitrac', 'currie', 'currie_service', 'financial',
            'customer_churn', 'eds_dashboard'
        ],
        'actions': ['view', 'create', 'edit', 'export'],
    },
    'Sales Manager': {
        'resources': [
            'dashboard'
        ],
        'actions': ['view', 'export'],
    },
    'Leadership': {
        'resources': [
            'dashboard',
            'parts_overview', 'parts_employee_performance', 'parts_velocity',
            'service_overview',
            'rental_overview',
            'accounting_overview',
            'customer_churn',
            'financial',
            'currie', 'currie_service',
            'minitrac',
            'qbr',
        ],
        'actions': ['view', 'export'],
    },
    'Parts Manager': {
        'resources': [
            'parts_work_orders', 'parts_inventory', 'parts_stock_alerts',
            'parts_forecast', 'parts_overview', 'parts_employee_performance',
            'parts_velocity', 'parts_inventory_turns', 'parts_sold_by_customer'
        ],
        'actions': ['view', 'create', 'edit', 'export'],
    },
    'Parts User': {
        'resources': [
            'parts_work_orders', 'parts_inventory',
            'parts_stock_alerts', 'parts_forecast', 'parts_inventory_turns', 'parts_sold_by_customer', 'minitrac'
        ],
        'actions': ['view', 'export'],
    },
    'Service Manager': {
        'resources': [
            'service_work_orders', 'service_overview', 'knowledge_base', 'currie_service'
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
            'currie', 'currie_service',
            'minitrac'
        ],
        'actions': ['view', 'export'],
    },
    'Accounting Manager': {
        'resources': [
            'accounting_overview', 'accounting_ar', 'accounting_ap',
            'accounting_commissions', 'accounting_control', 'accounting_inventory',
            'financial',
            'currie', 'currie_service',
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
            'dashboard', 'vital_hubspot', 'vital_quickbooks', 'vital_azure_sql', 'vital_zoom', 'vital_high_fives', 'vital_anonymous_questions', 'vital_finance', 'vital_mobile_app', 'vital_claude_analytics', 'user_management'
        ],
        'actions': ACTIONS,  # All actions
    },
    'VITAL User': {
        'resources': [
            'dashboard', 'vital_hubspot', 'vital_quickbooks', 'vital_azure_sql', 'vital_zoom', 'vital_high_fives', 'vital_anonymous_questions', 'vital_finance', 'vital_mobile_app', 'vital_claude_analytics'
        ],
        'actions': ['view', 'export'],
    },
    'Finance Manager': {
        'resources': [
            'financial', 'currie', 'currie_service',
            'accounting_overview', 'accounting_ar', 'accounting_ap',
            'accounting_commissions', 'accounting_control', 'accounting_inventory'
        ],
        'actions': ['view', 'create', 'edit', 'export'],
    },
    'Read Only': {
        'resources': [
            'dashboard', 'minitrac'
        ],
        'actions': ['view'],
    },
    # Aloha Holdings roles (SAP multi-subsidiary holding company)
    'Aloha Admin': {
        'resources': [
            'aloha_dashboard', 'aloha_financials', 'aloha_inventory', 'aloha_orders',
            'aloha_data_sources', 'user_management'
        ],
        'actions': ACTIONS,  # All actions
    },
    'Aloha User': {
        'resources': [
            'aloha_dashboard', 'aloha_financials', 'aloha_inventory', 'aloha_orders'
        ],
        'actions': ['view', 'export'],
    },
}

# Navigation menu configuration
NAVIGATION_CONFIG = {
    'dashboard': {
        'label': 'Sales',
        'icon': 'LayoutDashboard',
        'path': 'dashboard',
        'required_resource': 'dashboard',
        'order': 1,
        'tabs': {
            'sales': {'label': 'Sales', 'resource': 'dashboard'},
            'invoiced-sales': {'label': 'Invoiced Sales', 'resource': 'dashboard'},
            'sales-breakdown': {'label': 'Sales Breakdown', 'resource': 'dashboard'},
            'customers': {'label': 'Customers', 'resource': 'dashboard'},
            'workorders': {'label': 'Work Orders', 'resource': 'dashboard'},
            'forecast': {'label': 'AI Sales Forecast', 'resource': 'dashboard'},
            'accuracy': {'label': 'AI Forecast Accuracy', 'resource': 'dashboard'},
        }
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
            'sold-by-customer': {'label': 'Parts Sold by Customer', 'resource': 'parts_sold_by_customer'},
        }
    },
    'service': {
        'label': 'Service',
        'icon': 'Wrench',
        'path': 'service',
        'order': 3,
        'tabs': {
            'overview': {'label': 'Overview', 'resource': 'service_overview'},
            'pms': {'label': "PM's", 'resource': 'service_overview'},
            'pm-route-planner': {'label': 'PM Route Planner', 'resource': 'service_overview'},
            'pm-contest': {'label': 'PM Contest', 'resource': 'service_overview'},
            'shop-work-orders': {'label': 'Cash Burn', 'resource': 'service_work_orders'},
            'work-orders': {'label': 'Cash Stalled', 'resource': 'service_work_orders'},
            'all-work-orders': {'label': 'All Work Orders', 'resource': 'service_work_orders'},
            'invoice-billing': {'label': 'Customer Billing', 'resource': 'service_work_orders'},
            'maintenance-contracts': {'label': 'Maintenance Contract Profitability', 'resource': 'service_overview'},
            'customer-profitability': {'label': 'Customer Profitability', 'resource': 'service_overview'},
            'units-repair-cost': {'label': 'Units by Repair Cost', 'resource': 'service_overview'},
            'cost-per-hour': {'label': 'Cost per Hour', 'resource': 'service_overview'},
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
            'depreciation': {'label': 'Depreciation', 'resource': 'rental_overview'},
            'service-report': {'label': 'Service Report', 'resource': 'rental_overview'},
        }
    },
    'accounting': {
        'label': 'Accounting',
        'icon': 'DollarSign',
        'path': 'accounting',
        'order': 1.6,
        'tabs': {
            'overview': {'label': 'Overview', 'resource': 'accounting_overview'},
            'ar-aging': {'label': 'AR Aging', 'resource': 'accounting_ar'},
            'ap-aging': {'label': 'AP Aging', 'resource': 'accounting_ap'},
            'commissions': {'label': 'Sales Commissions', 'resource': 'accounting_commissions'},
            'control': {'label': 'Control Numbers', 'resource': 'accounting_control'},
            'inventory': {'label': 'Inventory', 'resource': 'accounting_inventory'},
            'parts-commissions': {'label': 'Parts Commissions', 'resource': 'accounting_commissions'},
        }
    },
    'customer-churn': {
        'label': 'Customers',
        'icon': 'TrendingDown',
        'path': 'customer-churn',
        'required_resource': 'customer_churn',
        'order': 5.5,
        'tabs': {
            'sales-by-customer': {'label': 'Sales by Customer', 'resource': 'customer_churn'},
            'customer-churn': {'label': 'Customer Churn', 'resource': 'customer_churn'},
            'customer-profitability': {'label': 'Customer Profitability', 'resource': 'customer_churn'},
        }
    },
    'knowledge-base': {
        'label': 'Knowledge Base',
        'icon': 'Book',
        'path': 'knowledge-base',
        'required_resource': 'knowledge_base',
        'order': 6,
        'tabs': {
            'articles': {'label': 'Articles', 'resource': 'knowledge_base'},
            'work-orders': {'label': 'Work Orders', 'resource': 'knowledge_base'},
            'assistant': {'label': 'Service Assistant', 'resource': 'knowledge_base'},
            'analytics': {'label': 'Analytics', 'resource': 'knowledge_base'},
        }
    },
    'financial': {
        'label': 'Finance',
        'icon': 'FileSpreadsheet',
        'path': 'financial',
        'required_resource': 'financial',
        'order': 1.5,
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
    'gl-mapping': {
        'label': 'GL Account Mapping',
        'icon': 'Settings2',
        'path': 'gl-mapping',
        'required_resource': 'gl_mapping',
        'order': 100,
    },
    'qbr': {
        'label': 'QBR',
        'icon': 'FileBarChart',
        'path': 'qbr',
        'required_resource': 'qbr',
        'order': 10,
        'tabs': {
            'overview': {'label': 'Fleet Overview', 'resource': 'qbr'},
            'health': {'label': 'Fleet Health', 'resource': 'qbr'},
            'service': {'label': 'Service Performance', 'resource': 'qbr'},
            'costs': {'label': 'Costs & Value', 'resource': 'qbr'},
            'recommendations': {'label': 'Recommendations', 'resource': 'qbr'},
        }
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
        'label': 'CMS',
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
        'label': 'Sales & Marketing',
        'icon': 'Target',
        'path': 'vital-hubspot',
        'required_resource': 'vital_hubspot',
        'order': 24,
    },
    # QuickBooks removed - reports moved to Finance
    # 'vital-quickbooks': {
    #     'label': 'QuickBooks',
    #     'icon': 'Calculator',
    #     'path': 'vital-quickbooks',
    #     'required_resource': 'vital_quickbooks',
    #     'order': 25,
    # },
    'vital-azure-sql': {
        'label': 'Customer 360',
        'icon': 'Building2',
        'path': 'vital-azure-sql',
        'required_resource': 'vital_azure_sql',
        'order': 26,
    },
    'vital-zoom': {
        'label': 'Call Center',
        'icon': 'Phone',
        'path': 'vital-zoom',
        'required_resource': 'vital_zoom',
        'order': 27,
    },
    'vital-high-fives': {
        'label': 'High Fives',
        'icon': 'Heart',
        'path': 'vital-high-fives',
        'required_resource': 'vital_high_fives',
        'order': 28,
    },
    'vital-anonymous-questions': {
        'label': 'Anonymous Q&A',
        'icon': 'MessageSquare',
        'path': 'vital-anonymous-questions',
        'required_resource': 'vital_anonymous_questions',
        'order': 29,
    },
    'vital-claude-analytics': {
        'label': 'Claude Analytics',
        'icon': 'Brain',
        'path': 'vital-claude-analytics',
        'required_resource': 'vital_claude_analytics',
        'order': 30,
    },
    'vital-finance': {
        'label': 'Finance',
        'icon': 'Wallet',
        'path': 'vital-finance',
        'required_resource': 'vital_finance',
        'order': 2,  # Moved under Dashboard
    },
    'vital-mobile-app': {
        'label': 'Mobile App',
        'icon': 'Smartphone',
        'path': 'vital-mobile-app',
        'required_resource': 'vital_mobile_app',
        'order': 3,  # After Finance
    },
    'currie': {
        'label': 'Currie',
        'icon': 'FileSpreadsheet',
        'path': 'currie',
        'order': 7.5,
        'tabs': {
            'kpis': {'label': "Currie KPI's", 'resource': 'currie'},
            'sales': {'label': 'Sales', 'resource': 'currie'},
            'expenses': {'label': 'Expenses', 'resource': 'currie'},
            'balance': {'label': 'Balance Sheet', 'resource': 'currie'},
        }
    },
    'currie-service': {
        'label': 'Currie (Service)',
        'icon': 'Wrench',
        'path': 'currie-service',
        'required_resource': 'currie_service',
        'order': 7.6,
    },
    'tenant-admin': {
        'label': 'Tenant Management',
        'icon': 'Building2',
        'path': 'tenant-admin',
        'required_resource': 'tenant_admin',
        'order': 101,
    },
    'report-visibility': {
        'label': 'Report Visibility',
        'icon': 'Eye',
        'path': 'report-visibility',
        'required_resource': 'tenant_admin',
        'order': 102,
    },
    'support-tickets': {
        'label': 'Support Tickets',
        'icon': 'Ticket',
        'path': 'support-tickets',
        'required_resource': 'user_management',
        'order': 98,
    },
    'eds-dashboard': {
        'label': "Ed's Dashboard",
        'icon': 'Crown',
        'path': 'eds-dashboard',
        'required_resource': 'eds_dashboard',
        'order': 0.5,
    },
    # Aloha Holdings navigation (SAP multi-subsidiary holding company)
    'aloha-dashboard': {
        'label': 'Executive Dashboard',
        'icon': 'Globe',
        'path': 'aloha-dashboard',
        'required_resource': 'aloha_dashboard',
        'order': 1,
    },
    'aloha-financials': {
        'label': 'Financials',
        'icon': 'DollarSign',
        'path': 'aloha-financials',
        'required_resource': 'aloha_financials',
        'order': 2,
    },
    'aloha-inventory': {
        'label': 'Inventory',
        'icon': 'Package',
        'path': 'aloha-inventory',
        'required_resource': 'aloha_inventory',
        'order': 3,
    },
    'aloha-orders': {
        'label': 'Orders',
        'icon': 'ShoppingCart',
        'path': 'aloha-orders',
        'required_resource': 'aloha_orders',
        'order': 4,
    },
    'aloha-data-sources': {
        'label': 'Data Sources',
        'icon': 'Database',
        'path': 'aloha-data-sources',
        'required_resource': 'aloha_data_sources',
        'order': 90,
    },
}
