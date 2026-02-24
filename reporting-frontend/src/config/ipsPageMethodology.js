/**
 * IPS Page Methodology Configurations
 * 
 * Defines the sections and metrics shown in the Methodology panel
 * for each page. References IPS_METRICS from ipsMetricDefinitions.js.
 */
import { IPS_METRICS } from './ipsMetricDefinitions';

// ============================================================
// ED'S DASHBOARD / SALES GP REPORT
// ============================================================
export const EDS_DASHBOARD_METHODOLOGY = {
  title: "Ed's Dashboard — Methodology",
  description: "GL accounts, formulas, and data sources for the Owner Dashboard. All data is sourced from the General Ledger detail (GLDetail table) in the ERP system.",
  sections: [
    {
      heading: "Summary Cards",
      metrics: [
        IPS_METRICS.eds_total_revenue,
        IPS_METRICS.eds_total_cogs,
        IPS_METRICS.eds_gross_profit,
        IPS_METRICS.eds_gp_pct,
      ],
    },
    {
      heading: "New Equipment (Dept 10)",
      metrics: [
        IPS_METRICS.new_equipment_revenue,
        IPS_METRICS.new_equipment_cogs,
        IPS_METRICS.new_equipment_gp,
      ],
    },
    {
      heading: "Allied Equipment (Dept 20)",
      metrics: [
        IPS_METRICS.allied_revenue,
        IPS_METRICS.allied_cogs,
        IPS_METRICS.allied_gp,
      ],
    },
    {
      heading: "Used Equipment (Dept 30)",
      metrics: [
        IPS_METRICS.used_equipment_revenue,
        IPS_METRICS.used_equipment_cogs,
        IPS_METRICS.used_equipment_gp,
      ],
    },
    {
      heading: "Service (Dept 40/45)",
      metrics: [
        IPS_METRICS.service_revenue,
        IPS_METRICS.service_cogs,
        IPS_METRICS.service_gp,
        IPS_METRICS.service_labor_revenue,
        IPS_METRICS.service_parts_revenue,
      ],
    },
    {
      heading: "Parts (Dept 50)",
      metrics: [
        IPS_METRICS.parts_revenue,
        IPS_METRICS.parts_cogs,
        IPS_METRICS.parts_gp,
      ],
    },
    {
      heading: "Rental (Dept 60)",
      metrics: [
        IPS_METRICS.rental_revenue,
        IPS_METRICS.rental_cogs,
        IPS_METRICS.rental_gp,
      ],
    },
    {
      heading: "Lease (Dept 70)",
      metrics: [
        IPS_METRICS.lease_revenue,
      ],
    },
    {
      heading: "Demo (Dept 74)",
      metrics: [
        IPS_METRICS.demo_revenue,
        IPS_METRICS.demo_cogs,
      ],
    },
    {
      heading: "AMI/Alside (Dept 75)",
      metrics: [
        IPS_METRICS.ami_revenue,
        IPS_METRICS.ami_cogs,
      ],
    },
    {
      heading: "Miscellaneous (Dept 80)",
      metrics: [
        IPS_METRICS.misc_revenue,
      ],
    },
  ],
};

// ============================================================
// SALES DASHBOARD
// ============================================================
export const SALES_DASHBOARD_METHODOLOGY = {
  title: "Sales Dashboard — Methodology",
  description: "GL accounts and formulas for the Sales Dashboard KPI cards and charts.",
  sections: [
    {
      heading: "Top-Level KPI Cards",
      metrics: [
        IPS_METRICS.dashboard_mtd_sales || { label: "MTD Sales", formula: "Sum of all revenue (4xxxx) accounts for the current calendar month", accounts: [] },
        IPS_METRICS.dashboard_ytd_sales || { label: "YTD Sales", formula: "Sum of all revenue (4xxxx) accounts from fiscal year start (Nov 1) through today", accounts: [] },
        IPS_METRICS.dashboard_blended_gp || { label: "Blended GP%", formula: "YTD Gross Profit ÷ YTD Revenue × 100", accounts: [] },
        { label: "Equipment Units (FY)", formula: "Count of Linde new truck units invoiced in the current fiscal year (Nov–Oct). Counted from invoices with SaleCode 'LINDEN' in the Invoice Register.", accounts: [] },
        { label: "Active Customers", formula: "Count of distinct customers invoiced in the last 30 days. Excludes internal accounts.", accounts: [] },
      ],
    },
    {
      heading: "Department Revenue",
      metrics: [
        IPS_METRICS.new_equipment_revenue,
        IPS_METRICS.allied_revenue,
        IPS_METRICS.used_equipment_revenue,
        IPS_METRICS.service_revenue,
        IPS_METRICS.parts_revenue,
        IPS_METRICS.rental_revenue,
      ],
    },
  ],
};

