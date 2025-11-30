"""
Data Sync Routes

Handles scheduled and manual data synchronization from ERP systems.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date

from src.models.database import db
from src.models.core import Dealer, User, ERPConnection, DataSyncJob
from src.models.financial import (
    ReportingPeriod, DepartmentFinancial,
    ExpenseAllocation, OperationalMetric
)
from src.adapters.adapter_factory import AdapterFactory

data_sync_bp = Blueprint('data_sync', __name__)


def get_current_user():
    """Helper to get current user from JWT."""
    user_id = get_jwt_identity()
    return User.query.get(user_id)


@data_sync_bp.route('/jobs', methods=['GET'])
@jwt_required()
def get_sync_jobs():
    """Get sync job history."""
    user = get_current_user()
    dealer_id = request.args.get('dealer_id', type=int)

    if user.user_type in ('currie_admin', 'currie_analyst'):
        if dealer_id:
            jobs = DataSyncJob.query.filter_by(dealer_id=dealer_id)
        else:
            jobs = DataSyncJob.query
    else:
        jobs = DataSyncJob.query.filter_by(dealer_id=user.dealer_id)

    jobs = jobs.order_by(DataSyncJob.created_at.desc()).limit(50).all()

    return jsonify({
        'jobs': [j.to_dict() for j in jobs]
    }), 200


@data_sync_bp.route('/jobs/<int:job_id>', methods=['GET'])
@jwt_required()
def get_sync_job(job_id):
    """Get details of a specific sync job."""
    job = DataSyncJob.query.get_or_404(job_id)

    user = get_current_user()
    if user.user_type not in ('currie_admin', 'currie_analyst'):
        if user.dealer_id != job.dealer_id:
            return jsonify({'error': 'Access denied'}), 403

    return jsonify({'job': job.to_dict()}), 200


@data_sync_bp.route('/trigger', methods=['POST'])
@jwt_required()
def trigger_sync():
    """
    Trigger a manual data sync for a dealer.
    """
    user = get_current_user()
    data = request.get_json()

    # Determine dealer
    dealer_id = data.get('dealer_id')
    if user.user_type not in ('currie_admin',):
        dealer_id = user.dealer_id

    if not dealer_id:
        return jsonify({'error': 'dealer_id required'}), 400

    dealer = Dealer.query.get_or_404(dealer_id)

    # Get ERP connection
    connection = ERPConnection.query.filter_by(
        dealer_id=dealer_id,
        is_active=True
    ).first()

    if not connection:
        return jsonify({'error': 'No active ERP connection configured'}), 404

    # Get date range
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    if not start_date or not end_date:
        return jsonify({'error': 'start_date and end_date required'}), 400

    # Create sync job record
    job = DataSyncJob(
        dealer_id=dealer_id,
        erp_connection_id=connection.id,
        job_type=data.get('job_type', 'manual'),
        status='running',
        period_start=date.fromisoformat(start_date),
        period_end=date.fromisoformat(end_date),
        started_at=datetime.utcnow()
    )
    db.session.add(job)
    db.session.commit()

    try:
        # Create adapter
        adapter = AdapterFactory.get_adapter(
            connection.erp_type,
            {
                'server': connection.server,
                'database': connection.database,
                'username': connection.username,
                'password': connection.password_encrypted,  # TODO: Decrypt
                'schema': 'ben002'  # TODO: Make configurable
            }
        )

        # Pull data
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)

        financials = adapter.get_department_financials(start, end)
        expenses = adapter.get_expense_allocations(start, end)
        metrics = adapter.get_operational_metrics(start, end)

        adapter.close()

        # Create or update reporting period
        period = ReportingPeriod.query.filter_by(
            dealer_id=dealer_id,
            period_start=start,
            period_end=end
        ).first()

        if not period:
            period = ReportingPeriod(
                dealer_id=dealer_id,
                period_start=start,
                period_end=end,
                data_source='auto_sync',
                sync_job_id=job.id
            )
            db.session.add(period)
            db.session.flush()

        # Store financial data
        records_created = 0

        for fin_data in financials:
            # Check if record exists
            existing = DepartmentFinancial.query.filter_by(
                reporting_period_id=period.id,
                department=fin_data['department']
            ).first()

            if existing:
                # Update existing
                existing.gross_sales = fin_data['gross_sales']
                existing.discounts = fin_data.get('discounts', 0)
                existing.cost_of_goods_sold = fin_data['cost_of_goods_sold']
                existing.units_sold = fin_data.get('units_sold', 0)
                existing.calculate_derived_fields()
            else:
                # Create new
                fin = DepartmentFinancial(
                    reporting_period_id=period.id,
                    dealer_id=dealer_id,
                    department=fin_data['department'],
                    gross_sales=fin_data['gross_sales'],
                    discounts=fin_data.get('discounts', 0),
                    cost_of_goods_sold=fin_data['cost_of_goods_sold'],
                    units_sold=fin_data.get('units_sold', 0)
                )
                fin.calculate_derived_fields()
                db.session.add(fin)
                records_created += 1

        for exp_data in expenses:
            exp = ExpenseAllocation(
                reporting_period_id=period.id,
                dealer_id=dealer_id,
                expense_category=exp_data['expense_category'],
                department=exp_data.get('department'),
                amount=exp_data['amount'],
                allocation_method=exp_data.get('allocation_method')
            )
            db.session.add(exp)
            records_created += 1

        for metric_data in metrics:
            metric = OperationalMetric(
                reporting_period_id=period.id,
                dealer_id=dealer_id,
                metric_name=metric_data['metric_name'],
                metric_category=metric_data.get('metric_category'),
                metric_value=metric_data['metric_value'],
                metric_unit=metric_data.get('metric_unit')
            )
            db.session.add(metric)
            records_created += 1

        # Update job status
        job.status = 'completed'
        job.completed_at = datetime.utcnow()
        job.records_processed = len(financials) + len(expenses) + len(metrics)
        job.records_created = records_created

        # Update connection last sync
        connection.last_sync = datetime.utcnow()
        connection.last_sync_status = 'success'

        db.session.commit()

        return jsonify({
            'message': 'Sync completed successfully',
            'job': job.to_dict()
        }), 200

    except Exception as e:
        job.status = 'failed'
        job.completed_at = datetime.utcnow()
        job.errors = [str(e)]

        connection.last_sync = datetime.utcnow()
        connection.last_sync_status = 'failed'
        connection.last_sync_message = str(e)

        db.session.commit()

        return jsonify({
            'error': f'Sync failed: {str(e)}',
            'job': job.to_dict()
        }), 500
