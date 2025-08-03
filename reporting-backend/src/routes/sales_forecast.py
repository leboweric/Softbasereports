from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService
from datetime import datetime, timedelta
import numpy as np
from statistics import stdev, mean

sales_forecast_bp = Blueprint('sales_forecast', __name__)

@sales_forecast_bp.route('/api/dashboard/sales-forecast', methods=['GET'])
@jwt_required()
def get_sales_forecast():
    """Generate sales forecast for current month based on historical patterns"""
    try:
        db = AzureSQLService()
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        current_day = now.day
        
        # Get historical daily sales patterns for all available months
        daily_pattern_query = """
        WITH DailySales AS (
            SELECT 
                YEAR(InvoiceDate) as year,
                MONTH(InvoiceDate) as month,
                DAY(InvoiceDate) as day,
                SUM(GrandTotal) as daily_total,
                COUNT(*) as invoice_count
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= '2025-03-01'
                AND InvoiceDate < CAST(GETDATE() AS DATE)
            GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate), DAY(InvoiceDate)
        ),
        MonthlyTotals AS (
            SELECT 
                year,
                month,
                SUM(daily_total) as month_total,
                MAX(day) as days_in_month
            FROM DailySales
            GROUP BY year, month
        ),
        DailyPercentages AS (
            SELECT 
                ds.year,
                ds.month,
                ds.day,
                ds.daily_total,
                ds.invoice_count,
                CASE WHEN mt.month_total > 0 
                    THEN (ds.daily_total / mt.month_total) * 100 
                    ELSE 0 
                END as pct_of_month
            FROM DailySales ds
            JOIN MonthlyTotals mt ON ds.year = mt.year AND ds.month = mt.month
        )
        SELECT * FROM DailyPercentages
        ORDER BY year, month, day
        """
        
        # Get current month sales to date
        current_month_query = f"""
        SELECT 
            SUM(GrandTotal) as mtd_sales,
            COUNT(*) as mtd_invoices,
            AVG(GrandTotal) as avg_invoice_value
        FROM ben002.InvoiceReg
        WHERE YEAR(InvoiceDate) = {current_year}
            AND MONTH(InvoiceDate) = {current_month}
        """
        
        # Get quotes pipeline for current month
        quotes_pipeline_query = f"""
        WITH LatestQuotes AS (
            SELECT 
                WONo,
                MAX(CAST(CreationTime AS DATE)) as latest_quote_date
            FROM ben002.WOQuote
            WHERE YEAR(CreationTime) = {current_year}
                AND MONTH(CreationTime) = {current_month}
                AND Amount > 0
            GROUP BY WONo
        )
        SELECT 
            COUNT(DISTINCT lq.WONo) as open_quotes,
            SUM(wq.Amount) as pipeline_value
        FROM LatestQuotes lq
        INNER JOIN ben002.WOQuote wq
            ON lq.WONo = wq.WONo
            AND CAST(wq.CreationTime AS DATE) = lq.latest_quote_date
        WHERE wq.Amount > 0
        """
        
        # Execute queries
        daily_patterns = db.execute_query(daily_pattern_query)
        current_month_data = db.execute_query(current_month_query)[0]
        quotes_data = db.execute_query(quotes_pipeline_query)[0]
        
        # Analyze patterns
        forecast_result = analyze_sales_patterns(
            daily_patterns, 
            current_month_data, 
            quotes_data,
            current_year,
            current_month,
            current_day
        )
        
        return jsonify(forecast_result)
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate forecast: {str(e)}'}), 500

