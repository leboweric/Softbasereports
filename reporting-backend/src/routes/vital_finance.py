"""
VITAL WorkLife Finance Module API Routes
Handles billing management, contracts, and revenue tracking
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date
from decimal import Decimal
import json

vital_finance_bp = Blueprint('vital_finance', __name__)

# Import services
from src.services.postgres_service import get_postgres_db

def get_db():
    """Get PostgreSQL database connection"""
    return get_postgres_db()


# =============================================================================
# CLIENTS ENDPOINTS
# =============================================================================

@vital_finance_bp.route('/api/vital/finance/clients', methods=['GET'])
@jwt_required()
def get_clients():
    """Get all billing clients for the organization"""
    try:
        db = get_db()
        current_user = get_jwt_identity()
        
        # Get user's org_id
        user_result = db.execute_query(
            "SELECT organization_id FROM \"user\" WHERE email = %s",
            (current_user,)
        )
        if not user_result:
            return jsonify({'error': 'User not found'}), 404
        
        org_id = user_result[0]['organization_id']
        
        # Get all clients with latest population and rate
        query = """
            SELECT 
                c.*,
                (SELECT population_count FROM finance_population_history 
                 WHERE client_id = c.id ORDER BY effective_date DESC LIMIT 1) as current_population,
                (SELECT pepm_rate FROM finance_rate_schedules rs
                 JOIN finance_contracts fc ON rs.contract_id = fc.id
                 WHERE fc.client_id = c.id AND rs.effective_date <= CURRENT_DATE
                 ORDER BY rs.effective_date DESC LIMIT 1) as current_rate,
                (SELECT renewal_date FROM finance_contracts 
                 WHERE client_id = c.id AND status = 'active' LIMIT 1) as renewal_date
            FROM finance_clients c
            WHERE c.org_id = %s
            ORDER BY c.billing_name
        """
        
        clients = db.execute_query(query, (org_id,))
        
        # Calculate monthly revenue for each client
        for client in clients:
            pop = client.get('current_population') or 0
            rate = float(client.get('current_rate') or 0)
            client['monthly_revenue'] = pop * rate
        
        return jsonify({
            'success': True,
            'clients': clients,
            'count': len(clients)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@vital_finance_bp.route('/api/vital/finance/clients', methods=['POST'])
@jwt_required()
def create_client():
    """Create a new billing client"""
    try:
        db = get_db()
        current_user = get_jwt_identity()
        data = request.json
        
        # Get user's org_id
        user_result = db.execute_query(
            "SELECT organization_id FROM \"user\" WHERE email = %s",
            (current_user,)
        )
        org_id = user_result[0]['organization_id']
        
        # Insert client
        query = """
            INSERT INTO finance_clients 
            (org_id, billing_name, hubspot_company_id, hubspot_company_name, 
             industry, tier, solution_type, applicable_law_state, nexus_state, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        result = db.execute_query(query, (
            org_id,
            data.get('billing_name'),
            data.get('hubspot_company_id'),
            data.get('hubspot_company_name'),
            data.get('industry'),
            data.get('tier'),
            data.get('solution_type'),
            data.get('applicable_law_state'),
            data.get('nexus_state'),
            data.get('status', 'active')
        ))
        
        # Log the action
        _log_audit('finance_clients', result[0]['id'], 'INSERT', None, data, current_user)
        
        return jsonify({
            'success': True,
            'client_id': result[0]['id'],
            'message': 'Client created successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@vital_finance_bp.route('/api/vital/finance/clients/<int:client_id>', methods=['PUT'])
@jwt_required()
def update_client(client_id):
    """Update a billing client"""
    try:
        db = get_db()
        current_user = get_jwt_identity()
        data = request.json
        
        # Get old values for audit
        old_result = db.execute_query(
            "SELECT * FROM finance_clients WHERE id = %s", (client_id,)
        )
        
        # Update client
        query = """
            UPDATE finance_clients SET
                billing_name = COALESCE(%s, billing_name),
                hubspot_company_id = COALESCE(%s, hubspot_company_id),
                hubspot_company_name = COALESCE(%s, hubspot_company_name),
                industry = COALESCE(%s, industry),
                tier = COALESCE(%s, tier),
                solution_type = COALESCE(%s, solution_type),
                applicable_law_state = COALESCE(%s, applicable_law_state),
                nexus_state = COALESCE(%s, nexus_state),
                status = COALESCE(%s, status),
                at_risk_reason = COALESCE(%s, at_risk_reason),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        db.execute_query(query, (
            data.get('billing_name'),
            data.get('hubspot_company_id'),
            data.get('hubspot_company_name'),
            data.get('industry'),
            data.get('tier'),
            data.get('solution_type'),
            data.get('applicable_law_state'),
            data.get('nexus_state'),
            data.get('status'),
            data.get('at_risk_reason'),
            client_id
        ))
        
        # Log the action
        _log_audit('finance_clients', client_id, 'UPDATE', old_result[0] if old_result else None, data, current_user)
        
        return jsonify({
            'success': True,
            'message': 'Client updated successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# POPULATION ENDPOINTS
# =============================================================================

@vital_finance_bp.route('/api/vital/finance/clients/<int:client_id>/population', methods=['GET'])
@jwt_required()
def get_population_history(client_id):
    """Get population history for a client"""
    try:
        db = get_db()
        
        query = """
            SELECT * FROM finance_population_history
            WHERE client_id = %s
            ORDER BY effective_date DESC
        """
        
        history = db.execute_query(query, (client_id,))
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@vital_finance_bp.route('/api/vital/finance/clients/<int:client_id>/population', methods=['POST'])
@jwt_required()
def add_population(client_id):
    """Add a population change for a client"""
    try:
        db = get_db()
        current_user = get_jwt_identity()
        data = request.json
        
        query = """
            INSERT INTO finance_population_history
            (client_id, effective_date, population_count, source, notes)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (client_id, effective_date) 
            DO UPDATE SET 
                population_count = EXCLUDED.population_count,
                notes = EXCLUDED.notes
            RETURNING id
        """
        
        result = db.execute_query(query, (
            client_id,
            data.get('effective_date'),
            data.get('population_count'),
            data.get('source', 'manual'),
            data.get('notes')
        ))
        
        # Recalculate billing for affected months
        _recalculate_billing(db, client_id, data.get('effective_date'))
        
        return jsonify({
            'success': True,
            'population_id': result[0]['id'],
            'message': 'Population updated successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# RATE SCHEDULE ENDPOINTS
# =============================================================================

@vital_finance_bp.route('/api/vital/finance/clients/<int:client_id>/rates', methods=['GET'])
@jwt_required()
def get_rate_schedules(client_id):
    """Get rate schedules for a client"""
    try:
        db = get_db()
        
        query = """
            SELECT rs.*, fc.renewal_date
            FROM finance_rate_schedules rs
            JOIN finance_contracts fc ON rs.contract_id = fc.id
            WHERE fc.client_id = %s
            ORDER BY rs.effective_date DESC
        """
        
        rates = db.execute_query(query, (client_id,))
        
        return jsonify({
            'success': True,
            'rates': rates
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@vital_finance_bp.route('/api/vital/finance/clients/<int:client_id>/rates', methods=['POST'])
@jwt_required()
def add_rate_schedule(client_id):
    """Add a rate schedule for a client"""
    try:
        db = get_db()
        current_user = get_jwt_identity()
        data = request.json
        
        # Get or create active contract
        contract_result = db.execute_query(
            "SELECT id FROM finance_contracts WHERE client_id = %s AND status = 'active' LIMIT 1",
            (client_id,)
        )
        
        if not contract_result:
            # Create a contract if none exists
            contract_result = db.execute_query(
                """INSERT INTO finance_contracts (client_id, start_date, renewal_date, status)
                   VALUES (%s, %s, %s, 'active') RETURNING id""",
                (client_id, data.get('effective_date'), data.get('effective_date'))
            )
        
        contract_id = contract_result[0]['id']
        
        # End previous rate if exists
        db.execute_query(
            """UPDATE finance_rate_schedules 
               SET end_date = %s 
               WHERE contract_id = %s AND end_date IS NULL""",
            (data.get('effective_date'), contract_id)
        )
        
        # Insert new rate
        query = """
            INSERT INTO finance_rate_schedules
            (contract_id, effective_date, pepm_rate, rate_type)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """
        
        result = db.execute_query(query, (
            contract_id,
            data.get('effective_date'),
            data.get('pepm_rate'),
            data.get('rate_type', 'confirmed')
        ))
        
        # Recalculate billing for affected months
        _recalculate_billing(db, client_id, data.get('effective_date'))
        
        return jsonify({
            'success': True,
            'rate_id': result[0]['id'],
            'message': 'Rate schedule added successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# BILLING SUMMARY ENDPOINTS
# =============================================================================

@vital_finance_bp.route('/api/vital/finance/billing/summary', methods=['GET'])
@jwt_required()
def get_billing_summary():
    """Get billing summary with pivot-table-like aggregations"""
    try:
        db = get_db()
        current_user = get_jwt_identity()
        
        # Get user's org_id
        user_result = db.execute_query(
            "SELECT organization_id FROM \"user\" WHERE email = %s",
            (current_user,)
        )
        org_id = user_result[0]['organization_id']
        
        year = request.args.get('year', datetime.now().year)
        
        # Get monthly billing totals
        query = """
            SELECT 
                mb.billing_month,
                SUM(mb.revenue_revrec) as total_revrec,
                SUM(mb.revenue_cash) as total_cash,
                SUM(mb.population_count) as total_population,
                COUNT(DISTINCT mb.client_id) as client_count
            FROM finance_monthly_billing mb
            JOIN finance_clients c ON mb.client_id = c.id
            WHERE c.org_id = %s AND mb.billing_year = %s
            GROUP BY mb.billing_month
            ORDER BY mb.billing_month
        """
        
        monthly = db.execute_query(query, (org_id, year))
        
        # Get totals by tier
        tier_query = """
            SELECT 
                c.tier,
                SUM(mb.revenue_revrec) as total_revenue,
                COUNT(DISTINCT c.id) as client_count,
                AVG(mb.pepm_rate) as avg_pepm
            FROM finance_monthly_billing mb
            JOIN finance_clients c ON mb.client_id = c.id
            WHERE c.org_id = %s AND mb.billing_year = %s
            GROUP BY c.tier
        """
        
        by_tier = db.execute_query(tier_query, (org_id, year))
        
        # Get totals by solution
        solution_query = """
            SELECT 
                c.solution_type,
                SUM(mb.revenue_revrec) as total_revenue,
                COUNT(DISTINCT c.id) as client_count,
                AVG(mb.pepm_rate) as avg_pepm
            FROM finance_monthly_billing mb
            JOIN finance_clients c ON mb.client_id = c.id
            WHERE c.org_id = %s AND mb.billing_year = %s
            GROUP BY c.solution_type
        """
        
        by_solution = db.execute_query(solution_query, (org_id, year))
        
        # Get at-risk summary
        at_risk_query = """
            SELECT 
                SUM(ar.monthly_revenue_at_risk) as monthly_at_risk,
                SUM(ar.annual_revenue_at_risk) as annual_at_risk,
                COUNT(*) as at_risk_count
            FROM finance_at_risk ar
            JOIN finance_clients c ON ar.client_id = c.id
            WHERE c.org_id = %s AND ar.status = 'active'
        """
        
        at_risk = db.execute_query(at_risk_query, (org_id,))
        
        # Calculate book of business value
        book_value_query = """
            SELECT 
                SUM(
                    COALESCE((SELECT population_count FROM finance_population_history 
                     WHERE client_id = c.id ORDER BY effective_date DESC LIMIT 1), 0) *
                    COALESCE((SELECT pepm_rate FROM finance_rate_schedules rs
                     JOIN finance_contracts fc ON rs.contract_id = fc.id
                     WHERE fc.client_id = c.id AND rs.effective_date <= CURRENT_DATE
                     ORDER BY rs.effective_date DESC LIMIT 1), 0) * 12
                ) as annual_book_value
            FROM finance_clients c
            WHERE c.org_id = %s AND c.status = 'active'
        """
        
        book_value = db.execute_query(book_value_query, (org_id,))
        
        return jsonify({
            'success': True,
            'year': year,
            'monthly': monthly,
            'by_tier': by_tier,
            'by_solution': by_solution,
            'at_risk': at_risk[0] if at_risk else {},
            'book_value': float(book_value[0]['annual_book_value'] or 0) if book_value else 0
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@vital_finance_bp.route('/api/vital/finance/renewals', methods=['GET'])
@jwt_required()
def get_renewals():
    """Get upcoming renewals"""
    try:
        db = get_db()
        current_user = get_jwt_identity()
        
        # Get user's org_id
        user_result = db.execute_query(
            "SELECT organization_id FROM \"user\" WHERE email = %s",
            (current_user,)
        )
        org_id = user_result[0]['organization_id']
        
        months_ahead = request.args.get('months', 6, type=int)
        
        query = """
            SELECT 
                c.id, c.billing_name, c.tier, c.solution_type, c.status,
                fc.renewal_date, fc.renewal_status,
                (SELECT population_count FROM finance_population_history 
                 WHERE client_id = c.id ORDER BY effective_date DESC LIMIT 1) as population,
                (SELECT pepm_rate FROM finance_rate_schedules rs
                 WHERE rs.contract_id = fc.id AND rs.effective_date <= CURRENT_DATE
                 ORDER BY rs.effective_date DESC LIMIT 1) as current_rate
            FROM finance_clients c
            JOIN finance_contracts fc ON fc.client_id = c.id
            WHERE c.org_id = %s 
              AND fc.status = 'active'
              AND fc.renewal_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '%s months'
            ORDER BY fc.renewal_date
        """
        
        renewals = db.execute_query(query, (org_id, months_ahead))
        
        # Calculate annual value for each
        for r in renewals:
            pop = r.get('population') or 0
            rate = float(r.get('current_rate') or 0)
            r['annual_value'] = pop * rate * 12
        
        return jsonify({
            'success': True,
            'renewals': renewals,
            'count': len(renewals)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# HUBSPOT SYNC ENDPOINT
# =============================================================================

@vital_finance_bp.route('/api/vital/finance/sync/hubspot', methods=['POST'])
@jwt_required()
def sync_from_hubspot():
    """Sync population changes from HubSpot"""
    try:
        # This will be implemented to pull from HubSpot and update populations
        # For now, return a placeholder
        return jsonify({
            'success': True,
            'message': 'HubSpot sync not yet implemented',
            'synced': 0
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _recalculate_billing(db, client_id, from_date):
    """Recalculate monthly billing from a given date forward"""
    try:
        from_date = datetime.strptime(from_date, '%Y-%m-%d').date() if isinstance(from_date, str) else from_date
        
        # Get all months from from_date to end of next year
        current_year = datetime.now().year
        
        for year in [current_year, current_year + 1]:
            for month in range(1, 13):
                month_date = date(year, month, 1)
                if month_date < from_date:
                    continue
                
                # Get population for this month
                pop_result = db.execute_query(
                    """SELECT population_count FROM finance_population_history
                       WHERE client_id = %s AND effective_date <= %s
                       ORDER BY effective_date DESC LIMIT 1""",
                    (client_id, month_date)
                )
                population = pop_result[0]['population_count'] if pop_result else 0
                
                # Get rate for this month
                rate_result = db.execute_query(
                    """SELECT rs.pepm_rate FROM finance_rate_schedules rs
                       JOIN finance_contracts fc ON rs.contract_id = fc.id
                       WHERE fc.client_id = %s AND rs.effective_date <= %s
                       ORDER BY rs.effective_date DESC LIMIT 1""",
                    (client_id, month_date)
                )
                rate = float(rate_result[0]['pepm_rate']) if rate_result else 0
                
                # Calculate revenue
                revenue = population * rate
                
                # Upsert billing record
                db.execute_query(
                    """INSERT INTO finance_monthly_billing
                       (client_id, billing_year, billing_month, population_count, pepm_rate, revenue_revrec, revenue_cash)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (client_id, billing_year, billing_month)
                       DO UPDATE SET
                           population_count = EXCLUDED.population_count,
                           pepm_rate = EXCLUDED.pepm_rate,
                           revenue_revrec = EXCLUDED.revenue_revrec,
                           revenue_cash = EXCLUDED.revenue_cash,
                           updated_at = CURRENT_TIMESTAMP""",
                    (client_id, year, month, population, rate, revenue, revenue)
                )
                
    except Exception as e:
        print(f"Error recalculating billing: {e}")


def _log_audit(table_name, record_id, action, old_values, new_values, user_email):
    """Log an audit entry"""
    try:
        db = get_db()
        
        # Convert to JSON-serializable format
        def serialize(obj):
            if obj is None:
                return None
            if isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            if isinstance(obj, Decimal):
                return float(obj)
            return obj
        
        db.execute_query(
            """INSERT INTO finance_audit_log
               (table_name, record_id, action, old_values, new_values, user_email)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (table_name, record_id, action, 
             json.dumps(serialize(old_values)) if old_values else None,
             json.dumps(serialize(new_values)) if new_values else None,
             user_email)
        )
    except Exception as e:
        print(f"Error logging audit: {e}")
