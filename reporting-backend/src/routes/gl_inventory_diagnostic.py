from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from src.utils.tenant_utils import get_tenant_db
from ..services.azure_sql_service import AzureSQLService
import logging

from flask_jwt_extended import get_jwt_identity
from src.models.user import User

def get_tenant_schema():
    """Get the database schema for the current user's organization"""
    try:
        user_id = get_jwt_identity()
        if user_id:
            user = User.query.get(int(user_id))
            if user and user.organization and user.organization.database_schema:
                return user.organization.database_schema
        return 'ben002'  # Fallback
    except:
        return 'ben002'



logger = logging.getLogger(__name__)

gl_inventory_diagnostic_bp = Blueprint('gl_inventory_diagnostic', __name__)

@gl_inventory_diagnostic_bp.route('/api/diagnostics/gl-inventory', methods=['GET'])
@jwt_required()
def diagnose_gl_inventory():
    """
    Diagnostic endpoint to explore GL inventory accounts and equipment connections
    Investigates accounts: 131000, 131200, 131300, 183000, 193000
    """
    try:
        db = get_tenant_db()
        schema = get_tenant_schema()
        results = {}
        
        # Target GL accounts for inventory
        target_accounts = ['131000', '131200', '131300', '183000', '193000']
        
        # Step 1: Check if these accounts exist in ChartOfAccounts
        chart_query = f"""
        SELECT 
            AccountNo,
            AccountDescription,
            AccountType,
            CASE 
                WHEN AccountNo = '131000' THEN 'New Equipment'
                WHEN AccountNo = '131200' THEN 'Used + Batteries'
                WHEN AccountNo = '131300' THEN 'Allied'
                WHEN AccountNo = '183000' THEN 'Rental Gross Value'
                WHEN AccountNo = '193000' THEN 'Accumulated Depreciation'
                ELSE 'Unknown'
            END as Expected_Purpose
        FROM {schema}.ChartOfAccounts
        WHERE AccountNo IN ('131000', '131200', '131300', '183000', '193000')
        ORDER BY AccountNo
        """
        
        results['chart_of_accounts'] = db.execute_query(chart_query)
        
        # Step 2: Get GL account balances for these accounts
        gl_balances_query = f"""
        SELECT 
            gl.AccountNo,
            coa.AccountDescription,
            gl.CurrentBalance,
            gl.YTDBalance,
            gl.LastTransDate,
            gl.LastTransAmount
        FROM {schema}.GL gl
        LEFT JOIN {schema}.ChartOfAccounts coa ON gl.AccountNo = coa.AccountNo
        WHERE gl.AccountNo IN ('131000', '131200', '131300', '183000', '193000')
        ORDER BY gl.AccountNo
        """
        
        try:
            results['gl_current_balances'] = db.execute_query(gl_balances_query)
        except Exception as e:
            logger.warning(f"Could not get GL balances: {str(e)}")
            results['gl_current_balances'] = []
            results['gl_balance_error'] = str(e)
        
        # Step 3: Get recent GLDetail transactions for these accounts
        gldetail_query = f"""
        SELECT TOP 50
            gld.AccountNo,
            coa.AccountDescription,
            gld.EffectiveDate,
            gld.Amount,
            gld.TransactionType,
            gld.Description,
            gld.Reference,
            gld.JournalNo
        FROM {schema}.GLDetail gld
        LEFT JOIN {schema}.ChartOfAccounts coa ON gld.AccountNo = coa.AccountNo
        WHERE gld.AccountNo IN ('131000', '131200', '131300', '183000', '193000')
        AND gld.EffectiveDate >= '2024-11-01'  -- Fiscal year Nov 2024 - Oct 2025
        ORDER BY gld.EffectiveDate DESC, gld.AccountNo
        """
        
        results['recent_transactions'] = db.execute_query(gldetail_query)
        
        # Step 4: Look for equipment-related entries
        equipment_connection_query = f"""
        SELECT TOP 20
            gld.AccountNo,
            gld.EffectiveDate,
            gld.Amount,
            gld.Description,
            gld.Reference,
            gld.JournalNo
        FROM {schema}.GLDetail gld
        WHERE gld.AccountNo IN ('131000', '131200', '131300', '183000', '193000')
        AND (
            gld.Description LIKE '%serial%'
            OR gld.Description LIKE '%equipment%'
            OR gld.Description LIKE '%unit%'
            OR gld.Reference LIKE '%serial%'
            OR gld.Reference LIKE '%equipment%'
            OR gld.Reference LIKE '%unit%'
        )
        ORDER BY gld.EffectiveDate DESC
        """
        
        results['equipment_related_transactions'] = db.execute_query(equipment_connection_query)
        
        # Step 5: Check Equipment table structure to understand serial number fields
        equipment_structure_query = f"""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{schema}'
        AND TABLE_NAME = 'Equipment'
        ORDER BY ORDINAL_POSITION
        """
        
        results['equipment_table_structure'] = db.execute_query(equipment_structure_query)
        
        # Step 6: Sample equipment records to see serial number format
        equipment_sample_query = f"""
        SELECT TOP 10
            SerialNo,
            Make,
            Model,
            Year,
            AcquisitionCost,
            BookValue,
            AccumulatedDepreciation,
            InventoryDept
        FROM {schema}.Equipment
        WHERE SerialNo IS NOT NULL
        ORDER BY SerialNo
        """
        
        results['equipment_samples'] = db.execute_query(equipment_sample_query)
        
        # Step 7: Look for potential linking tables between Equipment and GL
        linking_tables_query = f"""
        SELECT 
            t.TABLE_NAME,
            COUNT(c.COLUMN_NAME) as column_count
        FROM INFORMATION_SCHEMA.TABLES t
        LEFT JOIN INFORMATION_SCHEMA.COLUMNS c 
            ON t.TABLE_NAME = c.TABLE_NAME 
            AND t.TABLE_SCHEMA = c.TABLE_SCHEMA
        WHERE t.TABLE_SCHEMA = '{schema}'
        AND (
            t.TABLE_NAME LIKE '%equipment%'
            OR t.TABLE_NAME LIKE '%asset%'
            OR t.TABLE_NAME LIKE '%depreciation%'
            OR t.TABLE_NAME LIKE '%journal%'
            OR t.TABLE_NAME LIKE '%gl%'
        )
        GROUP BY t.TABLE_NAME
        ORDER BY t.TABLE_NAME
        """
        
        results['potential_linking_tables'] = db.execute_query(linking_tables_query)
        
        # Step 8: Check for depreciation-specific transactions (fiscal year filter)
        depreciation_query = f"""
        SELECT 
            gld.AccountNo,
            gld.EffectiveDate,
            SUM(gld.Amount) as Monthly_Amount,
            COUNT(*) as Transaction_Count
        FROM {schema}.GLDetail gld
        WHERE gld.AccountNo = '193000'  -- Accumulated Depreciation
        AND gld.EffectiveDate >= '2024-11-01'  -- Fiscal year start
        AND gld.EffectiveDate < '2025-11-01'   -- Fiscal year end
        GROUP BY gld.AccountNo, gld.EffectiveDate
        ORDER BY gld.EffectiveDate DESC
        """
        
        results['ytd_depreciation_transactions'] = db.execute_query(depreciation_query)
        
        # Step 9: Summary statistics
        summary = {
            'accounts_found': len(results['chart_of_accounts']),
            'recent_transactions_count': len(results['recent_transactions']),
            'equipment_related_count': len(results['equipment_related_transactions']),
            'potential_linking_tables': len(results['potential_linking_tables']),
            'fiscal_year_range': '2024-11-01 to 2025-10-31'
        }
        
        results['summary'] = summary
        
        return jsonify({
            'success': True,
            'message': 'GL inventory diagnostic completed',
            'data': results
        })
        
    except Exception as e:
        logger.error(f"GL inventory diagnostic failed: {str(e)}")
        return jsonify({
            'error': str(e),
            'type': 'gl_inventory_diagnostic_error'
        }), 500

