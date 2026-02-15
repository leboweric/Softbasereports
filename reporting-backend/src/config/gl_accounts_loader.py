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

# ============================================================
# CURRIE FINANCIAL MODEL MAPPINGS
# Maps Currie report categories to tenant-specific GL accounts
# ============================================================

CURRIE_MAPPINGS_BENNETT = {
    # --- NEW EQUIPMENT SALES ---
    'new_equipment': {
        'new_lift_truck_primary': {
            'revenue': ['413001'],
            'cogs': ['513001']
        },
        'new_lift_truck_other': {
            'revenue': ['426001'],
            'cogs': ['526001']
        },
        'new_allied': {
            'revenue': ['412001'],
            'cogs': ['512001']
        },
        'batteries': {
            'revenue': ['414001'],
            'cogs': ['514001']
        },
        'other_new_equipment': {
            'revenue': [],
            'cogs': []
        },
        'operator_training': {
            'revenue': [],
            'cogs': []
        },
        'ecommerce': {
            'revenue': [],
            'cogs': []
        },
        'systems': {
            'revenue': [],
            'cogs': []
        },
    },
    'used_equipment': {
        'revenue': ['412002', '413002', '414002', '426002', '431002', '410002'],
        'cogs': ['512002', '513002', '514002', '526002', '531002', '510002']
    },

    # --- RENTAL ---
    'rental': {
        'revenue': ['411001', '419000', '420000', '421000', '434012', '410008'],
        'cogs': ['510008', '511001', '519000', '520000', '521008', '537001', '539000', '534014', '545000']
    },

    # --- SERVICE ---
    'service': {
        'customer_labor': {
            'revenue': ['410004', '410005', '410007'],
            'cogs': ['510004', '510005', '510007']
        },
        'internal_labor': {
            'revenue': ['423000', '425000'],
            'cogs': ['523000']
        },
        'warranty_labor': {
            'revenue': ['435000', '435001', '435002', '435003', '435004'],
            'cogs': ['535001', '535002', '535003', '535004', '535005']
        },
        'sublet': {
            'revenue': ['432000'],
            'cogs': ['532000']
        },
        'other': {
            'revenue': ['428000', '429002'],
            'cogs': ['528000', '529001']
        }
    },

    # --- PARTS ---
    # Parts uses the main GL_ACCOUNTS loader (already tenant-aware)
    # These are the Currie sub-category mappings for Bennett
    'parts': {
        'counter_primary': {
            'revenue': ['410003', '424000', '429001', '430000', '433000', '434003', '436002', '439000'],
            'cogs': ['510003', '522001', '524000', '529002', '530000', '533000', '534003', '536002', '542000']
        },
        'counter_other': {
            'revenue': [],
            'cogs': []
        },
        'ro_primary': {
            'revenue': ['410012'],
            'cogs': ['510012', '510013']
        },
        'ro_other': {
            'revenue': [],
            'cogs': []
        },
        'internal': {
            'revenue': ['410015'],
            'cogs': ['510015']
        },
        'warranty': {
            'revenue': ['410014'],
            'cogs': ['510014']
        },
        'ecommerce_parts': {
            'revenue': [],
            'cogs': []
        },
        'other_parts': {
            'revenue': [],
            'cogs': ['543000', '544000']
        }
    },

    # --- TRUCKING ---
    'trucking': {
        'revenue': ['410010', '421010', '434001', '434002', '434003', '434010', '434011', '434012', '434013'],
        'cogs': ['510010', '521010', '534001', '534002', '534003', '534010', '534011', '534012', '534013', '534014', '534015']
    },

    # --- EXPENSES ---
    'expenses': {
        'personnel': {
            'accounts': ['602600', '601100', '601500', '602700', '602701', '600400'],
            'detail': {
                'payroll': ['602600'],
                'payroll_taxes': ['601100'],
                'benefits': ['601500', '602700', '602701'],
                'commissions': ['600400']
            }
        },
        'occupancy': {
            'accounts': ['600200', '600201', '600300', '604000', '601700', '600900'],
            'detail': {
                'rent': ['600200', '600201'],
                'utilities': ['604000'],
                'insurance': ['601700'],
                'building_maintenance': ['600300'],
                'depreciation': ['600900']
            }
        },
        'operating': {
            'accounts': ['600000', '600500', '601000', '601200', '601300', '602100', '602200',
                         '602400', '602900', '603000', '603300', '603500', '603501', '603600',
                         '603700', '603800', '603900', '604100'],
            'detail': {
                'advertising': ['600000'],
                'computer_it': ['600500', '601300'],
                'supplies': ['603500', '603501', '602400'],
                'telephone': ['603600'],
                'training': ['603700'],
                'travel': ['603800'],
                'vehicle_expense': ['604100'],
                'professional_services': ['603000'],
                'other': ['601000', '601200', '602900', '603300', '603900', '602100', '602200']
            }
        }
    },

    # --- OTHER INCOME & INTEREST ---
    'other_income_interest': {
        'other_expenses': ['601400', '602500', '603400', '604200', '999999'],
        'interest_expense': ['601800'],
        'fi_income': ['440000']
    },

    # --- RENTAL FLEET BALANCE SHEET ACCOUNTS ---
    'rental_fleet_bs': {
        'gross_equipment': '183000',
        'accumulated_depreciation': '193000'
    },

    # --- BALANCE SHEET CATEGORIZATION ---
    # Account number prefix rules for categorizing BS accounts
    # Bennett uses 6-digit accounts: 1xxxxx=Assets, 2xxxxx=Liabilities, 3xxxxx=Equity
    'balance_sheet_categories': {
        'assets': {
            'cash': ['11'],                    # 110xxx-119xxx
            'accounts_receivable': ['12'],      # 120xxx-129xxx
            'inventory': ['13'],                # 130xxx-139xxx
            'other_current': ['14', '15'],      # 140xxx-159xxx (prepaid, other current)
            'fixed_assets': ['18', '19'],       # 180xxx-199xxx (fixed assets + accum depreciation)
        },
        'liabilities': {
            'current': ['21', '22', '23', '24'],  # 210xxx-249xxx
            'long_term': ['25', '26'],             # 250xxx-269xxx
        },
        'equity': {
            'capital_stock': ['31'],             # 310xxx
            'distributions': ['33'],             # 330xxx
            'retained_earnings': ['34'],          # 340xxx
        }
    },
    # Description-based patterns for inventory sub-categorization
    'inventory_patterns': {
        'new_equipment_primary': ['NEW TRUCK'],
        'new_allied_inventory': ['NEW ALLIED'],
        'used_equipment_inventory': ['USED TRUCK'],
        'parts_inventory': ['PARTS'],
        'battery_inventory': ['BATTRY', 'BATTERY', 'CHARGER'],
        'wip': ['WORK-IN-PROCESS', 'WORK IN PROCESS'],
    },
    # Description-based patterns for liability sub-categorization
    'liability_patterns': {
        'current': {
            'ap_primary': ['ACCOUNTS PAYABLE', 'A/P TRADE'],
            'short_term_rental_finance': ['RENTAL FINANCE', 'FLOOR PLAN'],
            'used_equipment_financing': ['TRUCKS PURCHASED', 'USED EQUIPMENT'],
        },
        'long_term': {
            'long_term_notes': ['NOTES PAYABLE', 'SCALE BANK'],
            'loans_from_stockholders': ['STOCKHOLDER', 'SHAREHOLDER'],
            'lt_rental_fleet_financing': ['RENTAL', 'FLEET'],
        }
    },
    # Description-based patterns for fixed asset sub-categorization
    'fixed_asset_patterns': {
        'rental_fleet': ['RENTAL EQUIP', 'RENTAL EQUIPMENT'],
    },

    # --- SERVICE DEPARTMENT CODES (for WO queries) ---
    'service_dept_codes': [4, 5, 6, 7, 8],

    # --- DEPARTMENT EXPENSE ALLOCATIONS (Currie model) ---
    'dept_allocations': {
        'new': 0.47517,
        'used': 0.03209,
        'rental': 0.20694,
        'parts': 0.13121,
        'service': 0.14953,
        'trucking': 0.00507
    }
}