// ============================================================
// PARTS PAGE
// ============================================================
export const PARTS_METHODOLOGY = {
  title: "Parts Department — Methodology",
  description: "GL accounts and formulas for the Parts department KPI cards, charts, and reports.",
  sections: [
    {
      heading: "Overview KPI Cards",
      metrics: [
        IPS_METRICS.parts_revenue,
        IPS_METRICS.parts_cogs,
        IPS_METRICS.parts_gp,
        IPS_METRICS.parts_gp_margin,
        IPS_METRICS.parts_fill_rate,
        IPS_METRICS.parts_inventory_turns,
        IPS_METRICS.parts_obsolete_value,
        IPS_METRICS.parts_reorder_alerts,
      ],
    },
    {
      heading: "Revenue Breakdown",
      metrics: [
        { label: "Counter Parts Revenue", formula: "Sum of Linde, Combi, Tire, Other, TVH parts sales accounts", accounts: ['4125601', '4125602', '4126601', '4126602', '4127601', '4127602', '4129601', '4129602', '4146601'] },
        { label: "RO Parts Revenue", formula: "Sum of internal parts sales accounts (to Service, New, Used, Rental)", accounts: ['4300601', '4300602', '4306201', '4306401', '4306402', '4306501', '4306502', '4306503', '4306504', '4306601', '4306602', '4306701', '4306702', '4306901', '4306902'] },
      ],
    },
  ],
};

// ============================================================
// SERVICE PAGE
// ============================================================
export const SERVICE_METHODOLOGY = {
  title: "Service Department — Methodology",
  description: "GL accounts and formulas for the Service department KPI cards and reports.",
  sections: [
    {
      heading: "Overview KPI Cards",
      metrics: [
        IPS_METRICS.service_revenue,
        IPS_METRICS.service_cogs,
        IPS_METRICS.service_gp,
        IPS_METRICS.service_effective_labor_rate,
        IPS_METRICS.service_tech_efficiency,
        IPS_METRICS.service_wo_count,
        IPS_METRICS.service_avg_ro_value,
      ],
    },
    {
      heading: "Revenue Breakdown",
      metrics: [
        IPS_METRICS.service_labor_revenue,
        IPS_METRICS.service_parts_revenue,
      ],
    },
  ],
};

// ============================================================
// RENTAL PAGE
// ============================================================
export const RENTAL_METHODOLOGY = {
  title: "Rental Department — Methodology",
  description: "GL accounts and formulas for the Rental department KPI cards and reports.",
  sections: [
    {
      heading: "Overview KPI Cards",
      metrics: [
        IPS_METRICS.rental_revenue,
        IPS_METRICS.rental_cogs,
        IPS_METRICS.rental_gp,
        IPS_METRICS.rental_utilization,
        IPS_METRICS.rental_fleet_size,
        IPS_METRICS.rental_avg_rate,
        IPS_METRICS.rental_depreciation,
      ],
    },
  ],
};

// ============================================================
// FINANCE / P&L PAGE
// ============================================================
export const FINANCE_METHODOLOGY = {
  title: "Finance / P&L Report — Methodology",
  description: "GL accounts and formulas for the Profit & Loss statement and financial overview.",
  sections: [
    {
      heading: "P&L Summary Cards",
      metrics: [
        IPS_METRICS.pl_total_revenue,
        IPS_METRICS.pl_total_cogs,
        IPS_METRICS.pl_gross_profit,
        IPS_METRICS.pl_total_expenses,
        IPS_METRICS.pl_net_income,
      ],
    },
    {
      heading: "Expense Categories",
      metrics: [
        IPS_METRICS.expense_depreciation,
        IPS_METRICS.expense_salaries,
        IPS_METRICS.expense_payroll_benefits,
        IPS_METRICS.expense_rent,
        IPS_METRICS.expense_utilities,
        IPS_METRICS.expense_insurance,
        IPS_METRICS.expense_marketing,
        IPS_METRICS.expense_professional_fees,
        IPS_METRICS.expense_office_admin,
        IPS_METRICS.expense_vehicle_equipment,
        IPS_METRICS.expense_other,
        IPS_METRICS.expense_interest,
      ],
    },
    {
      heading: "Other Income",
      metrics: [
        IPS_METRICS.other_income,
      ],
    },
  ],
};

// ============================================================
// ACCOUNTING PAGE
// ============================================================
export const ACCOUNTING_METHODOLOGY = {
  title: "Accounting — Methodology",
  description: "Data sources and formulas for the Accounting page KPI cards and reports.",
  sections: [
    {
      heading: "Summary Cards",
      metrics: [
        { label: "Total Accounts Receivable", formula: "Sum of all outstanding customer invoices from Accounts Receivable aging report", accounts: [], source: "AR Aging (ARDetail table)" },
        { label: "AR Over 90 Days", formula: "(AR balance > 90 days past due ÷ Total AR) × 100. Green if < 10%, red if ≥ 10%.", accounts: [], source: "AR Aging (ARDetail table)" },
        { label: "Total Accounts Payable", formula: "Sum of all outstanding vendor invoices from Accounts Payable aging report", accounts: [], source: "AP Aging (APDetail table)" },
      ],
    },
    {
      heading: "Gross Margin Dollars",
      metrics: [
        IPS_METRICS.eds_gross_profit,
      ],
    },
    {
      heading: "G&A Expenses",
      metrics: [
        IPS_METRICS.pl_total_expenses,
      ],
    },
  ],
};
