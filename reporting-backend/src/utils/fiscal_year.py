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


def get_fiscal_year_months(as_of_date=None, trailing_months=13):
    """
    Get a list of trailing months for chart display in chronological order.
    
    Args:
        as_of_date: Optional datetime to use instead of current date
        trailing_months: Number of months to return (default: 13 for current month + previous 12)
        
    Returns:
        list: List of (year, month) tuples representing the trailing months
        
    Example:
        For November 19, 2025 with trailing_months=13:
        Returns: [(2024, 10), (2024, 11), (2024, 12), (2025, 1), ..., (2025, 11)]
        That's: Oct '24, Nov '24, Dec '24, Jan '25, ..., Nov '25
    """
    if as_of_date is None:
        as_of_date = datetime.now()
    
    # Start from (trailing_months - 1) months ago to include current month
    # For trailing_months=13: start 12 months ago, then add 13 months total
    start_date = as_of_date - relativedelta(months=trailing_months - 1)
    
    months = []
    for i in range(trailing_months):
        month_date = start_date + relativedelta(months=i)
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
