# GL Account Configuration for Detailed P&L Export
# This file contains the GL account mappings for each department
# These MUST match the GL_ACCOUNTS in pl_report.py EXACTLY

# Department Configuration - EXACT copy from pl_report.py GL_ACCOUNTS
DEPARTMENT_CONFIG = {
    'new_equipment': {
        'dept_code': 10,
        'dept_name': 'New Equipment',
        'tab_name': 'P&L New Equip',
        'sales_accounts': [
            ('410001', 'SALES - New Equipment'),
            ('412001', 'SALES - ALLIED - New Equip'),
            ('413001', 'SALES - LINDE - New Equip'),
            ('414001', 'SALES - BATTERY/CHARGERS - New Equip'),
            ('421001', 'SALES - FREIGHT - New Equip'),
            ('426001', 'SALES - KOMATSU - New Equip'),
            # Removed: ('431001', 'SALES - SKID LOADERS - New Equip') - no longer used
            # Removed: ('434001', 'SALES - TRUCKING/DELIVERY - New Equip') - no longer used
        ],
        'cos_accounts': [
            ('510001', 'COS - New Equip'),
            ('513001', 'COS - LINDE - New Equip'),
            ('514001', 'COS - BATTERIES/CHARGERS - New Equip'),
            ('521001', 'COS - FREIGHT - New Equip'),
            ('525001', 'COS - INTERNAL NEW EQUIP'),
            ('526001', 'COS - KOMATSU - New Equip'),
            # Removed: ('531001', 'COS - SKID LOADERS - New Equip') - no longer used
            # Removed: ('534001', 'COS - TRUCKING/DELIVERY - New Equip') - no longer used
            ('534013', 'COS - TRUCKING/DELIVERY - New Equipment Demo'),
            ('538000', 'COS - EQ. ADJUSTMENT'),
        ]
    },
    'used_equipment': {
        'dept_code': 20,
        'dept_name': 'Used Equipment',
        'tab_name': 'P&L Used Equip',
        'sales_accounts': [
            ('410002', 'SALES - Used Equipment'),
            # Removed: ('412002', 'SALES - ALLIED - Used Equip') - no longer used
            # Removed: ('413002', 'SALES - LINDE - Used Equip') - no longer used
            # Removed: ('414002', 'SALES - BATTERY/CHARGERS - Used Equip') - no longer used
            ('421002', 'SALES - FREIGHT - Used Equip'),
            # Removed: ('426002', 'SALES - KOMATSU - Used Equip') - no longer used
            # Removed: ('431002', 'SALES - SKID LOADERS - Used Equip') - no longer used
            # Removed: ('434002', 'SALES - TRUCKING/DELIVERY - Used Equip') - no longer used
            # Removed: ('436001', 'SALES - MISC - Used Equip') - no longer used
        ],
        'cos_accounts': [
            ('510002', 'COS - Used Equip'),
            # Removed: ('512002', 'COS - ALLIED - Used Equip') - no longer used
            # Removed: ('513002', 'COS - LINDE - Used Equip') - no longer used
            # Removed: ('514002', 'COS - BATTERY/CHARGERS - Used Equip') - no longer used
            ('521002', 'COS - FREIGHT - Used Equip'),
            ('525002', 'COS - INTERNAL - Used Equip'),
            # Removed: ('526002', 'COS - KOMATSU - Used Equip') - no longer used
            # Removed: ('531002', 'COS - SKID LOADERS - Used Equip') - no longer used
            # Removed: ('534002', 'COS - TRUCKING/DELIVERY - Used Equip') - no longer used
            # Removed: ('536001', 'COS - MISC - Used Equip') - no longer used
        ]
    },
    'parts': {
        'dept_code': 30,
        'dept_name': 'Parts',
        'tab_name': 'P&L Parts',
        'sales_accounts': [
            ('410003', 'SALES - Parts'),
            ('410012', 'SALES - Parts 12'),
            ('410014', 'SALES - Parts 14'),
            ('410015', 'SALES - Parts 15'),
            ('421003', 'SALES - FREIGHT - Parts'),
            ('424000', 'SALES - SHOP SUPPLIES'),
            ('429001', 'SALES - PM CONTRACT - Parts'),
            ('430000', 'SALES - FULL MAINT CONTRACT'),
            ('433000', 'SALES - SERVICE OTHER'),
            ('434003', 'SALES - TRUCKING/DELIVERY - Parts'),
            ('436002', 'SALES - MISC - Parts'),
            ('439000', 'SALES - OTHER'),
        ],
        'cos_accounts': [
            ('510003', 'COS - Parts'),
            ('510012', 'COS - Parts 12'),
            ('510013', 'COS - Parts 13'),
            ('510014', 'COS - Parts 14'),
            ('510015', 'COS - Parts 15'),
            ('521003', 'COS - FREIGHT - Parts'),
            ('522001', 'COS - LABOR - Parts'),
            ('524000', 'COS - SHOP SUPPLIES'),
            ('529002', 'COS - PM CONTRACT'),
            ('530000', 'COS - FULL MAINT CONTRACT'),
            ('533000', 'COS - SERVICE OTHER'),
            ('534003', 'COS - TRUCKING/DELIVERY - Parts'),
            ('536002', 'COS - MISC - Parts'),
            ('542000', 'COS - OTHER'),
            ('543000', 'COS - DEPRECIATION'),
            ('544000', 'COS - OTHER 2'),
        ]
    },
    'service': {
        'dept_code': 40,
        'dept_name': 'Service',
        'tab_name': 'P&L Service',
        'sales_accounts': [
            ('410004', 'SALES - Service'),
            ('410005', 'SALES - Service 5'),
            ('410007', 'SALES - Service 7'),
            ('410016', 'SALES - Service 16'),
            ('421004', 'SALES - FREIGHT - Service'),
            ('421005', 'SALES - FREIGHT - Service 5'),
            ('421006', 'SALES - FREIGHT - Service 6'),
            ('421007', 'SALES - FREIGHT - Service 7'),
            ('423000', 'SALES - LABOR'),
            ('425000', 'SALES - SUBLET'),
            ('428000', 'SALES - SHOP SUPPLIES'),
            ('429002', 'SALES - PM CONTRACT'),
            ('432000', 'SALES - FULL MAINT CONTRACT'),
            ('435000', 'SALES - SERVICE OTHER'),
            ('435001', 'SALES - SERVICE OTHER 1'),
            ('435002', 'SALES - SERVICE OTHER 2'),
            ('435003', 'SALES - SERVICE OTHER 3'),
            ('435004', 'SALES - SERVICE OTHER 4'),
            ('422100', 'SALES INT. LABOR GM'),
        ],
        'cos_accounts': [
            ('510004', 'COS - Service'),
            ('510005', 'COS - Service 5'),
            ('510007', 'COS - Service 7'),
            ('512001', 'COS - ALLIED'),
            ('521004', 'COS - FREIGHT - Service'),
            ('521005', 'COS - FREIGHT - Service 5'),
            ('521006', 'COS - FREIGHT - Service 6'),
            ('521007', 'COS - FREIGHT - Service 7'),
            ('522000', 'COS - LABOR'),
            ('523000', 'COS - LABOR 2'),
            ('528000', 'COS - SHOP SUPPLIES'),
            ('529001', 'COS - PM CONTRACT'),
            ('534015', 'COS - TRUCKING/DELIVERY - Service'),
            ('535001', 'COS - SERVICE OTHER 1'),
            ('535002', 'COS - SERVICE OTHER 2'),
            ('535003', 'COS - SERVICE OTHER 3'),
            ('535004', 'COS - SERVICE OTHER 4'),
            ('535005', 'COS - SERVICE OTHER 5'),
            ('522100', 'COS INT. LABOR GM'),
            ('527000', 'COS OPER AWARENESS TRNG'),
            ('532000', 'COS SUBLET LABOR'),
            ('534011', 'COS TRUCKING/DELIVERY G&A'),
        ]
    },
    'rental': {
        'dept_code': 60,
        'dept_name': 'Rental',
        'tab_name': 'P&L Rental',
        'sales_accounts': [
            ('410008', 'SALES - Rental'),
            ('411001', 'SALES - ABUSE - Rental'),
            ('419000', 'SALES - EQ. DISPOSAL RENTAL'),
            # Removed: ('420000', 'SALES - EXPENSE RECAPTURE') - no longer used
            ('421000', 'SALES - FREIGHT - Rental'),
            ('434012', 'SALES - TRUCKING/DELIVERY - Rental'),
        ],
        'cos_accounts': [
            ('510008', 'COS - Rental'),
            ('511001', 'COS - ABUSE - Rental'),
            ('519000', 'COS - EQ. DISPOSAL RENTAL'),
            # Removed: ('520000', 'COS - EXPENSE RECAPTURE') - no longer used
            ('521008', 'COS - FREIGHT - Rental'),
            ('534014', 'COS - TRUCKING/DELIVERY - Rental'),
            ('537001', 'COS - DEPRECIATION - Rental'),
            # Removed: ('539000', 'COS - RENTAL INTEREST') - no longer used
            ('545000', 'COS - OUTSIDE(RTR) Rental'),
            ('541000', 'COS RENTAL INTERNAL MAINTENANCE'),
        ]
    },
    'transportation': {
        'dept_code': 80,
        'dept_name': 'Transportation',
        'tab_name': 'P&L Transportation',
        'sales_accounts': [
            ('410010', 'SALES - Transportation'),
            ('421010', 'SALES - FREIGHT - Transportation'),
            ('434010', 'SALES - TRUCKING/DELIVERY - Transportation'),
            ('434013', 'SALES - TRUCKING/DELIVERY - Transportation 2'),
        ],
        'cos_accounts': [
            ('510010', 'COS - Transportation'),
            ('521010', 'COS - FREIGHT - Transportation'),
            ('534010', 'COS - TRUCKING/DELIVERY - Transportation'),
            ('534012', 'COS - TRUCKING/DELIVERY - Transportation 2'),
        ]
    },
    'in_house': {
        'dept_code': 90,
        'dept_name': 'In House / Administrative',
        'tab_name': 'P&L In House',
        'sales_accounts': [
            ('410011', 'Sales - Administrative'),
            ('421011', 'SALES - FREIGHT - Administrative'),
            ('427000', 'SALES - OPERATOR AWARENESS TRAINING'),
            ('434011', 'SALES - TRUCKING/DELIVERY - Administrative'),
        ],
        'cos_accounts': [
            ('510011', 'COS - Administrative'),
            ('521011', 'COS - FREIGHT - Administrative'),
            ('525000', 'COS - INTERNAL'),
            ('540000', 'COS - ADMINISTRATIVE'),
        ]
    }
}

