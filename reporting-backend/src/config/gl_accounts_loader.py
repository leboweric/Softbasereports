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
        'cogs': ['510004', '510005', '510007', '512001', '521004', '521005', '521006', '521007', '522000', '523000', '528000', '529001', '534015', '535001', '535002', '535003', '535004', '535005'],
        # Currie-aligned accounts for department cards (controllable margin only)
        # Customer Labor (410004/410005/410007), Internal Labor (423000/425000),
        # Warranty (435000-435004), Sublet (432000), Other Service (428000/429002)
        'currie_revenue': ['410004', '410005', '410007', '423000', '425000', '428000', '429002', '432000', '435000', '435001', '435002', '435003', '435004'],
        'currie_cogs': ['510004', '510005', '510007', '523000', '528000', '529001', '532000', '535001', '535002', '535003', '535004', '535005']
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

# IPS Expense Accounts - Discovered from ind004.GL (2025 data)
# Account format: 7-digit (XXXXYYZ) where last 2 digits = department/location
EXPENSE_ACCOUNTS_IPS = {
    'depreciation': [
        '6100501', '6100503', '6100504',  # Depreciation - New Equipment locations
        '6100701',  # Depreciation - Service
        '6100801',  # Depreciation - Admin/General
    ],
    'salaries_wages': [
        '6840701',  # Salaries - Management (Service)
        '6850501',  # Salaries - Office (Parts)
        '6880201',  # Wages - Allied/IF
        '6880501',  # Wages - Parts
        '6880801',  # Wages - Admin
        '6880901',  # Wages - Rental
        '6910201',  # Commission/Bonus - Allied
        '6910501',  # Commission/Bonus - New Equipment Canton
        '6910503',  # Commission/Bonus - New Equipment
        '6910601',  # Commission/Bonus - Parts
        '6911801',  # Commission/Bonus - Admin 1
        '6911802',  # Commission/Bonus - Admin 2
    ],
    'payroll_benefits': [
        '6210201',  # Employee Benefits - Allied
        '6210501', '6210502', '6210503', '6210504',  # Employee Benefits - New Equipment
        '6210601',  # Employee Benefits - Parts
        '6210701', '6210702',  # Employee Benefits - Service
        '6210801',  # Employee Benefits - Admin
        '6470201',  # Medical/Health - Allied
        '6470401',  # Medical/Health - Used Equipment
        '6470501', '6470502', '6470503', '6470504',  # Medical/Health - New Equipment
        '6470601',  # Medical/Health - Parts
        '6470701', '6470702',  # Medical/Health - Service
        '6470901', '6470902',  # Medical/Health - Rental
        '6530201',  # Payroll Taxes - Allied
        '6530501', '6530502', '6530503', '6530504',  # Payroll Taxes - New Equipment
        '6530601',  # Payroll Taxes - Parts
        '6530701',  # Payroll Taxes - Service
        '6530801',  # Payroll Taxes - Admin
    ],
    'rent_facilities': [
        '6733401',  # Rent - Used Equipment
        '6733501', '6733502', '6733503', '6733504',  # Rent - New Equipment
        '6733601',  # Rent - Parts
        '6733701',  # Rent - Service
        '6733801',  # Rent - Admin
        '6733901',  # Rent - Rental
        '6555201',  # Property Tax - Allied
        '6555501',  # Property Tax - New Equipment
        '6555503',  # Property Tax - New Equipment
    ],
    'utilities': [
        '6430101',  # Utilities/Janitorial - General
        '6430201',  # Utilities/Janitorial - Allied
        '6430401',  # Utilities/Janitorial - Used Equipment
        '6430501', '6430502', '6430503', '6430504',  # Utilities/Janitorial - New Equipment
        '6430601',  # Utilities/Janitorial - Parts
        '6430701',  # Utilities/Janitorial - Service
        '6430801',  # Utilities/Janitorial - Admin
        '6430901',  # Utilities/Janitorial - Rental
    ],
    'insurance': [
        '6410201',  # Insurance - Allied
        '6410501', '6410502', '6410503',  # Insurance - New Equipment
        '6410601',  # Insurance - Parts
        '6410701',  # Insurance - Service
        '6410801',  # Insurance - Admin
    ],
    'marketing': [
        '6010701',  # Advertising - Service
        '6010801',  # Advertising - Admin
        '6460201',  # Meals/Entertainment - Allied
        '6460501', '6460502', '6460503',  # Meals/Entertainment - New Equipment
        '6460601',  # Meals/Entertainment - Parts
        '6460701',  # Meals/Entertainment - Service
        '6460801',  # Meals/Entertainment - Admin
    ],
    'professional_fees': [
        '6540501', '6540502', '6540503',  # Professional Fees - New Equipment
        '6540601',  # Professional Fees - Parts
        '6540701',  # Professional Fees - Service
        '6540801',  # Professional Fees - Admin
    ],
    'office_admin': [
        '6050201',  # Building Maintenance - Allied
        '6050701',  # Building Maintenance - Service
        '6050801',  # Building Maintenance - Admin
        '6070201',  # Computer/IT - Allied
        '6070501', '6070502', '6070503', '6070504',  # Computer/IT - New Equipment
        '6070601',  # Computer/IT - Parts
        '6070701',  # Computer/IT - Service
        '6070801',  # Computer/IT - Admin
        '6110501', '6110502',  # Dues/Subscriptions - New Equipment
        '6110601',  # Dues/Subscriptions - Parts
        '6110701',  # Dues/Subscriptions - Service
        '6110801',  # Dues/Subscriptions - Admin
        '6111401', '6111402',  # Dues - Used Equipment
        '6111501', '6111502', '6111503',  # Dues - New Equipment
        '6112001', '6112002',  # Dues - Allied
        '6112203', '6112204',  # Dues - Allied
        '6510801',  # Office Supplies - Admin
        '6520801',  # Outside Services - Admin
        '6920701', '6920702',  # Telephone - Service
    ],
    'vehicle_equipment': [
        '6020501', '6020502', '6020503', '6020504',  # Auto/Vehicle - New Equipment
        '6020601',  # Auto/Vehicle - Parts
        '6310201',  # Equipment Rental - Allied
        '6310401',  # Equipment Rental - Used Equipment
        '6310501', '6310502', '6310503', '6310504',  # Equipment Rental - New Equipment
        '6310601',  # Equipment Rental - Parts
        '6310701',  # Equipment Rental - Service
        '6310901',  # Equipment Rental - Rental
        '6320801', '6320802',  # Freight - Admin
        '6330801', '6330802',  # Fuel - Admin
        '6740801',  # Repairs/Maintenance - Admin
        '6820701',  # Small Tools - Service
        '6820801',  # Small Tools - Admin
    ],
    'interest_finance': [
        '6420701', '6420702',  # Interest Expense - Service
    ],
    'other_expenses': [
        '6030701',  # Bad Debt - Service
        '6061001', '6061003',  # Charitable Contributions
        '6061601',  # Charitable Contributions - Parts
        '6440501', '6440502', '6440503',  # Licenses/Permits - New Equipment
        '6440701', '6440702',  # Licenses/Permits - Service
        '6440801',  # Licenses/Permits - Admin
        '6450801',  # Management Fees - Admin
        '6480501', '6480503',  # Miscellaneous - New Equipment
        '6480701',  # Miscellaneous - Service
        # NOTE: Overhead allocation accounts (698xxxx) and internal allocation accounts (693xxxx)
        # are EXCLUDED from operating expenses because they are internal transfers that net to zero.
        # The real expenses are already captured in the other categories above.
    ]
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
    config = TENANT_GL_CONFIGS.get(schema)
    if config is None:
        import logging
        logging.getLogger(__name__).warning(f"No GL config for schema '{schema}' - falling back to ben002. Add this tenant to TENANT_GL_CONFIGS!")
        config = TENANT_GL_CONFIGS['ben002']
    return config['gl_accounts']


def get_other_income_accounts(schema: str) -> list:
    """
    Get the Other Income account list for a specific tenant schema.
    
    Args:
        schema: The tenant's database schema
    
    Returns:
        List of Other Income GL account codes
    """
    config = TENANT_GL_CONFIGS.get(schema)
    if config is None:
        import logging
        logging.getLogger(__name__).warning(f"No GL config for schema '{schema}' - falling back to ben002. Add this tenant to TENANT_GL_CONFIGS!")
        config = TENANT_GL_CONFIGS['ben002']
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
    config = TENANT_GL_CONFIGS.get(schema)
    if config is None:
        import logging
        logging.getLogger(__name__).warning(f"No GL config for schema '{schema}' - falling back to ben002. Add this tenant to TENANT_GL_CONFIGS!")
        config = TENANT_GL_CONFIGS['ben002']
    return config['expense_accounts']
