"""
Reports Routes

Handles financial report generation and data retrieval.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date

from src.models.database import db
from src.models.core import Dealer, User, ERPConnection
from src.models.financial import (
    ReportingPeriod, DepartmentFinancial,
    ExpenseAllocation, OperationalMetric
)
from src.adapters.adapter_factory import AdapterFactory

reports_bp = Blueprint('reports', __name__)


def get_current_user():
    """Helper to get current user from JWT."""
    user_id = get_jwt_identity()
    return User.query.get(user_id)


@reports_bp.route('/periods', methods=['GET'])
@jwt_required()
def get_reporting_periods():
    """Get reporting periods for current user's dealer or all dealers for Currie."""
    user = get_current_user()

    if user.user_type in ('currie_admin', 'currie_analyst'):
        dealer_id = request.args.get('dealer_id', type=int)
        if dealer_id:
            periods = ReportingPeriod.query.filter_by(dealer_id=dealer_id).order_by(
                ReportingPeriod.period_end.desc()
            ).all()
        else:
            periods = ReportingPeriod.query.order_by(
                ReportingPeriod.period_end.desc()
            ).limit(100).all()
    else:
        periods = ReportingPeriod.query.filter_by(dealer_id=user.dealer_id).order_by(
            ReportingPeriod.period_end.desc()
        ).all()

    return jsonify({
        'periods': [p.to_dict() for p in periods]
    }), 200


@reports_bp.route('/periods/<int:period_id>/financials', methods=['GET'])
@jwt_required()
def get_period_financials(period_id):
    """Get financial data for a reporting period."""
    user = get_current_user()
    period = ReportingPeriod.query.get_or_404(period_id)

    # Check access
    if user.user_type not in ('currie_admin', 'currie_analyst'):
        if user.dealer_id != period.dealer_id:
            return jsonify({'error': 'Access denied'}), 403

    financials = DepartmentFinancial.query.filter_by(
        reporting_period_id=period_id
    ).all()

    expenses = ExpenseAllocation.query.filter_by(
        reporting_period_id=period_id
    ).all()

    metrics = OperationalMetric.query.filter_by(
        reporting_period_id=period_id
    ).all()

    return jsonify({
        'period': period.to_dict(),
        'department_financials': [f.to_dict() for f in financials],
        'expense_allocations': [e.to_dict() for e in expenses],
        'operational_metrics': [m.to_dict() for m in metrics]
    }), 200


@reports_bp.route('/currie-model', methods=['GET'])
@jwt_required()
def get_currie_model_report():
    """
    Generate Currie Financial Model report data.
    Similar to existing currie report but using normalized data.
    """
    user = get_current_user()
    dealer_id = request.args.get('dealer_id', type=int)

    # Determine dealer
    if user.user_type in ('currie_admin', 'currie_analyst'):
        if not dealer_id:
            return jsonify({'error': 'dealer_id required for Currie users'}), 400
    else:
        dealer_id = user.dealer_id

    dealer = Dealer.query.get_or_404(dealer_id)

    # Get date range
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        return jsonify({'error': 'start_date and end_date are required'}), 400

    # Get reporting periods in range
    periods = ReportingPeriod.query.filter(
        ReportingPeriod.dealer_id == dealer_id,
        ReportingPeriod.period_start >= start_date,
        ReportingPeriod.period_end <= end_date
    ).all()

    # Aggregate financial data
    financials_by_dept = {}
    for period in periods:
        for fin in period.department_financials:
            dept = fin.department
            if dept not in financials_by_dept:
                financials_by_dept[dept] = {
                    'gross_sales': 0, 'discounts': 0, 'net_sales': 0,
                    'cost_of_goods_sold': 0, 'gross_profit': 0, 'units_sold': 0
                }

            financials_by_dept[dept]['gross_sales'] += float(fin.gross_sales or 0)
            financials_by_dept[dept]['discounts'] += float(fin.discounts or 0)
            financials_by_dept[dept]['net_sales'] += float(fin.net_sales or 0)
            financials_by_dept[dept]['cost_of_goods_sold'] += float(fin.cost_of_goods_sold or 0)
            financials_by_dept[dept]['gross_profit'] += float(fin.gross_profit or 0)
            financials_by_dept[dept]['units_sold'] += fin.units_sold or 0

    # Calculate totals
    total_sales = sum(d['net_sales'] for d in financials_by_dept.values())
    total_cogs = sum(d['cost_of_goods_sold'] for d in financials_by_dept.values())
    total_gp = sum(d['gross_profit'] for d in financials_by_dept.values())

    return jsonify({
        'dealer': dealer.to_dict(),
        'period': {
            'start_date': start_date,
            'end_date': end_date
        },
        'department_financials': financials_by_dept,
        'totals': {
            'net_sales': total_sales,
            'cost_of_goods_sold': total_cogs,
            'gross_profit': total_gp,
            'gross_profit_margin': total_gp / total_sales if total_sales else 0
        }
    }), 200


@reports_bp.route('/benchmark', methods=['GET'])
@jwt_required()
def get_benchmark_data():
    """
    Get industry benchmark data comparing dealer to aggregates.
    Only available for Professional and Enterprise subscription tiers.
    """
    user = get_current_user()
    dealer_id = request.args.get('dealer_id', type=int) or user.dealer_id

    if not dealer_id:
        return jsonify({'error': 'dealer_id required'}), 400

    dealer = Dealer.query.get_or_404(dealer_id)

    # Check subscription tier
    if dealer.subscription_tier == 'basic':
        return jsonify({
            'error': 'Benchmarking requires Professional or Enterprise subscription'
        }), 403

    # Get aggregate data across all dealers (anonymized)
    # This would compare the dealer's metrics to industry averages

    # TODO: Implement actual benchmarking logic
    return jsonify({
        'message': 'Benchmarking feature coming soon',
        'dealer': dealer.to_dict()
    }), 200


@reports_bp.route('/live-pull', methods=['POST'])
@jwt_required()
def live_data_pull():
    """
    Pull fresh data directly from dealer's ERP system.
    Useful for on-demand data refresh.
    """
    user = get_current_user()
    data = request.get_json()

    dealer_id = data.get('dealer_id') or user.dealer_id
    if not dealer_id:
        return jsonify({'error': 'dealer_id required'}), 400

    # Get dealer's ERP connection
    connection = ERPConnection.query.filter_by(
        dealer_id=dealer_id,
        is_active=True
    ).first()

    if not connection:
        return jsonify({'error': 'No active ERP connection found'}), 404

    start_date = data.get('start_date')
    end_date = data.get('end_date')

    if not start_date or not end_date:
        return jsonify({'error': 'start_date and end_date required'}), 400

    try:
        # Create adapter and pull data
        adapter = AdapterFactory.get_adapter(
            connection.erp_type,
            {
                'server': connection.server,
                'database': connection.database,
                'username': connection.username,
                'password': connection.password_encrypted  # TODO: Decrypt
            }
        )

        # Get full report data
        report = adapter.get_full_report(
            date.fromisoformat(start_date),
            date.fromisoformat(end_date)
        )

        adapter.close()

        return jsonify({
            'message': 'Data pulled successfully',
            'data': report
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to pull data: {str(e)}'}), 500