@gl_inventory_diagnostic_bp.route('/api/diagnostics/gl-equipment-links', methods=['GET'])
@jwt_required()
def explore_equipment_gl_links():
    """
    Deep dive to find how Equipment.SerialNo connects to GL transactions
    """
    try:
        db = get_tenant_db()
        schema = get_tenant_schema()
        results = {}
        
        # Step 1: Look for tables that might link Equipment to GL
        potential_link_query = f"""
        SELECT 
            t.TABLE_NAME,
            STRING_AGG(c.COLUMN_NAME, ', ') as columns
        FROM INFORMATION_SCHEMA.TABLES t
        JOIN INFORMATION_SCHEMA.COLUMNS c 
            ON t.TABLE_NAME = c.TABLE_NAME 
            AND t.TABLE_SCHEMA = c.TABLE_SCHEMA
        WHERE t.TABLE_SCHEMA = '{schema}'
        AND (
            c.COLUMN_NAME LIKE '%serial%'
            OR c.COLUMN_NAME LIKE '%equipment%'
            OR c.COLUMN_NAME LIKE '%asset%'
            OR c.COLUMN_NAME LIKE '%account%'
        )
        GROUP BY t.TABLE_NAME
        HAVING COUNT(c.COLUMN_NAME) > 0
        ORDER BY t.TABLE_NAME
        """
        
        results['tables_with_equipment_fields'] = db.execute_query(potential_link_query)
        
        # Step 2: Check if GLDetail has any equipment identifiers
        gldetail_equipment_check = """
        SELECT TOP 20
            AccountNo,
            EffectiveDate,
            Amount,
            Description,
            Reference,
            JournalNo
        FROM {schema}.GLDetail
        WHERE AccountNo IN ('131000', '131200', '131300', '183000', '193000')
        AND (
            Description IS NOT NULL 
            OR Reference IS NOT NULL
        )
        ORDER BY EffectiveDate DESC
        """
        
        results['gldetail_with_descriptions'] = db.execute_query(gldetail_equipment_check)
        
        # Step 3: Look for Asset or FixedAsset tables
        asset_tables_query = f"""
        SELECT 
            TABLE_NAME,
            COLUMN_NAME,
            DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{schema}'
        AND TABLE_NAME LIKE '%asset%'
        ORDER BY TABLE_NAME, ORDINAL_POSITION
        """
        
        results['asset_table_structures'] = db.execute_query(asset_tables_query)
        
        # Step 4: Check Journal tables that might link GL to assets
        journal_tables_query = f"""
        SELECT 
            TABLE_NAME,
            COLUMN_NAME,
            DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{schema}'
        AND (
            TABLE_NAME LIKE '%journal%'
            OR TABLE_NAME LIKE '%entry%'
        )
        ORDER BY TABLE_NAME, ORDINAL_POSITION
        """
        
        results['journal_table_structures'] = db.execute_query(journal_tables_query)
        
        return jsonify({
            'success': True,
            'message': 'Equipment-GL link exploration completed',
            'data': results
        })
        
    except Exception as e:
        logger.error(f"Equipment-GL link exploration failed: {str(e)}")
        return jsonify({
            'error': str(e),
            'type': 'equipment_gl_link_error'
        }), 500