# IPS Currie Mappings - Fully populated for Currie Financial Model reporting
# Account format: 7-digit (e.g., 4110501)
# Mapping logic: IPS accounts → Currie standard categories
CURRIE_MAPPINGS_IPS = {
    # --- NEW EQUIPMENT SALES ---
    'new_equipment': {
        # Linde new equipment (primary brand)
        'new_lift_truck_primary': {
            'revenue': ['4110501', '4110502', '4110503', '4110504'],  # New Equipment Linde
            'cogs': ['5110501', '5110502', '5110503', '5110504']  # New Equip Linde
        },
        # Combi + Other new equipment
        'new_lift_truck_other': {
            'revenue': ['4113501', '4113502', '4113503', '4113504',  # New Equipment Combi
                        '4115501', '4115502'],  # New Equipment Other
            'cogs': ['5113501', '5113502', '5113503', '5113504',  # New Equip Combi
                     '5115501', '5115502']  # New Equip Other
        },
        # Allied lines (IPS has a dedicated allied department)
        # Also includes lease billing (dept 70) and AMI/Alside (dept 75) revenue
        'new_allied': {
            'revenue': ['4112001', '4112002', '4112203', '4112204',  # Commission-Allied
                        '4140501', '4140502', '4140503', '4140504',  # Allied Lines
                        # Lease dept (70) - IPSCO/Alside lease billing
                        '4114501',  # IPSCO Lease Billing
                        '4114502', '4114503',  # New Alside Sale
                        # AMI/Alside dept (75) - allied-related
                        '4112201',  # AMI Freight Income
                        '4114201'],  # AMI Lease Sales
            'cogs': ['5140501', '5140502', '5140503', '5140504',  # Allied Line
                     '5152201',  # Internal Delivery Charge-IF
                     '5192201',  # Internal Rental to Alside
                     '5935201',  # Sales Discount IF
                     '5950201',  # P/L Make Ready - Alside
                     '5951201',  # P/L Alside Trucks
                     '5956201']  # CGS Demo
        },
        # IPS doesn't separate batteries as a distinct category
        'batteries': {
            'revenue': [],
            'cogs': []
        },
        # Other new equipment items (commissions, freight, make-ready, demos)
        'other_new_equipment': {
            'revenue': ['4111501', '4111502', '4111503', '4111504',  # Commission-New Equipment
                        '4112501', '4112502', '4112503', '4112504'],  # Freight Income
            'cogs': ['5152501', '5152502', '5152503', '5152504',  # Internal Delivery Charge
                     '5192501', '5192502', '5192503', '5192504',  # Internal Rental
                     '5950501', '5950502', '5950503', '5950504',  # P/L Make Ready
                     '5951501', '5951502', '5951503', '5951504',  # P/L IPSCO/Alside
                     '5953501', '5953502', '5953503', '5953504',  # Sales Discount
                     '5956501', '5956502', '5956503', '5956504']  # CGS Demo
        },
        'operator_training': {
            'revenue': [],
            'cogs': []
        },
        'ecommerce': {
            'revenue': [],
            'cogs': []
        },
        'systems': {
            'revenue': [],
            'cogs': []
        },
    },

    # --- USED EQUIPMENT ---
    'used_equipment': {
        'revenue': ['4111401', '4111402', '4111403', '4111404',  # Commission-Used Equipment
                    '4143401', '4143402',  # Delivery Charge Used
                    '4210401', '4210402',  # Used Equipment Sale-Linde
                    '4211401', '4211402',  # Used Equipment Wholesale
                    '4212401', '4212402',  # Used Rental Equipment Sale
                    '4213401', '4213402',  # Used Equipment Sale Combi
                    '4214401', '4214402',  # Used Equipment Sale-Other
                    # Demo equipment sales (dept 74)
                    '4115401', '4115402',  # Demo Equipment Linde
                    # AMI/Alside used equipment (dept 75)
                    '4215401'],  # AMI Used Equipment Sale
        'cogs': ['5152401', '5152402',  # Internal Delivery Charge-Used
                 '5192401', '5192402',  # Internal Rental to Used
                 '5210401', '5210402',  # Used Equipment-Linde
                 '5211401', '5211402',  # Used Equipment-Wholesale
                 '5212401', '5212402',  # Rental Fleet Sales
                 '5213401', '5213402',  # Used Equipment-Combi
                 '5214401', '5214402',  # Used Equipment-Other
                 '5410401', '5410402',  # Local Warranty
                 '5940401', '5940402',  # P/L Used
                 '5956401', '5956402',  # CGS Used Truck Demo
                 # Demo equipment COGS (dept 74)
                 '5115401', '5115402',  # Demo Equip Linde
                 # AMI/Alside used equipment COGS (dept 75)
                 '5215401',  # AMI Used Equipment
                 '5950401']  # AMI Used Equipment-Prep
    },

    # --- RENTAL ---
    'rental': {
        'revenue': ['4191901', '4191902',  # Rental Income - Customer
                    '4192901', '4192902',  # Rental Income - Internal
                    '4193901', '4193902'],  # Rental Delivery Income
        'cogs': ['5152901', '5152902',  # Internal Delivery Charge-Rental
                 '5371901', '5371902',  # Depreciation - Rental
                 '5990901', '5990902']  # P/L Rental
    },

    # --- SERVICE ---
    'service': {
        # Customer labor = field labor + shop labor + customer PM + pickup/delivery
        'customer_labor': {
            'revenue': ['4151701', '4151702',  # Field Labor
                        '4153701', '4153702',  # Field Labor Variance
                        '4154701', '4154702',  # Shop Labor Variance
                        '4155701', '4155702',  # Shop Labor
                        '4157701', '4157702',  # Customer PM
                        '4171701', '4171702',  # Customer Pickup/Delivery
                        '4173701', '4173702',  # Freight Recovery
                        # Road Parts (sold through service)
                        '4133601', '4133602',  # Road Parts-Linde
                        '4134601', '4134602',  # Road Parts-Combi
                        '4135601', '4135602',  # Road Parts-Other
                        '4144601',  # Road Parts-TVH
                        # Shop Parts (sold through service)
                        '4130601', '4130602',  # Shop Parts-Linde
                        '4131601', '4131602',  # Shop Parts-Combi
                        '4132601', '4132602',  # Shop Parts-Other
                        '4141601',  # Shop Parts-TVH
                        # PM accounts
                        '4136601', '4136602',  # PM Parts
                        '4137601', '4137602',  # PM
                        '4138601', '4138602',  # PM
                        '4147601',  # PM-TVH
                        # Shop Supplies
                        '4158701', '4158702'],  # Shop Supplies
            'cogs': ['5151701', '5151702',  # CGS Customer Road Labor
                     '5152701', '5152702',  # Lease Maintenance
                     '5155701', '5155702',  # CGS Customer Shop Labor
                     '5157701', '5157702',  # CGS Customer PM Labor
                     '5175701', '5175702',  # Van Maintenance
                     '5200701', '5200702',  # Service Material
                     # Road Parts COGS
                     '5133601', '5133602',  # Road Parts-Linde
                     '5134601', '5134602',  # Road Parts-Combi
                     '5135601', '5135602',  # Road Parts-Other
                     '5144601',  # Road Parts-TVH
                     # Shop Parts COGS
                     '5130601', '5130602',  # Shop Parts-Linde
                     '5131601', '5131602',  # Shop Parts-Combi
                     '5132601', '5132602',  # Shop Parts-Other
                     '5141601',  # Shop Parts-TVH
                     # PM COGS
                     '5136601', '5136602',  # PM Parts
                     '5137601', '5137602',  # PM
                     '5138601', '5138602',  # PM
                     '5147601',  # PM-TVH
                     '5156701', '5156702']  # CGS Service Training Labor
        },
        # Internal labor = nonbillable time + internal labor allocations
        'internal_labor': {
            'revenue': ['4311701', '4311702',  # Nonbillable Field Time
                        '4320701',  # Internal Labor-AMI Lease Prep
                        '4322701', '4322702',  # Nonbillable Shop Time
                        '4340701', '4340702',  # Internal Labor-Used
                        '4350701', '4350702',  # Internal Labor-Sales
                        '4360701', '4360702',  # Internal Labor-Parts
                        '4370701', '4370702',  # Internal Labor-Service
                        '4380701', '4380702',  # Internal Labor-Building
                        '4390701', '4390702',  # Internal Labor-Rental
                        '4152701', '4152702',  # Internal Pickup/Delivery
                        '4160701', '4160702'],  # Lease Maintenance
            'cogs': ['5311701', '5311702',  # Nonbillable Field Time
                     '5322701', '5322702',  # Nonbillable Shop Time
                     '5220701', '5220702',  # CGS Labor Internal Labor
                     '5192701', '5192702',  # Internal Rental to Service
                     '5970701', '5970702',  # P/L Service to Service
                     '5980701', '5980702']  # Building Maintenance
        },
        # Warranty labor
        'warranty_labor': {
            'revenue': ['4400701', '4400702',  # Warranty-Customer
                        '4410701', '4410702'],  # Warranty-Internal
            'cogs': ['5400701', '5400702',  # CGS Warranty
                     '5159701', '5159702']  # Rework
        },
        # IPS doesn't have a separate sublet category
        'sublet': {
            'revenue': [],
            'cogs': []
        },
        # Other service (training)
        'other': {
            'revenue': ['4156701', '4156702'],  # Service Training
            'cogs': []
        }
    },

    # --- PARTS ---
    'parts': {
        # Counter parts = external customer parts sales (walk-in / over-the-counter)
        'counter_primary': {
            'revenue': ['4036503',  # Parts Sales to CH Steel
                        '4125601', '4125602',  # Linde Parts Sale
                        '4126601', '4126602',  # Combi Parts Sale
                        '4127601', '4127602',  # Tire Sale
                        '4129601', '4129602',  # Parts Sale Other
                        '4146601'],  # TVH Parts Sale
            'cogs': ['5125601', '5125602',  # Parts-Linde
                     '5126601', '5126602',  # Parts-Combi
                     '5127601', '5127602',  # Tires
                     '5129601', '5129602',  # Parts-Other
                     '5146601']  # Parts-TVH
        },
        'counter_other': {
            'revenue': [],
            'cogs': []
        },
        # RO parts = parts sold through service repair orders
        'ro_primary': {
            'revenue': ['4300601', '4300602',  # Internal Parts Sales-Service
                        '4306701', '4306702'],  # Parts Sales to Service
            'cogs': ['5300601', '5300602']  # Internal Parts
        },
        'ro_other': {
            'revenue': [],
            'cogs': []
        },
        # Internal parts = parts sold to other departments
        'internal': {
            'revenue': ['4128601', '4128602',  # Freight - Parts
                        '4306201',  # Parts Sales to Alside Lease
                        '4306401', '4306402',  # Parts Sales to Used
                        '4306501', '4306502', '4306503', '4306504',  # Parts Sales to New
                        '4306601', '4306602',  # Parts Sales to Parts
                        '4306901', '4306902'],  # Parts Sales to Rental
            'cogs': ['5960601', '5960602']  # Internal Labor to Parts
        },
        # IPS warranty parts flow through service department
        'warranty': {
            'revenue': [],
            'cogs': []
        },
        'ecommerce_parts': {
            'revenue': [],
            'cogs': []
        },
        'other_parts': {
            'revenue': [],
            'cogs': ['5306601', '5306602']  # Parts Obsolescence
        }
    },

    # --- TRUCKING ---
    # IPS does not have a separate trucking department;
    # delivery charges are embedded in new/used equipment accounts
    'trucking': {
        'revenue': [],
        'cogs': []
    },

    # --- EXPENSES ---
    # Mapped from EXPENSE_ACCOUNTS_IPS into Currie's 3-category structure
    'expenses': {
        'personnel': {
            'accounts': [
                # Salaries & Wages
                '6840701', '6850501',
                '6880201', '6880501', '6880801', '6880901',
                # Commissions/Bonuses
                '6910201', '6910501', '6910503', '6910601',
                '6911801', '6911802',
                # Payroll Taxes
                '6530201',
                '6530501', '6530502', '6530503', '6530504',
                '6530601', '6530701', '6530801',
                # Employee Benefits
                '6210201',
                '6210501', '6210502', '6210503', '6210504',
                '6210601', '6210701', '6210702', '6210801',
                # Medical/Health
                '6470201', '6470401',
                '6470501', '6470502', '6470503', '6470504',
                '6470601', '6470701', '6470702',
                '6470901', '6470902',
            ],
            'detail': {
                'payroll': [
                    '6840701', '6850501',
                    '6880201', '6880501', '6880801', '6880901',
                ],
                'payroll_taxes': [
                    '6530201',
                    '6530501', '6530502', '6530503', '6530504',
                    '6530601', '6530701', '6530801',
                ],
                'benefits': [
                    '6210201',
                    '6210501', '6210502', '6210503', '6210504',
                    '6210601', '6210701', '6210702', '6210801',
                    '6470201', '6470401',
                    '6470501', '6470502', '6470503', '6470504',
                    '6470601', '6470701', '6470702',
                    '6470901', '6470902',
                ],
                'commissions': [
                    '6910201', '6910501', '6910503', '6910601',
                    '6911801', '6911802',
                ]
            }
        },
        'occupancy': {
            'accounts': [
                # Rent
                '6733401',
                '6733501', '6733502', '6733503', '6733504',
                '6733601', '6733701', '6733801', '6733901',
                # Property Tax
                '6555201', '6555501', '6555503',
                # Utilities/Janitorial
                '6430101', '6430201', '6430401',
                '6430501', '6430502', '6430503', '6430504',
                '6430601', '6430701', '6430801', '6430901',
                # Insurance
                '6410201',
                '6410501', '6410502', '6410503',
                '6410601', '6410701', '6410801',
                # Building Maintenance
                '6050201', '6050701', '6050801',
                # Depreciation
                '6100501', '6100503', '6100504',
                '6100701', '6100801',
            ],
            'detail': {
                'rent': [
                    '6733401',
                    '6733501', '6733502', '6733503', '6733504',
                    '6733601', '6733701', '6733801', '6733901',
                    '6555201', '6555501', '6555503',
                ],
                'utilities': [
                    '6430101', '6430201', '6430401',
                    '6430501', '6430502', '6430503', '6430504',
                    '6430601', '6430701', '6430801', '6430901',
                ],
                'insurance': [
                    '6410201',
                    '6410501', '6410502', '6410503',
                    '6410601', '6410701', '6410801',
                ],
                'building_maintenance': [
                    '6050201', '6050701', '6050801',
                ],
                'depreciation': [
                    '6100501', '6100503', '6100504',
                    '6100701', '6100801',
                ]
            }
        },
        'operating': {
            'accounts': [
                # Advertising/Marketing
                '6010701', '6010801',
                '6460201', '6460501', '6460502', '6460503',
                '6460601', '6460701', '6460801',
                # Computer/IT
                '6070201',
                '6070501', '6070502', '6070503', '6070504',
                '6070601', '6070701', '6070801',
                # Office Supplies
                '6510801',
                # Telephone
                '6920701', '6920702',
                # Vehicle/Equipment
                '6020501', '6020502', '6020503', '6020504',
                '6020601',
                '6310201', '6310401',
                '6310501', '6310502', '6310503', '6310504',
                '6310601', '6310701', '6310901',
                '6320801', '6320802',
                '6330801', '6330802',
                '6740801',
                '6820701', '6820801',
                # Professional Services
                '6540501', '6540502', '6540503',
                '6540601', '6540701', '6540801',
                # Outside Services
                '6520801',
                # Dues/Subscriptions
                '6110501', '6110502', '6110601', '6110701', '6110801',
                '6111401', '6111402',
                '6111501', '6111502', '6111503',
                '6112001', '6112002', '6112203', '6112204',
                # Other (bad debt, charitable, licenses, management fees, misc)
                '6030701',
                '6061001', '6061003', '6061601',
                '6440501', '6440502', '6440503',
                '6440701', '6440702', '6440801',
                '6450801',
                '6480501', '6480503', '6480701',
            ],
            'detail': {
                'advertising': [
                    '6010701', '6010801',
                    '6460201', '6460501', '6460502', '6460503',
                    '6460601', '6460701', '6460801',
                ],
                'computer_it': [
                    '6070201',
                    '6070501', '6070502', '6070503', '6070504',
                    '6070601', '6070701', '6070801',
                ],
                'supplies': [
                    '6510801',
                ],
                'telephone': [
                    '6920701', '6920702',
                ],
                'training': [],
                'travel': [],
                'vehicle_expense': [
                    '6020501', '6020502', '6020503', '6020504',
                    '6020601',
                    '6310201', '6310401',
                    '6310501', '6310502', '6310503', '6310504',
                    '6310601', '6310701', '6310901',
                    '6320801', '6320802',
                    '6330801', '6330802',
                    '6740801',
                    '6820701', '6820801',
                ],
                'professional_services': [
                    '6540501', '6540502', '6540503',
                    '6540601', '6540701', '6540801',
                    '6520801',
                ],
                'other': [
                    '6110501', '6110502', '6110601', '6110701', '6110801',
                    '6111401', '6111402',
                    '6111501', '6111502', '6111503',
                    '6112001', '6112002', '6112203', '6112204',
                    '6030701',
                    '6061001', '6061003', '6061601',
                    '6440501', '6440502', '6440503',
                    '6440701', '6440702', '6440801',
                    '6450801',
                    '6480501', '6480503', '6480701',
                ]
            }
        }
    },

    # --- OTHER INCOME & INTEREST ---
    'other_income_interest': {
        # IPS miscellaneous income accounts (from dept 80)
        'other_expenses': ['4184801'],  # Gain or Loss on Sale of F.A.
        'interest_expense': ['6420701', '6420702'],  # Interest Expense - Service
        'fi_income': ['4181801', '4181811', '4182801', '4183801']  # Misc Income, Officer Revenue, Interest Income, Cash Discounts
    },

    # --- RENTAL FLEET BALANCE SHEET ACCOUNTS ---
    # IPS uses 7-digit accounts; rental fleet assets are in the 18x/19x range
    # These are used with LIKE patterns (first 3 digits) for fleet value queries
    'rental_fleet_bs': {
        'gross_equipment': '1830901',  # Rental fleet gross value (prefix 183)
        'accumulated_depreciation': '1930901'  # Accumulated depreciation (prefix 193)
    },

    # --- BALANCE SHEET CATEGORIZATION ---
    # Account number prefix rules for IPS 7-digit accounts
    # IPS chart of accounts: 1xxxxxx=Assets, 2xxxxxx=Liabilities, 3xxxxxx=Equity
    'balance_sheet_categories': {
        'assets': {
            # Cash: 1010xxx (Money Market), 1011xxx (Checking) — more specific to avoid
            # catching AR-Other (1014), AR-Promler (1015), AR-Ed Jr (1016), AR-Mark (1017)
            'cash': ['1010', '1011'],
            # AR: 103xxxx (Trade, Employees) + 101[4-7]xxx (Other, Promler, Ed Jr, Mark)
            'accounts_receivable': ['103', '1014', '1015', '1016', '1017'],
            # Inventory: 111=New Equip, 112=Used, 114=Allied, 115=WIP
            'inventory': ['111', '112', '114', '115'],
            # Other Current: 1210xxx (Prepaid Expense), 1213xxx (Prepaid Income Tax), 1216xxx (Prepaid Interest)
            'other_current': ['1210', '1213', '1216'],
            # Fixed Assets: 1217-1219=Finance Leases, 122-126=Gross assets (F&F, Vehicles, Rental Fleet, Leasehold)
            # 151-156=Accumulated depreciation, 160=Clearing
            'fixed_assets': ['1217', '1218', '1219', '122', '123', '124', '125', '1260',
                             '151', '154', '155', '156', '160'],
        },
        # Other assets: anything starting with 1 not matching above (e.g. 1260401=Deposits, 1260402=Note-Ed Jr)
        'liabilities': {
            'current': ['204', '205', '207', '208', '209'],  # 204=ST Notes, 205=AP, 207-209=Accrued
            'long_term': ['202', '203'],                       # 202=Deferred Tax, 203=LT Notes/Leases
        },
        'equity': {
            'capital_stock': ['391'],               # 391xxxx (Common Stock, Treasury Stock)
            'distributions': ['392', '393'],         # 392xxxx (Officer Advance), 393xxxx (Dividends)
            'retained_earnings': ['394'],             # 394xxxx (YTD Net Income, Retained Earnings)
        }
    },
    # Description-based patterns for inventory sub-categorization
    'inventory_patterns': {
        'new_equipment_primary': ['NEW EQUIPMENT INVENTORY'],
        'new_allied_inventory': ['ALLIED LINES INVENTORY'],
        'used_equipment_inventory': ['USED EQUIPMENT INVENTORY', 'AMI USED EQUIPMENT'],
        'parts_inventory': ['PARTS INVENTORY'],
        'battery_inventory': ['BATTERY', 'CHARGER'],
        'wip': ['WORK IN PROGRESS'],
    },
    # Description-based patterns for liability sub-categorization
    'liability_patterns': {
        'current': {
            'ap_primary': ['ACCOUNTS PAYABLE TRADE', 'ACCOUNTS PAYABLE CREDIT'],
            'short_term_rental_finance': ['FLOORPLAN', 'S.T. FLOORPLAN'],
            'used_equipment_financing': [],  # IPS doesn't have separate used equip financing
        },
        'long_term': {
            # Order matters: check floorplan BEFORE general notes payable
            'lt_rental_fleet_financing': ['FLOORPLAN', 'L.T. FLOORPLAN'],
            'loans_from_stockholders': ['STOCKHOLDER', 'SHAREHOLDER'],
            'long_term_notes': ['NOTES PAYABLE L.T', 'NOTE PAYABLE MARK'],
        }
    },
    # Description-based patterns for fixed asset sub-categorization
    'fixed_asset_patterns': {
        'rental_fleet': ['RENTAL FLEET', 'AMI LEASE FLEET', 'IPS LEASE FLEET',
                         'ACCUM.DEPR.-RENTAL FLEET', 'ACCUM.DEPR.-AMI LEASE FLEET', 'ACCUM.DEPR.-IPS LEASE FLEET'],
    },

    # --- SERVICE DEPARTMENT CODES (for WO queries) ---
    # IPS service uses dept codes 40 (service), 45 (shop parts), 47 (PM parts)
    'service_dept_codes': [40, 45, 47],

    # --- DEPARTMENT EXPENSE ALLOCATIONS (Currie model) ---
    # IPS allocation percentages - estimated based on department revenue mix
    # These should be refined with actual IPS management input
    'dept_allocations': {
        'new': 0.30000,
        'used': 0.05000,
        'rental': 0.10000,
        'parts': 0.20000,
        'service': 0.30000,
        'trucking': 0.00000  # IPS has no trucking department
    }
}


