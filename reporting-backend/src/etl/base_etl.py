"""
Base ETL Class
Provides common functionality for all ETL jobs
"""

import os
import logging
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseETL(ABC):
    """Abstract base class for all ETL jobs"""
    
    def __init__(self, job_name: str, org_id: int, source_system: str, target_table: str):
        self.job_name = job_name
        self.org_id = org_id
        self.source_system = source_system
        self.target_table = target_table
        self.started_at = None
        self.records_processed = 0
        self.records_inserted = 0
        self.records_updated = 0
        self._pg = None
    
    @property
    def pg(self):
        """Lazy load PostgreSQL service"""
        if self._pg is None:
            from src.services.postgres_service import PostgreSQLService
            self._pg = PostgreSQLService()
        return self._pg
    
    def run(self) -> bool:
        """Execute the ETL job with logging"""
        self.started_at = datetime.now()
        log_id = self._log_start()
        
        try:
            logger.info(f"Starting ETL job: {self.job_name} for org_id={self.org_id}")
            
            # Extract
            logger.info("  [1/3] Extracting data...")
            data = self.extract()
            self.records_processed = len(data) if data else 0
            logger.info(f"  [1/3] Extracted {self.records_processed} records")
            
            if not data:
                logger.info("  No data to process, skipping transform and load")
                self._log_complete(log_id, 'success')
                return True
            
            # Transform
            logger.info("  [2/3] Transforming data...")
            transformed = self.transform(data)
            logger.info(f"  [2/3] Transformed {len(transformed)} records")
            
            # Load
            logger.info("  [3/3] Loading data...")
            self.load(transformed)
            logger.info(f"  [3/3] Loaded {self.records_inserted} inserted, {self.records_updated} updated")
            
            self._log_complete(log_id, 'success')
            logger.info(f"ETL job completed: {self.job_name}")
            return True
            
        except Exception as e:
            logger.error(f"ETL job failed: {self.job_name} - {str(e)}")
            import traceback
            traceback.print_exc()
            self._log_complete(log_id, 'failed', str(e))
            return False
    
    @abstractmethod
    def extract(self) -> list:
        """Extract data from source system"""
        pass
    
    @abstractmethod
    def transform(self, data: list) -> list:
        """Transform extracted data"""
        pass
    
    @abstractmethod
    def load(self, data: list) -> None:
        """Load transformed data into target table"""
        pass
    
    def _log_start(self) -> int:
        """Log ETL job start"""
        query = """
        INSERT INTO mart_etl_log 
        (job_name, org_id, started_at, status, source_system, target_table)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        result = self.pg.execute_insert_returning(
            query, 
            (self.job_name, self.org_id, self.started_at, 'running', 
             self.source_system, self.target_table)
        )
        return result['id'] if result else None
    
    def _log_complete(self, log_id: int, status: str, error_message: str = None):
        """Log ETL job completion"""
        if not log_id:
            return
        
        query = """
        UPDATE mart_etl_log 
        SET completed_at = %s, status = %s, 
            records_processed = %s, records_inserted = %s, 
            records_updated = %s, error_message = %s
        WHERE id = %s
        """
        self.pg.execute_update(
            query,
            (datetime.now(), status, self.records_processed, 
             self.records_inserted, self.records_updated, error_message, log_id)
        )
    
    def upsert_record(self, data: dict, unique_columns: list) -> str:
        """
        Insert or update a record based on unique columns
        Returns 'inserted' or 'updated'
        """
        # Build the column lists
        columns = list(data.keys())
        values = list(data.values())
        placeholders = ', '.join(['%s'] * len(columns))
        column_list = ', '.join(columns)
        
        # Build the ON CONFLICT UPDATE clause
        update_clause = ', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col not in unique_columns])
        unique_clause = ', '.join(unique_columns)
        
        query = f"""
        INSERT INTO {self.target_table} ({column_list})
        VALUES ({placeholders})
        ON CONFLICT ({unique_clause}) 
        DO UPDATE SET {update_clause}, updated_at = CURRENT_TIMESTAMP
        RETURNING (xmax = 0) as inserted
        """
        
        result = self.pg.execute_insert_returning(query, tuple(values))
        
        if result and result.get('inserted'):
            self.records_inserted += 1
            return 'inserted'
        else:
            self.records_updated += 1
            return 'updated'
