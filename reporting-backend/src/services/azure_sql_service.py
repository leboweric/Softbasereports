import pandas as pd
from typing import List, Dict, Any, Optional
from ..config.database_config import DatabaseConfig
import logging

try:
    import pyodbc
    HAS_PYODBC = True
except ImportError:
    HAS_PYODBC = False
    logging.warning("pyodbc not available")

logger = logging.getLogger(__name__)

class AzureSQLService:
    """Service for connecting to and querying Azure SQL Database"""
    
    def __init__(self):
        self.server = DatabaseConfig.SERVER
        self.database = DatabaseConfig.DATABASE
        self.username = DatabaseConfig.USERNAME
        self.password = DatabaseConfig.PASSWORD
    
    def get_connection(self):
        """Create and return a connection to Azure SQL Database"""
        if not HAS_PYODBC:
            raise ImportError("pyodbc is not available")
            
        logger.info(f"Attempting to connect to Azure SQL: {self.server}/{self.database}")
        logger.info(f"Using username: {self.username}")
        
        try:
            # Connection string for Azure SQL
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
            logger.info("Successfully connected to Azure SQL")
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to Azure SQL: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Server: {self.server}, Database: {self.database}, User: {self.username}")
            raise
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results as a list of dictionaries"""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if params:
                # Convert dict params to positional params for pyodbc
                cursor.execute(query, list(params.values()))
            else:
                cursor.execute(query)
            
            # Get column names
            columns = [column[0] for column in cursor.description] if cursor.description else []
            
            # Fetch all results and convert to list of dicts
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
        """Get list of all tables in the database"""
        query = """
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE' 
        ORDER BY TABLE_NAME
        """
        results = self.execute_query(query)
        return [row['TABLE_NAME'] for row in results]
    
    def get_table_columns(self, table_name: str) -> List[Dict[str, str]]:
        """Get column information for a specific table"""
        query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = ?
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