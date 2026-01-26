"""
Detailed GL Account Mappings for P&L Reports
Aligned with dashboard (pl_report.py) GL_ACCOUNTS to ensure matching totals
"""

# Department configurations with GL account mappings
# IMPORTANT: These account lists MUST match the GL_ACCOUNTS in pl_report.py exactly
# to ensure the detailed export totals match the dashboard
DEPARTMENT_CONFIG = {
    'new_equipment': {
        'dept_code': 10,
        'dept_name': 'New Equipment',
        'tab_name': 'P&L New Equip',
        # Dashboard: ['410001', '412001', '413001', '414001', '421001', '426001', '431001', '434001']
        'sales_accounts': [
            ('410001', 'Sales - New Equipment'),
            ('412001', 'SALES - ALLIED - New Equip'),
            ('413001', 'SALES - LINDE - New Equip'),
            ('414001', 'SALES - BATTERY/CHARGERS - New Equip'),
            ('421001', 'SALES - FREIGHT - New Equip'),
            ('426001', 'SALES - KOMATSU - New Equip'),
            ('431001', 'SALES - SKID LOADERS - New Equip'),
            ('434001', 'SALES - TRUCKING/DELIVERY - New Equip'),
        ],
        # Dashboard: ['510001', '513001', '514001', '521001', '525001', '526001', '531001', '534001', '534013', '538000']
        'cos_accounts': [
            ('510001', 'COS - New Equip'),
            ('513001', 'COS - LINDE - New Equip'),
            ('514001', 'COS - BATTERIES/CHARGERS - New Equip'),
            ('521001', 'COS - FREIGHT - New Equip'),
            ('525001', 'COS - INTERNAL NEW EQUIP'),
            ('526001', 'COS - KOMATSU - New Equip'),
            ('531001', 'COS - SKID LOADERS - New Equip'),
            ('534001', 'COS - TRUCKING/DELIVERY - New Equip'),
            ('534013', 'COS - TRUCKING/DELIVERY - New Equipment Demo'),
            ('538000', 'COS - EQ. ADJUSTMENT'),
        ]
    },
    'used_equipment': {
        'dept_code': 20,
        'dept_name': 'Used Equipment',
        'tab_name': 'P&L Used Equip',
        # Dashboard: ['410002', '412002', '413002', '414002', '421002', '426002', '431002', '434002', '436001']
        'sales_accounts': [
            ('410002', 'Sales - Used Equipment'),
            ('412002', 'SALES - ALLIED - Used Equip'),
            ('413002', 'SALES - LINDE - Used Equip'),
            ('414002', 'SALES - BATTERY/CHARGERS - Used Equip'),
            ('421002', 'SALES - FREIGHT - Used Equip'),
            ('426002', 'SALES - KOMATSU - Used Equip'),
            ('431002', 'SALES - SKID LOADERS - Used Equip'),
            ('434002', 'SALES - TRUCKING/DELIVERY - Used Equip'),
            ('436001', 'SALES - WHOLESALE - Used Equip'),
        ],
        # Dashboard: ['510002', '512002', '513002', '514002', '521002', '525002', '526002', '531002', '534002', '536001']
        'cos_accounts': [
            ('510002', 'COS - Used Equip'),
            ('512002', 'COS - ALLIED - Used Equip'),
            ('513002', 'COS - LINDE- Used Equip'),
            ('514002', 'COS - BATTERIES/CHARGERS - Used Equip'),
            ('521002', 'COS - FREIGHT - Used Equip'),
            ('525002', 'COS - INTERNAL USED EQUIP'),
            ('526002', 'COS - KOMATSU - Used Equip'),
            ('531002', 'COS - SKID LOADERS - Used Equip'),
            ('534002', 'COS - TRUCKING/DELIVERY - Used Equip'),
            ('536001', 'COS - WHOLESALE - Used Equip'),
        ]
    },
    'parts': {
        'dept_code': 30,
        'dept_name': 'Parts',
        'tab_name': 'P&L Parts',
        # Dashboard: ['410003', '410012', '410014', '410015', '421003', '424000', '429001', '430000', '433000', '434003', '436002', '439000']
        'sales_accounts': [
            ('410003', 'Sales - Parts - Counter'),
            ('410012', 'Sales - Parts - Cust Repair Order'),
            ('410014', 'Sales - Parts - Warranty'),
            ('410015', 'Sales - GM Parts'),
            ('421003', 'SALES - FREIGHT - Parts'),
            ('424000', 'SALES - INTERNAL PARTS REPAIR ORDER'),
            ('429001', 'SALES - P.M. CONTRACTS - Parts'),
            ('430000', 'SALES - SHOP SUPPLIES'),
            ('433000', 'SALES - TIRES'),
            ('434003', 'SALES - TRUCKING/DELIVERY - Parts'),
            ('436002', 'SALES - WHOLESALE - Parts'),
            ('439000', 'SALES - TRADE-IN OVERALLOW'),
        ],
        # Dashboard: ['510003', '510012', '510013', '510014', '510015', '521003', '522001', '524000', '529002', '530000', '533000', '534003', '536002', '542000', '543000', '544000']
        'cos_accounts': [
            ('510003', 'COS - Parts - Counter'),
            ('510012', 'COS - Parts - Cust Repair Order'),
            ('510013', 'COS - Parts - PM'),
            ('510014', 'COS - Parts - Warranty'),
            ('510015', 'COS - Parts - GM'),
            ('521003', 'COS - FREIGHT - Parts'),
            ('522001', 'COS - GUARNTEED MAINTENANCE - Parts'),
            ('524000', 'COS - PARTS INTERNAL REPAIR ORDER'),
            ('529002', 'COS - P.M. CONTRACTS - Parts'),
            ('530000', 'COS - SHOP SUPPLIES'),
            ('533000', 'COS - TIRES'),
            ('534003', 'COS - TRUCKING/DELIVERY - Parts'),
            ('536002', 'COS - WHOLESALE - Parts'),
            ('542000', 'COS - INVENTORY ADJUSTMENT'),
            ('543000', 'COS - RESTOCKING FEES'),
            ('544000', 'COS - RETAIL'),
        ]
    },
    'service': {
        'dept_code': 40,
        'dept_name': 'Service',
        'tab_name': 'P&L Service',
        # Dashboard: ['410004', '410005', '410007', '410016', '421004', '421005', '421006', '421007', '423000', '425000', '428000', '429002', '432000', '435000', '435001', '435002', '435003', '435004']
        'sales_accounts': [
            ('410004', 'Sales - Field'),
            ('410005', 'Sales - Shop'),
            ('410007', 'Sales - Full Maint.'),
            ('410016', 'Sales - GM Service'),
            ('421004', 'Sales - FREIGHT - Field'),
            ('421005', 'Sales - FREIGHT - Shop'),
            ('421006', 'Sales - FREIGHT - PM'),
            ('421007', 'Sales - FREIGHT - Full Maint.'),
            ('423000', 'SALES - INTERNAL REPAIR FIELD'),
            ('425000', 'SALES - INTERNAL REPAIRS SHOP'),
            ('428000', 'SALES - OTHER'),
            ('429002', 'SALES - P.M. CONTRACTS - Service'),
            ('432000', 'SALES - SUBLET LABOR'),
            ('435000', 'SALES - WARRANTY CLAIM OTHER'),
            ('435001', 'SALES-SRV. WARRANTY KOMATSU'),
            ('435002', 'SALES-SRV. WARRANTY LINDE'),
            ('435003', 'SALES-SRV. WARRANTY BENDI'),
            ('435004', 'SALES-SRV. WARRANTY SCHAEFF'),
        ],
        # Dashboard: ['510004', '510005', '510007', '512001', '521004', '521005', '521006', '521007', '522000', '523000', '528000', '529001', '534015', '535001', '535002', '535003', '535004', '535005']
        'cos_accounts': [
            ('510004', 'COS - Field'),
            ('510005', 'COS - Shop'),
            ('510007', 'COS - Full Maint'),
            ('512001', 'COS - ALLIED - New Equip'),
            ('521004', 'COS - FREIGHT - Field'),
            ('521005', 'COS - FREIGHT - Shop'),
            ('521006', 'COS - FREIGHT - PM'),
            ('521007', 'COS - FREIGHT - Full Maint'),
            ('522000', 'COS - GUARNTEED MAINTENANCE - Service'),
            ('523000', 'COS - INTERNAL REPAIRS FIELD'),
            ('528000', 'COS - OTHER'),
            ('529001', 'COS - P.M. CONTRACTS - Service'),
            ('534015', 'COS - TRUCKING/DELIVERY - Service'),
            ('535001', 'COS-SRV. WARRANTY KOMATSU'),
            ('535002', 'COS-SRV. WARRANTY LINDE'),
            ('535003', 'COS-SRV. WARRANTY SCHAEFF'),
            ('535004', 'COS-SRV. WARRANTY BENDI'),
            ('535005', 'COS-SRV. WARRANTY OTHER'),
        ]
    },
    'rental': {
        'dept_code': 60,
        'dept_name': 'Rental',
        'tab_name': 'P&L Rental',
        # Dashboard: ['410008', '411001', '419000', '420000', '421000', '434012']
        'sales_accounts': [
            ('410008', 'Sales - RENTAL'),
            ('411001', 'SALES - ABUSE - Rental'),
            ('419000', 'SALES - EQ. DISPOSAL RENTAL'),
            ('420000', 'SALES - EXPENSE RECAPTURE'),
            ('421000', 'SALES - FREIGHT RENTAL'),
            ('434012', 'SALES - TRUCKING/DELIVERY - RENTAL'),
        ],
        # Dashboard: ['510008', '511001', '519000', '520000', '521008', '534014', '537001', '539000', '545000']
        'cos_accounts': [
            ('510008', 'COS - Rental'),
            ('511001', 'COS - ABUSE - Rental'),
            ('519000', 'COS - EQ. DISPOSAL RENTAL'),
            ('520000', 'COS - EXPENSE RECAPTURE'),
            ('521008', 'COS - FREIGHT - Rental'),
            ('534014', 'COS - TRUCKING/DELIVERY - Rental'),
            ('537001', 'COS - DEPRECIATION - Rental'),
            ('539000', 'COS - RENTAL INTEREST'),
            ('545000', 'COS - OUTSIDE(RTR) Rental'),
        ]
    },
    'transportation': {
        'dept_code': 80,
        'dept_name': 'Transportation',
        'tab_name': 'P&L Transportation',
        # Dashboard: ['410010', '421010', '434010', '434013']
        'sales_accounts': [
            ('410010', 'Sales - Trucking'),
            ('421010', 'SALES - FREIGHT - Trucking'),
            ('434010', 'SALES - TRUCKING/DELIVERY - Trucking'),
            ('434013', 'SALES - TRUCKING/DELIVERY - SERVICE'),
        ],
        # Dashboard: ['510010', '521010', '534010', '534012']
        'cos_accounts': [
            ('510010', 'COS - Trucking'),
            ('521010', 'COS - FREIGHT - Trucking'),
            ('534010', 'COS - TRUCKING/DELIVERY - Trucking'),
            ('534012', 'COS - TRUCKING/DELIVERY - Customer'),
        ]
    },
    'administrative': {
        'dept_code': 90,
        'dept_name': 'In House / Administrative',
        'tab_name': 'P&L In House',
        # Dashboard: ['410011', '421011', '422100', '427000', '434011']
        'sales_accounts': [
            ('410011', 'Sales - Administrative'),
            ('421011', 'SALES - FREIGHT - Administrative'),
            ('422100', 'SALES INT. LABOR GM'),
            ('427000', 'SALES - OPERATOR AWARENESS TRAINING'),
            ('434011', 'SALES - TRUCKING/DELIVERY - Administrative'),
        ],
        # Dashboard: ['510011', '521011', '522100', '525000', '527000', '532000', '534011', '540000', '541000']
        'cos_accounts': [
            ('510011', 'COS - Administrative'),
            ('521011', 'COS - FREIGHT - Administrative'),
            ('522100', 'COS INT. LABOR GM'),
            ('525000', 'COS - INTERNAL'),
            ('527000', 'COS OPER AWARENESS TRNG'),
            ('532000', 'COS SUBLET LABOR'),
            ('534011', 'COS TRUCKING/DELIVERY G&A'),
            ('540000', 'COS - ADMINISTRATIVE'),
            ('541000', 'COS RENTAL INTERNAL MAINTENANCE'),
        ]
    }
}

