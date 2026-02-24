/**
 * IPS Metric Definitions
 * 
 * Centralized source of truth for all GL accounts and calculation formulas
 * used by each metric/card across the IPS dashboards.
 * 
 * Structure:
 *   [metricKey]: {
 *     label: "Human-readable metric name",
 *     formula: "How the metric is calculated",
 *     accounts: ["GL account numbers"],
 *     source: "Department or data source"
 *   }
 * 
 * When accounts change in gl_accounts_loader.py or gl_accounts_detailed_ips.py,
 * update this file to keep tooltips accurate.
 */

// ============================================================
// NEW EQUIPMENT (Dept 10)
// ============================================================
const NEW_EQUIPMENT_REVENUE = [
  '4110501', '4110502', '4110503', '4110504',  // Sales - NE Linde
  '4111501', '4111502', '4111503', '4111504',  // Commission - NE
  '4112501', '4112502', '4112503', '4112504',  // Freight Income - NE
  '4113501', '4113502', '4113503', '4113504',  // Sales - NE Combi
  '4115501', '4115502',                         // Sales - NE Other
];

const NEW_EQUIPMENT_COGS = [
  '5110501', '5110502', '5110503', '5110504',  // COS - NE Linde
  '5113501', '5113502', '5113503', '5113504',  // COS - NE Combi
  '5115501', '5115502',                         // COS - NE Other
  '5152501', '5152502', '5152503', '5152504',  // COS - Internal Delivery
  '5192501', '5192502', '5192503', '5192504',  // COS - Internal Rental
  '5950501', '5950502', '5950503', '5950504',  // COS - P/L Make Ready
  '5951501', '5951502', '5951503', '5951504',  // COS - P/L IPSCO/Alside
  '5953501', '5953502', '5953503', '5953504',  // COS - Sales Discount
  '5956501', '5956502', '5956503', '5956504',  // COS - CGS Demo
];

// ============================================================
// ALLIED SALES (Dept 20)
// ============================================================
const ALLIED_REVENUE = [
  '4112001', '4112002', '4112203', '4112204',  // Commission - Allied
  '4140501', '4140502', '4140503', '4140504',  // Allied Lines
];

const ALLIED_COGS = [
  '5140501', '5140502', '5140503', '5140504',  // COS - Allied Line
  '5152201',                                     // COS - Internal Delivery
  '5192201',                                     // COS - Internal Rental
  '5935201',                                     // COS - Sales Discount
  '5950201',                                     // COS - P/L Make Ready
  '5951201',                                     // COS - P/L Alside Trucks
  '5956201',                                     // COS - CGS Demo
];

// ============================================================
// USED EQUIPMENT (Dept 30)
// ============================================================
const USED_EQUIPMENT_REVENUE = [
  '4111401', '4111402', '4111403', '4111404',  // Commission - Used
  '4143401', '4143402',                         // Delivery Charge Used
  '4210401', '4210402',                         // Used Sale - Linde
  '4211401', '4211402',                         // Used Wholesale
  '4212401', '4212402',                         // Used Rental Equipment Sale
  '4213401', '4213402',                         // Used Sale - Combi
  '4214401', '4214402',                         // Used Sale - Other
];

const USED_EQUIPMENT_COGS = [
  '5152401', '5152402',                         // COS - Internal Delivery
  '5192401', '5192402',                         // COS - Internal Rental
  '5210401', '5210402',                         // COS - Used Linde
  '5211401', '5211402',                         // COS - Used Wholesale
  '5212401', '5212402',                         // COS - Rental Fleet Sales
  '5213401', '5213402',                         // COS - Used Combi
  '5214401', '5214402',                         // COS - Used Other
  '5410401', '5410402',                         // COS - Local Warranty
  '5940401', '5940402',                         // COS - P/L Used
  '5956401', '5956402',                         // COS - CGS Used Demo
];

