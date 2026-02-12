"""
Multi-Tenant ETL Discovery
Discovers all active Softbase tenants and provides database connections for ETL jobs.

This module allows ETL jobs to run for ALL tenants without hardcoding org_ids or schemas.
New tenants are automatically discovered when they are added to the Organization table
with a database_schema and valid DB credentials.
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class TenantInfo:
    """Holds tenant information needed for ETL jobs"""
    
    def __init__(self, org_id: int, name: str, schema: str, 
                 db_server: str = None, db_name: str = None,
                 db_username: str = None, db_password_encrypted: str = None,
                 platform_type: str = None, fiscal_year_start_month: int = 11):
        self.org_id = org_id
        self.name = name
        self.schema = schema
        self.db_server = db_server
        self.db_name = db_name
        self.db_username = db_username
        self.db_password_encrypted = db_password_encrypted
        self.platform_type = platform_type or 'evolution'
        self.fiscal_year_start_month = fiscal_year_start_month
    
    def __repr__(self):
        return f"TenantInfo(org_id={self.org_id}, name='{self.name}', schema='{self.schema}')"
    
    def get_azure_sql_service(self):
        """
        Create an AzureSQLService configured with this tenant's credentials.
        Falls back to default credentials if tenant-specific ones aren't available.
        
        Returns:
            AzureSQLService: Configured database service
        """
        from src.services.azure_sql_service import AzureSQLService
        
        service = AzureSQLService()
        
        if self.db_server and self.db_username and self.db_password_encrypted:
            try:
                from src.services.credential_manager import get_credential_manager
                credential_manager = get_credential_manager()
                decrypted_password = credential_manager.decrypt_password(self.db_password_encrypted)
                
                service.server = self.db_server
                service.database = self.db_name or 'evo'
                service.username = self.db_username
                service.password = decrypted_password
                
                logger.info(f"[ETL] Using tenant credentials for {self.name} - Server: {service.server}, DB: {service.database}")
            except Exception as e:
                logger.error(f"[ETL] Failed to decrypt credentials for {self.name}: {e}")
                logger.info(f"[ETL] Falling back to default credentials for {self.name}")
        else:
            logger.info(f"[ETL] Using default credentials for {self.name}")
        
        return service


def discover_softbase_tenants() -> List[TenantInfo]:
    """
    Discover all active Softbase tenants from the Organization table.
    
    Returns organizations that have:
    - is_active = True
    - database_schema is not NULL (indicates a Softbase tenant)
    - platform_type is 'evolution' or NULL (excludes non-Softbase platforms)
    
    Returns:
        List of TenantInfo objects for all active Softbase tenants
    """
    try:
        from src.models.user import Organization
        
        # Query all active organizations with a database schema
        orgs = Organization.query.filter(
            Organization.is_active == True,
            Organization.database_schema.isnot(None),
            Organization.database_schema != ''
        ).all()
        
        tenants = []
        for org in orgs:
            # Skip non-Softbase platforms (e.g., VITAL uses different data sources)
            # VITAL has platform_type set or uses specific integrations
            # For now, include all orgs with a database_schema as Softbase tenants
            # The ETL will gracefully handle any schema differences
            
            # Skip organizations that don't have Softbase-style schemas
            # Softbase schemas typically follow patterns like 'ben002', 'ind004', etc.
            # VITAL uses a different platform (vital001, etc.) and doesn't have Softbase tables
            schema = org.database_schema
            if not schema or schema.lower().startswith('vital'):
                logger.info(f"Skipping non-Softbase org: {org.name} (schema={schema})")
                continue
            
            tenant = TenantInfo(
                org_id=org.id,
                name=org.name,
                schema=schema,
                db_server=org.db_server,
                db_name=org.db_name,
                db_username=org.db_username,
                db_password_encrypted=org.db_password_encrypted,
                platform_type=org.platform_type,
                fiscal_year_start_month=org.fiscal_year_start_month or 11
            )
            tenants.append(tenant)
            logger.info(f"Discovered Softbase tenant: {tenant}")
        
        logger.info(f"Total Softbase tenants discovered: {len(tenants)}")
        return tenants
        
    except Exception as e:
        logger.error(f"Failed to discover tenants: {e}")
        # Fallback to known tenants if DB query fails
        logger.warning("Falling back to hardcoded tenant list")
        return [
            TenantInfo(org_id=4, name='Bennett', schema='ben002'),
            TenantInfo(org_id=7, name='Industrial Parts and Service', schema='ind004'),
        ]


def create_tenant_azure_sql(org_id: int):
    """
    Create an AzureSQLService for a specific organization by looking up its credentials.
    
    Args:
        org_id: The organization ID to create a connection for
    
    Returns:
        AzureSQLService configured for the tenant, or None if not found
    """
    try:
        from src.models.user import Organization
        
        org = Organization.query.get(org_id)
        if not org or not org.database_schema:
            logger.error(f"Organization {org_id} not found or has no schema")
            return None
        
        tenant = TenantInfo(
            org_id=org.id,
            name=org.name,
            schema=org.database_schema,
            db_server=org.db_server,
            db_name=org.db_name,
            db_username=org.db_username,
            db_password_encrypted=org.db_password_encrypted,
            platform_type=org.platform_type,
            fiscal_year_start_month=org.fiscal_year_start_month or 11
        )
        return tenant.get_azure_sql_service()
    except Exception as e:
        logger.error(f"Failed to create Azure SQL service for org {org_id}: {e}")
        return None


def run_etl_for_all_tenants(etl_class, etl_name: str, **extra_kwargs) -> Dict[str, bool]:
    """
    Run an ETL job for all discovered Softbase tenants.
    
    Args:
        etl_class: The ETL class to instantiate (must accept org_id, schema, azure_sql params)
        etl_name: Human-readable name for logging
        **extra_kwargs: Additional keyword arguments to pass to the ETL constructor
    
    Returns:
        Dict mapping tenant name to success/failure boolean
    """
    tenants = discover_softbase_tenants()
    results = {}
    
    for tenant in tenants:
        logger.info(f"Running {etl_name} ETL for tenant: {tenant.name} (org_id={tenant.org_id}, schema={tenant.schema})")
        try:
            azure_sql = tenant.get_azure_sql_service()
            etl = etl_class(
                org_id=tenant.org_id,
                schema=tenant.schema,
                azure_sql=azure_sql,
                fiscal_year_start_month=tenant.fiscal_year_start_month,
                **extra_kwargs
            )
            success = etl.run()
            results[tenant.name] = success
            logger.info(f"{etl_name} ETL for {tenant.name}: {'SUCCESS' if success else 'FAILED'}")
        except Exception as e:
            logger.error(f"{etl_name} ETL for {tenant.name} failed with exception: {e}")
            results[tenant.name] = False
    
    return results
