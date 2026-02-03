# GL Account Mappings for Industrial Parts and Service (IPS)
# Schema: ind004
# Account format: 7-digit (e.g., 4110501)

GL_ACCOUNTS_IPS = {
    'new_equipment': {
        'dept_code': 10,
        'dept_name': 'New Equipment',
        'revenue': [
            '4110501', '4110502', '4110503', '4110504',  # New Equipment Linde
            '4111501', '4111502', '4111503', '4111504',  # Commission-New Equipment
            '4112501', '4112502', '4112503', '4112504',  # Freight Income
            '4113501', '4113502', '4113503', '4113504',  # New Equipment Combi
            '4115501', '4115502',  # New Equipment Other
        ],
        'cogs': [
            '5110501', '5110502', '5110503', '5110504',  # New Equip Linde
            '5113501', '5113502', '5113503', '5113504',  # New Equip Combi
            '5115501', '5115502',  # New Equip Other
            '5152501', '5152502', '5152503', '5152504',  # Internal Delivery Charge
            '5192501', '5192502', '5192503', '5192504',  # Internal Rental
            '5950501', '5950502', '5950503', '5950504',  # P/L Make Ready
            '5951501', '5951502', '5951503', '5951504',  # P/L IPSCO/Alside
            '5953501', '5953502', '5953503', '5953504',  # Sales Discount
            '5956501', '5956502', '5956503', '5956504',  # CGS Demo
        ]
    },
    'used_equipment': {
        'dept_code': 30,
        'dept_name': 'Used Equipment',
        'revenue': [
            '4111401', '4111402', '4111403', '4111404',  # Commission-Used Equipment
            '4143401', '4143402',  # Delivery Charge Used
            '4210401', '4210402',  # Used Equipment Sale-Linde
            '4211401', '4211402',  # Used Equipment Wholesale
            '4212401', '4212402',  # Used Rental Equipment Sale
            '4213401', '4213402',  # Used Equipment Sale Combi
            '4214401', '4214402',  # Used Equipment Sale-Other
        ],
        'cogs': [
            '5152401', '5152402',  # Internal Delivery Charge-Used
            '5192401', '5192402',  # Internal Rental to Used
            '5210401', '5210402',  # Used Equipment-Linde
            '5211401', '5211402',  # Used Equipment-Wholesale
            '5212401', '5212402',  # Rental Fleet Sales
            '5213401', '5213402',  # Used Equipment-Combi
            '5214401', '5214402',  # Used Equipment-Other
            '5410401', '5410402',  # Local Warranty
            '5940401', '5940402',  # P/L Used
            '5956401', '5956402',  # CGS Used Truck Demo
        ]
    },
    'parts': {
        'dept_code': 50,
        'dept_name': 'Parts',
        'revenue': [
            '4036503',  # Parts Sales to CH Steel
            '4125601', '4125602',  # Linde Parts Sale
            '4126601', '4126602',  # Combi Parts Sale
            '4127601', '4127602',  # Tire Sale
            '4128601', '4128602',  # Freight - Parts
            '4129601', '4129602',  # Parts Sale Other
            '4146601',  # TVH Parts Sale
            '4300601', '4300602',  # Internal Parts Sales-Service
            '4306201',  # Parts Sales to Alside Lease
            '4306401', '4306402',  # Parts Sales to Used
            '4306501', '4306502', '4306503', '4306504',  # Parts Sales to New
            '4306601', '4306602',  # Parts Sales to Parts
            '4306701', '4306702',  # Parts Sales to Service
            '4306901', '4306902',  # Parts Sales to Rental
        ],
        'cogs': [
            '5125601', '5125602',  # Parts-Linde
            '5126601', '5126602',  # Parts-Combi
            '5127601', '5127602',  # Tires
            '5129601', '5129602',  # Parts-Other
            '5146601',  # Parts-TVH
            '5300601', '5300602',  # Internal Parts
            '5306601', '5306602',  # Parts Obsolescence
            '5960601', '5960602',  # Internal Labor to Parts
        ]
    },
    'service': {
        'dept_code': 40,
        'dept_name': 'Service',
        'revenue': [
            # Road Parts
            '4133601', '4133602',  # Road Parts-Linde
            '4134601', '4134602',  # Road Parts-Combi
            '4135601', '4135602',  # Road Parts-Other
            '4144601',  # Road Parts-TVH
            # PM
            '4136602', '4137601', '4137602', '4138602', '4147601',  # PM accounts
            # Labor
            '4151701', '4151702',  # Field Labor
            '4152701', '4152702',  # Internal Pickup/Delivery
            '4153701', '4153702',  # Field Labor Variance
            '4154701', '4154702',  # Shop Labor Variance
            '4155702',  # Shop Labor
            '4156701', '4156702',  # Service Training
            '4157702',  # Customer PM
            '4158701', '4158702',  # Shop Supplies
            '4160701', '4160702',  # Lease Maintenance
            '4171701', '4171702',  # Customer Pickup/Delivery
            '4173701', '4173702',  # Freight Recovery
            # Internal/Nonbillable
            '4311701', '4311702',  # Nonbillable Field Time
            '4320701',  # Internal Labor-AMI Lease Prep
            '4322701', '4322702',  # Nonbillable Shop Time
            '4340701', '4340702',  # Internal Labor-Used
            '4350701', '4350702',  # Internal Labor-Sales
            '4360701', '4360702',  # Internal Labor-Parts
            '4370701', '4370702',  # Internal Labor-Service
            '4380701', '4380702',  # Internal Labor-Building
            '4390701', '4390702',  # Internal Labor-Rental
            '4400701', '4400702',  # Warranty-Customer
            '4410701', '4410702',  # Warranty-Internal
            # Shop Parts (Dept 45)
            '4130601', '4130602',  # Shop Parts-Linde
            '4131601', '4131602',  # Shop Parts-Combi
            '4132601', '4132602',  # Shop Parts-Other
            '4141601',  # Shop Parts-TVH
            '4155701',  # Shop Labor
            # PM Parts (Dept 47)
            '4136601', '4138601', '4157701',  # PM Parts/Labor
        ],
        'cogs': [
            # Road Parts
            '5133601', '5133602',  # Road Parts-Linde
            '5134601', '5134602',  # Road Parts-Combi
            '5135601', '5135602',  # Road Parts-Other
            '5144601',  # Road Parts-TVH
            # PM
            '5136602', '5137601', '5137602', '5138602', '5147601',  # PM accounts
            # Labor
            '5151701', '5151702',  # CGS Customer Road Labor
            '5152701', '5152702',  # Lease Maintenance
            '5155702',  # CGS Customer Shop Labor
            '5156701', '5156702',  # CGS Service Training Labor
            '5157702',  # CGS Customer PM Labor
            '5159701', '5159702',  # Rework
            '5175701', '5175702',  # Van Maintenance
            '5192701', '5192702',  # Internal Rental to Service
            '5200701', '5200702',  # Service Material
            '5220701', '5220702',  # CGS Labor Internal Labor
            '5311701', '5311702',  # Nonbillable Field Time
            '5322701', '5322702',  # Nonbillable Shop Time
            '5400701', '5400702',  # CGS Warranty
            '5970701', '5970702',  # P/L Service to Service
            '5980701', '5980702',  # Building Maintenance
            # Shop Parts (Dept 45)
            '5130601', '5130602',  # Shop Parts-Linde
            '5131601', '5131602',  # Shop Parts-Combi
            '5132601', '5132602',  # Shop Parts-Other
            '5141601',  # Shop Parts-TVH
            '5155701',  # CGS Customer Shop Labor
            # PM Parts (Dept 47)
            '5136601', '5138601', '5157701',  # PM Parts/Labor
        ]
    },
    'rental': {
        'dept_code': 60,
        'dept_name': 'Rental',
        'revenue': [
            '4191901', '4191902',  # Rental Income - Customer
            '4192901', '4192902',  # Rental Income - Internal
            '4193901', '4193902',  # Rental Delivery Income
        ],
        'cogs': [
            '5152901', '5152902',  # Internal Delivery Charge-Rental
            '5371901', '5371902',  # Rental Material
            '5990901', '5990902',  # P/L Rental
        ]
    },
    'allied': {
        'dept_code': 20,
        'dept_name': 'Allied Sales',
        'revenue': [
            '4112001', '4112002', '4112203', '4112204',  # Commission-Allied
            '4140501',  # Allied Lines Canton
            '4140502', '4140503', '4140504',  # Allied Lines (in dept 10 but allied category)
        ],
        'cogs': [
            '5140501', '5140502', '5140503', '5140504',  # Allied Line
            '5152201',  # Internal Delivery Charge-I F
            '5192201',  # Internal Rental to Alside
            '5935201',  # Sales Discount I F
            '5950201',  # P/L Make Ready - Alside
            '5951201',  # P/L Alside Trucks
            '5956201',  # CGS Demo
        ]
    },
    'lease': {
        'dept_code': 70,
        'dept_name': 'Lease',
        'revenue': [
            '4114501',  # IPSCO Lease Billing
            '4114502', '4114503',  # New Alside Sale
        ],
        'cogs': []
    },
    'demo': {
        'dept_code': 74,
        'dept_name': 'Demo Equipment',
        'revenue': [
            '4115401', '4115402',  # Demo Equipment Linde
        ],
        'cogs': [
            '5115401', '5115402',  # Demo Equip Linde
        ]
    },
    'ami': {
        'dept_code': 75,
        'dept_name': 'AMI/Alside',
        'revenue': [
            '4112201',  # AMI Freight Income
            '4114201',  # AMI Lease Sales
            '4215401',  # AMI Used Equipment Sale
        ],
        'cogs': [
            '5215401',  # AMI Used Equipment
            '5950401',  # AMI Used Equipment-Prep
        ]
    },
    'miscellaneous': {
        'dept_code': 80,
        'dept_name': 'Miscellaneous',
        'revenue': [
            '4181801',  # Miscellaneous Income
            '4181811',  # Officer Revenue
            '4182801',  # Interest Income
            '4183801',  # Cash Discounts Earned
            '4184801',  # Gain or Loss on Sale of F.A.
        ],
        'cogs': []
    }
}

# Other Income accounts for IPS (similar to Bennett's 7xxxxx series)
OTHER_INCOME_ACCOUNTS_IPS = [
    '4181801',  # Miscellaneous Income
    '4182801',  # Interest Income
    '4183801',  # Cash Discounts Earned
]


def get_all_revenue_accounts():
    """Get all revenue accounts for IPS"""
    accounts = []
    for dept in GL_ACCOUNTS_IPS.values():
        accounts.extend(dept['revenue'])
    return accounts


def get_all_cogs_accounts():
    """Get all COGS accounts for IPS"""
    accounts = []
    for dept in GL_ACCOUNTS_IPS.values():
        accounts.extend(dept['cogs'])
    return accounts