# Overhead Expense Accounts (for Administrative/In House tab)
# These match the EXPENSE_ACCOUNTS in pl_report.py
OVERHEAD_EXPENSE_ACCOUNTS = {
    'depreciation': [
        ('600900', 'DEPRECIATION'),
    ],
    'salaries_wages': [
        ('602000', 'SERVICE LABOR-REDISTRIBUTION'),
        ('602001', 'TRANSP., LABOR-REDISTRIBUTION'),
        ('602300', 'NON-BILLABLE LABOR - Field'),
        ('602301', 'NON-BILLABLE LABOR - Shop'),
        ('602302', 'NON-BILLABLE LABOR - OTHER'),
        ('602600', 'PAYROLL'),
        ('602610', 'Payroll (Absorbed)'),
    ],
    'payroll_benefits': [
        ('601100', 'EMPLOYER P/R TAXES'),
        ('602700', 'PENSION & PROFIT SHARING'),
        ('602701', 'EMPLOYER 401K MATCH'),
    ],
    'rent_facilities': [
        ('600200', 'BLDG. RENT'),
        ('600201', 'Bldg Rent - Variable Lease Expense'),
        ('600300', 'BUILDING MAINTENANCE'),
        ('602100', 'MAINTENANCE'),
    ],
    'utilities': [
        ('604000', 'UTILITIES'),
    ],
    'insurance': [
        ('601700', 'INSURANCE'),
    ],
    'marketing': [
        ('600000', 'ADVERTISING'),
        ('603300', 'SALES PROMOTION'),
    ],
    'professional_fees': [
        ('603000', 'PROFESSIONAL SERVICES'),
    ],
    'office_admin': [
        ('600500', 'COMPUTER/SUPPLIES'),
        ('601300', 'EXPENSE - MGMT. INFO. SYSTEMS'),
        ('602400', 'OFFICE'),
        ('602900', 'POSTAGE'),
        ('603500', 'SUPPLIES'),
        ('603600', 'TELEPHONE'),
    ],
    'vehicle_equipment': [
        ('604100', 'VEHICLE EXPENSE'),
    ],
    'interest_finance': [
        ('601800', 'INTEREST'),
        ('602500', 'OTHER TAXES'),
    ],
    'other_expenses': [
        ('600100', 'BAD DEBTS'),
        ('600400', 'COMMISSIONS'),
        ('600600', 'CONTRIBUTIONS'),
        ('600700', 'DEALER COMMISSIONS'),
        ('600800', 'DEMO EXPENSES'),
        ('600901', 'DEPRECIATION - Rental'),
        ('600902', 'DEPRECIATION - Other'),
        ('601000', 'DUES AND MEMBERSHIPS'),
        ('601200', 'ENTERTAINMENT & MEALS'),
        ('601400', 'FEDERAL INCOME TAX'),
        ('601500', 'FRINGES'),
        ('601600', 'GPS'),
        ('601900', 'INTERNAL RENTAL'),
        ('602200', 'MISCELLANEOUS'),
        ('602601', 'PAYROLL - Other'),
        ('602800', 'POLICY ADJUSTMENT'),
        ('603100', 'REWORK - Field'),
        ('603101', 'REWORK - Shop'),
        ('603102', 'REWORK - PM'),
        ('603103', 'REWORK - Full Maint'),
        ('603200', 'SAFETY'),
        ('603400', 'STATE INCOME TAXES'),
        ('603501', 'SERVICE TOOLS'),
        ('603700', 'TRAINING'),
        ('603800', 'TRAVEL'),
        ('603900', 'UNIFORMS'),
        ('604200', 'WARRANTY'),
        ('650000', 'OTHER EXPENSE'),
        ('706000', 'ADMINISTRATIVE FUND EXPENSE'),
        ('999999', 'ERROR ACCOUNT'),
    ]
}

