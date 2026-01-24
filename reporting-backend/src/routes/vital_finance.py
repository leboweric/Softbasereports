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
        
        # Get user's org_id - JWT identity returns user ID
        user_result = db.execute_query(
            "SELECT organization_id FROM \"user\" WHERE id = %s",
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
            "SELECT organization_id FROM \"user\" WHERE id = %s",
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
            "SELECT organization_id FROM \"user\" WHERE id = %s",
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
            "SELECT organization_id FROM \"user\" WHERE id = %s",
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


# =============================================================================
# BILLING ENGINE ENDPOINTS
# =============================================================================

@vital_finance_bp.route('/api/vital/finance/billing/calculate', methods=['GET'])
@jwt_required()
def calculate_billing():
    """
    Calculate billing for all clients.
    Query params:
        - year: Year to calculate (default: current year)
        - type: 'cash', 'revrec', or 'both' (default: 'both')
    """
    try:
        from src.services.billing_engine import BillingEngine
        import psycopg2
        import os
        
        current_user = get_jwt_identity()
        year = request.args.get('year', datetime.now().year, type=int)
        revenue_type = request.args.get('type', 'both')
        
        # Get user's org_id
        db = get_db()
        user_result = db.execute_query(
            "SELECT organization_id FROM \"user\" WHERE id = %s",
            (current_user,)
        )
        org_id = user_result[0]['organization_id']
        
        # Create direct connection for billing engine
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        engine = BillingEngine(conn)
        
        results = engine.calculate_all_clients_billing(org_id, year)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'year': year,
            'type': revenue_type,
            'clients': results,
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@vital_finance_bp.route('/api/vital/finance/billing/report', methods=['GET'])
@jwt_required()
def get_billing_report():
    """
    Generate comprehensive billing report similar to spreadsheet.
    Query params:
        - year: Year to report (default: current year)
    """
    try:
        from src.services.billing_engine import BillingEngine
        import psycopg2
        import os
        
        current_user = get_jwt_identity()
        year = request.args.get('year', datetime.now().year, type=int)
        
        # Get user's org_id
        db = get_db()
        user_result = db.execute_query(
            "SELECT organization_id FROM \"user\" WHERE id = %s",
            (current_user,)
        )
        org_id = user_result[0]['organization_id']
        
        # Create direct connection for billing engine
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        engine = BillingEngine(conn)
        
        report = engine.generate_billing_report(org_id, year)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@vital_finance_bp.route('/api/vital/finance/billing/summary/v2', methods=['GET'])
@jwt_required()
def get_billing_summary_v2():
    """
    Get billing summary grouped by dimension (using BillingEngine).
    Query params:
        - year: Year to summarize (default: current year)
        - group_by: 'tier', 'industry', 'session_product', or 'month' (default: 'tier')
    """
    try:
        from src.services.billing_engine import BillingEngine
        import psycopg2
        import os
        
        current_user = get_jwt_identity()
        year = request.args.get('year', datetime.now().year, type=int)
        group_by = request.args.get('group_by', 'tier')
        
        # Get user's org_id
        db = get_db()
        user_result = db.execute_query(
            "SELECT organization_id FROM \"user\" WHERE id = %s",
            (current_user,)
        )
        org_id = user_result[0]['organization_id']
        
        # Create direct connection for billing engine
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        engine = BillingEngine(conn)
        
        summary = engine.get_billing_summary(org_id, year, group_by)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'year': year,
            'group_by': group_by,
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@vital_finance_bp.route('/api/vital/finance/billing/client/<int:client_id>', methods=['GET'])
@jwt_required()
def get_client_billing(client_id):
    """
    Get detailed billing for a specific client.
    Query params:
        - year: Year to calculate (default: current year)
    """
    try:
        from src.services.billing_engine import BillingEngine
        import psycopg2
        import os
        
        year = request.args.get('year', datetime.now().year, type=int)
        
        # Create direct connection for billing engine
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        engine = BillingEngine(conn)
        
        client_data = engine.get_client_billing_data(client_id)
        if not client_data:
            conn.close()
            return jsonify({'error': 'Client not found'}), 404
        
        billing = engine.calculate_year_billing(client_data, year)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'client': client_data,
            'billing': billing
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@vital_finance_bp.route('/api/vital/finance/billing/pivot', methods=['GET'])
@jwt_required()
def get_billing_pivot():
    """
    Get pivot-table style data for billing dashboard.
    Replicates the spreadsheet pivot tables.
    Query params:
        - year: Year to analyze (default: current year)
        - pivot: 'wpo', 'tier_product', 'renewals', 'top_clients', 'industry', 'nexus'
    """
    try:
        db = get_db()
        current_user = get_jwt_identity()
        year = request.args.get('year', datetime.now().year, type=int)
        pivot_type = request.args.get('pivot', 'tier_product')
        
        # Get user's org_id
        user_result = db.execute_query(
            "SELECT organization_id FROM \"user\" WHERE id = %s",
            (current_user,)
        )
        org_id = user_result[0]['organization_id']
        
        if pivot_type == 'tier_product':
            # Revenue by Tier & Session Product
            query = """
                SELECT 
                    fc.tier,
                    fc.session_product,
                    COUNT(fc.id) as client_count,
                    SUM(fph.population_count) as total_population,
                    SUM(fph.population_count * COALESCE(
                        (SELECT pepm_rate FROM finance_rate_schedules frs
                         JOIN finance_contracts fcon ON frs.contract_id = fcon.id
                         WHERE fcon.client_id = fc.id
                         ORDER BY effective_date DESC LIMIT 1), 0
                    ) * 12) as annual_revenue
                FROM finance_clients fc
                LEFT JOIN finance_population_history fph ON fc.id = fph.client_id
                WHERE fc.org_id = %s
                GROUP BY fc.tier, fc.session_product
                ORDER BY fc.tier, fc.session_product
            """
            result = db.execute_query(query, (org_id,))
            
        elif pivot_type == 'industry':
            # Revenue by Industry
            query = """
                SELECT 
                    fc.industry,
                    COUNT(fc.id) as client_count,
                    SUM(fph.population_count) as total_population,
                    SUM(fph.population_count * COALESCE(
                        (SELECT pepm_rate FROM finance_rate_schedules frs
                         JOIN finance_contracts fcon ON frs.contract_id = fcon.id
                         WHERE fcon.client_id = fc.id
                         ORDER BY effective_date DESC LIMIT 1), 0
                    ) * 12) as annual_revenue
                FROM finance_clients fc
                LEFT JOIN finance_population_history fph ON fc.id = fph.client_id
                WHERE fc.org_id = %s
                GROUP BY fc.industry
                ORDER BY annual_revenue DESC
            """
            result = db.execute_query(query, (org_id,))
            
        elif pivot_type == 'top_clients':
            # Top clients by revenue
            query = """
                SELECT 
                    fc.billing_name,
                    fc.tier,
                    fc.industry,
                    fph.population_count,
                    COALESCE(
                        (SELECT pepm_rate FROM finance_rate_schedules frs
                         JOIN finance_contracts fcon ON frs.contract_id = fcon.id
                         WHERE fcon.client_id = fc.id
                         ORDER BY effective_date DESC LIMIT 1), 0
                    ) as pepm_rate,
                    fph.population_count * COALESCE(
                        (SELECT pepm_rate FROM finance_rate_schedules frs
                         JOIN finance_contracts fcon ON frs.contract_id = fcon.id
                         WHERE fcon.client_id = fc.id
                         ORDER BY effective_date DESC LIMIT 1), 0
                    ) * 12 as annual_revenue
                FROM finance_clients fc
                LEFT JOIN finance_population_history fph ON fc.id = fph.client_id
                WHERE fc.org_id = %s
                ORDER BY annual_revenue DESC
                LIMIT 50
            """
            result = db.execute_query(query, (org_id,))
            
        elif pivot_type == 'renewals':
            # Renewals by year
            query = """
                SELECT 
                    EXTRACT(YEAR FROM fcon.renewal_date) as renewal_year,
                    COUNT(fc.id) as client_count,
                    SUM(fph.population_count * COALESCE(
                        (SELECT pepm_rate FROM finance_rate_schedules frs
                         WHERE frs.contract_id = fcon.id
                         ORDER BY effective_date DESC LIMIT 1), 0
                    ) * 12) as renewal_value
                FROM finance_clients fc
                JOIN finance_contracts fcon ON fc.id = fcon.client_id
                LEFT JOIN finance_population_history fph ON fc.id = fph.client_id
                WHERE fc.org_id = %s AND fcon.renewal_date IS NOT NULL
                GROUP BY EXTRACT(YEAR FROM fcon.renewal_date)
                ORDER BY renewal_year
            """
            result = db.execute_query(query, (org_id,))
            
        elif pivot_type == 'nexus':
            # Revenue by Nexus State (for tax purposes)
            query = """
                SELECT 
                    fc.nexus_state,
                    COUNT(fc.id) as client_count,
                    SUM(fph.population_count * COALESCE(
                        (SELECT pepm_rate FROM finance_rate_schedules frs
                         JOIN finance_contracts fcon ON frs.contract_id = fcon.id
                         WHERE fcon.client_id = fc.id
                         ORDER BY effective_date DESC LIMIT 1), 0
                    ) * 12) as annual_revenue
                FROM finance_clients fc
                LEFT JOIN finance_population_history fph ON fc.id = fph.client_id
                WHERE fc.org_id = %s
                GROUP BY fc.nexus_state
                ORDER BY annual_revenue DESC
            """
            result = db.execute_query(query, (org_id,))
            
        else:
            return jsonify({'error': f'Unknown pivot type: {pivot_type}'}), 400
        
        return jsonify({
            'success': True,
            'year': year,
            'pivot_type': pivot_type,
            'data': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500



# =============================================================================
# HUBSPOT SYNC ENDPOINTS
# =============================================================================

@vital_finance_bp.route('/api/vital/finance/hubspot/sync', methods=['POST'])
@jwt_required()
def sync_hubspot_population():
    """
    Sync population data from HubSpot companies to Finance clients.
    Matches by company name and updates population from HubSpot's numberofemployees field.
    """
    try:
        import os
        import requests as http_requests
        from fuzzywuzzy import fuzz
        
        db = get_db()
        current_user = get_jwt_identity()
        
        # Get user's org_id
        user_result = db.execute_query(
            "SELECT organization_id FROM \"user\" WHERE id = %s",
            (current_user,)
        )
        org_id = user_result[0]['organization_id']
        
        # Get HubSpot token for VITAL
        hubspot_token = os.environ.get('VITAL_HUBSPOT_TOKEN')
        if not hubspot_token:
            return jsonify({'error': 'HubSpot token not configured'}), 500
        
        # Get all Finance clients
        clients = db.execute_query("""
            SELECT id, billing_name, hubspot_company_id, hubspot_company_name
            FROM finance_clients
            WHERE org_id = %s
        """, (org_id,))
        
        # Get HubSpot companies with employee count
        hubspot_url = "https://api.hubapi.com/crm/v3/objects/companies"
        headers = {"Authorization": f"Bearer {hubspot_token}"}
        params = {
            "limit": 100,
            "properties": "name,numberofemployees,domain"
        }
        
        all_companies = []
        after = None
        
        # Paginate through all companies
        while True:
            if after:
                params['after'] = after
            
            resp = http_requests.get(hubspot_url, headers=headers, params=params, timeout=30)
            if resp.status_code != 200:
                return jsonify({'error': f'HubSpot API error: {resp.text}'}), 500
            
            data = resp.json()
            all_companies.extend(data.get('results', []))
            
            paging = data.get('paging', {})
            if paging.get('next'):
                after = paging['next'].get('after')
            else:
                break
            
            # Safety limit
            if len(all_companies) > 5000:
                break
        
        # Match and sync
        synced = []
        not_matched = []
        
        for client in clients:
            client_name = client['billing_name'].lower().strip()
            best_match = None
            best_score = 0
            
            # If already linked to HubSpot, use that
            if client['hubspot_company_id']:
                for company in all_companies:
                    if str(company['id']) == str(client['hubspot_company_id']):
                        best_match = company
                        best_score = 100
                        break
            
            # Otherwise, fuzzy match by name
            if not best_match:
                for company in all_companies:
                    company_name = (company.get('properties', {}).get('name') or '').lower().strip()
                    if not company_name:
                        continue
                    
                    # Try exact match first
                    if client_name == company_name:
                        best_match = company
                        best_score = 100
                        break
                    
                    # Fuzzy match
                    score = fuzz.ratio(client_name, company_name)
                    if score > best_score and score >= 80:  # 80% threshold
                        best_match = company
                        best_score = score
            
            if best_match:
                props = best_match.get('properties', {})
                employees = props.get('numberofemployees')
                
                if employees and str(employees).isdigit():
                    employee_count = int(employees)
                    
                    # Update client with HubSpot link
                    db.execute_update("""
                        UPDATE finance_clients 
                        SET hubspot_company_id = %s, 
                            hubspot_company_name = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """, (best_match['id'], props.get('name'), client['id']))
                    
                    # Add population history record
                    db.execute_update("""
                        INSERT INTO finance_population_history 
                        (client_id, population_count, effective_date, source, created_at)
                        VALUES (%s, %s, NOW(), 'hubspot_sync', NOW())
                    """, (client['id'], employee_count))
                    
                    synced.append({
                        'client_id': client['id'],
                        'client_name': client['billing_name'],
                        'hubspot_name': props.get('name'),
                        'match_score': best_score,
                        'population': employee_count
                    })
                else:
                    not_matched.append({
                        'client_name': client['billing_name'],
                        'reason': 'HubSpot company found but no employee count'
                    })
            else:
                not_matched.append({
                    'client_name': client['billing_name'],
                    'reason': 'No matching HubSpot company found'
                })
        
        return jsonify({
            'success': True,
            'synced_count': len(synced),
            'not_matched_count': len(not_matched),
            'synced': synced,
            'not_matched': not_matched[:20]  # Limit to first 20 for response size
        })
        
    except ImportError:
        return jsonify({'error': 'fuzzywuzzy package not installed. Run: pip install fuzzywuzzy python-Levenshtein'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@vital_finance_bp.route('/api/vital/finance/hubspot/link', methods=['POST'])
@jwt_required()
def link_hubspot_company():
    """
    Manually link a Finance client to a HubSpot company.
    Body: { client_id, hubspot_company_id }
    """
    try:
        import os
        import requests as http_requests
        
        db = get_db()
        data = request.get_json()
        
        client_id = data.get('client_id')
        hubspot_company_id = data.get('hubspot_company_id')
        
        if not client_id or not hubspot_company_id:
            return jsonify({'error': 'client_id and hubspot_company_id required'}), 400
        
        # Get HubSpot company details
        hubspot_token = os.environ.get('VITAL_HUBSPOT_TOKEN')
        hubspot_url = f"https://api.hubapi.com/crm/v3/objects/companies/{hubspot_company_id}"
        headers = {"Authorization": f"Bearer {hubspot_token}"}
        params = {"properties": "name,numberofemployees,domain"}
        
        resp = http_requests.get(hubspot_url, headers=headers, params=params, timeout=30)
        if resp.status_code != 200:
            return jsonify({'error': 'HubSpot company not found'}), 404
        
        company = resp.json()
        props = company.get('properties', {})
        
        # Update client
        db.execute_update("""
            UPDATE finance_clients 
            SET hubspot_company_id = %s, 
                hubspot_company_name = %s,
                updated_at = NOW()
            WHERE id = %s
        """, (hubspot_company_id, props.get('name'), client_id))
        
        # If employee count available, update population
        employees = props.get('numberofemployees')
        if employees and str(employees).isdigit():
            db.execute_update("""
                INSERT INTO finance_population_history 
                (client_id, population_count, effective_date, source, created_at)
                VALUES (%s, %s, NOW(), 'hubspot_link', NOW())
            """, (client_id, int(employees)))
        
        return jsonify({
            'success': True,
            'client_id': client_id,
            'hubspot_company_id': hubspot_company_id,
            'hubspot_company_name': props.get('name'),
            'population_synced': employees if employees else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@vital_finance_bp.route('/api/vital/finance/hubspot/search', methods=['GET'])
@jwt_required()
def search_hubspot_companies():
    """
    Search HubSpot companies for linking to Finance clients.
    Query params: q (search term)
    """
    try:
        import os
        import requests as http_requests
        
        search_term = request.args.get('q', '')
        if not search_term or len(search_term) < 2:
            return jsonify({'error': 'Search term must be at least 2 characters'}), 400
        
        hubspot_token = os.environ.get('VITAL_HUBSPOT_TOKEN')
        if not hubspot_token:
            return jsonify({'error': 'HubSpot token not configured'}), 500
        
        # Search HubSpot companies
        hubspot_url = "https://api.hubapi.com/crm/v3/objects/companies/search"
        headers = {
            "Authorization": f"Bearer {hubspot_token}",
            "Content-Type": "application/json"
        }
        body = {
            "filterGroups": [{
                "filters": [{
                    "propertyName": "name",
                    "operator": "CONTAINS_TOKEN",
                    "value": search_term
                }]
            }],
            "properties": ["name", "numberofemployees", "domain", "industry"],
            "limit": 20
        }
        
        resp = http_requests.post(hubspot_url, headers=headers, json=body, timeout=30)
        if resp.status_code != 200:
            return jsonify({'error': f'HubSpot search error: {resp.text}'}), 500
        
        data = resp.json()
        companies = []
        
        for company in data.get('results', []):
            props = company.get('properties', {})
            companies.append({
                'id': company['id'],
                'name': props.get('name'),
                'employees': props.get('numberofemployees'),
                'domain': props.get('domain'),
                'industry': props.get('industry')
            })
        
        return jsonify({
            'success': True,
            'results': companies
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