# Mapping of schema to GL configuration
TENANT_GL_CONFIGS = {
    'ben002': {
        'gl_accounts': GL_ACCOUNTS_BENNETT,
        'other_income': OTHER_INCOME_ACCOUNTS_BENNETT,
        'expense_accounts': EXPENSE_ACCOUNTS_BENNETT,
        'currie_mappings': CURRIE_MAPPINGS_BENNETT,
    },
    'ind004': {
        'gl_accounts': GL_ACCOUNTS_IPS,
        'other_income': OTHER_INCOME_ACCOUNTS_IPS,
        'expense_accounts': EXPENSE_ACCOUNTS_IPS,
        'currie_mappings': CURRIE_MAPPINGS_IPS,
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


def get_currie_mappings(schema: str) -> dict:
    """
    Get the Currie Financial Model account mappings for a specific tenant schema.
    These mappings define how tenant-specific GL accounts map to Currie report categories.
    
    Args:
        schema: The tenant's database schema (e.g., 'ben002', 'ind004')
    
    Returns:
        Dictionary of Currie category mappings with tenant-specific GL accounts
    """
    config = TENANT_GL_CONFIGS.get(schema)
    if config is None:
        import logging
        logging.getLogger(__name__).warning(f"No Currie config for schema '{schema}' - falling back to ben002. Add this tenant to TENANT_GL_CONFIGS!")
        config = TENANT_GL_CONFIGS['ben002']
    return config['currie_mappings']
