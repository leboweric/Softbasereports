#!/usr/bin/env python3
"""
Create test forecast data for October 2025 to demonstrate Forecast Accuracy dashboard
"""

import os
import sys
from datetime import datetime, date
import psycopg2
from psycopg2.extras import RealDictCursor

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import pymssql
from config.database_config import DatabaseConfig

def get_october_actuals():
    """Get actual October 2025 sales data"""
    print("Fetching October 2025 actual sales data...")
    
    try:
        # Try to connect to Azure SQL
        conn = pymssql.connect(
            server=DatabaseConfig.SERVER,
            user=DatabaseConfig.USERNAME,
            password=DatabaseConfig.PASSWORD,
            database=DatabaseConfig.DATABASE
        )
        
        cursor = conn.cursor(as_dict=True)
        
        query = """
        SELECT 
            SUM(GrandTotal) as actual_total,
            COUNT(*) as actual_invoices
        FROM ben002.InvoiceReg
        WHERE YEAR(InvoiceDate) = 2025
            AND MONTH(InvoiceDate) = 10
        """
        
        cursor.execute(query)
        result = cursor.fetchone()
        
        actual_total = float(result['actual_total'] or 0)
        actual_invoices = int(result['actual_invoices'] or 0)
        
        cursor.close()
        conn.close()
        
        print(f"October 2025 Actuals: ${actual_total:,.2f} ({actual_invoices} invoices)")
        
        return actual_total, actual_invoices
        
    except Exception as e:
        print(f"Could not connect to Azure SQL (firewall restriction)")
        print(f"Using realistic dummy data for demonstration...")
        # Use realistic sales data for demo
        actual_total = 285000.00
        actual_invoices = 165
        print(f"October 2025 Actuals (Demo): ${actual_total:,.2f} ({actual_invoices} invoices)")
        return actual_total, actual_invoices


def get_postgres_connection():
    """Get PostgreSQL connection"""
    database_url = (
        os.environ.get('POSTGRES_URL') or 
        os.environ.get('DATABASE_URL') or
        os.environ.get('DATABASE_PRIVATE_URL') or
        os.environ.get('POSTGRES_PRIVATE_URL')
    )
    
    if not database_url:
        raise Exception("PostgreSQL URL not found in environment variables")
    
    # Fix URL format if needed
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgres://', 1)
    
    return psycopg2.connect(database_url, cursor_factory=RealDictCursor)


def create_test_forecasts(actual_total, actual_invoices):
    """Create realistic test forecasts for October at different days of the month"""
    
    # Days in October
    days_in_month = 31
    
    # Create forecasts for days 5, 10, 15, 20, 25 (showing accuracy improvement)
    test_days = [5, 10, 15, 20, 25]
    
    forecasts = []
    
    for day in test_days:
        # Calculate MTD sales (actual sales up to that day)
        # Assume roughly linear distribution with some variance
        progress_pct = day / days_in_month
        mtd_sales = actual_total * progress_pct * (0.9 + (day % 3) * 0.1)  # Add variance
        
        # Early forecasts are less accurate, later ones more accurate
        if day <= 10:
            # Early month - wider variance
            accuracy_factor = 0.85 + (day * 0.015)  # 85-100%
        else:
            # Later in month - more accurate
            accuracy_factor = 0.95 + (day * 0.002)  # 95-105%
        
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
        
        # Typical completion percentage for this day (historical average)
        avg_pct_complete = (day / days_in_month) * 100 * (0.95 + (day % 2) * 0.05)
        
        forecast = {
            'forecast_date': date(2025, 10, day),
            'target_year': 2025,
            'target_month': 10,
            'days_into_month': day,
            'projected_total': round(projected_total, 2),
            'forecast_low': round(forecast_low, 2),
            'forecast_high': round(forecast_high, 2),
            'confidence_level': '68%',
            'mtd_sales': round(mtd_sales, 2),
            'mtd_invoices': int(actual_invoices * progress_pct),
            'month_progress_pct': round(progress_pct * 100, 2),
            'days_remaining': days_in_month - day,
            'pipeline_value': round(actual_total * 0.3, 2),  # Assume 30% pipeline
            'avg_pct_complete': round(avg_pct_complete, 2),
            'actual_total': round(actual_total, 2),
            'actual_invoices': actual_invoices,
            'accuracy_pct': round(accuracy_pct, 2),
            'absolute_error': round(absolute_error, 2),
            'within_range': within_range
        }
        
        forecasts.append(forecast)
        
        print(f"Day {day:2d}: Projected ${projected_total:,.0f} | Actual ${actual_total:,.0f} | MAPE {accuracy_pct:.1f}% | In Range: {within_range}")
    
    return forecasts


def insert_test_forecasts(forecasts):
    """Insert test forecasts into PostgreSQL"""
    print("\nInserting test forecasts into database...")
    
    conn = get_postgres_connection()
    
    try:
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'forecast_history'
            )
        """)
        
        if not cursor.fetchone()[0]:
            print("ERROR: forecast_history table does not exist!")
            return False
        
        # Clear any existing October 2025 test data
        cursor.execute("""
            DELETE FROM forecast_history
            WHERE target_year = 2025 AND target_month = 10
        """)
        deleted = cursor.rowcount
        if deleted > 0:
            print(f"Cleared {deleted} existing October 2025 forecasts")
        
        # Insert test forecasts
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
        
        for forecast in forecasts:
            cursor.execute(insert_query, (
                forecast['forecast_date'],
                datetime.combine(forecast['forecast_date'], datetime.min.time()),
                forecast['target_year'],
                forecast['target_month'],
                forecast['days_into_month'],
                forecast['projected_total'],
                forecast['forecast_low'],
                forecast['forecast_high'],
                forecast['confidence_level'],
                forecast['mtd_sales'],
                forecast['mtd_invoices'],
                forecast['month_progress_pct'],
                forecast['days_remaining'],
                forecast['pipeline_value'],
                forecast['avg_pct_complete'],
                forecast['actual_total'],
                forecast['actual_invoices'],
                forecast['accuracy_pct'],
                forecast['absolute_error'],
                forecast['within_range']
            ))
        
        conn.commit()
        print(f"✅ Successfully inserted {len(forecasts)} test forecasts!")
        
        # Verify
        cursor.execute("""
            SELECT COUNT(*) as count,
                   AVG(accuracy_pct) as avg_mape,
                   SUM(CASE WHEN within_range THEN 1 ELSE 0 END)::float / COUNT(*) * 100 as within_range_pct
            FROM forecast_history
            WHERE target_year = 2025 AND target_month = 10
        """)
        
        result = cursor.fetchone()
        print(f"\nVerification:")
        print(f"  Total forecasts: {result['count']}")
        print(f"  Average MAPE: {result['avg_mape']:.2f}%")
        print(f"  Within range: {result['within_range_pct']:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        conn.rollback()
        return False
        
    finally:
        cursor.close()
        conn.close()


def main():
    print("=" * 60)
    print("Creating Test Forecast Data for October 2025")
    print("=" * 60)
    print()
    
    try:
        # Get October actuals
        actual_total, actual_invoices = get_october_actuals()
        
        print()
        
        # Create test forecasts
        forecasts = create_test_forecasts(actual_total, actual_invoices)
        
        print()
        
        # Insert into database
        success = insert_test_forecasts(forecasts)
        
        print()
        print("=" * 60)
        if success:
            print("✅ Test data created successfully!")
            print("Go to Dashboard → Forecast Accuracy tab to see the results")
        else:
            print("❌ Failed to create test data")
        print("=" * 60)
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
