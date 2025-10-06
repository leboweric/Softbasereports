from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from ..services.azure_sql_service import AzureSQLService
import logging

logger = logging.getLogger(__name__)

equipment_gl_linker_bp = Blueprint('equipment_gl_linker', __name__)

@equipment_gl_linker_bp.route('/api/equipment/gl-linking-analysis', methods=['GET'])
@jwt_required()
def analyze_equipment_gl_linking():
    """
    Comprehensive analysis to determine how Equipment.SerialNo connects to GL accounts
    Uses multiple strategies to find the linking mechanism
    """
    try:
        db = AzureSQLService()
        results = {}
        
        # Strategy 1: Check for direct references in GLDetail descriptions/references
        strategy1_query = """
        SELECT 
            gld.AccountNo,
            gld.EffectiveDate,
            gld.Amount,
            gld.Description,
            gld.Reference,
            gld.JournalNo,
            CASE 
                WHEN gld.Description LIKE '%[0-9][0-9][0-9][0-9][0-9]%' 
                     OR gld.Reference LIKE '%[0-9][0-9][0-9][0-9][0-9]%' THEN 'Potential_Serial'
                ELSE 'No_Serial_Pattern'
            END as Serial_Pattern
        FROM ben002.GLDetail gld
        WHERE gld.AccountNo IN ('131000', '131200', '131300', '183000', '193000')
        AND (
            gld.Description IS NOT NULL 
            OR gld.Reference IS NOT NULL
        )
        AND gld.EffectiveDate >= '2024-01-01'
        ORDER BY gld.EffectiveDate DESC
        """
        
        results['strategy1_description_analysis'] = db.execute_query(strategy1_query)
        
        # Strategy 2: Look for Asset or Fixed Asset tables that might bridge Equipment to GL
        strategy2_query = """
        SELECT 
            t.TABLE_NAME,
            STRING_AGG(c.COLUMN_NAME, ', ') as Columns
        FROM INFORMATION_SCHEMA.TABLES t
        JOIN INFORMATION_SCHEMA.COLUMNS c 
            ON t.TABLE_NAME = c.TABLE_NAME 
            AND t.TABLE_SCHEMA = c.TABLE_SCHEMA
        WHERE t.TABLE_SCHEMA = 'ben002'
        AND (
            t.TABLE_NAME LIKE '%asset%'
            OR t.TABLE_NAME LIKE '%depreciation%'
            OR t.TABLE_NAME LIKE '%equipment%'
            OR t.TABLE_NAME LIKE '%inventory%'
        )
        AND t.TABLE_NAME != 'Equipment'  -- Exclude the main Equipment table
        GROUP BY t.TABLE_NAME
        ORDER BY t.TABLE_NAME
        """
        
        results['strategy2_asset_tables'] = db.execute_query(strategy2_query)
        
        # Strategy 3: Check if there are Journal Entry tables with equipment references
        strategy3_query = """
        SELECT 
            t.TABLE_NAME,
            COUNT(*) as Row_Count
        FROM INFORMATION_SCHEMA.TABLES t
        LEFT JOIN sys.partitions p 
            ON p.object_id = OBJECT_ID(t.TABLE_SCHEMA + '.' + t.TABLE_NAME)
            AND p.index_id IN (0,1)
        WHERE t.TABLE_SCHEMA = 'ben002'
        AND (
            t.TABLE_NAME LIKE '%journal%'
            OR t.TABLE_NAME LIKE '%entry%'
            OR t.TABLE_NAME LIKE '%transaction%'
        )
        GROUP BY t.TABLE_NAME, p.rows
        ORDER BY t.TABLE_NAME
        """
        
        results['strategy3_journal_tables'] = db.execute_query(strategy3_query)
        
        # Strategy 4: Look for work orders or invoices that might link equipment to GL
        strategy4_query = """
        SELECT 
            wo.WONo,
            wo.Type,
            wo.BillTo,
            wo.SerialNo,
            wo.CompletedDate,
            ir.InvoiceNo,
            ir.InvoiceDate,
            ir.Amount
        FROM ben002.WO wo
        LEFT JOIN ben002.InvoiceReg ir ON wo.WONo = ir.WONo
        WHERE wo.SerialNo IS NOT NULL
        AND wo.CompletedDate >= '2024-01-01'
        AND wo.Type IN ('S', 'R', 'P')  -- Service, Rental, Parts
        ORDER BY wo.CompletedDate DESC
        """
        
        results['strategy4_wo_invoice_links'] = db.execute_query(strategy4_query)
        
        # Strategy 5: Check for department-based GL account mapping
        strategy5_query = """
        SELECT 
            e.InventoryDept,
            COUNT(*) as Equipment_Count,
            MIN(e.SerialNo) as Sample_SerialNo,
            AVG(e.AcquisitionCost) as Avg_Acquisition_Cost,
            AVG(e.BookValue) as Avg_Book_Value
        FROM ben002.Equipment e
        WHERE e.InventoryDept IS NOT NULL
        GROUP BY e.InventoryDept
        ORDER BY e.InventoryDept
        """
        
        results['strategy5_dept_mapping'] = db.execute_query(strategy5_query)
        
        # Strategy 6: Look for depreciation schedules or asset registers
        strategy6_query = """
        SELECT 
            t.TABLE_NAME,
            c.COLUMN_NAME,
            c.DATA_TYPE
        FROM INFORMATION_SCHEMA.TABLES t
        JOIN INFORMATION_SCHEMA.COLUMNS c 
            ON t.TABLE_NAME = c.TABLE_NAME 
            AND t.TABLE_SCHEMA = c.TABLE_SCHEMA
        WHERE t.TABLE_SCHEMA = 'ben002'
        AND c.COLUMN_NAME IN ('SerialNo', 'SerialNumber', 'EquipmentNo', 'AssetNo', 'AccountNo')
        ORDER BY t.TABLE_NAME, c.COLUMN_NAME
        """
        
        results['strategy6_serial_columns'] = db.execute_query(strategy6_query)
        
        # Strategy 7: Sample recent equipment transactions to understand patterns
        strategy7_query = """
        SELECT TOP 20
            e.SerialNo,
            e.Make,
            e.Model,
            e.InventoryDept,
            e.AcquisitionCost,
            e.BookValue,
            e.AccumulatedDepreciation,
            e.LastServiceDate,
            e.Notes
        FROM ben002.Equipment e
        WHERE e.SerialNo IS NOT NULL
        AND (
            e.LastServiceDate >= '2024-01-01'
            OR e.AcquisitionCost > 0
        )
        ORDER BY e.LastServiceDate DESC, e.SerialNo
        """
        
        results['strategy7_recent_equipment'] = db.execute_query(strategy7_query)
        
        # Generate recommendations based on findings
        recommendations = generate_linking_recommendations(results)
        results['recommendations'] = recommendations
        
        return jsonify({
            'success': True,
            'message': 'Equipment-GL linking analysis completed',
            'strategies_used': 7,
            'data': results
        })
        
    except Exception as e:
        logger.error(f"Equipment-GL linking analysis failed: {str(e)}")
        return jsonify({
            'error': str(e),
            'type': 'equipment_gl_linking_error'
        }), 500

