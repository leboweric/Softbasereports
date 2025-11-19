"""
Fiscal Year Utility Functions

Provides helper functions for calculating fiscal year dates and periods
based on organization-specific fiscal year start month configuration.
"""

from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import g


def get_fiscal_year_start_month():
    """
    Get the fiscal year start month for the current organization.
    
    Returns:
        int: Month number (1-12) where 1=January, 11=November, etc.
        Defaults to 11 (November) if not configured.
    """
    if hasattr(g, 'current_organization') and g.current_organization:
        return g.current_organization.fiscal_year_start_month or 11
    return 11  # Default to November


def get_current_fiscal_year_dates():
    """
    Get the start and end dates of the current fiscal year.
    
    Returns:
        tuple: (fiscal_year_start, fiscal_year_end) as datetime objects
    """
    fiscal_start_month = get_fiscal_year_start_month()
    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month
    
    # If we're past the fiscal year start month, we're in the current fiscal year
    if current_month >= fiscal_start_month:
        fiscal_year_start = datetime(current_year, fiscal_start_month, 1)
        fiscal_year_end = datetime(current_year + 1, fiscal_start_month, 1) - relativedelta(days=1)
    else:
        # We're before the fiscal year start, so we're in the previous fiscal year
        fiscal_year_start = datetime(current_year - 1, fiscal_start_month, 1)
        fiscal_year_end = datetime(current_year, fiscal_start_month, 1) - relativedelta(days=1)
    
    return fiscal_year_start, fiscal_year_end


def get_fiscal_year_months(as_of_date=None, use_previous_year=True):
    """
    Get a list of the 12 months in the fiscal year in chronological order.
    
    Args:
        as_of_date: Optional datetime to use instead of current date
        use_previous_year: If True, return the previous completed fiscal year.
                          If False, return the current fiscal year.
                          Default is True for chart display purposes.
        
    Returns:
        list: List of (year, month) tuples representing the fiscal year months
    """
    if as_of_date is None:
        as_of_date = datetime.now()
    
    fiscal_year_start, _ = get_current_fiscal_year_dates()
    
    # For charts, we typically want to show the previous completed fiscal year
    # unless we're well into the current fiscal year (e.g., past 3 months)
    if use_previous_year:
        fiscal_year_start = fiscal_year_start - relativedelta(years=1)
    
    months = []
    for i in range(12):
        month_date = fiscal_year_start + relativedelta(months=i)
        months.append((month_date.year, month_date.month))
    
    return months


def get_fiscal_ytd_start():
    """
    Get the start date for fiscal year-to-date calculations.
    
    Returns:
        datetime: Start of the current fiscal year
    """
    fiscal_year_start, _ = get_current_fiscal_year_dates()
    return fiscal_year_start


def is_fiscal_year_end_month(date=None):
    """
    Check if the given date (or current date) is in the fiscal year-end month.
    
    Args:
        date: Optional datetime to check (defaults to current date)
        
    Returns:
        bool: True if in fiscal year-end month
    """
    if date is None:
        date = datetime.now()
    
    _, fiscal_year_end = get_current_fiscal_year_dates()
    return date.year == fiscal_year_end.year and date.month == fiscal_year_end.month


def format_fiscal_year_label():
    """
    Get a formatted label for the current fiscal year.
    
    Returns:
        str: Fiscal year label like "FY 2024-2025" or "FY 2025"
    """
    fiscal_year_start, fiscal_year_end = get_current_fiscal_year_dates()
    
    if fiscal_year_start.year == fiscal_year_end.year:
        return f"FY {fiscal_year_start.year}"
    else:
        return f"FY {fiscal_year_start.year}-{fiscal_year_end.year}"
