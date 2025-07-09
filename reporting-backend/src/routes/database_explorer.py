from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.azure_sql_service import AzureSQLService
from ..models.user import User
import logging

logger = logging.getLogger(__name__)

explorer_bp = Blueprint('explorer', __name__)

@explorer_bp.route('/api/database/explore', methods=['GET'])
@jwt_required()
def explore_database():
    """Comprehensive database exploration endpoint"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        db = AzureSQLService()
        
        # Get all tables
        tables = db.get_tables()
        
        # Categorize tables
        categories = {
            'Customers': [],
            'Inventory': [],
            'Sales': [],
            'Service': [],
            'Parts': [],
            'Financial': [],
            'Other': []
        }
        
        for table in tables:
            table_lower = table.lower()
            if 'customer' in table_lower or 'client' in table_lower:
                categories['Customers'].append(table)
            elif 'inventory' in table_lower or 'equipment' in table_lower or 'forklift' in table_lower:
                categories['Inventory'].append(table)
            elif 'sale' in table_lower or 'order' in table_lower or 'invoice' in table_lower:
                categories['Sales'].append(table)
            elif 'service' in table_lower or 'repair' in table_lower or 'maintenance' in table_lower:
                categories['Service'].append(table)
            elif 'part' in table_lower or 'component' in table_lower:
                categories['Parts'].append(table)
            elif 'financial' in table_lower or 'payment' in table_lower or 'account' in table_lower:
                categories['Financial'].append(table)
            else:
                categories['Other'].append(table)
        
        # Get details for key tables
        key_tables = []
        for category, table_list in categories.items():
            if table_list and category != 'Other':
                # Get the shortest table name (likely the main one)
                main_table = min(table_list, key=len) if table_list else None
                if main_table:
                    try:
                        columns = db.get_table_columns(main_table)
                        sample_query = f"SELECT TOP 3 * FROM [{main_table}]"
                        sample_data = db.execute_query(sample_query)
                        
                        key_tables.append({
                            'category': category,
                            'table': main_table,
                            'columns': columns,
                            'sample_data': sample_data,
                            'row_count': len(sample_data)
                        })
                    except Exception as e:
                        logger.error(f"Error exploring table {main_table}: {str(e)}")
        
        return jsonify({
            'total_tables': len(tables),
            'categories': {k: v for k, v in categories.items() if v},
            'key_tables': key_tables,
            'database_info': {
                'server': db.server,
                'database': db.database
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Database exploration failed: {str(e)}")
        return jsonify({'error': 'Database exploration failed', 'message': str(e)}), 500

@explorer_bp.route('/api/database/schema-summary', methods=['GET'])
@jwt_required()
def get_schema_summary():
    """Get a simplified schema summary for the frontend"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        db = AzureSQLService()
        tables = db.get_tables()
        
        # Create a simple summary
        summary = {
            'customers': [t for t in tables if 'customer' in t.lower()],
            'inventory': [t for t in tables if any(x in t.lower() for x in ['inventory', 'equipment', 'forklift'])],
            'sales': [t for t in tables if any(x in t.lower() for x in ['sale', 'order', 'invoice'])],
            'service': [t for t in tables if any(x in t.lower() for x in ['service', 'repair', 'maintenance'])],
            'parts': [t for t in tables if 'part' in t.lower()]
        }
        
        return jsonify({
            'total_tables': len(tables),
            'categories': summary,
            'status': 'connected'
        }), 200
        
    except Exception as e:
        logger.error(f"Schema summary failed: {str(e)}")
        return jsonify({'error': 'Failed to get schema', 'message': str(e)}), 500