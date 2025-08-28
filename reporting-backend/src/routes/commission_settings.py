from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from src.services.postgres_service import PostgreSQLService

logger = logging.getLogger(__name__)
commission_settings_bp = Blueprint('commission_settings', __name__, url_prefix='/api/commission-settings')

@commission_settings_bp.route('', methods=['GET'])
@jwt_required()
def get_commission_settings():
    """Get all commission settings"""
    try:
        pg_service = PostgreSQLService()
        with pg_service.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get month parameter if provided
            month = request.args.get('month')
            
            if month:
                # Get settings for specific invoices in the month
                query = """
                    SELECT 
                        invoice_no,
                        sale_code,
                        category,
                        is_commissionable,
                        commission_rate
                    FROM commission_settings
                    WHERE invoice_no IN (
                        SELECT DISTINCT invoice_no 
                        FROM commission_settings
                        -- You might want to filter by month here if you store invoice dates
                    )
                """
            else:
                query = """
                    SELECT 
                        invoice_no,
                        sale_code,
                        category,
                        is_commissionable,
                        commission_rate
                    FROM commission_settings
                    ORDER BY invoice_no, sale_code, category
                """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            settings = {}
            for row in results:
                invoice_no = row[0]
                sale_code = row[1]
                category = row[2]
                is_commissionable = row[3]
                
                # Create a unique key for each invoice line
                key = f"{invoice_no}_{sale_code}_{category}"
                settings[key] = {
                    'is_commissionable': is_commissionable,
                    'commission_rate': row[4] if len(row) > 4 else None
                }
            
            return jsonify({'settings': settings}), 200
            
    except Exception as e:
        logger.error(f"Error fetching commission settings: {str(e)}")
        return jsonify({'error': str(e)}), 500


@commission_settings_bp.route('/batch', methods=['POST'])
@jwt_required()
def update_commission_settings_batch():
    """Update multiple commission settings at once"""
    try:
        data = request.json
        settings = data.get('settings', [])
        username = get_jwt_identity()
        
        if not settings:
            return jsonify({'error': 'No settings provided'}), 400
        
        pg_service = PostgreSQLService()
        with pg_service.get_connection() as conn:
            cursor = conn.cursor()
            
            # First, ensure the table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS commission_settings (
                    id SERIAL PRIMARY KEY,
                    invoice_no INTEGER NOT NULL,
                    sale_code VARCHAR(50),
                    category VARCHAR(100),
                    is_commissionable BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by VARCHAR(100),
                    CONSTRAINT unique_invoice_line UNIQUE (invoice_no, sale_code, category)
                );
                
                CREATE INDEX IF NOT EXISTS idx_commission_invoice_no ON commission_settings(invoice_no);
                CREATE INDEX IF NOT EXISTS idx_commission_is_commissionable ON commission_settings(is_commissionable);
            """)
            
            # Process each setting
            for setting in settings:
                invoice_no = setting.get('invoice_no')
                sale_code = setting.get('sale_code', '')
                category = setting.get('category', '')
                is_commissionable = setting.get('is_commissionable', True)
                commission_rate = setting.get('commission_rate')  # Can be None for non-rentals
                
                # Use UPSERT (INSERT ... ON CONFLICT UPDATE)
                cursor.execute("""
                    INSERT INTO commission_settings 
                        (invoice_no, sale_code, category, is_commissionable, commission_rate, updated_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (invoice_no, sale_code, category)
                    DO UPDATE SET 
                        is_commissionable = EXCLUDED.is_commissionable,
                        commission_rate = EXCLUDED.commission_rate,
                        updated_at = CURRENT_TIMESTAMP,
                        updated_by = EXCLUDED.updated_by
                """, (invoice_no, sale_code, category, is_commissionable, commission_rate, username))
            
            conn.commit()
            
            return jsonify({'message': f'Successfully updated {len(settings)} settings'}), 200
            
    except Exception as e:
        logger.error(f"Error updating commission settings: {str(e)}")
        return jsonify({'error': str(e)}), 500


@commission_settings_bp.route('/<int:invoice_no>', methods=['GET'])
@jwt_required()
def get_invoice_commission_settings(invoice_no):
    """Get commission settings for a specific invoice"""
    try:
        pg_service = PostgreSQLService()
        with pg_service.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    sale_code,
                    category,
                    is_commissionable
                FROM commission_settings
                WHERE invoice_no = %s
            """, (invoice_no,))
            
            results = cursor.fetchall()
            
            settings = []
            for row in results:
                settings.append({
                    'sale_code': row[0],
                    'category': row[1],
                    'is_commissionable': row[2]
                })
            
            return jsonify({'invoice_no': invoice_no, 'settings': settings}), 200
            
    except Exception as e:
        logger.error(f"Error fetching invoice settings: {str(e)}")
        return jsonify({'error': str(e)}), 500


@commission_settings_bp.route('/<int:invoice_no>/<sale_code>/<category>', methods=['PUT'])
@jwt_required()
def update_single_commission_setting(invoice_no, sale_code, category):
    """Update a single commission setting"""
    try:
        data = request.json
        is_commissionable = data.get('is_commissionable', True)
        username = get_jwt_identity()
        
        pg_service = PostgreSQLService()
        with pg_service.get_connection() as conn:
            cursor = conn.cursor()
            
            # Use UPSERT
            cursor.execute("""
                INSERT INTO commission_settings 
                    (invoice_no, sale_code, category, is_commissionable, updated_by)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (invoice_no, sale_code, category)
                DO UPDATE SET 
                    is_commissionable = EXCLUDED.is_commissionable,
                    updated_at = CURRENT_TIMESTAMP,
                    updated_by = EXCLUDED.updated_by
            """, (invoice_no, sale_code, category, is_commissionable, username))
            
            conn.commit()
            
            return jsonify({'message': 'Setting updated successfully'}), 200
            
    except Exception as e:
        logger.error(f"Error updating commission setting: {str(e)}")
        return jsonify({'error': str(e)}), 500


@commission_settings_bp.route('/create-table', methods=['POST'])
@jwt_required()
def create_commission_settings_table():
    """Create the commission settings table if it doesn't exist"""
    try:
        pg_service = PostgreSQLService()
        with pg_service.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create the table with all necessary columns and constraints
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS commission_settings (
                    id SERIAL PRIMARY KEY,
                    invoice_no INTEGER NOT NULL,
                    sale_code VARCHAR(50),
                    category VARCHAR(100),
                    is_commissionable BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by VARCHAR(100),
                    CONSTRAINT unique_invoice_line UNIQUE (invoice_no, sale_code, category)
                );
                
                CREATE INDEX IF NOT EXISTS idx_commission_invoice_no ON commission_settings(invoice_no);
                CREATE INDEX IF NOT EXISTS idx_commission_is_commissionable ON commission_settings(is_commissionable);
                
                -- Add trigger for updated_at
                CREATE OR REPLACE FUNCTION update_commission_settings_timestamp()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
                
                DROP TRIGGER IF EXISTS update_commission_settings_timestamp ON commission_settings;
                CREATE TRIGGER update_commission_settings_timestamp
                BEFORE UPDATE ON commission_settings
                FOR EACH ROW
                EXECUTE FUNCTION update_commission_settings_timestamp();
            """)
            
            conn.commit()
            
            return jsonify({'message': 'Commission settings table created successfully'}), 200
            
    except Exception as e:
        logger.error(f"Error creating commission settings table: {str(e)}")
        return jsonify({'error': str(e)}), 500