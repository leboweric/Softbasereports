from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from src.services.postgres_service import PostgreSQLService

logger = logging.getLogger(__name__)
commission_settings_bp = Blueprint('commission_settings', __name__, url_prefix='/api/commission-settings')

def ensure_commission_settings_table(cursor):
    """Ensure the commission_settings table exists with all required columns"""
    # Create table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS commission_settings (
            id SERIAL PRIMARY KEY,
            invoice_no INTEGER NOT NULL,
            sale_code VARCHAR(50),
            category VARCHAR(100),
            is_commissionable BOOLEAN DEFAULT TRUE,
            commission_rate DECIMAL(5, 4),
            cost_override DECIMAL(12, 2),
            extra_commission DECIMAL(12, 2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by VARCHAR(100),
            CONSTRAINT unique_invoice_line UNIQUE (invoice_no, sale_code, category)
        );

        CREATE INDEX IF NOT EXISTS idx_commission_invoice_no ON commission_settings(invoice_no);
        CREATE INDEX IF NOT EXISTS idx_commission_is_commissionable ON commission_settings(is_commissionable);
    """)

    # Add missing columns if table already exists (for existing deployments)
    cursor.execute("ALTER TABLE commission_settings ADD COLUMN IF NOT EXISTS commission_rate DECIMAL(5, 4);")
    cursor.execute("ALTER TABLE commission_settings ADD COLUMN IF NOT EXISTS cost_override DECIMAL(12, 2);")
    cursor.execute("ALTER TABLE commission_settings ADD COLUMN IF NOT EXISTS extra_commission DECIMAL(12, 2) DEFAULT 0;")


@commission_settings_bp.route('', methods=['GET'])
@jwt_required()
def get_commission_settings():
    """Get all commission settings"""
    try:
        pg_service = PostgreSQLService()
        with pg_service.get_connection() as conn:
            cursor = conn.cursor()

            # Ensure table and columns exist
            ensure_commission_settings_table(cursor)
            conn.commit()

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
                        commission_rate,
                        cost_override,
                        extra_commission
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
                        commission_rate,
                        cost_override,
                        extra_commission
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
                    'commission_rate': float(row[4]) if row[4] is not None else None,
                    'cost_override': float(row[5]) if row[5] is not None else None,
                    'extra_commission': float(row[6]) if row[6] is not None else 0
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

            # Ensure table and columns exist
            ensure_commission_settings_table(cursor)

            # Process each setting
            for setting in settings:
                invoice_no = setting.get('invoice_no')
                sale_code = setting.get('sale_code', '')
                category = setting.get('category', '')
                is_commissionable = setting.get('is_commissionable', True)
                commission_rate = setting.get('commission_rate')  # Can be None for non-rentals
                cost_override = setting.get('cost_override')  # Can be None if not overridden
                extra_commission = setting.get('extra_commission', 0)  # Default to 0
                
                # Use UPSERT (INSERT ... ON CONFLICT UPDATE)
                cursor.execute("""
                    INSERT INTO commission_settings 
                        (invoice_no, sale_code, category, is_commissionable, commission_rate, cost_override, extra_commission, updated_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (invoice_no, sale_code, category)
                    DO UPDATE SET 
                        is_commissionable = EXCLUDED.is_commissionable,
                        commission_rate = EXCLUDED.commission_rate,
                        cost_override = EXCLUDED.cost_override,
                        extra_commission = EXCLUDED.extra_commission,
                        updated_at = CURRENT_TIMESTAMP,
                        updated_by = EXCLUDED.updated_by
                """, (invoice_no, sale_code, category, is_commissionable, commission_rate, cost_override, extra_commission, username))
            
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

            # Ensure table and columns exist
            ensure_commission_settings_table(cursor)

            # Add trigger for updated_at
            cursor.execute("""
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