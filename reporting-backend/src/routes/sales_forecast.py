from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from src.services.postgres_service import get_postgres_db
from src.services.cache_service import cache_service
from src.utils.tenant_utils import get_tenant_db, get_tenant_schema, get_tenant_schema
from datetime import datetime, timedelta
import calendar
import numpy as np
from statistics import stdev, mean
import logging

logger = logging.getLogger(__name__)

sales_forecast_bp = Blueprint('sales_forecast', __name__)

@sales_forecast_bp.route('/api/dashboard/sales-forecast', methods=['GET'])
@jwt_required()
def get_sales_forecast():
    """Generate sales forecast for current month based on historical patterns"""
    # Get tenant schema
    from src.utils.tenant_utils import get_tenant_db, get_tenant_schema, get_tenant_schema
    try:
        schema = get_tenant_schema()
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    try:
        from flask import request
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        current_day = now.day
        
        # Use cache with 1-hour TTL (include schema for tenant isolation)
        cache_key = f'sales_forecast:{schema}:{current_year}:{current_month}:{current_day}'
        
        def fetch_forecast():
            return _fetch_sales_forecast_data(current_year, current_month, current_day, schema)
        
        result = cache_service.cache_query(cache_key, fetch_forecast, ttl_seconds=3600, force_refresh=force_refresh)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate forecast: {str(e)}'}), 500

