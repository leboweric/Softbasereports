import pandas as pd
from typing import List, Dict, Any, Optional
from ..config.database_config import DatabaseConfig
import logging
import re

# Try to import SQL drivers
HAS_PYMSSQL = False
HAS_PYODBC = False

try:
    import pymssql
    HAS_PYMSSQL = True
    logging.info("pymssql is available")
except ImportError:
    logging.warning("pymssql not available")

try:
    import pyodbc
    HAS_PYODBC = True
    logging.info("pyodbc is available")
except ImportError:
    logging.warning("pyodbc not available")

logger = logging.getLogger(__name__)

class AzureSQLService:
    """Service for connecting to and querying Azure SQL Database"""
    
    def __init__(self):
        self.server = DatabaseConfig.SERVER
        self.database = DatabaseConfig.DATABASE
        self.username = DatabaseConfig.USERNAME
        self.password = DatabaseConfig.PASSWORD
        
        # Determine which driver to use
        if HAS_PYMSSQL:
            self.driver = 'pymssql'
        elif HAS_PYODBC:
            self.driver = 'pyodbc'
        else:
            raise ImportError("Neither pymssql nor pyodbc is available")
    
    def get_connection(self):
        """Create and return a connection to Azure SQL Database"""
        logger.info(f"Attempting to connect to Azure SQL using {self.driver}: {self.server}/{self.database}")
        logger.info(f"Using username: {self.username}")
        
        try:
            if self.driver == 'pymssql':
                # Use the same connection parameters as the working test endpoint
                conn = pymssql.connect(
                    server=self.server,
                    user=self.username,
                    password=self.password,
                    database=self.database,
                    as_dict=True,
                    timeout=30
                )
                logger.info("Successfully connected to Azure SQL using pymssql")
                return conn
            else:  # pyodbc
                conn_str = (
                    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                    f"SERVER={self.server};"
                    f"DATABASE={self.database};"
                    f"UID={self.username};"
                    f"PWD={self.password};"
                    f"Encrypt=yes;"
                    f"TrustServerCertificate=no;"
                    f"Connection Timeout=30;"
                )
                conn = pyodbc.connect(conn_str)
                logger.info("Successfully connected to Azure SQL using pyodbc")
                return conn
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to connect to Azure SQL: {error_msg}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Server: {self.server}, Database: {self.database}, User: {self.username}")
            
            # Check if it's a firewall error and extract IP
            if "Client with IP address" in error_msg:
                ip_match = re.search(r"Client with IP address '(\d+\.\d+\.\d+\.\d+)'", error_msg)
                if ip_match:
                    ip_address = ip_match.group(1)
                    logger.error(f"FIREWALL ISSUE: Add IP {ip_address} to Azure SQL firewall rules")
                    raise Exception(f"Azure SQL firewall blocks Railway IP {ip_address}. Please add this IP to your Azure SQL firewall rules.")
            raise
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results as a list of dictionaries"""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if params:
                if self.driver == 'pymssql':
                    # pymssql uses %s placeholders
                    cursor.execute(query, params)
                else:  # pyodbc
                    # Convert dict params to positional params for pyodbc
                    cursor.execute(query, list(params.values()))
            else:
                cursor.execute(query)
            
            if self.driver == 'pymssql':
                # pymssql with as_dict=True returns dicts directly
                results = cursor.fetchall()
            else:  # pyodbc
                # Get column names and convert to dicts
                columns = [column[0] for column in cursor.description] if cursor.description else []
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
            
            return results
            
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def get_dataframe(self, query: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Execute a SQL query and return results as a pandas DataFrame"""
        try:
            results = self.execute_query(query, params)
            return pd.DataFrame(results)
        except Exception as e:
            logger.error(f"Failed to create DataFrame: {str(e)}")
            raise
    
    def get_tables(self) -> List[str]:
        """Get list of all views in the ben002 schema (Softbase uses views for data access)"""
        query = """
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'VIEW' 
        AND TABLE_SCHEMA = 'ben002'
        ORDER BY TABLE_NAME
        """
        results = self.execute_query(query)
        return [row['TABLE_NAME'] for row in results]
    
    def get_table_columns(self, table_name: str) -> List[Dict[str, str]]:
        """Get column information for a specific table"""
        if self.driver == 'pymssql':
            query = """
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = %s
            AND TABLE_SCHEMA = 'ben002'
            ORDER BY ORDINAL_POSITION
            """
        else:  # pyodbc
            query = """
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ?
            AND TABLE_SCHEMA = 'ben002'
            ORDER BY ORDINAL_POSITION
            """
        return self.execute_query(query, {'table_name': table_name})
    
    def test_connection(self) -> bool:
        """Test if the database connection is working"""
        try:
            conn = self.get_connection()
            conn.close()
            logger.info("Azure SQL connection test successful")
            return True
        except Exception as e:
            logger.error(f"Azure SQL connection test failed: {str(e)}")
            return False