# Overhead Expense Accounts (for Administrative/In House tab)
# These match the EXPENSE_ACCOUNTS in pl_report.py EXACTLY
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
        ('603501', 'SERVICE TOOLS'),
        ('603700', 'TRAINING'),
        ('603800', 'TRAVEL'),
        ('603900', 'UNIFORMS'),
        ('650000', 'OTHER EXPENSE'),
        ('706000', 'ADMINISTRATIVE FUND EXPENSE'),
    ],
    'interest_finance': [
        ('601800', 'INTEREST'),
    ]
}

# Other Income Accounts - matches OTHER_INCOME_ACCOUNTS in pl_report.py
OTHER_INCOME_EXPENSE_ACCOUNTS = {
    'other_income': [
        ('701000', 'GAIN/LOSS ON SALE OF ASSET'),
        ('702000', 'MISCELLANEOUS INCOME'),
        ('703000', 'A/R DISCOUNTS ALLOWED'),
        ('704000', 'A/P DISCOUNTS TAKEN'),
        ('705000', 'PARTS DISCOUNTS'),
    ],
    'other_expense': [
        ('601400', 'FEDERAL INCOME TAX'),
        ('602500', 'OTHER TAXES'),
        ('603400', 'STATE INCOME TAXES'),
        ('604200', 'WARRANTY'),
        ('999999', 'ERROR ACCOUNT'),
    ],
}

# Helper functions
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
