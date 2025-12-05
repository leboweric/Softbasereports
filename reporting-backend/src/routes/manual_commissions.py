from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from src.services.postgres_service import PostgreSQLService

logger = logging.getLogger(__name__)
manual_commissions_bp = Blueprint('manual_commissions', __name__, url_prefix='/api/manual-commissions')


def ensure_table_exists(cursor):
    """Ensure the manual_commissions table exists"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS manual_commissions (
            id SERIAL PRIMARY KEY,
            salesman_name VARCHAR(100) NOT NULL,
            month VARCHAR(7) NOT NULL,
            invoice_no VARCHAR(50),
            invoice_date DATE,
            bill_to VARCHAR(100),
            customer_name VARCHAR(200),
            sale_code VARCHAR(50),
            category VARCHAR(100),
            amount DECIMAL(12, 2) DEFAULT 0,
            cost DECIMAL(12, 2),
            commission_amount DECIMAL(12, 2) DEFAULT 0,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(100),
            updated_by VARCHAR(100)
        );

        CREATE INDEX IF NOT EXISTS idx_manual_commissions_salesman ON manual_commissions(salesman_name);
        CREATE INDEX IF NOT EXISTS idx_manual_commissions_month ON manual_commissions(month);
        CREATE INDEX IF NOT EXISTS idx_manual_commissions_salesman_month ON manual_commissions(salesman_name, month);
    """)


@manual_commissions_bp.route('', methods=['GET'])
@jwt_required()
def get_manual_commissions():
    """Get manual commissions, optionally filtered by month and/or salesman"""
    try:
        month = request.args.get('month')
        salesman = request.args.get('salesman')

        pg_service = PostgreSQLService()
        with pg_service.get_connection() as conn:
            cursor = conn.cursor()
            ensure_table_exists(cursor)

            query = """
                SELECT
                    id, salesman_name, month, invoice_no, invoice_date,
                    bill_to, customer_name, sale_code, category,
                    amount, cost, commission_amount, description,
                    created_at, updated_at, created_by
                FROM manual_commissions
                WHERE 1=1
            """
            params = []

            if month:
                query += " AND month = %s"
                params.append(month)

            if salesman:
                query += " AND salesman_name = %s"
                params.append(salesman)

            query += " ORDER BY salesman_name, invoice_date DESC, id"

            cursor.execute(query, params)
            results = cursor.fetchall()

            commissions = []
            for row in results:
                # Row is a dict due to RealDictCursor from PostgreSQLService
                commissions.append({
                    'id': row['id'],
                    'salesman_name': row['salesman_name'],
                    'month': row['month'],
                    'invoice_no': row['invoice_no'],
                    'invoice_date': row['invoice_date'].isoformat() if row['invoice_date'] else None,
                    'bill_to': row['bill_to'],
                    'customer_name': row['customer_name'],
                    'sale_code': row['sale_code'],
                    'category': row['category'],
                    'amount': float(row['amount']) if row['amount'] else 0,
                    'cost': float(row['cost']) if row['cost'] else None,
                    'commission_amount': float(row['commission_amount']) if row['commission_amount'] else 0,
                    'description': row['description'],
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                    'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None,
                    'created_by': row['created_by']
                })

            return jsonify({'commissions': commissions}), 200

    except Exception as e:
        logger.error(f"Error fetching manual commissions: {str(e)}")
        return jsonify({'error': str(e)}), 500