# Other Income & Expense Accounts
# These match the OTHER_INCOME_ACCOUNTS in pl_report.py
OTHER_INCOME_EXPENSE_ACCOUNTS = {
    'other_income': [
        ('701000', 'GAIN/LOSS ON SALE OF ASSET'),
        ('702000', 'MISCELLANEOUS INCOME'),
        ('703000', 'A/R DISCOUNTS ALLOWED'),
        ('704000', 'A/P DISCOUNTS TAKEN'),
        ('705000', 'PARTS DISCOUNTS'),
    ],
    'other_expense': [
        # Note: Most expense accounts are in OVERHEAD_EXPENSE_ACCOUNTS
        # This section is for true "other" items not in normal operations
    ],
}

# Helper function to get all accounts for a department
def get_all_sales_accounts():
    """Get all sales account numbers across all departments"""
    accounts = []
    for dept in DEPARTMENT_CONFIG.values():
        accounts.extend([acct[0] for acct in dept['sales_accounts']])
    return accounts

def get_all_cos_accounts():
    """Get all COS account numbers across all departments"""
    accounts = []
    for dept in DEPARTMENT_CONFIG.values():
        accounts.extend([acct[0] for acct in dept['cos_accounts']])
    return accounts

def get_all_expense_accounts():
    """Get all overhead expense account numbers"""
    accounts = []
    for category in OVERHEAD_EXPENSE_ACCOUNTS.values():
        accounts.extend([acct[0] for acct in category])
    return accounts

def get_all_other_accounts():
    """Get all other income/expense account numbers"""
    accounts = []
    for category in OTHER_INCOME_EXPENSE_ACCOUNTS.values():
        accounts.extend([acct[0] for acct in category])
    return accounts
