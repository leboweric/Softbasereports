# GL Accounts Loader - Provides tenant-specific GL account mappings
# This module loads the appropriate GL configuration based on the tenant schema

from src.config.gl_accounts_ips import GL_ACCOUNTS_IPS, OTHER_INCOME_ACCOUNTS_IPS

# Bennett GL Accounts (default/legacy)
GL_ACCOUNTS_BENNETT = {
    'new_equipment': {
        'dept_code': 10,
        'dept_name': 'New Equipment',
        'revenue': ['410001', '412001', '413001', '414001', '421001', '426001', '431001', '434001'],
        'cogs': ['510001', '513001', '514001', '521001', '525001', '526001', '531001', '534001', '534013', '538000']
    },
    'used_equipment': {
        'dept_code': 20,
        'dept_name': 'Used Equipment',
        'revenue': ['410002', '412002', '413002', '414002', '421002', '426002', '431002', '434002', '436001'],
        'cogs': ['510002', '512002', '513002', '514002', '521002', '525002', '526002', '531002', '534002', '536001']
    },
    'parts': {
        'dept_code': 30,
        'dept_name': 'Parts',
        'revenue': ['410003', '410012', '410014', '410015', '421003', '424000', '429001', '430000', '433000', '434003', '436002', '439000'],
        'cogs': ['510003', '510012', '510013', '510014', '510015', '521003', '522001', '524000', '529002', '530000', '533000', '534003', '536002', '542000', '543000', '544000']
    },
    'service': {
        'dept_code': 40,
        'dept_name': 'Service',
        'revenue': ['410004', '410005', '410007', '410016', '421004', '421005', '421006', '421007', '423000', '425000', '428000', '429002', '432000', '435000', '435001', '435002', '435003', '435004'],
        'cogs': ['510004', '510005', '510007', '512001', '521004', '521005', '521006', '521007', '522000', '523000', '528000', '529001', '534015', '535001', '535002', '535003', '535004', '535005']
    },
    'rental': {
        'dept_code': 60,
        'dept_name': 'Rental',
        'revenue': ['410008', '411001', '419000', '420000', '421000', '434012'],
        'cogs': ['510008', '511001', '519000', '520000', '521008', '534014', '537001', '539000', '545000']
    },
    'transportation': {
        'dept_code': 80,
        'dept_name': 'Transportation',
        'revenue': ['410010', '421010', '434010', '434013'],
        'cogs': ['510010', '521010', '534010', '534012']
    },
    'administrative': {
        'dept_code': 90,
        'dept_name': 'Administrative',
        'revenue': ['410011', '421011', '422100', '427000', '434011'],
        'cogs': ['510011', '521011', '522100', '525000', '527000', '532000', '534011', '540000', '541000']
    }
}

OTHER_INCOME_ACCOUNTS_BENNETT = ['701000', '702000', '703000', '704000', '705000']

# Expense Account Mappings (Bennett - all in Administrative department)
EXPENSE_ACCOUNTS_BENNETT = {
    'depreciation': ['600900'],
    'salaries_wages': ['602000', '602001', '602300', '602301', '602302', '602600', '602610'],
    'payroll_benefits': ['601100', '602700', '602701'],
    'rent_facilities': ['600200', '600201', '600300', '602100'],
    'utilities': ['604000'],
    'insurance': ['601700'],
    'marketing': ['600000', '603300'],
    'professional_fees': ['603000'],
    'office_admin': ['600500', '601300', '602400', '602900', '603500', '603600'],
    'vehicle_equipment': ['604100'],
    'interest_finance': ['601800', '602500'],
    'other_expenses': [
        '600100', '600400', '600600', '600700', '600800', '600901', '600902', '601000', '601200', 
        '601400', '601500', '601600', '601900', '602200', '602601', '602800', 
        '603100', '603101', '603102', '603103', '603200', '603400', '603501', 
        '603700', '603800', '603900', '604200', '650000', '706000', '999999'
    ]
}

# IPS Expense Accounts (placeholder - needs to be discovered from IPS database)
EXPENSE_ACCOUNTS_IPS = {
    'depreciation': [],
    'salaries_wages': [],
    'payroll_benefits': [],
    'rent_facilities': [],
    'utilities': [],
    'insurance': [],
    'marketing': [],
    'professional_fees': [],
    'office_admin': [],
    'vehicle_equipment': [],
    'interest_finance': [],
    'other_expenses': []
}

# Mapping of schema to GL configuration
TENANT_GL_CONFIGS = {
    'ben002': {
        'gl_accounts': GL_ACCOUNTS_BENNETT,
        'other_income': OTHER_INCOME_ACCOUNTS_BENNETT,
        'expense_accounts': EXPENSE_ACCOUNTS_BENNETT,
    },
    'ind004': {
        'gl_accounts': GL_ACCOUNTS_IPS,
        'other_income': OTHER_INCOME_ACCOUNTS_IPS,
        'expense_accounts': EXPENSE_ACCOUNTS_IPS,
    },
}


def get_gl_accounts(schema: str) -> dict:
    """
    Get the GL account mappings for a specific tenant schema.
    Falls back to Bennett configuration if schema not found.
    
    Args:
        schema: The tenant's database schema (e.g., 'ben002', 'ind004')
    
    Returns:
        Dictionary of GL account mappings by department
    """
    config = TENANT_GL_CONFIGS.get(schema, TENANT_GL_CONFIGS['ben002'])
    return config['gl_accounts']


def get_other_income_accounts(schema: str) -> list:
    """
    Get the Other Income account list for a specific tenant schema.
    
    Args:
        schema: The tenant's database schema
    
    Returns:
        List of Other Income GL account codes
    """
    config = TENANT_GL_CONFIGS.get(schema, TENANT_GL_CONFIGS['ben002'])
    return config['other_income']


def get_all_revenue_accounts(schema: str) -> list:
    """
    Get all revenue accounts for a specific tenant.
    
    Args:
        schema: The tenant's database schema
    
    Returns:
        List of all revenue GL account codes
    """
    gl_accounts = get_gl_accounts(schema)
    accounts = []
    for dept in gl_accounts.values():
        accounts.extend(dept['revenue'])
    return accounts


def get_all_cogs_accounts(schema: str) -> list:
    """
    Get all COGS accounts for a specific tenant.
    
    Args:
        schema: The tenant's database schema
    
    Returns:
        List of all COGS GL account codes
    """
    gl_accounts = get_gl_accounts(schema)
    accounts = []
    for dept in gl_accounts.values():
        accounts.extend(dept['cogs'])
    return accounts


def get_expense_accounts(schema: str) -> dict:
    """
    Get the Expense account mappings for a specific tenant schema.
    
    Args:
        schema: The tenant's database schema
    
    Returns:
        Dictionary of expense account mappings by category
    """
    config = TENANT_GL_CONFIGS.get(schema, TENANT_GL_CONFIGS['ben002'])
    return config['expense_accounts']
