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
            
            # Known column names from Case_Data_Summary_NOPHI table
            # Based on actual schema inspection:
            # - "Case Create Date" (date) - when case was created
            # - "Date Opened" (date) - when case was opened  
            # - "Date Closed" (date) - when case was closed
            # - "Workflow Status" (varchar) - case status
            
            date_col = 'Case Create Date'  # Use case creation date for new cases
            close_date_col = 'Date Closed'
            status_col = 'Workflow Status'
            
            logger.info(f"Using date_col={date_col}, close_date_col={close_date_col}, status_col={status_col}")
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get total open cases (current backlog) - cases without a close date
            open_cases = 0
            try:
                cursor.execute(f"""
                    SELECT COUNT(*) as count 
                    FROM [{self.ALLOWED_TABLE}]
                    WHERE [{close_date_col}] IS NULL
                """)
                result = cursor.fetchone()
                open_cases = result['count'] if result else 0
            except Exception as e:
                logger.warning(f"Could not get open cases: {str(e)}")
            
            # Get new cases in the period
            new_cases = 0
            daily_trend = []
            
            try:
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
            except Exception as e:
                logger.warning(f"Could not get new cases: {str(e)}")
            
            # Get closed cases in the period
            closed_cases = 0
            try:
                cursor.execute(f"""
                    SELECT COUNT(*) as count 
                    FROM [{self.ALLOWED_TABLE}]
                    WHERE [{close_date_col}] >= %s AND [{close_date_col}] <= %s
                """, (start_date, end_date))
                result = cursor.fetchone()
                closed_cases = result['count'] if result else 0
            except Exception as e:
                logger.warning(f"Could not get closed cases: {str(e)}")
            
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

    def get_cases_by_type(self, days=30):
        """
        Get breakdown of new cases by Case Type for the CEO Dashboard modal
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary with cases_by_type list and total count
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            
            # Use known column names
            date_col = 'Case Create Date'
            type_col = 'Case Type'
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get cases grouped by type
            cursor.execute(f"""
                SELECT 
                    COALESCE([{type_col}], 'Unknown') as case_type,
                    COUNT(*) as count
                FROM [{self.ALLOWED_TABLE}]
                WHERE [{date_col}] >= %s AND [{date_col}] <= %s
                GROUP BY [{type_col}]
                ORDER BY COUNT(*) DESC
            """, (start_date, end_date))
            
            results = cursor.fetchall()
            
            # Calculate total and percentages
            total = sum(r['count'] for r in results)
            cases_by_type = []
            
            for row in results:
                cases_by_type.append({
                    'case_type': row['case_type'] or 'Unknown',
                    'count': row['count'],
                    'percentage': round((row['count'] / total * 100), 1) if total > 0 else 0
                })
            
            conn.close()
            
            return {
                "cases_by_type": cases_by_type,
                "total": total,
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error getting cases by type: {str(e)}")
            raise

    def get_organizations(self):
        """
        Get list of all unique organizations for the customer selector
        
        Returns:
            List of organization names with case counts
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            
            cursor.execute(f"""
                SELECT 
                    [Organization] as organization,
                    COUNT(*) as case_count,
                    MAX([Case Create Date]) as last_case_date
                FROM [{self.ALLOWED_TABLE}]
                WHERE [Organization] IS NOT NULL AND [Organization] != ''
                GROUP BY [Organization]
                ORDER BY COUNT(*) DESC
            """)
            
            results = cursor.fetchall()
            conn.close()
            
            organizations = []
            for row in results:
                organizations.append({
                    'organization': row['organization'],
                    'case_count': row['case_count'],
                    'last_case_date': row['last_case_date'].isoformat() if row['last_case_date'] else None
                })
            
            return organizations
            
        except Exception as e:
            logger.error(f"Error getting organizations: {str(e)}")
            raise

    def get_customer_overview(self, organization, days=365):
        """
        Get overview metrics for a specific customer/organization
        
        Args:
            organization: The organization name to filter by
            days: Number of days to look back for metrics
            
        Returns:
            Dictionary with customer overview metrics
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get basic metrics
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total_cases,
                    COUNT(CASE WHEN [Case Create Date] >= %s THEN 1 END) as cases_in_period,
                    AVG(CAST([Satisfaction] as float)) as avg_satisfaction,
                    AVG(CAST([Net Promoter] as float)) as avg_nps,
                    MAX([Current Population]) as population,
                    MAX([Industry]) as industry,
                    MAX([Tier Level]) as tier_level,
                    SUM(CAST([Completed Session Count] as float)) as total_sessions,
                    AVG(CAST([Completed Session Count] as float)) as avg_sessions_per_case,
                    SUM(CAST([In-Person Sessions] as int)) as in_person_sessions,
                    SUM(CAST([Virtual Sessions] as int)) as virtual_sessions,
                    SUM(CAST([Web Hits] as int)) as total_web_hits,
                    SUM(CAST([Web Logins] as bigint)) as total_web_logins,
                    SUM(CAST([Mobile App Count] as int)) as total_mobile_app_usage,
                    AVG(CAST([TAT - Client Contact to Case Closed] as float)) as avg_tat_to_close,
                    AVG(CAST([TAT - Client Contact to First Session] as float)) as avg_tat_to_first_session,
                    AVG(CAST([Impact on Well Being] as float)) as avg_wellbeing_impact
                FROM [{self.ALLOWED_TABLE}]
                WHERE [Organization] = %s
            """, (start_date, organization))
            
            overview = cursor.fetchone()
            
            # Get case status breakdown
            cursor.execute(f"""
                SELECT 
                    COUNT(CASE WHEN [Date Closed] IS NULL THEN 1 END) as open_cases,
                    COUNT(CASE WHEN [Date Closed] IS NOT NULL THEN 1 END) as closed_cases
                FROM [{self.ALLOWED_TABLE}]
                WHERE [Organization] = %s AND [Case Create Date] >= %s
            """, (organization, start_date))
            
            status = cursor.fetchone()
            
            conn.close()
            
            return {
                "organization": organization,
                "total_cases": overview['total_cases'] or 0,
                "cases_in_period": overview['cases_in_period'] or 0,
                "open_cases": status['open_cases'] or 0,
                "closed_cases": status['closed_cases'] or 0,
                "avg_satisfaction": round(overview['avg_satisfaction'] or 0, 2),
                "avg_nps": round(overview['avg_nps'] or 0, 1),
                "population": overview['population'] or 0,
                "industry": overview['industry'] or 'Unknown',
                "tier_level": overview['tier_level'] or 'Unknown',
                "total_sessions": int(overview['total_sessions'] or 0),
                "avg_sessions_per_case": round(overview['avg_sessions_per_case'] or 0, 1),
                "in_person_sessions": overview['in_person_sessions'] or 0,
                "virtual_sessions": overview['virtual_sessions'] or 0,
                "total_web_hits": overview['total_web_hits'] or 0,
                "total_web_logins": overview['total_web_logins'] or 0,
                "total_mobile_app_usage": overview['total_mobile_app_usage'] or 0,
                "avg_tat_to_close": round(overview['avg_tat_to_close'] or 0, 1),
                "avg_tat_to_first_session": round(overview['avg_tat_to_first_session'] or 0, 1),
                "avg_wellbeing_impact": round(overview['avg_wellbeing_impact'] or 0, 2),
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error getting customer overview: {str(e)}")
            raise

    def get_customer_service_breakdown(self, organization, days=365):
        """
        Get breakdown of services used by a customer
        
        Args:
            organization: The organization name to filter by
            days: Number of days to look back
            
        Returns:
            Dictionary with service breakdown data
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Cases by Case Type
            cursor.execute(f"""
                SELECT 
                    COALESCE([Case Type], 'Unknown') as case_type,
                    COUNT(*) as count
                FROM [{self.ALLOWED_TABLE}]
                WHERE [Organization] = %s AND [Case Create Date] >= %s
                GROUP BY [Case Type]
                ORDER BY COUNT(*) DESC
            """, (organization, start_date))
            
            case_types = cursor.fetchall()
            total_cases = sum(r['count'] for r in case_types)
            
            by_case_type = [{
                'name': row['case_type'] or 'Unknown',
                'count': row['count'],
                'percentage': round((row['count'] / total_cases * 100), 1) if total_cases > 0 else 0
            } for row in case_types]
            
            # Cases by Solution
            cursor.execute(f"""
                SELECT 
                    COALESCE([Solution], 'Unknown') as solution,
                    COUNT(*) as count
                FROM [{self.ALLOWED_TABLE}]
                WHERE [Organization] = %s AND [Case Create Date] >= %s
                GROUP BY [Solution]
                ORDER BY COUNT(*) DESC
            """, (organization, start_date))
            
            solutions = cursor.fetchall()
            
            by_solution = [{
                'name': row['solution'] or 'Unknown',
                'count': row['count'],
                'percentage': round((row['count'] / total_cases * 100), 1) if total_cases > 0 else 0
            } for row in solutions]
            
            # Top Presenting Problems
            cursor.execute(f"""
                SELECT TOP 10
                    COALESCE([Primary Presenting Problem], 'Unknown') as problem,
                    COUNT(*) as count
                FROM [{self.ALLOWED_TABLE}]
                WHERE [Organization] = %s AND [Case Create Date] >= %s
                GROUP BY [Primary Presenting Problem]
                ORDER BY COUNT(*) DESC
            """, (organization, start_date))
            
            problems = cursor.fetchall()
            
            top_problems = [{
                'name': row['problem'] or 'Unknown',
                'count': row['count'],
                'percentage': round((row['count'] / total_cases * 100), 1) if total_cases > 0 else 0
            } for row in problems]
            
            conn.close()
            
            return {
                "by_case_type": by_case_type,
                "by_solution": by_solution,
                "top_presenting_problems": top_problems,
                "total_cases": total_cases,
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error getting customer service breakdown: {str(e)}")
            raise

    def get_customer_trends(self, organization, days=365):
        """
        Get trend data for a customer over time
        
        Args:
            organization: The organization name to filter by
            days: Number of days to look back
            
        Returns:
            Dictionary with trend data
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Monthly case volume trend
            cursor.execute(f"""
                SELECT 
                    YEAR([Case Create Date]) as year,
                    MONTH([Case Create Date]) as month,
                    COUNT(*) as case_count,
                    AVG(CAST([Satisfaction] as float)) as avg_satisfaction
                FROM [{self.ALLOWED_TABLE}]
                WHERE [Organization] = %s 
                    AND [Case Create Date] >= %s 
                    AND [Case Create Date] IS NOT NULL
                GROUP BY YEAR([Case Create Date]), MONTH([Case Create Date])
                ORDER BY YEAR([Case Create Date]), MONTH([Case Create Date])
            """, (organization, start_date))
            
            monthly_data = cursor.fetchall()
            
            monthly_trend = [{
                'year': row['year'],
                'month': row['month'],
                'month_label': f"{row['year']}-{str(row['month']).zfill(2)}",
                'case_count': row['case_count'],
                'avg_satisfaction': round(row['avg_satisfaction'] or 0, 2)
            } for row in monthly_data]
            
            # Digital engagement trend (monthly)
            cursor.execute(f"""
                SELECT 
                    YEAR([Case Create Date]) as year,
                    MONTH([Case Create Date]) as month,
                    SUM(CAST([Web Hits] as int)) as web_hits,
                    SUM(CAST([Web Logins] as bigint)) as web_logins,
                    SUM(CAST([Mobile App Count] as int)) as mobile_app
                FROM [{self.ALLOWED_TABLE}]
                WHERE [Organization] = %s 
                    AND [Case Create Date] >= %s 
                    AND [Case Create Date] IS NOT NULL
                GROUP BY YEAR([Case Create Date]), MONTH([Case Create Date])
                ORDER BY YEAR([Case Create Date]), MONTH([Case Create Date])
            """, (organization, start_date))
            
            engagement_data = cursor.fetchall()
            
            engagement_trend = [{
                'month_label': f"{row['year']}-{str(row['month']).zfill(2)}",
                'web_hits': row['web_hits'] or 0,
                'web_logins': row['web_logins'] or 0,
                'mobile_app': row['mobile_app'] or 0
            } for row in engagement_data]
            
            conn.close()
            
            return {
                "monthly_case_trend": monthly_trend,
                "engagement_trend": engagement_trend,
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error getting customer trends: {str(e)}")
            raise

    def get_customer_outcomes(self, organization, days=365):
        """
        Get outcomes and performance metrics for a customer
        
        Args:
            organization: The organization name to filter by
            days: Number of days to look back
            
        Returns:
            Dictionary with outcomes data
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Closing disposition breakdown
            cursor.execute(f"""
                SELECT 
                    COALESCE([Closing Disposition], 'Unknown') as disposition,
                    COUNT(*) as count
                FROM [{self.ALLOWED_TABLE}]
                WHERE [Organization] = %s 
                    AND [Case Create Date] >= %s
                    AND [Date Closed] IS NOT NULL
                GROUP BY [Closing Disposition]
                ORDER BY COUNT(*) DESC
            """, (organization, start_date))
            
            dispositions = cursor.fetchall()
            total_closed = sum(r['count'] for r in dispositions)
            
            by_disposition = [{
                'name': row['disposition'] or 'Unknown',
                'count': row['count'],
                'percentage': round((row['count'] / total_closed * 100), 1) if total_closed > 0 else 0
            } for row in dispositions]
            
            # Session modality breakdown
            cursor.execute(f"""
                SELECT 
                    SUM(CAST([In-Person Sessions] as int)) as in_person,
                    SUM(CAST([Virtual Sessions] as int)) as virtual
                FROM [{self.ALLOWED_TABLE}]
                WHERE [Organization] = %s AND [Case Create Date] >= %s
            """, (organization, start_date))
            
            modality = cursor.fetchone()
            in_person = modality['in_person'] or 0
            virtual = modality['virtual'] or 0
            total_sessions = in_person + virtual
            
            modality_breakdown = [
                {'name': 'In-Person', 'count': in_person, 'percentage': round((in_person / total_sessions * 100), 1) if total_sessions > 0 else 0},
                {'name': 'Virtual', 'count': virtual, 'percentage': round((virtual / total_sessions * 100), 1) if total_sessions > 0 else 0}
            ]
            
            # Pre/Post wellbeing scores (if available)
            cursor.execute(f"""
                SELECT 
                    AVG(CAST([Pre: Well-Being] as float)) as pre_wellbeing,
                    AVG(CAST([Post: Well-Being] as float)) as post_wellbeing,
                    AVG(CAST([Pre: Burnout] as float)) as pre_burnout,
                    AVG(CAST([Post: Burnout] as float)) as post_burnout,
                    AVG(CAST([Pre: Retention] as float)) as pre_retention,
                    AVG(CAST([Post: Retention] as float)) as post_retention
                FROM [{self.ALLOWED_TABLE}]
                WHERE [Organization] = %s AND [Case Create Date] >= %s
            """, (organization, start_date))
            
            outcomes = cursor.fetchone()
            
            conn.close()
            
            return {
                "by_disposition": by_disposition,
                "modality_breakdown": modality_breakdown,
                "total_closed_cases": total_closed,
                "pre_post_scores": {
                    "wellbeing": {
                        "pre": round(outcomes['pre_wellbeing'] or 0, 1),
                        "post": round(outcomes['post_wellbeing'] or 0, 1)
                    },
                    "burnout": {
                        "pre": round(outcomes['pre_burnout'] or 0, 1),
                        "post": round(outcomes['post_burnout'] or 0, 1)
                    },
                    "retention": {
                        "pre": round(outcomes['pre_retention'] or 0, 1),
                        "post": round(outcomes['post_retention'] or 0, 1)
                    }
                },
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error getting customer outcomes: {str(e)}")
            raise
