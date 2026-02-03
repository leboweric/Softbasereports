# Column mappings for different tenant database schemas
# This allows the same queries to work across tenants with different column names

# Default column names (Bennett - legacy schema)
DEFAULT_COLUMNS = {
    'GLDetail': {
        'gl_code': 'GLCode',
        'gl_desc': 'GLDesc',
        'trans_date': 'TransDate',
        'amount': 'Amount',
        'branch': 'Branch',
        'dept': 'Dept',
        'customer_no': 'CustomerNo',
        'invoice_no': 'InvoiceNo',
        'posted': 'Posted',
        'posted_date': 'PostedDate',
    },
    'Customer': {
        'cust_no': 'CustNo',
        'name': 'Name',
        'salesman': 'Salesman',
        'branch': 'Branch',
        'balance': 'Balance',
        'address': 'Address',
        'city': 'City',
        'state': 'State',
        'zip': 'Zip',
        'phone': 'Phone',
        'email': 'EMail',
    },
    'InvoiceReg': {
        'invoice_no': 'InvoiceNo',
        'cust_no': 'CustNo',
        'branch': 'Branch',
        'dept': 'Dept',
        'invoice_date': 'InvoiceDate',
        'grand_total': 'GrandTotal',
        'parts_cost': 'PartsCost',
        'labor_cost': 'LaborCost',
        'misc_cost': 'MiscCost',
        'rental_cost': 'RentalCost',
        'equipment_cost': 'EquipmentCost',
        'total_tax': 'TotalTax',
        'bill_to': 'BillTo',
        'bill_to_name': 'BillToName',
        'ship_to': 'ShipTo',
        'ship_to_name': 'ShipToName',
        'serial_no': 'SerialNo',
        'closed_date': 'ClosedDate',
    },
    'WOMisc': {
        'wo_no': 'WONo',
        'branch': 'Branch',
        'dept': 'Dept',
        'description': 'Description',
        'cost': 'Cost',
        'sell': 'Sell',
        'sale_account': 'SaleAccount',
        'cost_account': 'CostAccount',
        'taxable': 'Taxable',
        'customer': 'Customer',
    },
}

# IPS column names (new Evolution schema - 2025+)
IPS_COLUMNS = {
    'GLDetail': {
        'gl_code': 'AccountNo',
        'gl_desc': 'Description',
        'trans_date': 'EffectiveDate',
        'amount': 'Amount',
        'branch': 'Branch',
        'dept': 'Dept',
        'customer_no': 'CustomerNo',
        'invoice_no': 'InvoiceNo',
        'posted': 'Posted',
        'posted_date': 'PostedDate',
    },
    'Customer': {
        'cust_no': 'Number',
        'name': 'BillToName',
        'salesman': 'Salesman1',
        'branch': 'Branch',
        'balance': None,  # Column doesn't exist in IPS schema
        'address': 'Address',
        'city': 'City',
        'state': 'State',
        'zip': 'ZipCode',
        'phone': 'Phone',
        'email': 'EMail',
    },
    'InvoiceReg': {
        'invoice_no': 'InvoiceNo',
        'cust_no': 'Customer',
        'branch': 'SaleBranch',
        'dept': 'SaleDept',
        'invoice_date': 'InvoiceDate',
        'grand_total': 'GrandTotal',
        'parts_cost': 'PartsCost',
        'labor_cost': 'LaborCost',
        'misc_cost': 'MiscCost',
        'rental_cost': 'RentalCost',
        'equipment_cost': 'EquipmentCost',
        'total_tax': 'TotalTax',
        'bill_to': 'BillTo',
        'bill_to_name': 'BillToName',
        'ship_to': 'ShipTo',
        'ship_to_name': 'ShipToName',
        'serial_no': 'SerialNo',
        'closed_date': 'ClosedDate',
    },
    'WOMisc': {
        'wo_no': 'WONo',
        'branch': 'SaleBranch',
        'dept': 'SaleDept',
        'description': 'Description',
        'cost': 'Cost',
        'sell': 'Sell',
        'sale_account': 'SaleAccount',
        'cost_account': 'CostAccount',
        'taxable': 'Taxable',
        'customer': 'Customer',
    },
}

# Mapping of organization database_schema to column configuration
SCHEMA_COLUMN_MAPPINGS = {
    'ben002': DEFAULT_COLUMNS,  # Bennett - legacy schema
    'ind004': IPS_COLUMNS,       # IPS - new schema
    # Add more tenants here as needed
}


def get_column_mapping(schema: str) -> dict:
    """
    Get the column mapping for a specific tenant schema.
    Falls back to default columns if schema not found.
    """
    return SCHEMA_COLUMN_MAPPINGS.get(schema, DEFAULT_COLUMNS)


def get_column(schema: str, table: str, column_key: str) -> str:
    """
    Get the actual column name for a specific tenant, table, and logical column.
    
    Args:
        schema: The tenant's database schema (e.g., 'ben002', 'ind004')
        table: The table name (e.g., 'GLDetail', 'Customer')
        column_key: The logical column key (e.g., 'gl_code', 'cust_no')
    
    Returns:
        The actual column name for that tenant's schema
    
    Example:
        get_column('ind004', 'GLDetail', 'gl_code') -> 'AccountNo'
        get_column('ben002', 'GLDetail', 'gl_code') -> 'GLCode'
    """
    mapping = get_column_mapping(schema)
    table_mapping = mapping.get(table, {})
    column = table_mapping.get(column_key)
    
    if column is None:
        # Column doesn't exist in this schema
        return None
    
    return column


def get_columns(schema: str, table: str, *column_keys) -> dict:
    """
    Get multiple column names at once.
    
    Args:
        schema: The tenant's database schema
        table: The table name
        *column_keys: Variable number of logical column keys
    
    Returns:
        Dictionary mapping column_key -> actual_column_name
    
    Example:
        get_columns('ind004', 'GLDetail', 'gl_code', 'amount', 'trans_date')
        -> {'gl_code': 'AccountNo', 'amount': 'Amount', 'trans_date': 'EffectiveDate'}
    """
    return {key: get_column(schema, table, key) for key in column_keys}
