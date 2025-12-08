from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from datetime import datetime
from src.services.postgres_service import PostgreSQLService

logger = logging.getLogger(__name__)
sales_rep_comp_bp = Blueprint('sales_rep_comp', __name__, url_prefix='/api/sales-rep-comp')


# ============================================================================
# SETUP ENDPOINT - Create tables if they don't exist
# ============================================================================

@sales_rep_comp_bp.route('/init-tables', methods=['POST'])
@jwt_required()
def init_tables():
    """Create the sales rep comp tables if they don't exist"""
    try:
        pg_service = PostgreSQLService()
        with pg_service.get_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database connection not available'}), 500

            cursor = conn.cursor()
            cursor.execute(pg_service._get_sales_rep_comp_tables_sql())
            conn.commit()

            return jsonify({'message': 'Sales rep comp tables created successfully'}), 200

    except Exception as e:
        logger.error(f"Error creating tables: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ADMIN ENDPOINTS - For Bo to manage rep compensation plans
# ============================================================================

@sales_rep_comp_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_all_rep_settings():
    """Get all sales rep compensation settings (admin only)"""
    try:
        pg_service = PostgreSQLService()
        with pg_service.get_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database connection not available'}), 500

            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    id,
                    salesman_name,
                    salesman_code,
                    monthly_draw,
                    start_date,
                    starting_balance,
                    is_active,
                    notes,
                    created_at,
                    created_by,
                    updated_at,
                    updated_by
                FROM sales_rep_comp_settings
                ORDER BY salesman_name
            """)

            results = cursor.fetchall()
            settings = []
            for row in results:
                settings.append({
                    'id': row['id'],
                    'salesman_name': row['salesman_name'],
                    'salesman_code': row['salesman_code'],
                    'monthly_draw': float(row['monthly_draw']) if row['monthly_draw'] else 0,
                    'start_date': row['start_date'].isoformat() if row['start_date'] else None,
                    'starting_balance': float(row['starting_balance']) if row['starting_balance'] else 0,
                    'is_active': row['is_active'],
                    'notes': row['notes'],
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                    'created_by': row['created_by'],
                    'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None,
                    'updated_by': row['updated_by']
                })

            return jsonify({'settings': settings}), 200

    except Exception as e:
        logger.error(f"Error fetching rep comp settings: {str(e)}")
        return jsonify({'error': str(e)}), 500


@sales_rep_comp_bp.route('/settings', methods=['POST'])
@jwt_required()
def create_rep_settings():
    """Create a new sales rep compensation plan"""
    try:
        data = request.json
        username = get_jwt_identity()

        salesman_name = data.get('salesman_name')
        if not salesman_name:
            return jsonify({'error': 'salesman_name is required'}), 400

        pg_service = PostgreSQLService()
        with pg_service.get_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database connection not available'}), 500

            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO sales_rep_comp_settings
                    (salesman_name, salesman_code, monthly_draw, start_date, starting_balance, is_active, notes, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                salesman_name,
                data.get('salesman_code'),
                data.get('monthly_draw', 0),
                data.get('start_date'),
                data.get('starting_balance', 0),
                data.get('is_active', True),
                data.get('notes'),
                username
            ))

            result = cursor.fetchone()
            conn.commit()

            return jsonify({'message': 'Rep compensation settings created', 'id': result['id']}), 201

    except Exception as e:
        logger.error(f"Error creating rep comp settings: {str(e)}")
        return jsonify({'error': str(e)}), 500


@sales_rep_comp_bp.route('/settings/<int:setting_id>', methods=['PUT'])
@jwt_required()
def update_rep_settings(setting_id):
    """Update a sales rep compensation plan"""
    try:
        data = request.json
        username = get_jwt_identity()

        pg_service = PostgreSQLService()
        with pg_service.get_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database connection not available'}), 500

            cursor = conn.cursor()

            cursor.execute("""
                UPDATE sales_rep_comp_settings
                SET
                    salesman_name = COALESCE(%s, salesman_name),
                    salesman_code = COALESCE(%s, salesman_code),
                    monthly_draw = COALESCE(%s, monthly_draw),
                    start_date = COALESCE(%s, start_date),
                    starting_balance = COALESCE(%s, starting_balance),
                    is_active = COALESCE(%s, is_active),
                    notes = %s,
                    updated_at = CURRENT_TIMESTAMP,
                    updated_by = %s
                WHERE id = %s
            """, (
                data.get('salesman_name'),
                data.get('salesman_code'),
                data.get('monthly_draw'),
                data.get('start_date'),
                data.get('starting_balance'),
                data.get('is_active'),
                data.get('notes'),
                username,
                setting_id
            ))

            conn.commit()

            return jsonify({'message': 'Rep compensation settings updated'}), 200

    except Exception as e:
        logger.error(f"Error updating rep comp settings: {str(e)}")
        return jsonify({'error': str(e)}), 500


@sales_rep_comp_bp.route('/settings/<int:setting_id>', methods=['DELETE'])
@jwt_required()
def delete_rep_settings(setting_id):
    """Delete a sales rep compensation plan"""
    try:
        pg_service = PostgreSQLService()
        with pg_service.get_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database connection not available'}), 500

            cursor = conn.cursor()
            cursor.execute("DELETE FROM sales_rep_comp_settings WHERE id = %s", (setting_id,))
            conn.commit()

            return jsonify({'message': 'Rep compensation settings deleted'}), 200

    except Exception as e:
        logger.error(f"Error deleting rep comp settings: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# MONTHLY TRANSACTION ENDPOINTS
# ============================================================================

@sales_rep_comp_bp.route('/transactions/<salesman_name>', methods=['GET'])
@jwt_required()
def get_rep_transactions(salesman_name):
    """Get all monthly transactions for a sales rep"""
    try:
        pg_service = PostgreSQLService()
        with pg_service.get_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database connection not available'}), 500

            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    id,
                    salesman_name,
                    year_month,
                    gross_commissions,
                    draw_amount,
                    draw_taken,
                    opening_balance,
                    closing_balance,
                    is_locked,
                    locked_at,
                    locked_by,
                    notes,
                    created_at,
                    updated_at,
                    updated_by
                FROM sales_rep_monthly_transactions
                WHERE salesman_name = %s
                ORDER BY year_month DESC
            """, (salesman_name,))

            results = cursor.fetchall()
            transactions = []
            for row in results:
                transactions.append({
                    'id': row['id'],
                    'salesman_name': row['salesman_name'],
                    'year_month': row['year_month'],
                    'gross_commissions': float(row['gross_commissions']) if row['gross_commissions'] else 0,
                    'draw_amount': float(row['draw_amount']) if row['draw_amount'] else 0,
                    'draw_taken': row['draw_taken'],
                    'opening_balance': float(row['opening_balance']) if row['opening_balance'] else 0,
                    'closing_balance': float(row['closing_balance']) if row['closing_balance'] else 0,
                    'is_locked': row['is_locked'],
                    'locked_at': row['locked_at'].isoformat() if row['locked_at'] else None,
                    'locked_by': row['locked_by'],
                    'notes': row['notes'],
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                    'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None,
                    'updated_by': row['updated_by']
                })

            return jsonify({'transactions': transactions}), 200

    except Exception as e:
        logger.error(f"Error fetching rep transactions: {str(e)}")
        return jsonify({'error': str(e)}), 500


