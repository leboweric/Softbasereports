import os
from urllib.parse import quote_plus

class DatabaseConfig:
    """Configuration for Azure SQL Database connection"""
    
    # Azure SQL Database credentials
    SERVER = os.environ.get('AZURE_SQL_SERVER', 'evo1-sql-replica.database.windows.net')
    DATABASE = os.environ.get('AZURE_SQL_DATABASE', 'evo')
    USERNAME = os.environ.get('AZURE_SQL_USERNAME', 'ben002user')
    PASSWORD = os.environ.get('AZURE_SQL_PASSWORD', 'g6O8CE5mT83mDYOW')
    
    # Connection string for pyodbc
    @staticmethod
    def get_connection_string():
        """Get the Azure SQL connection string"""
        params = quote_plus(
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={DatabaseConfig.SERVER};"
            f"DATABASE={DatabaseConfig.DATABASE};"
            f"UID={DatabaseConfig.USERNAME};"
            f"PWD={DatabaseConfig.PASSWORD};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )
        return f"mssql+pyodbc:///?odbc_connect={params}"
    
    # Alternative connection string for pymssql
    @staticmethod
    def get_pymssql_connection_string():
        """Get the Azure SQL connection string for pymssql"""
        return (
            f"mssql+pymssql://{DatabaseConfig.USERNAME}:{DatabaseConfig.PASSWORD}"
            f"@{DatabaseConfig.SERVER}/{DatabaseConfig.DATABASE}"
        )