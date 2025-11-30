import os
from urllib.parse import quote_plus

class DatabaseConfig:
    """Configuration for Azure SQL Database connection"""

    # Azure SQL Database credentials - ALL MUST BE SET VIA ENVIRONMENT VARIABLES
    # No hardcoded defaults for security reasons
    SERVER = os.environ.get('AZURE_SQL_SERVER')
    DATABASE = os.environ.get('AZURE_SQL_DATABASE')
    USERNAME = os.environ.get('AZURE_SQL_USERNAME')
    PASSWORD = os.environ.get('AZURE_SQL_PASSWORD')

    @classmethod
    def validate(cls):
        """Validate that all required environment variables are set"""
        missing = []
        if not cls.SERVER:
            missing.append('AZURE_SQL_SERVER')
        if not cls.DATABASE:
            missing.append('AZURE_SQL_DATABASE')
        if not cls.USERNAME:
            missing.append('AZURE_SQL_USERNAME')
        if not cls.PASSWORD:
            missing.append('AZURE_SQL_PASSWORD')

        if missing:
            raise EnvironmentError(
                f"Missing required database environment variables: {', '.join(missing)}. "
                "Please set these in your environment or .env file."
            )
    
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