@sales_rep_comp_bp.route('/transactions', methods=['POST'])
@jwt_required()
def upsert_transaction():
    """Create or update a monthly transaction for a sales rep"""
    try:
        data = request.json
        username = get_jwt_identity()

        salesman_name = data.get('salesman_name')
        year_month = data.get('year_month')

        if not salesman_name or not year_month:
            return jsonify({'error': 'salesman_name and year_month are required'}), 400

        pg_service = PostgreSQLService()
        with pg_service.get_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database connection not available'}), 500

            cursor = conn.cursor()

            # Check if locked
            cursor.execute("""
                SELECT is_locked FROM sales_rep_monthly_transactions
                WHERE salesman_name = %s AND year_month = %s
            """, (salesman_name, year_month))

            existing = cursor.fetchone()
            if existing and existing['is_locked']:
                return jsonify({'error': 'This month is locked and cannot be modified'}), 400

            # Upsert the transaction
            cursor.execute("""
                INSERT INTO sales_rep_monthly_transactions
                    (salesman_name, year_month, gross_commissions, draw_amount, draw_taken,
                     opening_balance, closing_balance, notes, updated_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (salesman_name, year_month)
                DO UPDATE SET
                    gross_commissions = COALESCE(EXCLUDED.gross_commissions, sales_rep_monthly_transactions.gross_commissions),
                    draw_amount = COALESCE(EXCLUDED.draw_amount, sales_rep_monthly_transactions.draw_amount),
                    draw_taken = COALESCE(EXCLUDED.draw_taken, sales_rep_monthly_transactions.draw_taken),
                    opening_balance = COALESCE(EXCLUDED.opening_balance, sales_rep_monthly_transactions.opening_balance),
                    closing_balance = COALESCE(EXCLUDED.closing_balance, sales_rep_monthly_transactions.closing_balance),
                    notes = EXCLUDED.notes,
                    updated_at = CURRENT_TIMESTAMP,
                    updated_by = EXCLUDED.updated_by
                RETURNING id
            """, (
                salesman_name,
                year_month,
                data.get('gross_commissions'),
                data.get('draw_amount'),
                data.get('draw_taken'),
                data.get('opening_balance'),
                data.get('closing_balance'),
                data.get('notes'),
                username
            ))

            result = cursor.fetchone()
            conn.commit()

            return jsonify({'message': 'Transaction saved', 'id': result['id']}), 200

    except Exception as e:
        logger.error(f"Error saving transaction: {str(e)}")
        return jsonify({'error': str(e)}), 500


