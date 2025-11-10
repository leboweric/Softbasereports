"""
Scheduled Forecast Service
Generates daily forecasts automatically for consistent accuracy tracking
"""

import logging
from datetime import datetime
import calendar
from statistics import stdev, mean

from .azure_sql_service import AzureSQLService
from .postgres_service import get_postgres_db

logger = logging.getLogger(__name__)


class ScheduledForecastService:
    """Service for generating scheduled daily forecasts"""
    
    @staticmethod
    def generate_daily_forecast():
        """
        Generate and save daily forecast
        Called by cron job at 8 AM daily
        """
        try:
            logger.info("Starting scheduled daily forecast generation...")
            
            azure_db = AzureSQLService()
            postgres_db = get_postgres_db()
            
            if not postgres_db:
                logger.error("PostgreSQL not available - cannot save forecast")
                return False
            
            now = datetime.now()
            current_year = now.year
            current_month = now.month
            current_day = now.day
            
            # Get historical daily sales patterns (last 12 months)
            daily_pattern_query = """
            WITH DailySales AS (
                SELECT 
                    YEAR(InvoiceDate) as year,
                    MONTH(InvoiceDate) as month,
                    DAY(InvoiceDate) as day,
                    SUM(GrandTotal) as daily_total,
                    COUNT(*) as invoice_count
                FROM ben002.InvoiceReg
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
            FROM ben002.InvoiceReg
            WHERE YEAR(InvoiceDate) = {current_year}
                AND MONTH(InvoiceDate) = {current_month}
            """
            
            # Get quotes pipeline
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
            daily_patterns = azure_db.execute_query(daily_pattern_query)
            current_month_data = azure_db.execute_query(current_month_query)[0]
            quotes_data = azure_db.execute_query(quotes_pipeline_query)[0]
            
            # Analyze patterns and generate forecast
            forecast_result = ScheduledForecastService._analyze_sales_patterns(
                daily_patterns,
                current_month_data,
                quotes_data,
                current_year,
                current_month,
                current_day
            )
            
            # Save to history
            ScheduledForecastService._save_forecast_to_history(forecast_result, postgres_db)
            
            logger.info(f"✅ Daily forecast generated successfully: ${forecast_result['forecast']['projected_total']:,.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate daily forecast: {str(e)}")
            return False
    
    @staticmethod
    def _analyze_sales_patterns(daily_patterns, current_month_data, quotes_data, current_year, current_month, current_day):
        """Analyze historical patterns and generate forecast"""
        
        # Current month progress
        days_in_month = calendar.monthrange(current_year, current_month)[1]
        month_progress = current_day / days_in_month
        
        mtd_sales = float(current_month_data['mtd_sales'] or 0)
        mtd_invoices = int(current_month_data['mtd_invoices'] or 0)
        
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
        months_data = ScheduledForecastService._group_by_month(daily_patterns)
        
        for month_data in months_data:
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
            avg_pct_complete = (current_day / days_in_month) * 100
            pct_complete_std = 5
        
        # Generate forecasts
        if avg_pct_complete > 5:
            projected_total = mtd_sales / (avg_pct_complete / 100)
            
            if pct_complete_std > 0:
                lower_pct = max(avg_pct_complete - pct_complete_std, current_day / days_in_month * 100)
                upper_pct = avg_pct_complete + pct_complete_std
                forecast_low = mtd_sales / (upper_pct / 100)
                forecast_high = mtd_sales / (lower_pct / 100)
            else:
                forecast_low = projected_total * 0.9
                forecast_high = projected_total * 1.1
        else:
            daily_rate = mtd_sales / current_day if current_day > 0 else 0
            projected_total = daily_rate * days_in_month
            forecast_low = projected_total * 0.8
            forecast_high = projected_total * 1.2
        
        # Quote conversion impact
        pipeline_value = float(quotes_data['pipeline_value'] or 0)
        historical_conversion_rate = 0.3
        expected_pipeline_revenue = pipeline_value * historical_conversion_rate
        
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
                'daily_run_rate_needed': round((projected_total - mtd_sales) / (days_in_month - current_day), 2) if days_in_month > current_day else 0
            }
        }
    
    @staticmethod
    def _group_by_month(daily_patterns):
        """Group daily patterns by month"""
        months = {}
        for row in daily_patterns:
            key = f"{row['year']}-{row['month']}"
            if key not in months:
                months[key] = []
            months[key].append(row)
        return months.values()
    
    @staticmethod
    def _save_forecast_to_history(forecast_result, postgres_db):
        """Save forecast to PostgreSQL for accuracy tracking"""
        try:
            current = forecast_result['current_month']
            forecast = forecast_result['forecast']
            analysis = forecast_result['analysis']
            
            insert_query = """
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
                avg_pct_complete
            ) VALUES (
                CURRENT_DATE,
                CURRENT_TIMESTAMP,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
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
                0,  # mtd_invoices not in simplified version
                current['month_progress_pct'],
                current['days_remaining'],
                forecast['expected_from_pipeline'],
                analysis['typical_pct_complete_by_today']
            )
            
            result = postgres_db.execute_insert_returning(insert_query, params)
            if result:
                logger.info(f"Saved scheduled forecast to history with ID: {result['id']}")
            
        except Exception as e:
            logger.error(f"Error saving scheduled forecast to history: {str(e)}")
            raise