@manual_commissions_bp.route('', methods=['POST'])
@jwt_required()
def create_manual_commission():
    """Create a new manual commission entry"""
    try:
        data = request.json
        username = get_jwt_identity()

        required_fields = ['salesman_name', 'month']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400

        pg_service = PostgreSQLService()
        with pg_service.get_connection() as conn:
            cursor = conn.cursor()
            ensure_table_exists(cursor)

            cursor.execute("""
                INSERT INTO manual_commissions
                    (salesman_name, month, invoice_no, invoice_date, bill_to,
                     customer_name, sale_code, category, amount, cost,
                     commission_amount, description, created_by, updated_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                data.get('salesman_name'),
                data.get('month'),
                data.get('invoice_no'),
                data.get('invoice_date'),
                data.get('bill_to'),
                data.get('customer_name'),
                data.get('sale_code'),
                data.get('category'),
                data.get('amount', 0),
                data.get('cost'),
                data.get('commission_amount', 0),
                data.get('description'),
                username,
                username
            ))

            # Row is a dict due to RealDictCursor from PostgreSQLService
            result = cursor.fetchone()
            new_id = result['id']
            conn.commit()

            return jsonify({'id': new_id, 'message': 'Manual commission created successfully'}), 201

    except Exception as e:
        logger.error(f"Error creating manual commission: {str(e)}")
        return jsonify({'error': str(e)}), 500


@manual_commissions_bp.route('/<int:commission_id>', methods=['PUT'])
@jwt_required()
def update_manual_commission(commission_id):
    """Update an existing manual commission entry"""
    try:
        data = request.json
        username = get_jwt_identity()

        pg_service = PostgreSQLService()
        with pg_service.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE manual_commissions SET
                    salesman_name = COALESCE(%s, salesman_name),
                    invoice_no = %s,
                    invoice_date = %s,
                    bill_to = %s,
                    customer_name = %s,
                    sale_code = %s,
                    category = %s,
                    amount = %s,
                    cost = %s,
                    commission_amount = %s,
                    description = %s,
                    updated_by = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id
            """, (
                data.get('salesman_name'),
                data.get('invoice_no'),
                data.get('invoice_date'),
                data.get('bill_to'),
                data.get('customer_name'),
                data.get('sale_code'),
                data.get('category'),
                data.get('amount', 0),
                data.get('cost'),
                data.get('commission_amount', 0),
                data.get('description'),
                username,
                commission_id
            ))

            result = cursor.fetchone()
            if not result:
                return jsonify({'error': 'Manual commission not found'}), 404

            conn.commit()

            return jsonify({'message': 'Manual commission updated successfully'}), 200

    except Exception as e:
        logger.error(f"Error updating manual commission: {str(e)}")
        return jsonify({'error': str(e)}), 500


@manual_commissions_bp.route('/<int:commission_id>', methods=['DELETE'])
@jwt_required()
def delete_manual_commission(commission_id):
    """Delete a manual commission entry"""
    try:
        pg_service = PostgreSQLService()
        with pg_service.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM manual_commissions WHERE id = %s RETURNING id
            """, (commission_id,))

            result = cursor.fetchone()
            if not result:
                return jsonify({'error': 'Manual commission not found'}), 404

            conn.commit()

            return jsonify({'message': 'Manual commission deleted successfully'}), 200

    except Exception as e:
        logger.error(f"Error deleting manual commission: {str(e)}")
        return jsonify({'error': str(e)}), 500


@manual_commissions_bp.route('/by-salesman', methods=['GET'])
@jwt_required()
def get_manual_commissions_by_salesman():
    """Get manual commissions grouped by salesman for a specific month"""
    try:
        month = request.args.get('month')
        if not month:
            return jsonify({'error': 'Month parameter is required'}), 400

        pg_service = PostgreSQLService()
        with pg_service.get_connection() as conn:
            cursor = conn.cursor()
            ensure_table_exists(cursor)

            cursor.execute("""
                SELECT
                    id, salesman_name, month, invoice_no, invoice_date,
                    bill_to, customer_name, sale_code, category,
                    amount, cost, commission_amount, description
                FROM manual_commissions
                WHERE month = %s
                ORDER BY salesman_name, invoice_date DESC, id
            """, (month,))

            results = cursor.fetchall()

            # Group by salesman
            by_salesman = {}
            for row in results:
                # Row is a dict due to RealDictCursor from PostgreSQLService
                salesman = row['salesman_name']
                if salesman not in by_salesman:
                    by_salesman[salesman] = []

                by_salesman[salesman].append({
                    'id': row['id'],
                    'invoice_no': row['invoice_no'],
                    'invoice_date': row['invoice_date'].isoformat() if row['invoice_date'] else None,
                    'bill_to': row['bill_to'],
                    'customer_name': row['customer_name'],
                    'sale_code': row['sale_code'],
                    'category': row['category'],
                    'amount': float(row['amount']) if row['amount'] else 0,
                    'cost': float(row['cost']) if row['cost'] else None,
                    'commission_amount': float(row['commission_amount']) if row['commission_amount'] else 0,
                    'description': row['description'],
                    'is_manual': True
                })

            return jsonify({'commissions_by_salesman': by_salesman}), 200

    except Exception as e:
        logger.error(f"Error fetching manual commissions by salesman: {str(e)}")
        return jsonify({'error': str(e)}), 500