@sales_rep_comp_bp.route('/transactions/<salesman_name>/<year_month>/lock', methods=['POST'])
@jwt_required()
def lock_transaction(salesman_name, year_month):
    """Lock a monthly transaction (prevents further edits)"""
    try:
        username = get_jwt_identity()

        pg_service = PostgreSQLService()
        with pg_service.get_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database connection not available'}), 500

            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sales_rep_monthly_transactions
                SET is_locked = TRUE, locked_at = CURRENT_TIMESTAMP, locked_by = %s
                WHERE salesman_name = %s AND year_month = %s
            """, (username, salesman_name, year_month))

            conn.commit()

            return jsonify({'message': 'Transaction locked'}), 200

    except Exception as e:
        logger.error(f"Error locking transaction: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# SALES REP VIEW ENDPOINTS - For reps to view their own commission data
# ============================================================================

@sales_rep_comp_bp.route('/my-report/<year_month>', methods=['GET'])
@jwt_required()
def get_my_commission_report(year_month):
    """
    Get commission report for the logged-in sales rep.
    This will be restricted by RBAC to only show the rep's own data.
    """
    try:
        username = get_jwt_identity()

        # Get the salesman name mapping for this user
        # For now we'll use a simple lookup - this can be enhanced later
        pg_service = PostgreSQLService()
        with pg_service.get_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database connection not available'}), 500

            cursor = conn.cursor()

            # First, get the rep's settings (including their salesman name mapping)
            cursor.execute("""
                SELECT
                    s.salesman_name,
                    s.monthly_draw,
                    s.starting_balance,
                    s.start_date
                FROM sales_rep_comp_settings s
                WHERE s.is_active = TRUE
                -- In the future, link to user table via email or user_id
            """)

            all_reps = cursor.fetchall()

            # For now, return all active reps - will filter by user once RBAC is set up
            report_data = []

            for rep in all_reps:
                salesman_name = rep['salesman_name']

                # Get the transaction for this month
                cursor.execute("""
                    SELECT * FROM sales_rep_monthly_transactions
                    WHERE salesman_name = %s AND year_month = %s
                """, (salesman_name, year_month))

                transaction = cursor.fetchone()

                # Get previous month's closing balance for opening balance
                prev_month = get_previous_month(year_month)
                cursor.execute("""
                    SELECT closing_balance FROM sales_rep_monthly_transactions
                    WHERE salesman_name = %s AND year_month = %s
                """, (salesman_name, prev_month))

                prev_trans = cursor.fetchone()
                opening_balance = prev_trans['closing_balance'] if prev_trans else rep['starting_balance']

                report_data.append({
                    'salesman_name': salesman_name,
                    'monthly_draw': float(rep['monthly_draw']) if rep['monthly_draw'] else 0,
                    'opening_balance': float(opening_balance) if opening_balance else 0,
                    'gross_commissions': float(transaction['gross_commissions']) if transaction and transaction['gross_commissions'] else 0,
                    'draw_amount': float(transaction['draw_amount']) if transaction and transaction['draw_amount'] else 0,
                    'draw_taken': transaction['draw_taken'] if transaction else False,
                    'closing_balance': float(transaction['closing_balance']) if transaction and transaction['closing_balance'] else 0,
                    'is_locked': transaction['is_locked'] if transaction else False
                })

            return jsonify({'report': report_data, 'year_month': year_month}), 200

    except Exception as e:
        logger.error(f"Error fetching my commission report: {str(e)}")
        return jsonify({'error': str(e)}), 500


@sales_rep_comp_bp.route('/calculate/<salesman_name>/<year_month>', methods=['POST'])
@jwt_required()
def calculate_rep_commission(salesman_name, year_month):
    """
    Calculate commission for a rep for a specific month.
    This pulls verified (checked) invoices from the main commission report.
    """
    try:
        username = get_jwt_identity()

        pg_service = PostgreSQLService()
        with pg_service.get_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database connection not available'}), 500

            cursor = conn.cursor()

            # Get rep settings
            cursor.execute("""
                SELECT * FROM sales_rep_comp_settings
                WHERE salesman_name = %s AND is_active = TRUE
            """, (salesman_name,))

            rep_settings = cursor.fetchone()
            if not rep_settings:
                return jsonify({'error': f'No active settings found for {salesman_name}'}), 404

            # Get previous month's closing balance
            prev_month = get_previous_month(year_month)
            cursor.execute("""
                SELECT closing_balance FROM sales_rep_monthly_transactions
                WHERE salesman_name = %s AND year_month = %s
            """, (salesman_name, prev_month))

            prev_trans = cursor.fetchone()
            opening_balance = float(prev_trans['closing_balance']) if prev_trans else float(rep_settings['starting_balance'])

            # The gross_commissions will be passed in from the frontend
            # (calculated from verified invoices in the commission report)
            data = request.json or {}
            gross_commissions = float(data.get('gross_commissions', 0))
            draw_taken = data.get('draw_taken', False)
            monthly_draw = float(rep_settings['monthly_draw'])

            # Calculate the closing balance
            # Opening Balance + Draw (if taken) - Commissions = Closing Balance
            # Positive balance = rep owes company (overdraw)
            # Negative balance = company owes rep (banked excess)
            draw_amount = monthly_draw if draw_taken else 0
            closing_balance = opening_balance + draw_amount - gross_commissions

            # Upsert the transaction
            cursor.execute("""
                INSERT INTO sales_rep_monthly_transactions
                    (salesman_name, year_month, gross_commissions, draw_amount, draw_taken,
                     opening_balance, closing_balance, updated_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (salesman_name, year_month)
                DO UPDATE SET
                    gross_commissions = EXCLUDED.gross_commissions,
                    draw_amount = EXCLUDED.draw_amount,
                    draw_taken = EXCLUDED.draw_taken,
                    opening_balance = EXCLUDED.opening_balance,
                    closing_balance = EXCLUDED.closing_balance,
                    updated_at = CURRENT_TIMESTAMP,
                    updated_by = EXCLUDED.updated_by
                RETURNING *
            """, (
                salesman_name,
                year_month,
                gross_commissions,
                draw_amount,
                draw_taken,
                opening_balance,
                closing_balance,
                username
            ))

            result = cursor.fetchone()
            conn.commit()

            return jsonify({
                'message': 'Commission calculated',
                'transaction': {
                    'salesman_name': result['salesman_name'],
                    'year_month': result['year_month'],
                    'monthly_draw': monthly_draw,
                    'gross_commissions': float(result['gross_commissions']),
                    'draw_amount': float(result['draw_amount']),
                    'draw_taken': result['draw_taken'],
                    'opening_balance': float(result['opening_balance']),
                    'closing_balance': float(result['closing_balance'])
                }
            }), 200

    except Exception as e:
        logger.error(f"Error calculating commission: {str(e)}")
        return jsonify({'error': str(e)}), 500


def get_previous_month(year_month):
    """Get the previous month in YYYY-MM format"""
    year, month = map(int, year_month.split('-'))
    if month == 1:
        return f"{year - 1}-12"
    return f"{year}-{month - 1:02d}"
