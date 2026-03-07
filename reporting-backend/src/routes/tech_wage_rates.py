"""
Tech Wage Rates API
Stores fully-loaded hourly cost per technician per organization.
Used by the Technician Productivity report to calculate true profitability.
"""
import logging
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.postgres_service import PostgreSQLService
from src.models.user import User

logger = logging.getLogger(__name__)

tech_wage_rates_bp = Blueprint('tech_wage_rates', __name__, url_prefix='/api/tech-wage-rates')


def _get_org_id():
    """Get the current user's organization ID."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        return user.organization_id if user else None
    except Exception:
        return None


# ── Init table ────────────────────────────────────────────────────────────────

@tech_wage_rates_bp.route('/init-tables', methods=['POST'])
@jwt_required()
def init_tables():
    """Create the tech_wage_rates table if it doesn't exist."""
    try:
        pg = PostgreSQLService()
        with pg.get_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database connection not available'}), 500
            cursor = conn.cursor()
            cursor.execute(pg._get_tech_wage_rates_sql())
            conn.commit()
            return jsonify({'message': 'tech_wage_rates table created/verified'}), 200
    except Exception as e:
        logger.error(f"Error creating tech_wage_rates table: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ── GET all rates for this org ────────────────────────────────────────────────

@tech_wage_rates_bp.route('/', methods=['GET'])
@jwt_required()
def get_wage_rates():
    """Return all tech wage rates for the current organization."""
    try:
        org_id = _get_org_id()
        if not org_id:
            return jsonify({'error': 'Could not determine organization'}), 400

        pg = PostgreSQLService()
        with pg.get_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database connection not available'}), 500
            cursor = conn.cursor()
            # Auto-create table on first access
            cursor.execute(pg._get_tech_wage_rates_sql())
            cursor.execute("""
                SELECT id, org_id, tech_name, fully_loaded_rate, notes,
                       is_active, created_at, created_by, updated_at, updated_by
                FROM tech_wage_rates
                WHERE org_id = %s
                ORDER BY tech_name
            """, (org_id,))
            rows = cursor.fetchall()
            rates = []
            for r in rows:
                rates.append({
                    'id':               r['id'],
                    'orgId':            r['org_id'],
                    'techName':         r['tech_name'],
                    'fullyLoadedRate':  float(r['fully_loaded_rate']) if r['fully_loaded_rate'] else 0.0,
                    'notes':            r['notes'],
                    'isActive':         r['is_active'],
                    'createdAt':        r['created_at'].isoformat() if r['created_at'] else None,
                    'createdBy':        r['created_by'],
                    'updatedAt':        r['updated_at'].isoformat() if r['updated_at'] else None,
                    'updatedBy':        r['updated_by'],
                })
            return jsonify({'rates': rates}), 200
    except Exception as e:
        logger.error(f"Error fetching tech wage rates: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ── POST — create or upsert a rate ────────────────────────────────────────────

@tech_wage_rates_bp.route('/', methods=['POST'])
@jwt_required()
def save_wage_rate():
    """Create or update a tech wage rate (upsert on org_id + tech_name)."""
    try:
        org_id = _get_org_id()
        if not org_id:
            return jsonify({'error': 'Could not determine organization'}), 400

        data = request.get_json() or {}
        tech_name = (data.get('techName') or '').strip()
        rate = data.get('fullyLoadedRate')

        if not tech_name:
            return jsonify({'error': 'techName is required'}), 400
        if rate is None:
            return jsonify({'error': 'fullyLoadedRate is required'}), 400

        username = get_jwt_identity()
        pg = PostgreSQLService()
        with pg.get_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database connection not available'}), 500
            cursor = conn.cursor()
            cursor.execute(pg._get_tech_wage_rates_sql())
            cursor.execute("""
                INSERT INTO tech_wage_rates
                    (org_id, tech_name, fully_loaded_rate, notes, is_active, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (org_id, tech_name) DO UPDATE SET
                    fully_loaded_rate = EXCLUDED.fully_loaded_rate,
                    notes             = EXCLUDED.notes,
                    is_active         = EXCLUDED.is_active,
                    updated_at        = CURRENT_TIMESTAMP,
                    updated_by        = EXCLUDED.created_by
                RETURNING id
            """, (
                org_id,
                tech_name,
                float(rate),
                data.get('notes'),
                data.get('isActive', True),
                username,
            ))
            result = cursor.fetchone()
            conn.commit()
            return jsonify({'message': 'Wage rate saved', 'id': result['id']}), 200
    except Exception as e:
        logger.error(f"Error saving tech wage rate: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ── PUT — update a single rate by id ─────────────────────────────────────────

@tech_wage_rates_bp.route('/<int:rate_id>', methods=['PUT'])
@jwt_required()
def update_wage_rate(rate_id):
    """Update a specific tech wage rate by id."""
    try:
        org_id = _get_org_id()
        if not org_id:
            return jsonify({'error': 'Could not determine organization'}), 400

        data = request.get_json() or {}
        username = get_jwt_identity()
        pg = PostgreSQLService()
        with pg.get_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database connection not available'}), 500
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tech_wage_rates SET
                    fully_loaded_rate = %s,
                    notes             = %s,
                    is_active         = %s,
                    updated_at        = CURRENT_TIMESTAMP,
                    updated_by        = %s
                WHERE id = %s AND org_id = %s
            """, (
                float(data.get('fullyLoadedRate', 0)),
                data.get('notes'),
                data.get('isActive', True),
                username,
                rate_id,
                org_id,
            ))
            conn.commit()
            return jsonify({'message': 'Wage rate updated'}), 200
    except Exception as e:
        logger.error(f"Error updating tech wage rate: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ── DELETE ────────────────────────────────────────────────────────────────────

@tech_wage_rates_bp.route('/<int:rate_id>', methods=['DELETE'])
@jwt_required()
def delete_wage_rate(rate_id):
    """Delete a tech wage rate by id."""
    try:
        org_id = _get_org_id()
        if not org_id:
            return jsonify({'error': 'Could not determine organization'}), 400

        pg = PostgreSQLService()
        with pg.get_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database connection not available'}), 500
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM tech_wage_rates WHERE id = %s AND org_id = %s",
                (rate_id, org_id)
            )
            conn.commit()
            return jsonify({'message': 'Wage rate deleted'}), 200
    except Exception as e:
        logger.error(f"Error deleting tech wage rate: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ── Bulk save (used by the Configure panel to save all at once) ───────────────

@tech_wage_rates_bp.route('/bulk', methods=['POST'])
@jwt_required()
def bulk_save_wage_rates():
    """
    Save a list of {techName, fullyLoadedRate, notes} objects at once.
    Uses upsert so it's safe to call repeatedly.
    """
    try:
        org_id = _get_org_id()
        if not org_id:
            return jsonify({'error': 'Could not determine organization'}), 400

        data = request.get_json() or {}
        rates_list = data.get('rates', [])
        if not isinstance(rates_list, list):
            return jsonify({'error': 'rates must be a list'}), 400

        username = get_jwt_identity()
        pg = PostgreSQLService()
        saved = 0
        with pg.get_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database connection not available'}), 500
            cursor = conn.cursor()
            cursor.execute(pg._get_tech_wage_rates_sql())
            for item in rates_list:
                tech_name = (item.get('techName') or '').strip()
                rate = item.get('fullyLoadedRate')
                if not tech_name or rate is None:
                    continue
                cursor.execute("""
                    INSERT INTO tech_wage_rates
                        (org_id, tech_name, fully_loaded_rate, notes, is_active, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (org_id, tech_name) DO UPDATE SET
                        fully_loaded_rate = EXCLUDED.fully_loaded_rate,
                        notes             = EXCLUDED.notes,
                        is_active         = EXCLUDED.is_active,
                        updated_at        = CURRENT_TIMESTAMP,
                        updated_by        = EXCLUDED.created_by
                """, (
                    org_id,
                    tech_name,
                    float(rate),
                    item.get('notes'),
                    item.get('isActive', True),
                    username,
                ))
                saved += 1
            conn.commit()
        return jsonify({'message': f'{saved} wage rates saved'}), 200
    except Exception as e:
        logger.error(f"Error bulk-saving tech wage rates: {str(e)}")
        return jsonify({'error': str(e)}), 500