@equipment_gl_linker_bp.route('/api/equipment/test-linking-strategy', methods=['POST'])
@jwt_required()
def test_linking_strategy():
    """
    Test a specific linking strategy based on user input
    """
    try:
        data = request.get_json()
        strategy = data.get('strategy', 'department_mapping')
        
        db = AzureSQLService()
        
        if strategy == 'department_mapping':
            # Test department-based mapping
            test_query = """
            SELECT 
                e.InventoryDept,
                COUNT(*) as Equipment_Count,
                SUM(e.AcquisitionCost) as Total_Acquisition_Cost,
                SUM(e.BookValue) as Total_Book_Value,
                CASE 
                    WHEN e.InventoryDept = 10 THEN '131000'  -- New Equipment
                    WHEN e.InventoryDept = 20 THEN '131200'  -- Used Equipment
                    WHEN e.InventoryDept = 30 THEN '131300'  -- Allied
                    WHEN e.InventoryDept = 60 THEN '183000'  -- Rental
                    ELSE 'Unknown'
                END as Mapped_GL_Account
            FROM ben002.Equipment e
            WHERE e.InventoryDept IS NOT NULL
            GROUP BY e.InventoryDept
            ORDER BY e.InventoryDept
            """
            
            results = db.execute_query(test_query)
            
        elif strategy == 'serial_search':
            # Test serial number search in GL descriptions
            sample_serial = data.get('serial_no', '')
            if sample_serial:
                test_query = f"""
                SELECT 
                    AccountNo,
                    EffectiveDate,
                    Amount,
                    Description,
                    Reference
                FROM ben002.GLDetail
                WHERE (
                    Description LIKE '%{sample_serial}%'
                    OR Reference LIKE '%{sample_serial}%'
                )
                ORDER BY EffectiveDate DESC
                """
                
                results = db.execute_query(test_query)
            else:
                results = []
                
        else:
            return jsonify({
                'error': 'Unknown strategy',
                'supported_strategies': ['department_mapping', 'serial_search']
            }), 400
        
        return jsonify({
            'success': True,
            'strategy': strategy,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Linking strategy test failed: {str(e)}")
        return jsonify({
            'error': str(e),
            'type': 'linking_strategy_test_error'
        }), 500

def generate_linking_recommendations(analysis_results):
    """Generate recommendations based on the linking analysis"""
    recommendations = []
    
    # Check if we found serial numbers in GL descriptions
    description_analysis = analysis_results.get('strategy1_description_analysis', [])
    serial_patterns = [row for row in description_analysis if row.get('Serial_Pattern') == 'Potential_Serial']
    
    if serial_patterns:
        recommendations.append({
            'type': 'serial_in_descriptions',
            'confidence': 'medium',
            'message': f'Found {len(serial_patterns)} GL entries with potential serial number patterns',
            'action': 'Parse serial numbers from Description/Reference fields'
        })
    
    # Check for asset bridge tables
    asset_tables = analysis_results.get('strategy2_asset_tables', [])
    if asset_tables:
        recommendations.append({
            'type': 'asset_bridge_tables',
            'confidence': 'high',
            'message': f'Found {len(asset_tables)} potential asset bridge tables',
            'tables': [table['TABLE_NAME'] for table in asset_tables],
            'action': 'Investigate these tables for Equipment-GL relationships'
        })
    
    # Check department mapping viability
    dept_mapping = analysis_results.get('strategy5_dept_mapping', [])
    if len(dept_mapping) > 0:
        recommendations.append({
            'type': 'department_mapping',
            'confidence': 'high',
            'message': f'Equipment distributed across {len(dept_mapping)} departments',
            'action': 'Use InventoryDept to map equipment to GL accounts',
            'departments': dept_mapping
        })
    
    # Check for serial number columns in other tables
    serial_columns = analysis_results.get('strategy6_serial_columns', [])
    bridge_tables = [row for row in serial_columns if row['TABLE_NAME'] != 'Equipment']
    
    if bridge_tables:
        recommendations.append({
            'type': 'serial_bridge_tables',
            'confidence': 'high',
            'message': f'Found SerialNo columns in {len(set(row["TABLE_NAME"] for row in bridge_tables))} other tables',
            'tables': list(set(row['TABLE_NAME'] for row in bridge_tables)),
            'action': 'These tables may link Equipment to GL transactions'
        })
    
    # Default recommendation
    if not recommendations:
        recommendations.append({
            'type': 'department_fallback',
            'confidence': 'medium',
            'message': 'No direct linking mechanism found - recommend department-based mapping',
            'action': 'Map InventoryDept to GL accounts as primary strategy'
        })
    
    return recommendations