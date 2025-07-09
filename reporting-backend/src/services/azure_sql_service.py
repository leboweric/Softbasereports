import pandas as pd
from typing import List, Dict, Any, Optional
from ..config.database_config import DatabaseConfig
import logging

try:
    import pymssql
    HAS_PYMSSQL = True
except ImportError:
    HAS_PYMSSQL = False
    logging.warning("pymssql not available")

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
        if not HAS_PYMSSQL:
            raise ImportError("pymssql is not available")
            
        logger.info(f"Attempting to connect to Azure SQL: {self.server}/{self.database}")
        logger.info(f"Using username: {self.username}")
        
        try:
            conn = pymssql.connect(
                server=self.server,
                user=self.username,
                password=self.password,
                database=self.database,
                tds_version='7.0',
                as_dict=True
            )
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
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()
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
        WHERE TABLE_NAME = %s
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