def analyze_sales_patterns(daily_patterns, current_month_data, quotes_data, current_year, current_month, current_day):
    """Analyze historical patterns and generate forecast"""
    
    # Current month progress
    days_in_month = 31 if current_month in [1, 3, 5, 7, 8, 10, 12] else 30 if current_month != 2 else 28
    month_progress = current_day / days_in_month
    
    mtd_sales = float(current_month_data['mtd_sales'] or 0)
    mtd_invoices = int(current_month_data['mtd_invoices'] or 0)
    avg_invoice = float(current_month_data['avg_invoice_value'] or 0)
    
    # Calculate velocity patterns by day of month
    day_velocities = {}
    for row in daily_patterns:
        day = row['day']
        pct = float(row['pct_of_month'])
        if day not in day_velocities:
            day_velocities[day] = []
        day_velocities[day].append(pct)
    
    # Calculate average percentage complete by current day
    cumulative_by_day = {}
    for month_data in group_by_month(daily_patterns):
        cumulative = 0
        for day in range(1, 32):
            day_data = [d for d in month_data if d['day'] == day]
            if day_data:
                cumulative += float(day_data[0]['pct_of_month'])
            cumulative_by_day.setdefault(day, []).append(cumulative)
    
    # Get average completion percentage by current day
    if current_day in cumulative_by_day and cumulative_by_day[current_day]:
        avg_pct_complete = mean(cumulative_by_day[current_day])
        pct_complete_std = stdev(cumulative_by_day[current_day]) if len(cumulative_by_day[current_day]) > 1 else 0
    else:
        # Fallback to linear projection
        avg_pct_complete = (current_day / days_in_month) * 100
        pct_complete_std = 5  # Default uncertainty
    
    # Generate forecasts
    if avg_pct_complete > 0:
        # Base projection
        projected_total = mtd_sales / (avg_pct_complete / 100)
        
        # Calculate confidence intervals
        if pct_complete_std > 0:
            # 68% confidence interval (1 std dev)
            lower_pct = max(avg_pct_complete - pct_complete_std, current_day / days_in_month * 100)
            upper_pct = avg_pct_complete + pct_complete_std
            
            forecast_low = mtd_sales / (upper_pct / 100)
            forecast_high = mtd_sales / (lower_pct / 100)
        else:
            forecast_low = projected_total * 0.9
            forecast_high = projected_total * 1.1
    else:
        # No historical data, use simple projection
        daily_rate = mtd_sales / current_day if current_day > 0 else 0
        projected_total = daily_rate * days_in_month
        forecast_low = projected_total * 0.8
        forecast_high = projected_total * 1.2
    
    # Quote conversion impact
    pipeline_value = float(quotes_data['pipeline_value'] or 0)
    historical_conversion_rate = 0.3  # Assume 30% conversion for now
    expected_pipeline_revenue = pipeline_value * historical_conversion_rate
    
    # Calculate momentum (comparing to previous months)
    recent_months = get_recent_month_totals(daily_patterns, current_year, current_month)
    if len(recent_months) >= 2:
        avg_recent = mean(recent_months)
        momentum = ((projected_total / avg_recent) - 1) * 100 if avg_recent > 0 else 0
    else:
        momentum = 0
    
    # Key factors affecting forecast
    factors = []
    
    # Day of month velocity
    if current_day <= 5:
        factors.append({
            'factor': 'Early Month Pattern',
            'impact': 'neutral',
            'description': f'Limited data ({current_day} days) - forecast has higher uncertainty'
        })
    elif avg_pct_complete < month_progress * 100 - 5:
        factors.append({
            'factor': 'Sales Velocity',
            'impact': 'negative',
            'description': f'Sales pace is {round(month_progress * 100 - avg_pct_complete, 1)}% behind typical pattern'
        })
    elif avg_pct_complete > month_progress * 100 + 5:
        factors.append({
            'factor': 'Sales Velocity',
            'impact': 'positive',
            'description': f'Sales pace is {round(avg_pct_complete - month_progress * 100, 1)}% ahead of typical pattern'
        })
    
    # Pipeline strength
    if pipeline_value > avg_recent * 0.5:
        factors.append({
            'factor': 'Quote Pipeline',
            'impact': 'positive',
            'description': f'Strong pipeline of {format_currency(pipeline_value)} in quotes'
        })
    
    # Momentum
    if momentum > 10:
        factors.append({
            'factor': 'Growth Momentum',
            'impact': 'positive',
            'description': f'Trending {round(momentum, 1)}% above recent average'
        })
    elif momentum < -10:
        factors.append({
            'factor': 'Growth Momentum',
            'impact': 'negative',
            'description': f'Trending {round(abs(momentum), 1)}% below recent average'
        })
    
    return {
        'current_month': {
            'year': current_year,
            'month': current_month,
            'day': current_day,
            'mtd_sales': mtd_sales,
            'days_elapsed': current_day,
            'days_remaining': days_in_month - current_day,
            'month_progress_pct': round(month_progress * 100, 1)
        },
        'forecast': {
            'projected_total': round(projected_total, 2),
            'forecast_low': round(forecast_low, 2),
            'forecast_high': round(forecast_high, 2),
            'confidence_level': '68%',
            'expected_from_pipeline': round(expected_pipeline_revenue, 2)
        },
        'analysis': {
            'typical_pct_complete_by_today': round(avg_pct_complete, 1),
            'actual_pct_of_forecast': round((mtd_sales / projected_total) * 100, 1) if projected_total > 0 else 0,
            'momentum_vs_recent': round(momentum, 1),
            'daily_run_rate_needed': round((projected_total - mtd_sales) / (days_in_month - current_day), 2) if days_in_month > current_day else 0
        },
        'factors': factors
    }

def group_by_month(daily_patterns):
    """Group daily patterns by month"""
    months = {}
    for row in daily_patterns:
        key = f"{row['year']}-{row['month']}"
        if key not in months:
            months[key] = []
        months[key].append(row)
    return months.values()

def get_recent_month_totals(daily_patterns, current_year, current_month):
    """Get total sales for recent complete months"""
    totals = {}
    for row in daily_patterns:
        # Skip current month
        if row['year'] == current_year and row['month'] == current_month:
            continue
        key = f"{row['year']}-{row['month']}"
        if key not in totals:
            totals[key] = 0
        totals[key] += float(row['daily_total'])
    
    # Return list of totals for recent months
    return list(totals.values())

def format_currency(value):
    """Format value as currency"""
    return f"${value:,.0f}"