def _fetch_sales_forecast_data(current_year, current_month, current_day, schema):
    """Internal function to fetch sales forecast data"""
    db = get_tenant_db()
    
    # Get historical daily sales patterns (last 12 months for better patterns)
    daily_pattern_query = f"""
    WITH DailySales AS (
        SELECT 
            YEAR(InvoiceDate) as year,
            MONTH(InvoiceDate) as month,
            DAY(InvoiceDate) as day,
            SUM(GrandTotal) as daily_total,
            COUNT(*) as invoice_count
        FROM {schema}.InvoiceReg
        WHERE InvoiceDate >= DATEADD(month, -12, GETDATE())
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
    FROM {schema}.InvoiceReg
    WHERE YEAR(InvoiceDate) = {current_year}
        AND MONTH(InvoiceDate) = {current_month}
    """
    
    # Get quotes pipeline for current month
    quotes_pipeline_query = f"""
    WITH LatestQuotes AS (
        SELECT 
            WONo,
            MAX(CAST(CreationTime AS DATE)) as latest_quote_date
        FROM {schema}.WOQuote
        WHERE YEAR(CreationTime) = {current_year}
            AND MONTH(CreationTime) = {current_month}
            AND Amount > 0
        GROUP BY WONo
    )
    SELECT 
        COUNT(DISTINCT lq.WONo) as open_quotes,
        SUM(wq.Amount) as pipeline_value
    FROM LatestQuotes lq
    INNER JOIN {schema}.WOQuote wq
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
    
    # Save forecast to history for accuracy tracking
    try:
        save_forecast_to_history(forecast_result)
    except Exception as e:
        logger.error(f"Failed to save forecast to history: {str(e)}")
        # Don't fail the request if history save fails
    
    return forecast_result

def analyze_sales_patterns(daily_patterns, current_month_data, quotes_data, current_year, current_month, current_day):
    """Analyze historical patterns and generate forecast"""
    
    # Current month progress
    days_in_month = calendar.monthrange(current_year, current_month)[1]
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
    if avg_pct_complete > 5:  # Need at least 5% completion for reliable projection
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

def save_forecast_to_history(forecast_result, is_scheduled_snapshot=False):
    """Save forecast to PostgreSQL for accuracy tracking
    
    Args:
        forecast_result: The forecast data to save
        is_scheduled_snapshot: If True, this is from the scheduled 15th job (always mark as snapshot)
    """
    try:
        postgres_db = get_postgres_db()
        if not postgres_db:
            logger.warning("PostgreSQL not available - skipping forecast history save")
            return
        
        current = forecast_result['current_month']
        forecast = forecast_result['forecast']
        analysis = forecast_result['analysis']
        
        # Mark as mid-month snapshot if it's the 15th or if this is a scheduled snapshot
        is_mid_month_snapshot = (current['day'] == 15) or is_scheduled_snapshot
        
        insert_query = f"""
        INSERT INTO forecast_history (
            forecast_date,
            forecast_timestamp,
            target_year,
            target_month,
            days_into_month,
            projected_total,
            forecast_low,
            forecast_high,
            confidence_level,
            mtd_sales,
            mtd_invoices,
            month_progress_pct,
            days_remaining,
            pipeline_value,
            avg_pct_complete,
            is_mid_month_snapshot
        ) VALUES (
            CURRENT_DATE,
            CURRENT_TIMESTAMP,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        RETURNING id
        """
        
        params = (
            current['year'],
            current['month'],
            current['day'],
            forecast['projected_total'],
            forecast['forecast_low'],
            forecast['forecast_high'],
            forecast['confidence_level'],
            current['mtd_sales'],
            current.get('mtd_invoices', 0),  # May not be in response
            current['month_progress_pct'],
            current['days_remaining'],
            forecast['expected_from_pipeline'],
            analysis['typical_pct_complete_by_today'],
            is_mid_month_snapshot
        )
        
        result = postgres_db.execute_insert_returning(insert_query, params)
        if result:
            snapshot_msg = " (MID-MONTH SNAPSHOT)" if is_mid_month_snapshot else ""
            logger.info(f"Saved forecast to history with ID: {result['id']}{snapshot_msg}")
        
    except Exception as e:
        logger.error(f"Error saving forecast to history: {str(e)}")
        raise


@sales_forecast_bp.route('/api/dashboard/forecast-accuracy/backfill', methods=['POST'])
@jwt_required()
def backfill_forecast_actuals():
    """Backfill actual totals for completed months in forecast history"""
    # Get tenant schema
    from src.utils.tenant_utils import get_tenant_db, get_tenant_schema, get_tenant_schema
    try:
        schema = get_tenant_schema()
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    try:
        postgres_db = get_postgres_db()
        azure_db = get_tenant_db()
        
        if not postgres_db:
            return jsonify({'error': 'PostgreSQL not available'}), 500
        
        # Get all forecasts that don't have actuals yet
        pending_query = f"""
        SELECT DISTINCT target_year, target_month
        FROM forecast_history
        WHERE actual_total IS NULL
        ORDER BY target_year, target_month
        """
        
        pending_months = postgres_db.execute_query(pending_query)
        
        if not pending_months:
            return jsonify({
                'message': 'No pending forecasts to backfill',
                'updated_count': 0
            })
        
        updated_count = 0
        now = datetime.now()
        
        for month_record in pending_months:
            target_year = month_record['target_year']
            target_month = month_record['target_month']
            
            # Only backfill if the month has ended
            target_date = datetime(target_year, target_month, 1)
            next_month = target_date + timedelta(days=32)
            next_month = next_month.replace(day=1)
            
            if now < next_month:
                logger.info(f"Skipping {target_year}-{target_month} - month not yet complete")
                continue
            
            # Get actual totals from Azure SQL
            actual_query = f"""
            SELECT 
                SUM(GrandTotal) as actual_total,
                COUNT(*) as actual_invoices
            FROM {schema}.InvoiceReg
            WHERE YEAR(InvoiceDate) = {target_year}
                AND MONTH(InvoiceDate) = {target_month}
            """
            
            actual_result = azure_db.execute_query(actual_query)[0]
            actual_total = float(actual_result['actual_total'] or 0)
            actual_invoices = int(actual_result['actual_invoices'] or 0)
            
            # Update all forecasts for this month
            update_query = f"""
            UPDATE forecast_history
            SET 
                actual_total = %s,
                actual_invoices = %s,
                accuracy_pct = CASE 
                    WHEN %s > 0 THEN 
                        ABS(projected_total - %s) / %s * 100
                    ELSE NULL
                END,
                absolute_error = ABS(projected_total - %s),
                within_range = CASE 
                    WHEN %s BETWEEN COALESCE(forecast_low, projected_total) 
                        AND COALESCE(forecast_high, projected_total) THEN TRUE
                    ELSE FALSE
                END,
                updated_at = CURRENT_TIMESTAMP
            WHERE target_year = %s
                AND target_month = %s
                AND actual_total IS NULL
            """
            
            params = (
                actual_total,
                actual_invoices,
                actual_total, actual_total, actual_total,  # For accuracy_pct calculation
                actual_total,  # For absolute_error
                actual_total,  # For within_range check
                target_year,
                target_month
            )
            
            rows_updated = postgres_db.execute_update(update_query, params)
            updated_count += rows_updated
            logger.info(f"Updated {rows_updated} forecasts for {target_year}-{target_month} with actual: ${actual_total:,.2f}")
        
        return jsonify({
            'message': f'Successfully backfilled actuals for {len(pending_months)} months',
            'updated_count': updated_count,
            'months_processed': [f"{m['target_year']}-{m['target_month']}" for m in pending_months]
        })
        
    except Exception as e:
        logger.error(f"Failed to backfill forecast actuals: {str(e)}")
        return jsonify({'error': f'Failed to backfill actuals: {str(e)}'}), 500


@sales_forecast_bp.route('/api/dashboard/forecast-accuracy', methods=['GET'])
@jwt_required()
def get_forecast_accuracy():
    """Get forecast accuracy metrics and historical performance"""
    try:
        postgres_db = get_postgres_db()
        
        if not postgres_db:
            return jsonify({'error': 'PostgreSQL not available'}), 500
        
        # Get overall accuracy metrics
        metrics_query = f"""
        SELECT 
            COUNT(*) as total_forecasts,
            COUNT(CASE WHEN actual_total IS NOT NULL THEN 1 END) as completed_forecasts,
            AVG(accuracy_pct) as mean_absolute_percentage_error,
            MIN(accuracy_pct) as best_accuracy,
            MAX(accuracy_pct) as worst_accuracy,
            AVG(CASE WHEN within_range THEN 1.0 ELSE 0.0 END) * 100 as within_range_pct,
            AVG(projected_total - actual_total) as avg_bias
        FROM forecast_history
        WHERE actual_total IS NOT NULL
        """
        
        metrics = postgres_db.execute_query(metrics_query)
        
        # Get accuracy by month
        monthly_query = f"""
        SELECT 
            target_year,
            target_month,
            COUNT(*) as forecast_count,
            AVG(projected_total) as avg_projected,
            MAX(actual_total) as actual_total,
            AVG(accuracy_pct) as mape,
            AVG(projected_total - actual_total) as bias,
            AVG(CASE WHEN within_range THEN 1.0 ELSE 0.0 END) * 100 as within_range_pct
        FROM forecast_history
        WHERE actual_total IS NOT NULL
        GROUP BY target_year, target_month
        ORDER BY target_year DESC, target_month DESC
        LIMIT 12
        """
        
        monthly_accuracy = postgres_db.execute_query(monthly_query)
        
        # Get accuracy trend by days into month
        days_trend_query = f"""
        SELECT 
            days_into_month,
            COUNT(*) as forecast_count,
            AVG(accuracy_pct) as avg_accuracy,
            AVG(CASE WHEN within_range THEN 1.0 ELSE 0.0 END) * 100 as within_range_pct
        FROM forecast_history
        WHERE actual_total IS NOT NULL
        GROUP BY days_into_month
        ORDER BY days_into_month
        """
        
        days_trend = postgres_db.execute_query(days_trend_query)
        
        # Get recent forecasts with details - deduplicated to one per day per month
        recent_query = f"""
        SELECT DISTINCT ON (forecast_date, target_year, target_month)
            forecast_date,
            target_year,
            target_month,
            days_into_month,
            projected_total,
            forecast_low,
            forecast_high,
            actual_total,
            accuracy_pct,
            within_range,
            mtd_sales,
            month_progress_pct
        FROM forecast_history
        WHERE actual_total IS NOT NULL
        ORDER BY forecast_date DESC, target_year DESC, target_month DESC, id DESC
        LIMIT 20
        """
        
        recent_forecasts = postgres_db.execute_query(recent_query)
        
        # Format results
        result = {
            'summary': {
                'total_forecasts': metrics[0]['total_forecasts'] if metrics else 0,
                'completed_forecasts': metrics[0]['completed_forecasts'] if metrics else 0,
                'mape': round(float(metrics[0]['mean_absolute_percentage_error'] or 0), 2) if metrics else None,
                'best_accuracy': round(float(metrics[0]['best_accuracy'] or 0), 2) if metrics else None,
                'worst_accuracy': round(float(metrics[0]['worst_accuracy'] or 0), 2) if metrics else None,
                'within_range_pct': round(float(metrics[0]['within_range_pct'] or 0), 1) if metrics else None,
                'avg_bias': round(float(metrics[0]['avg_bias'] or 0), 2) if metrics else None,
                'performance_rating': get_performance_rating(float(metrics[0]['mean_absolute_percentage_error'] or 0)) if metrics else 'Unknown'
            },
            'monthly_accuracy': [
                {
                    'year': m['target_year'],
                    'month': m['target_month'],
                    'forecast_count': m['forecast_count'],
                    'avg_projected': round(float(m['avg_projected']), 2),
                    'actual_total': round(float(m['actual_total']), 2),
                    'mape': round(float(m['mape']), 2),
                    'bias': round(float(m['bias']), 2),
                    'within_range_pct': round(float(m['within_range_pct']), 1)
                }
                for m in monthly_accuracy
            ],
            'accuracy_by_day': [
                {
                    'day': d['days_into_month'],
                    'forecast_count': d['forecast_count'],
                    'avg_accuracy': round(float(d['avg_accuracy']), 2),
                    'within_range_pct': round(float(d['within_range_pct']), 1)
                }
                for d in days_trend
            ],
            'recent_forecasts': [
                {
                    'forecast_date': str(f['forecast_date']),
                    'target_month': f"{f['target_year']}-{f['target_month']:02d}",
                    'days_into_month': f['days_into_month'],
                    'projected': round(float(f['projected_total']), 2),
                    'actual': round(float(f['actual_total']), 2),
                    'accuracy_pct': round(float(f['accuracy_pct']), 2),
                    'within_range': bool(f['within_range']),
                    'error': round(float(f['projected_total']) - float(f['actual_total']), 2)
                }
                for f in recent_forecasts
            ]
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Failed to get forecast accuracy: {str(e)}")
        return jsonify({'error': f'Failed to get accuracy metrics: {str(e)}'}), 500


def get_performance_rating(mape):
    """Get performance rating based on MAPE"""
    if mape is None or mape == 0:
        return 'Unknown'
    elif mape < 10:
        return 'Excellent'
    elif mape < 20:
        return 'Good'
    elif mape < 30:
        return 'Fair'
    else:
        return 'Needs Improvement'


@sales_forecast_bp.route('/api/dashboard/forecast-accuracy/generate-test-data', methods=['POST'])
@jwt_required()
def generate_test_data():
    """Generate test forecast data for October 2025 for demonstration purposes"""
    # Get tenant schema
    from src.utils.tenant_utils import get_tenant_db, get_tenant_schema, get_tenant_schema
    try:
        schema = get_tenant_schema()
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    try:
        postgres_db = get_postgres_db()
        azure_db = get_tenant_db()
        
        if not postgres_db:
            return jsonify({'error': 'PostgreSQL not available'}), 500
        
        # Get October 2025 actual sales
        actual_query = f"""
        SELECT 
            SUM(GrandTotal) as actual_total,
            COUNT(*) as actual_invoices
        FROM {schema}.InvoiceReg
        WHERE YEAR(InvoiceDate) = 2025
            AND MONTH(InvoiceDate) = 10
        """
        
        actual_result = azure_db.execute_query(actual_query)[0]
        actual_total = float(actual_result['actual_total'] or 285000.00)  # Default if no data
        actual_invoices = int(actual_result['actual_invoices'] or 165)
        
        # Clear existing October 2025 test data
        delete_query = f"""
        DELETE FROM forecast_history
        WHERE target_year = 2025 AND target_month = 10
        """
        postgres_db.execute_update(delete_query)
        
        # Create test forecasts for days 5, 10, 15, 20, 25
        test_days = [5, 10, 15, 20, 25]
        days_in_month = 31
        forecasts_created = 0
        
        for day in test_days:
            # Calculate MTD sales (actual sales up to that day)
            progress_pct = day / days_in_month
            mtd_sales = actual_total * progress_pct * (0.9 + (day % 3) * 0.1)
            
            # Early forecasts less accurate, later ones more accurate
            if day <= 10:
                accuracy_factor = 0.85 + (day * 0.015)
            else:
                accuracy_factor = 0.95 + (day * 0.002)
            
            projected_total = mtd_sales / progress_pct * accuracy_factor
            
            # Confidence intervals (wider early, narrower later)
            confidence_width = max(0.05, 0.20 - (day * 0.006))
            forecast_low = projected_total * (1 - confidence_width)
            forecast_high = projected_total * (1 + confidence_width)
            
            # Check if actual falls within range
            within_range = forecast_low <= actual_total <= forecast_high
            
            # Calculate accuracy metrics
            absolute_error = abs(projected_total - actual_total)
            accuracy_pct = (absolute_error / actual_total * 100) if actual_total > 0 else 0
            
            # Typical completion percentage
            avg_pct_complete = (day / days_in_month) * 100 * (0.95 + (day % 2) * 0.05)
            
            # Insert forecast
            insert_query = f"""
            INSERT INTO forecast_history (
                forecast_date,
                forecast_timestamp,
                target_year,
                target_month,
                days_into_month,
                projected_total,
                forecast_low,
                forecast_high,
                confidence_level,
                mtd_sales,
                mtd_invoices,
                month_progress_pct,
                days_remaining,
                pipeline_value,
                avg_pct_complete,
                actual_total,
                actual_invoices,
                accuracy_pct,
                absolute_error,
                within_range
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            
            from datetime import date as dt_date
            forecast_date = dt_date(2025, 10, day)
            forecast_timestamp = datetime(2025, 10, day, 12, 0, 0)
            
            params = (
                forecast_date,
                forecast_timestamp,
                2025,
                10,
                day,
                round(projected_total, 2),
                round(forecast_low, 2),
                round(forecast_high, 2),
                '68%',
                round(mtd_sales, 2),
                int(actual_invoices * progress_pct),
                round(progress_pct * 100, 2),
                days_in_month - day,
                round(actual_total * 0.3, 2),
                round(avg_pct_complete, 2),
                round(actual_total, 2),
                actual_invoices,
                round(accuracy_pct, 2),
                round(absolute_error, 2),
                within_range
            )
            
            postgres_db.execute_insert_returning(insert_query, params)
            forecasts_created += 1
        
        # Get summary stats
        summary_query = f"""
        SELECT 
            COUNT(*) as count,
            AVG(accuracy_pct) as avg_mape,
            SUM(CASE WHEN within_range THEN 1 ELSE 0 END)::float / COUNT(*) * 100 as within_range_pct
        FROM forecast_history
        WHERE target_year = 2025 AND target_month = 10
        """
        
        summary = postgres_db.execute_query(summary_query)[0]
        
        return jsonify({
            'success': True,
            'message': f'Created {forecasts_created} test forecasts for October 2025',
            'actual_total': round(actual_total, 2),
            'actual_invoices': actual_invoices,
            'summary': {
                'total_forecasts': summary['count'],
                'avg_mape': round(float(summary['avg_mape']), 2),
                'within_range_pct': round(float(summary['within_range_pct']), 1)
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to generate test data: {str(e)}")
        return jsonify({'error': f'Failed to generate test data: {str(e)}'}), 500


@sales_forecast_bp.route('/api/dashboard/forecast-snapshot/capture', methods=['POST'])
def capture_mid_month_snapshot():
    """
    Capture a mid-month forecast snapshot.
    This endpoint is designed to be called by a scheduled job on the 15th of each month.
    No authentication required for scheduled job access.
    """
    try:
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        current_day = now.day
        
        logger.info(f"Capturing mid-month forecast snapshot for {current_year}-{current_month}-{current_day}")
        
        # Fetch the forecast data
        forecast_result = _fetch_sales_forecast_data(current_year, current_month, current_day)
        
        # Save to history with snapshot flag
        save_forecast_to_history(forecast_result, is_scheduled_snapshot=True)
        
        return jsonify({
            'success': True,
            'message': f'Mid-month snapshot captured for {current_year}-{current_month:02d}',
            'snapshot_date': f'{current_year}-{current_month:02d}-{current_day:02d}',
            'projected_total': forecast_result['forecast']['projected_total'],
            'mtd_sales': forecast_result['current_month']['mtd_sales']
        })
        
    except Exception as e:
        logger.error(f"Failed to capture mid-month snapshot: {str(e)}")
        return jsonify({'error': f'Failed to capture snapshot: {str(e)}'}), 500


@sales_forecast_bp.route('/api/dashboard/forecast-accuracy/snapshots', methods=['GET'])
@jwt_required()
def get_mid_month_snapshots():
    """
    Get all mid-month snapshots with their accuracy compared to actual results.
    Shows side-by-side comparison of 15th forecast vs end-of-month actuals.
    """
    try:
        postgres_db = get_postgres_db()
        if not postgres_db:
            return jsonify({'error': 'PostgreSQL not available'}), 500
        
        # Get all mid-month snapshots with accuracy data
        mid_month_query = f"""
        SELECT 
            target_year,
            target_month,
            forecast_date,
            forecast_timestamp,
            days_into_month,
            projected_total,
            forecast_low,
            forecast_high,
            mtd_sales as mtd_sales_at_15th,
            mtd_invoices as invoices_at_15th,
            month_progress_pct,
            actual_total,
            actual_invoice_count,
            accuracy_pct,
            absolute_error,
            within_range,
            end_of_month_captured_at,
            CASE 
                WHEN actual_total IS NOT NULL THEN 
                    ROUND(((projected_total - actual_total) / actual_total * 100)::numeric, 1)
                ELSE NULL 
            END as variance_pct,
            CASE 
                WHEN actual_total IS NOT NULL THEN 
                    projected_total - actual_total
                ELSE NULL 
            END as variance_amount
        FROM forecast_history
        WHERE is_mid_month_snapshot = TRUE
        ORDER BY target_year DESC, target_month DESC
        """
        
        snapshots = postgres_db.execute_query(mid_month_query)
        
        # Convert to list of dicts with proper formatting
        formatted_snapshots = []
        for s in snapshots:
            formatted_snapshots.append({
                'target_year': s['target_year'],
                'target_month': s['target_month'],
                'forecast_date': str(s['forecast_date']) if s['forecast_date'] else None,
                'forecast_timestamp': str(s['forecast_timestamp']) if s.get('forecast_timestamp') else None,
                'days_into_month': s['days_into_month'],
                # 15th snapshot data
                'projected_total': float(s['projected_total']) if s['projected_total'] else None,
                'forecast_low': float(s['forecast_low']) if s['forecast_low'] else None,
                'forecast_high': float(s['forecast_high']) if s['forecast_high'] else None,
                'mtd_sales_at_15th': float(s['mtd_sales_at_15th']) if s['mtd_sales_at_15th'] else None,
                'invoices_at_15th': s['invoices_at_15th'],
                'month_progress_pct': float(s['month_progress_pct']) if s['month_progress_pct'] else None,
                # End-of-month actual data
                'actual_total': float(s['actual_total']) if s['actual_total'] else None,
                'actual_invoice_count': s['actual_invoice_count'],
                'end_of_month_captured_at': str(s['end_of_month_captured_at']) if s.get('end_of_month_captured_at') else None,
                # Accuracy metrics
                'accuracy_pct': float(s['accuracy_pct']) if s['accuracy_pct'] else None,
                'absolute_error': float(s['absolute_error']) if s['absolute_error'] else None,
                'within_range': s['within_range'],
                'variance_pct': float(s['variance_pct']) if s['variance_pct'] else None,
                'variance_amount': float(s['variance_amount']) if s['variance_amount'] else None
            })
        
        # Calculate summary statistics
        completed_snapshots = [s for s in formatted_snapshots if s['actual_total'] is not None]
        
        summary = {
            'total_snapshots': len(formatted_snapshots),
            'completed_count': len(completed_snapshots),
            'pending_count': len(formatted_snapshots) - len(completed_snapshots)
        }
        
        if completed_snapshots:
            accuracies = [s['accuracy_pct'] for s in completed_snapshots if s['accuracy_pct'] is not None]
            within_range_count = sum(1 for s in completed_snapshots if s['within_range'])
            
            summary['avg_accuracy'] = round(sum(accuracies) / len(accuracies), 1) if accuracies else None
            summary['within_range_count'] = within_range_count
            summary['within_range_pct'] = round(within_range_count / len(completed_snapshots) * 100, 1)
            summary['best_accuracy'] = min(accuracies) if accuracies else None
            summary['worst_accuracy'] = max(accuracies) if accuracies else None
            
            # Calculate average variance
            variances = [s['variance_amount'] for s in completed_snapshots if s['variance_amount'] is not None]
            summary['avg_variance'] = round(sum(variances) / len(variances), 2) if variances else None
        
        return jsonify({
            'snapshots': formatted_snapshots,
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"Failed to get mid-month snapshots: {str(e)}")
        return jsonify({'error': f'Failed to get snapshots: {str(e)}'}), 500