// ============================================================
// SERVICE (Dept 40 + Shop Parts Dept 45)
// ============================================================
const SERVICE_REVENUE = [
  // Road Parts
  '4133601', '4133602', '4134601', '4134602', '4135601', '4135602', '4144601',
  // PM
  '4136601', '4136602', '4137601', '4137602', '4138601', '4138602', '4147601',
  // Labor
  '4151701', '4151702', '4152701', '4152702', '4153701', '4153702',
  '4154701', '4154702', '4155701', '4155702', '4156701', '4156702',
  '4157701', '4157702', '4158701', '4158702', '4160701', '4160702',
  '4171701', '4171702', '4173701', '4173702',
  // Internal/Nonbillable
  '4311701', '4311702', '4320701', '4322701', '4322702',
  '4340701', '4340702', '4350701', '4350702', '4360701', '4360702',
  '4370701', '4370702', '4380701', '4380702', '4390701', '4390702',
  '4400701', '4400702', '4410701', '4410702',
  // Shop Parts (Dept 45)
  '4130601', '4130602', '4131601', '4131602', '4132601', '4132602', '4141601',
];

const SERVICE_COGS = [
  // Road Parts
  '5133601', '5133602', '5134601', '5134602', '5135601', '5135602', '5144601',
  // PM
  '5136601', '5136602', '5137601', '5137602', '5138601', '5138602', '5147601',
  // Labor
  '5151701', '5151702', '5152701', '5152702', '5155701', '5155702',
  '5156701', '5156702', '5157701', '5157702', '5159701', '5159702',
  '5175701', '5175702', '5192701', '5192702', '5200701', '5200702',
  '5220701', '5220702', '5311701', '5311702', '5322701', '5322702',
  '5400701', '5400702', '5970701', '5970702', '5980701', '5980702',
  // Shop Parts (Dept 45)
  '5130601', '5130602', '5131601', '5131602', '5132601', '5132602', '5141601',
];

// ============================================================
// PARTS (Dept 50)
// ============================================================
const PARTS_REVENUE = [
  '4036503',                                     // Parts Sales to CH Steel
  '4125601', '4125602',                         // Linde Parts Sale
  '4126601', '4126602',                         // Combi Parts Sale
  '4127601', '4127602',                         // Tire Sale
  '4128601', '4128602',                         // Freight - Parts
  '4129601', '4129602',                         // Parts Sale Other
  '4146601',                                     // TVH Parts Sale
  '4300601', '4300602',                         // Internal Parts Sales - Service
  '4306201',                                     // Parts Sales to Alside Lease
  '4306401', '4306402',                         // Parts Sales to Used
  '4306501', '4306502', '4306503', '4306504',  // Parts Sales to New
  '4306601', '4306602',                         // Parts Sales to Parts
  '4306701', '4306702',                         // Parts Sales to Service
  '4306901', '4306902',                         // Parts Sales to Rental
];

const PARTS_COGS = [
  '5125601', '5125602',                         // COS - Parts Linde
  '5126601', '5126602',                         // COS - Parts Combi
  '5127601', '5127602',                         // COS - Tires
  '5129601', '5129602',                         // COS - Parts Other
  '5146601',                                     // COS - Parts TVH
  '5300601', '5300602',                         // COS - Internal Parts
  '5306601', '5306602',                         // COS - Parts Obsolescence
  '5960601', '5960602',                         // COS - Internal Labor to Parts
];

// ============================================================
// RENTAL (Dept 60)
// ============================================================
const RENTAL_REVENUE = [
  '4191901', '4191902',  // Rental Income - Customer
  '4192901', '4192902',  // Rental Income - Internal
  '4193901', '4193902',  // Rental Delivery Income
];

const RENTAL_COGS = [
  '5152901', '5152902',  // COS - Internal Delivery Charge
  '5371901', '5371902',  // COS - Depreciation - Rental
  '5990901', '5990902',  // COS - P/L Rental
];

// ============================================================
// LEASE (Dept 70)
// ============================================================
const LEASE_REVENUE = [
  '4114501',  // IPSCO Lease Billing
  '4114502',  // New Alside Sale - Youngstown
  '4114503',  // New Alside Sale - Pittsburgh
];

