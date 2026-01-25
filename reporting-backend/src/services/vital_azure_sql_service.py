"""
VITAL Azure SQL Service
Provides secure, read-only access to Case_Data_Summary_NOPHI table for VITAL WorkLife
"""

import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Lazy import pymssql to handle environments where it's not available
pymssql = None

def get_pymssql():
    """Lazy load pymssql"""
    global pymssql
    if pymssql is None:
        try:
            import pymssql as _pymssql
            pymssql = _pymssql
        except ImportError:
            logger.warning("pymssql not available - Azure SQL features disabled")
            raise ImportError("pymssql is required for Azure SQL connectivity")
    return pymssql


class VitalAzureSQLService:
    """Service class for VITAL Azure SQL data access - restricted to Case_Data_Summary_NOPHI"""
    
    # Only allow access to this specific table for security
    ALLOWED_TABLE = "Case_Data_Summary_NOPHI"
    
    def __init__(self, server=None, database=None, username=None, password=None):
        """Initialize with connection credentials"""
        self.server = server or os.environ.get('VITAL_AZURE_SQL_SERVER')
        self.database = database or os.environ.get('VITAL_AZURE_SQL_DATABASE')
        self.username = username or os.environ.get('VITAL_AZURE_SQL_USERNAME')
        self.password = password or os.environ.get('VITAL_AZURE_SQL_PASSWORD')
        
        if not all([self.server, self.database, self.username, self.password]):
            raise ValueError("Azure SQL credentials not fully configured")
    
    def _get_connection(self):
        """Create a new database connection"""
        _pymssql = get_pymssql()
        return _pymssql.connect(
            server=self.server,
            user=self.username,
            password=self.password,
            database=self.database,
            timeout=30
        )
    
    def test_connection(self):
        """Test database connectivity"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            conn.close()
            return {"status": "connected", "result": result[0]}
        except Exception as e:
            logger.error(f"Azure SQL connection test failed: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def get_table_schema(self):
        """Get the schema/columns of the Case_Data_Summary_NOPHI table"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(f"""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    CHARACTER_MAXIMUM_LENGTH,
                    IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = '{self.ALLOWED_TABLE}'
                ORDER BY ORDINAL_POSITION
            """)
            
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    "name": row[0],
                    "type": row[1],
                    "max_length": row[2],
                    "nullable": row[3] == "YES"
                })
            
            conn.close()
            return columns
        except Exception as e:
            logger.error(f"Error getting table schema: {str(e)}")
            raise
    
    def get_row_count(self):
        """Get total row count"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM [{self.ALLOWED_TABLE}]")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Error getting row count: {str(e)}")
            raise
    
    def get_summary_stats(self):
        """Get summary statistics from the case data"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            
            # Get total count
            cursor.execute(f"SELECT COUNT(*) as total FROM [{self.ALLOWED_TABLE}]")
            total = cursor.fetchone()['total']
            
            # Try to get column names to understand the data structure
            cursor.execute(f"""
                SELECT TOP 1 * FROM [{self.ALLOWED_TABLE}]
            """)
            sample_row = cursor.fetchone()
            columns = list(sample_row.keys()) if sample_row else []
            
            conn.close()
            
            return {
                "total_records": total,
                "columns": columns,
                "sample_columns_count": len(columns)
            }
        except Exception as e:
            logger.error(f"Error getting summary stats: {str(e)}")
            raise
    
    def get_case_data(self, limit=100, offset=0):
        """
        Get case data with pagination
        
        Args:
            limit: Maximum rows to return (default 100, max 1000)
            offset: Number of rows to skip for pagination
        """
        try:
            # Enforce limits for security/performance
            limit = min(limit, 1000)
            
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            
            # Build query with pagination
            query = f"""
                SELECT * FROM [{self.ALLOWED_TABLE}]
                ORDER BY (SELECT NULL)
                OFFSET {offset} ROWS
                FETCH NEXT {limit} ROWS ONLY
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Convert any bytes to strings and handle dates
            clean_rows = []
            for row in rows:
                clean_row = {}
                for key, value in row.items():
                    if isinstance(value, bytes):
                        try:
                            clean_row[key] = value.decode('utf-8')
                        except:
                            clean_row[key] = str(value)
                    elif isinstance(value, datetime):
                        clean_row[key] = value.isoformat()
                    else:
                        clean_row[key] = value
                clean_rows.append(clean_row)
            
            # Get total count for pagination info
            cursor.execute(f"SELECT COUNT(*) as total FROM [{self.ALLOWED_TABLE}]")
            total = cursor.fetchone()['total']
            
            conn.close()
            
            return {
                "data": clean_rows,
                "pagination": {
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                    "has_more": (offset + limit) < total
                }
            }
        except Exception as e:
            logger.error(f"Error getting case data: {str(e)}")
            raise
    
    def get_aggregated_data(self, group_by_column):
        """
        Get aggregated counts grouped by a specific column
        
        Args:
            group_by_column: Column name to group by
        """
        try:
            # Validate column exists (security measure)
            schema = self.get_table_schema()
            valid_columns = [col['name'] for col in schema]
            
            if group_by_column not in valid_columns:
                raise ValueError(f"Invalid column: {group_by_column}")
            
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            
            query = f"""
                SELECT 
                    [{group_by_column}] as category,
                    COUNT(*) as count
                FROM [{self.ALLOWED_TABLE}]
                GROUP BY [{group_by_column}]
                ORDER BY count DESC
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            # Clean up results
            clean_results = []
            for row in results:
                clean_row = {}
                for key, value in row.items():
                    if isinstance(value, bytes):
                        try:
                            clean_row[key] = value.decode('utf-8')
                        except:
                            clean_row[key] = str(value)
                    elif isinstance(value, datetime):
                        clean_row[key] = value.isoformat()
                    else:
                        clean_row[key] = value
                clean_results.append(clean_row)
            
            conn.close()
            
            return {
                "group_by": group_by_column,
                "data": clean_results
            }
        except Exception as e:
            logger.error(f"Error getting aggregated data: {str(e)}")
            raise
    
    def get_dashboard_data(self):
        """
        Get comprehensive dashboard data for the Case Data Summary
        Returns summary stats, column info, and sample aggregations
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            
            # Get total count
            cursor.execute(f"SELECT COUNT(*) as total FROM [{self.ALLOWED_TABLE}]")
            total_records = cursor.fetchone()['total']
            
            # Get column info
            cursor.execute(f"""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = '{self.ALLOWED_TABLE}'
                ORDER BY ORDINAL_POSITION
            """)
            columns = [{"name": row['COLUMN_NAME'], "type": row['DATA_TYPE']} for row in cursor.fetchall()]
            
            # Get sample data (first 10 rows)
            cursor.execute(f"SELECT TOP 10 * FROM [{self.ALLOWED_TABLE}]")
            sample_data = cursor.fetchall()
            
            # Clean sample data
            clean_sample = []
            for row in sample_data:
                clean_row = {}
                for key, value in row.items():
                    if isinstance(value, bytes):
                        try:
                            clean_row[key] = value.decode('utf-8')
                        except:
                            clean_row[key] = str(value)
                    elif isinstance(value, datetime):
                        clean_row[key] = value.isoformat()
                    else:
                        clean_row[key] = value
                clean_sample.append(clean_row)
            
            conn.close()
            
            return {
                "table_name": self.ALLOWED_TABLE,
                "total_records": total_records,
                "columns": columns,
                "column_count": len(columns),
                "sample_data": clean_sample,
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting dashboard data: {str(e)}")
            raise

    def get_case_metrics(self, days=30):
        """
        Get case metrics for the CEO Dashboard
        
        Args:
            days: Number of days to look back for metrics
            
        Returns:
            Dictionary with new_cases, closed_cases, open_cases, and daily_trend
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            
            # First, let's understand what date columns are available
            cursor.execute(f"""
                SELECT COLUMN_NAME, DATA_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = '{self.ALLOWED_TABLE}'
                AND (DATA_TYPE LIKE '%date%' OR DATA_TYPE LIKE '%time%')
            """)
            date_columns = cursor.fetchall()
            logger.info(f"Date columns found: {date_columns}")
            
            # Get column names to find status and date fields
            cursor.execute(f"SELECT TOP 1 * FROM [{self.ALLOWED_TABLE}]")
            sample = cursor.fetchone()
            columns = list(sample.keys()) if sample else []
            logger.info(f"All columns: {columns}")
            
            # Look for common date column patterns
            date_col = None
            close_date_col = None
            status_col = None
            
            for col in columns:
                col_lower = col.lower()
                if 'open' in col_lower and 'date' in col_lower:
                    date_col = col
                elif 'created' in col_lower or 'create_date' in col_lower:
                    date_col = date_col or col
                elif 'close' in col_lower and 'date' in col_lower:
                    close_date_col = col
                elif 'status' in col_lower:
                    status_col = col
            
            # If no specific date column found, try to use the first date column
            if not date_col and date_columns:
                date_col = date_columns[0]['COLUMN_NAME']
            
            logger.info(f"Using date_col={date_col}, close_date_col={close_date_col}, status_col={status_col}")
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get total open cases (current backlog)
            open_cases = 0
            if status_col:
                cursor.execute(f"""
                    SELECT COUNT(*) as count 
                    FROM [{self.ALLOWED_TABLE}]
                    WHERE [{status_col}] IN ('Open', 'Active', 'In Progress', 'Pending')
                """)
                result = cursor.fetchone()
                open_cases = result['count'] if result else 0
            
            # Get new cases in the period
            new_cases = 0
            daily_trend = []
            
            if date_col:
                # Count new cases in the period
                cursor.execute(f"""
                    SELECT COUNT(*) as count 
                    FROM [{self.ALLOWED_TABLE}]
                    WHERE [{date_col}] >= %s AND [{date_col}] <= %s
                """, (start_date, end_date))
                result = cursor.fetchone()
                new_cases = result['count'] if result else 0
                
                # Get daily trend
                cursor.execute(f"""
                    SELECT 
                        CAST([{date_col}] AS DATE) as date,
                        COUNT(*) as new_cases
                    FROM [{self.ALLOWED_TABLE}]
                    WHERE [{date_col}] >= %s AND [{date_col}] <= %s
                    GROUP BY CAST([{date_col}] AS DATE)
                    ORDER BY date
                """, (start_date, end_date))
                
                trend_data = cursor.fetchall()
                for row in trend_data:
                    daily_trend.append({
                        'date': row['date'].isoformat() if hasattr(row['date'], 'isoformat') else str(row['date']),
                        'new_cases': row['new_cases']
                    })
            
            # Get closed cases in the period
            closed_cases = 0
            if close_date_col:
                cursor.execute(f"""
                    SELECT COUNT(*) as count 
                    FROM [{self.ALLOWED_TABLE}]
                    WHERE [{close_date_col}] >= %s AND [{close_date_col}] <= %s
                """, (start_date, end_date))
                result = cursor.fetchone()
                closed_cases = result['count'] if result else 0
            
            # Get total cases for context
            cursor.execute(f"SELECT COUNT(*) as total FROM [{self.ALLOWED_TABLE}]")
            total_cases = cursor.fetchone()['total']
            
            conn.close()
            
            return {
                "new_cases": new_cases,
                "closed_cases": closed_cases,
                "open_cases": open_cases,
                "total_cases": total_cases,
                "daily_trend": daily_trend,
                "period_days": days,
                "date_column_used": date_col,
                "close_date_column_used": close_date_col,
                "status_column_used": status_col
            }
            
        except Exception as e:
            logger.error(f"Error getting case metrics: {str(e)}")
            raise
