"""
Equipment inventory diagnostic endpoint to understand data structure
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from src.utils.tenant_utils import get_tenant_db, get_tenant_schema
from flask_jwt_extended import get_jwt_identity
from src.models.user import User

inventory_diagnostic_bp = Blueprint('inventory_diagnostic', __name__)

@inventory_diagnostic_bp.route('/api/diagnostic/equipment-schema', methods=['GET'])
@jwt_required()
def get_equipment_schema():
    """Get Equipment table schema to understand available fields"""
    try:
        db = get_tenant_db()
        schema = get_tenant_schema()
        # Get Equipment table schema
        schema_query = f"""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'Equipment' 
        AND TABLE_SCHEMA = '{schema}'
        ORDER BY ORDINAL_POSITION;
        """
        
        schema_results = db.execute_query(schema_query)
        
        return jsonify({
            'equipment_schema': schema_results,
            'total_columns': len(schema_results)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error getting schema: {str(e)}'}), 500

@inventory_diagnostic_bp.route('/api/diagnostic/equipment-sample', methods=['GET'])
@jwt_required()
def get_equipment_sample():
    """Get sample equipment data to understand categorization"""
    try:
        db = get_tenant_db()
        schema = get_tenant_schema()
        # Get sample equipment records with all fields
        sample_query = f"""
        SELECT TOP 20 *
        FROM {schema}.Equipment
        WHERE SerialNo IS NOT NULL
        ORDER BY Id DESC;
        """
        
        sample_results = db.execute_query(sample_query)
        
        return jsonify({
            'sample_equipment': sample_results,
            'total_records': len(sample_results)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error getting sample: {str(e)}'}), 500

@inventory_diagnostic_bp.route('/api/diagnostic/equipment-categories', methods=['GET'])
@jwt_required()
def analyze_equipment_categories():
    """Analyze how equipment might be categorized"""
    try:
        db = get_tenant_db()
        schema = get_tenant_schema()
        # Check for status/type fields
        status_analysis = """
        SELECT 
            'Status Values' as analysis_type,
            ISNULL(Status, 'NULL') as value,
            COUNT(*) as count
        FROM {schema}.Equipment
        WHERE SerialNo IS NOT NULL
        GROUP BY Status
        
        UNION ALL
        
        SELECT 
            'Type Values' as analysis_type,
            ISNULL(Type, 'NULL') as value,
            COUNT(*) as count
        FROM {schema}.Equipment
        WHERE SerialNo IS NOT NULL
        GROUP BY Type
        
        UNION ALL
        
        SELECT 
            'Category Values' as analysis_type,
            ISNULL(Category, 'NULL') as value,
            COUNT(*) as count
        FROM {schema}.Equipment
        WHERE SerialNo IS NOT NULL
        GROUP BY Category
        
        ORDER BY analysis_type, count DESC;
        """
        
        category_results = db.execute_query(status_analysis)
        
        # Check for rental equipment (equipment currently on rental)
        rental_check = """
        SELECT 
            COUNT(DISTINCT e.Id) as total_rental_equipment,
            COUNT(DISTINCT wo.WONo) as open_rental_work_orders
        FROM {schema}.Equipment e
        INNER JOIN {schema}.WORental wr ON e.Id = wr.EquipmentId
        INNER JOIN {schema}.WO wo ON wr.WONo = wo.WONo
        WHERE wo.Type = 'R' 
        AND wo.ClosedDate IS NULL
        AND wo.WONo NOT LIKE '9%'
        AND e.SerialNo IS NOT NULL;
        """
        
        rental_results = db.execute_query(rental_check)
        
        # Check Make/Model patterns for batteries/chargers/Allied
        pattern_analysis = """
        SELECT 
            'Make Analysis' as analysis_type,
            Make as value,
            COUNT(*) as count
        FROM {schema}.Equipment
        WHERE SerialNo IS NOT NULL
        AND Make IS NOT NULL
        GROUP BY Make
        HAVING COUNT(*) > 5
        
        UNION ALL
        
        SELECT 
            'Battery/Charger Models' as analysis_type,
            Model as value,
            COUNT(*) as count
        FROM {schema}.Equipment
        WHERE SerialNo IS NOT NULL
        AND (Model LIKE '%battery%' OR Model LIKE '%charger%' OR Model LIKE '%batt%')
        GROUP BY Model
        
        ORDER BY analysis_type, count DESC;
        """
        
        pattern_results = db.execute_query(pattern_analysis)
        
        return jsonify({
            'category_analysis': category_results,
            'rental_equipment_count': rental_results,
            'make_model_patterns': pattern_results
        })
        
    except Exception as e:
        return jsonify({'error': f'Error analyzing categories: {str(e)}'}), 500

@inventory_diagnostic_bp.route('/api/diagnostic/equipment-financial', methods=['GET'])
@jwt_required()
def analyze_financial_fields():
    """Analyze financial data fields in Equipment table"""
    try:
        db = get_tenant_db()
        schema = get_tenant_schema()
        # Check financial fields
        financial_query = f"""
        SELECT TOP 10
            SerialNo,
            Make,
            Model,
            BookValue,
            Cost,
            ListPrice,
            SalePrice,
            InServiceDate,
            PurchaseDate,
            VendorInvoiceNo
        FROM {schema}.Equipment
        WHERE SerialNo IS NOT NULL
        AND BookValue > 0
        ORDER BY BookValue DESC;
        """
        
        financial_results = db.execute_query(financial_query)
        
        # Check for depreciation or accumulated depreciation fields
        depreciation_fields = """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'Equipment' 
        AND TABLE_SCHEMA = '{schema}'
        AND (COLUMN_NAME LIKE '%depreciat%' 
             OR COLUMN_NAME LIKE '%accum%'
             OR COLUMN_NAME LIKE '%gross%'
             OR COLUMN_NAME LIKE '%original%'
             OR COLUMN_NAME LIKE '%basis%');
        """
        
        depreciation_fields_results = db.execute_query(depreciation_fields)
        
        return jsonify({
            'sample_financial_data': financial_results,
            'depreciation_related_fields': depreciation_fields_results
        })
        
    except Exception as e:
        return jsonify({'error': f'Error analyzing financial fields: {str(e)}'}), 500