// ============================================================
// DEMO (Dept 74)
// ============================================================
const DEMO_REVENUE = ['4115401', '4115402'];
const DEMO_COGS = ['5115401', '5115402'];

// ============================================================
// AMI/ALSIDE (Dept 75)
// ============================================================
const AMI_REVENUE = ['4112201', '4114201', '4215401'];
const AMI_COGS = ['5215401', '5950401'];

// ============================================================
// MISCELLANEOUS (Dept 80)
// ============================================================
const MISC_REVENUE = [
  '4181801',  // Miscellaneous Income
  '4181811',  // Officer Revenue
  '4182801',  // Interest Income
  '4183801',  // Cash Discounts Earned
  '4184801',  // Gain or Loss on Sale of F.A.
];

// ============================================================
// EXPENSE ACCOUNTS
// ============================================================
const EXPENSE_DEPRECIATION = ['6100501', '6100503', '6100504', '6100701', '6100801'];

const EXPENSE_SALARIES = [
  '6840701', '6850501', '6880201', '6880501', '6880801', '6880901',
  '6910201', '6910501', '6910503', '6910601', '6911801', '6911802',
];

const EXPENSE_PAYROLL_BENEFITS = [
  '6210201', '6210501', '6210502', '6210503', '6210504', '6210601',
  '6210701', '6210702', '6210801',
  '6470201', '6470401', '6470501', '6470502', '6470503', '6470504',
  '6470601', '6470701', '6470702', '6470901', '6470902',
  '6530201', '6530501', '6530502', '6530503', '6530504',
  '6530601', '6530701', '6530801',
];

const EXPENSE_RENT = [
  '6733401', '6733501', '6733502', '6733503', '6733504',
  '6733601', '6733701', '6733801', '6733901',
  '6555201', '6555501', '6555503',
];

const EXPENSE_UTILITIES = [
  '6430101', '6430201', '6430401', '6430501', '6430502', '6430503', '6430504',
  '6430601', '6430701', '6430801', '6430901',
];

const EXPENSE_INSURANCE = [
  '6410201', '6410501', '6410502', '6410503', '6410601', '6410701', '6410801',
];

const EXPENSE_MARKETING = [
  '6010701', '6010801',
  '6460201', '6460501', '6460502', '6460503', '6460601', '6460701', '6460801',
];

const EXPENSE_PROFESSIONAL = [
  '6540501', '6540502', '6540503', '6540601', '6540701', '6540801',
];

const EXPENSE_OFFICE = [
  '6050201', '6050701', '6050801',
  '6070201', '6070501', '6070502', '6070503', '6070504', '6070601', '6070701', '6070801',
  '6110501', '6110502', '6110601', '6110701', '6110801',
  '6111401', '6111402', '6111501', '6111502', '6111503',
  '6112001', '6112002', '6112203', '6112204',
  '6510801', '6520801', '6920701', '6920702',
];

const EXPENSE_VEHICLE = [
  '6020501', '6020502', '6020503', '6020504', '6020601',
  '6310201', '6310401', '6310501', '6310502', '6310503', '6310504',
  '6310601', '6310701', '6310901',
  '6320801', '6320802', '6330801', '6330802',
  '6740801', '6820701', '6820801',
];

const EXPENSE_OTHER = [
  '6030701', '6061001', '6061003', '6061601',
  '6440501', '6440502', '6440503', '6440701', '6440702', '6440801',
  '6450801', '6480501', '6480503', '6480701',
];

const EXPENSE_INTEREST = ['6420701', '6420702'];

const ALL_EXPENSES = [
  ...EXPENSE_DEPRECIATION, ...EXPENSE_SALARIES, ...EXPENSE_PAYROLL_BENEFITS,
  ...EXPENSE_RENT, ...EXPENSE_UTILITIES, ...EXPENSE_INSURANCE,
  ...EXPENSE_MARKETING, ...EXPENSE_PROFESSIONAL, ...EXPENSE_OFFICE,
  ...EXPENSE_VEHICLE, ...EXPENSE_OTHER, ...EXPENSE_INTEREST,
];

