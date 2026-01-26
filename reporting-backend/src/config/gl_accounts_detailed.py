# GL Account Configuration for Detailed P&L Export
# This file contains the GL account mappings for each department
# These MUST match the GL_ACCOUNTS in pl_report.py exactly

# Department Configuration - matches GL_ACCOUNTS in pl_report.py
DEPARTMENT_CONFIG = {
    'new_equipment': {
        'dept_code': 10,
        'dept_name': 'New Equipment',
        'tab_name': 'P&L New Equip',
        'sales_accounts': [
            ('412001', 'SALES - ALLIED - New Equip'),
            ('413001', 'SALES - LINDE - New Equip'),
            ('414001', 'SALES - BATTERY/CHARGERS - New Equip'),
            ('414002', 'SALES - BATTERY/CHARGERS 2 - New Equip'),
            ('415001', 'SALES - ATTACHMENTS - New Equip'),
            ('417001', 'SALES - OTHER - New Equip'),
            ('417003', 'SALES - OTHER 3 - New Equip'),
            ('434001', 'SALES - TRUCKING/DELIVERY - New Equip'),
        ],
        'cos_accounts': [
            ('512001', 'COS - ALLIED - New Equip'),
            ('513001', 'COS - LINDE - New Equip'),
            ('514001', 'COS - BATTERY/CHARGERS - New Equip'),
            ('514002', 'COS - BATTERY/CHARGERS 2 - New Equip'),
            ('515001', 'COS - ATTACHMENTS - New Equip'),
            ('517001', 'COS - OTHER - New Equip'),
            ('517003', 'COS - OTHER 3 - New Equip'),
            ('534001', 'COS - TRUCKING/DELIVERY - New Equip'),
            ('540001', 'COS - ADMINISTRATIVE - New Equip'),
            ('541001', 'COS - RENTAL INTERNAL - New Equip'),
        ]
    },
    'used_equipment': {
        'dept_code': 20,
        'dept_name': 'Used Equipment',
        'tab_name': 'P&L Used Equip',
        'sales_accounts': [
            ('412002', 'SALES - ALLIED - Used Equip'),
            ('413002', 'SALES - LINDE - Used Equip'),
            ('414003', 'SALES - BATTERY/CHARGERS - Used Equip'),
            ('415002', 'SALES - ATTACHMENTS - Used Equip'),
            ('417002', 'SALES - OTHER - Used Equip'),
            ('417004', 'SALES - OTHER 4 - Used Equip'),
            ('418000', 'SALES - WHOLESALE'),
            ('434002', 'SALES - TRUCKING/DELIVERY - Used Equip'),
            ('436000', 'SALES - MISC'),
        ],
        'cos_accounts': [
            ('512002', 'COS - ALLIED - Used Equip'),
            ('513002', 'COS - LINDE - Used Equip'),
            ('514003', 'COS - BATTERY/CHARGERS - Used Equip'),
            ('515002', 'COS - ATTACHMENTS - Used Equip'),
            ('517002', 'COS - OTHER - Used Equip'),
            ('517004', 'COS - OTHER 4 - Used Equip'),
            ('518000', 'COS - WHOLESALE'),
            ('534002', 'COS - TRUCKING/DELIVERY - Used Equip'),
            ('540002', 'COS - ADMINISTRATIVE - Used Equip'),
            ('541002', 'COS - RENTAL INTERNAL - Used Equip'),
        ]
    },
    'parts': {
        'dept_code': 30,
        'dept_name': 'Parts',
        'tab_name': 'P&L Parts',
        'sales_accounts': [
            ('410003', 'SALES - Parts'),
            ('410006', 'SALES - Parts 6'),
            ('410008', 'SALES - Parts 8'),
            ('410009', 'SALES - Parts 9'),
            ('410010', 'SALES - Parts 10'),
            ('410012', 'SALES - Parts 12'),
            ('410013', 'SALES - Parts 13'),
            ('410014', 'SALES - Parts 14'),
            ('410015', 'SALES - Parts 15'),
            ('421003', 'SALES - FREIGHT - Parts'),
            ('434003', 'SALES - TRUCKING/DELIVERY - Parts'),
            ('436003', 'SALES - MISC - Parts'),
        ],
        'cos_accounts': [
            ('510003', 'COS - Parts'),
            ('510006', 'COS - Parts 6'),
            ('510008', 'COS - Parts 8'),
            ('510009', 'COS - Parts 9'),
            ('510010', 'COS - Parts 10'),
            ('510012', 'COS - Parts 12'),
            ('510013', 'COS - Parts 13'),
            ('510014', 'COS - Parts 14'),
            ('510015', 'COS - Parts 15'),
            ('521003', 'COS - FREIGHT - Parts'),
            ('525003', 'COS - INTERNAL - Parts'),
            ('534003', 'COS - TRUCKING/DELIVERY - Parts'),
            ('536003', 'COS - MISC - Parts'),
            ('540003', 'COS - ADMINISTRATIVE - Parts'),
            ('541003', 'COS - RENTAL INTERNAL - Parts'),
            ('542003', 'COS - OTHER - Parts'),
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
        ],
        'cos_accounts': [
            ('510004', 'COS - Service'),
            ('510005', 'COS - Service 5'),
            ('510007', 'COS - Service 7'),
            ('510016', 'COS - Service 16'),
            ('521004', 'COS - FREIGHT - Service'),
            ('521005', 'COS - FREIGHT - Service 5'),
            ('521006', 'COS - FREIGHT - Service 6'),
            ('521007', 'COS - FREIGHT - Service 7'),
            ('523000', 'COS - LABOR'),
            ('525004', 'COS - INTERNAL - Service'),
            ('528000', 'COS - SHOP SUPPLIES'),
            ('529002', 'COS - PM CONTRACT'),
            ('534004', 'COS - TRUCKING/DELIVERY - Service'),
            ('535000', 'COS - SERVICE OTHER'),
            ('535001', 'COS - SERVICE OTHER 1'),
            ('535002', 'COS - SERVICE OTHER 2'),
            ('535003', 'COS - SERVICE OTHER 3'),
            ('535004', 'COS - SERVICE OTHER 4'),
        ]
    },
    'rental': {
        'dept_code': 60,
        'dept_name': 'Rental',
        'tab_name': 'P&L Rental',
        'sales_accounts': [
            ('410006R', 'SALES - Rental'),
            ('419000', 'SALES - RENTAL REVENUE'),
            ('419001', 'SALES - RENTAL REVENUE 1'),
            ('419002', 'SALES - RENTAL REVENUE 2'),
            ('421006R', 'SALES - FREIGHT - Rental'),
            ('434006', 'SALES - TRUCKING/DELIVERY - Rental'),
        ],
        'cos_accounts': [
            ('510006R', 'COS - Rental'),
            ('519000', 'COS - RENTAL'),
            ('519001', 'COS - RENTAL 1'),
            ('519002', 'COS - RENTAL 2'),
            ('521006R', 'COS - FREIGHT - Rental'),
            ('534006', 'COS - TRUCKING/DELIVERY - Rental'),
            ('540006', 'COS - ADMINISTRATIVE - Rental'),
            ('541006', 'COS - RENTAL INTERNAL - Rental'),
            ('542006', 'COS - OTHER - Rental'),
            ('543006', 'COS - DEPRECIATION - Rental'),
        ]
    },
    'transportation': {
        'dept_code': 80,
        'dept_name': 'Transportation',
        'tab_name': 'P&L Transportation',
        'sales_accounts': [
            ('410008T', 'SALES - Transportation'),
            ('421008', 'SALES - FREIGHT - Transportation'),
            ('434008', 'SALES - TRUCKING/DELIVERY - Transportation'),
            ('436008', 'SALES - MISC - Transportation'),
        ],
        'cos_accounts': [
            ('510008T', 'COS - Transportation'),
            ('521008', 'COS - FREIGHT - Transportation'),
            ('534008', 'COS - TRUCKING/DELIVERY - Transportation'),
            ('540008', 'COS - ADMINISTRATIVE - Transportation'),
        ]
    },
    'in_house': {
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
# Deployment trigger: Mon Jan 26 14:44:41 EST 2026