const ALL_REVENUE = [
  ...NEW_EQUIPMENT_REVENUE, ...ALLIED_REVENUE, ...USED_EQUIPMENT_REVENUE,
  ...SERVICE_REVENUE, ...PARTS_REVENUE, ...RENTAL_REVENUE,
  ...LEASE_REVENUE, ...DEMO_REVENUE, ...AMI_REVENUE, ...MISC_REVENUE,
];

const ALL_COGS = [
  ...NEW_EQUIPMENT_COGS, ...ALLIED_COGS, ...USED_EQUIPMENT_COGS,
  ...SERVICE_COGS, ...PARTS_COGS, ...RENTAL_COGS,
  ...DEMO_COGS, ...AMI_COGS,
];

// ============================================================
// OTHER INCOME
// ============================================================
const OTHER_INCOME = ['4181801', '4182801', '4183801'];


// ============================================================
// METRIC DEFINITIONS
// ============================================================
export const IPS_METRICS = {

  // ---- ED'S DASHBOARD / SALES GP REPORT ----
  eds_total_revenue: {
    label: "Total Revenue",
    formula: "Sum of all revenue (4xxxx) accounts across all departments and branches",
    accounts: ALL_REVENUE,
  },
  eds_total_cogs: {
    label: "Total COGS",
    formula: "Sum of all cost of sales (5xxxx) accounts across all departments and branches",
    accounts: ALL_COGS,
  },
  eds_gross_profit: {
    label: "Gross Profit",
    formula: "Total Revenue − Total COGS",
    accounts: [...ALL_REVENUE, ...ALL_COGS],
  },
  eds_gp_pct: {
    label: "GP %",
    formula: "Gross Profit ÷ Total Revenue × 100 (departmental margin, not contribution %)",
    accounts: [],
  },

  // ---- NEW EQUIPMENT ----
  new_equipment_revenue: {
    label: "New Equipment Revenue",
    formula: "Sum of all Dept 10 revenue accounts (Linde, Combi, Other, Commission, Freight)",
    accounts: NEW_EQUIPMENT_REVENUE,
  },
  new_equipment_cogs: {
    label: "New Equipment COGS",
    formula: "Sum of all Dept 10 COS accounts (Linde, Combi, Other, Delivery, Rental, Make Ready, Discount, Demo)",
    accounts: NEW_EQUIPMENT_COGS,
  },
  new_equipment_gp: {
    label: "New Equipment Gross Profit",
    formula: "NE Revenue − NE COGS",
    accounts: [...NEW_EQUIPMENT_REVENUE, ...NEW_EQUIPMENT_COGS],
  },

  // ---- ALLIED ----
  allied_revenue: {
    label: "Allied Revenue",
    formula: "Sum of all Dept 20 revenue accounts (Commission, Allied Lines)",
    accounts: ALLIED_REVENUE,
  },
  allied_cogs: {
    label: "Allied COGS",
    formula: "Sum of all Dept 20 COS accounts",
    accounts: ALLIED_COGS,
  },
  allied_gp: {
    label: "Allied Gross Profit",
    formula: "Allied Revenue − Allied COGS",
    accounts: [...ALLIED_REVENUE, ...ALLIED_COGS],
  },

  // ---- USED EQUIPMENT ----
  used_equipment_revenue: {
    label: "Used Equipment Revenue",
    formula: "Sum of all Dept 30 revenue accounts (Linde, Combi, Other, Wholesale, Rental Fleet)",
    accounts: USED_EQUIPMENT_REVENUE,
  },
  used_equipment_cogs: {
    label: "Used Equipment COGS",
    formula: "Sum of all Dept 30 COS accounts",
    accounts: USED_EQUIPMENT_COGS,
  },
  used_equipment_gp: {
    label: "Used Equipment Gross Profit",
    formula: "Used Revenue − Used COGS",
    accounts: [...USED_EQUIPMENT_REVENUE, ...USED_EQUIPMENT_COGS],
  },

  // ---- SERVICE ----
  service_revenue: {
    label: "Service Revenue",
    formula: "Sum of all Dept 40/45 revenue accounts (Road Parts, PM, Labor, Internal, Shop Parts)",
    accounts: SERVICE_REVENUE,
  },
  service_cogs: {
    label: "Service COGS",
    formula: "Sum of all Dept 40/45 COS accounts",
    accounts: SERVICE_COGS,
  },
  service_gp: {
    label: "Service Gross Profit",
    formula: "Service Revenue − Service COGS",
    accounts: [...SERVICE_REVENUE, ...SERVICE_COGS],
  },
  service_labor_revenue: {
    label: "Service Labor Revenue",
    formula: "Sum of labor revenue accounts (Field, Shop, PM, Internal, Nonbillable, Warranty)",
    accounts: [
      '4151701', '4151702', '4152701', '4152702', '4153701', '4153702',
      '4154701', '4154702', '4155701', '4155702', '4156701', '4156702',
      '4157701', '4157702', '4158701', '4158702', '4160701', '4160702',
      '4171701', '4171702', '4173701', '4173702',
      '4311701', '4311702', '4320701', '4322701', '4322702',
      '4340701', '4340702', '4350701', '4350702', '4360701', '4360702',
      '4370701', '4370702', '4380701', '4380702', '4390701', '4390702',
      '4400701', '4400702', '4410701', '4410702',
    ],
  },
  service_parts_revenue: {
    label: "Service Parts Revenue",
    formula: "Sum of road parts + shop parts + PM parts revenue accounts",
    accounts: [
      '4133601', '4133602', '4134601', '4134602', '4135601', '4135602', '4144601',
      '4136601', '4136602', '4137601', '4137602', '4138601', '4138602', '4147601',
      '4130601', '4130602', '4131601', '4131602', '4132601', '4132602', '4141601',
    ],
  },

  // ---- PARTS ----
  parts_revenue: {
    label: "Parts Revenue",
    formula: "Sum of all Dept 50 revenue accounts (Linde, Combi, Tire, Other, TVH, Internal, Freight)",
    accounts: PARTS_REVENUE,
  },
  parts_cogs: {
    label: "Parts COGS",
    formula: "Sum of all Dept 50 COS accounts",
    accounts: PARTS_COGS,
  },
  parts_gp: {
    label: "Parts Gross Profit",
    formula: "Parts Revenue − Parts COGS",
    accounts: [...PARTS_REVENUE, ...PARTS_COGS],
  },
  parts_gp_margin: {
    label: "Parts GP Margin",
    formula: "Parts Gross Profit ÷ Parts Revenue × 100",
    accounts: [...PARTS_REVENUE, ...PARTS_COGS],
  },

  // ---- RENTAL ----
  rental_revenue: {
    label: "Rental Revenue",
    formula: "Sum of all Dept 60 revenue accounts (Customer, Internal, Delivery)",
    accounts: RENTAL_REVENUE,
  },
  rental_cogs: {
    label: "Rental COGS",
    formula: "Sum of all Dept 60 COS accounts (Internal Delivery, Depreciation, P/L Rental)",
    accounts: RENTAL_COGS,
  },
  rental_gp: {
    label: "Rental Gross Profit",
    formula: "Rental Revenue − Rental COGS",
    accounts: [...RENTAL_REVENUE, ...RENTAL_COGS],
  },

  // ---- LEASE ----
  lease_revenue: {
    label: "Lease Revenue",
    formula: "Sum of all Dept 70 revenue accounts (IPSCO Lease, Alside)",
    accounts: LEASE_REVENUE,
  },

  // ---- DEMO ----
  demo_revenue: {
    label: "Demo Revenue",
    formula: "Sum of all Dept 74 revenue accounts",
    accounts: DEMO_REVENUE,
  },
  demo_cogs: {
    label: "Demo COGS",
    formula: "Sum of all Dept 74 COS accounts",
    accounts: DEMO_COGS,
  },

  // ---- AMI/ALSIDE ----
  ami_revenue: {
    label: "AMI/Alside Revenue",
    formula: "Sum of all Dept 75 revenue accounts (AMI Freight, Lease, Used)",
    accounts: AMI_REVENUE,
  },
  ami_cogs: {
    label: "AMI/Alside COGS",
    formula: "Sum of all Dept 75 COS accounts",
    accounts: AMI_COGS,
  },

  // ---- MISCELLANEOUS ----
  misc_revenue: {
    label: "Miscellaneous Revenue",
    formula: "Sum of all Dept 80 revenue accounts (Misc Income, Officer Revenue, Interest, Discounts, Gain/Loss)",
    accounts: MISC_REVENUE,
  },

  // ---- FINANCE / P&L ----
  pl_total_revenue: {
    label: "Total Revenue (P&L)",
    formula: "Sum of all revenue (4xxxx) accounts across all departments",
    accounts: ALL_REVENUE,
  },
  pl_total_cogs: {
    label: "Total COGS (P&L)",
    formula: "Sum of all cost of sales (5xxxx) accounts across all departments",
    accounts: ALL_COGS,
  },
  pl_gross_profit: {
    label: "Gross Profit (P&L)",
    formula: "Total Revenue − Total COGS",
    accounts: [],
  },
  pl_total_expenses: {
    label: "Total Expenses (P&L)",
    formula: "Sum of all overhead expense (6xxxx) accounts",
    accounts: ALL_EXPENSES,
  },
  pl_net_income: {
    label: "Net Income (P&L)",
    formula: "Gross Profit − Total Expenses + Other Income",
    accounts: [],
  },

  // ---- EXPENSE CATEGORIES ----
  expense_depreciation: {
    label: "Depreciation",
    formula: "Sum of depreciation expense accounts (6100xxx)",
    accounts: EXPENSE_DEPRECIATION,
  },
  expense_salaries: {
    label: "Salaries & Wages",
    formula: "Sum of salary, wage, and commission accounts (68xx, 69xx)",
    accounts: EXPENSE_SALARIES,
  },
  expense_payroll_benefits: {
    label: "Payroll Benefits",
    formula: "Sum of employee benefits, medical/health, and payroll tax accounts",
    accounts: EXPENSE_PAYROLL_BENEFITS,
  },
  expense_rent: {
    label: "Rent & Facilities",
    formula: "Sum of rent and property tax accounts (6733xxx, 6555xxx)",
    accounts: EXPENSE_RENT,
  },
  expense_utilities: {
    label: "Utilities",
    formula: "Sum of utilities/janitorial accounts (6430xxx)",
    accounts: EXPENSE_UTILITIES,
  },
  expense_insurance: {
    label: "Insurance",
    formula: "Sum of insurance accounts (6410xxx)",
    accounts: EXPENSE_INSURANCE,
  },
  expense_marketing: {
    label: "Marketing",
    formula: "Sum of advertising and meals/entertainment accounts",
    accounts: EXPENSE_MARKETING,
  },
  expense_professional_fees: {
    label: "Professional Fees",
    formula: "Sum of professional fee accounts (6540xxx)",
    accounts: EXPENSE_PROFESSIONAL,
  },
  expense_office_admin: {
    label: "Office & Admin",
    formula: "Sum of building maintenance, IT, dues/subscriptions, office supplies, outside services, telephone",
    accounts: EXPENSE_OFFICE,
  },
  expense_vehicle_equipment: {
    label: "Vehicle & Equipment",
    formula: "Sum of auto/vehicle, equipment rental, freight, fuel, repairs, small tools accounts",
    accounts: EXPENSE_VEHICLE,
  },
  expense_other: {
    label: "Other Expenses",
    formula: "Sum of bad debt, charitable contributions, licenses, management fees, miscellaneous",
    accounts: EXPENSE_OTHER,
  },
  expense_interest: {
    label: "Interest & Finance",
    formula: "Sum of interest expense accounts (6420xxx)",
    accounts: EXPENSE_INTEREST,
  },

  // ---- OTHER INCOME ----
  other_income: {
    label: "Other Income",
    formula: "Sum of miscellaneous income, interest income, and cash discounts earned",
    accounts: OTHER_INCOME,
  },

  // ---- DASHBOARD SUMMARY CARDS ----
  dashboard_total_revenue: {
    label: "Total Revenue (Dashboard)",
    formula: "Sum of all revenue (4xxxx) accounts for the selected period",
    accounts: ALL_REVENUE,
  },
  dashboard_gross_profit: {
    label: "Gross Profit (Dashboard)",
    formula: "Total Revenue − Total COGS for the selected period",
    accounts: [...ALL_REVENUE, ...ALL_COGS],
  },
  dashboard_net_income: {
    label: "Net Income (Dashboard)",
    formula: "Gross Profit − Total Expenses + Other Income for the selected period",
    accounts: [...ALL_REVENUE, ...ALL_COGS, ...ALL_EXPENSES, ...OTHER_INCOME],
  },
  dashboard_gp_margin: {
    label: "GP Margin (Dashboard)",
    formula: "Gross Profit ÷ Total Revenue × 100",
    accounts: [],
  },

  // ---- PARTS-SPECIFIC METRICS ----
  parts_fill_rate: {
    label: "Parts Fill Rate",
    formula: "Lines filled from stock ÷ Total lines ordered × 100 (from work order data)",
    accounts: [],
  },
  parts_inventory_turns: {
    label: "Parts Inventory Turns",
    formula: "Annual COGS ÷ Average Inventory Value (annualized)",
    accounts: PARTS_COGS,
  },
  parts_obsolete_value: {
    label: "Obsolete Inventory Value",
    formula: "Sum of parts with no movement in 12+ months (from inventory data)",
    accounts: [],
  },
  parts_reorder_alerts: {
    label: "Reorder Alerts",
    formula: "Count of parts where current stock ≤ reorder point (critical + warning)",
    accounts: [],
  },

  // ---- SERVICE-SPECIFIC METRICS ----
  service_effective_labor_rate: {
    label: "Effective Labor Rate",
    formula: "Total Labor Revenue ÷ Total Billed Hours",
    accounts: ['4151701', '4151702', '4155701', '4155702'],
  },
  service_tech_efficiency: {
    label: "Technician Efficiency",
    formula: "Billed Hours ÷ Available Hours × 100",
    accounts: [],
  },
  service_wo_count: {
    label: "Work Order Count",
    formula: "Count of work orders in the selected period (from work order data)",
    accounts: [],
  },
  service_avg_ro_value: {
    label: "Average RO Value",
    formula: "Total Service Revenue ÷ Number of Work Orders",
    accounts: SERVICE_REVENUE,
  },

  // ---- RENTAL-SPECIFIC METRICS ----
  rental_utilization: {
    label: "Rental Utilization",
    formula: "Units on rent ÷ Total fleet units × 100 (from rental fleet data)",
    accounts: [],
  },
  rental_fleet_size: {
    label: "Fleet Size",
    formula: "Count of active rental units (from equipment master data)",
    accounts: [],
  },
  rental_avg_rate: {
    label: "Average Rental Rate",
    formula: "Total Rental Revenue ÷ Total Units on Rent ÷ Days in Period",
    accounts: RENTAL_REVENUE,
  },
  rental_depreciation: {
    label: "Rental Depreciation",
    formula: "Sum of rental depreciation COS accounts",
    accounts: ['5371901', '5371902'],
  },
};

// Helper: Get metric definition by key
export function getMetric(key) {
  return IPS_METRICS[key] || null;
}

// Helper: Get all metrics for a department
export function getDeptMetrics(dept) {
  const prefix = dept.toLowerCase().replace(/[^a-z]/g, '_');
  return Object.entries(IPS_METRICS)
    .filter(([key]) => key.startsWith(prefix))
    .reduce((acc, [key, val]) => ({ ...acc, [key]: val }), {});
}

export default IPS_METRICS;
