"""
QBR API Routes
Provides endpoints for Quarterly Business Review dashboard and PowerPoint export
"""

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.azure_sql_service import AzureSQLService
from src.services.postgres_service import get_postgres_db
from src.services.qbr_service import QBRService
import logging
from datetime import datetime
import uuid
import os

logger = logging.getLogger(__name__)

qbr_bp = Blueprint('qbr', __name__)


def get_qbr_service():
    """Get QBR service instance with both Azure SQL (Softbase) and PostgreSQL (sessions)"""
    sql_service = AzureSQLService()  # For Softbase data (customers, WOs, invoices)
    postgres_service = get_postgres_db()  # For QBR session storage
    return QBRService(sql_service, postgres_service)


@qbr_bp.route('/api/qbr/customers', methods=['GET'])
@jwt_required()
def get_qbr_customers():
    """
    Get list of customers for QBR dropdown
    Returns: List of customers with service history
    """
    try:
        qbr_service = get_qbr_service()
        customers = qbr_service.get_customers_for_qbr()

        return jsonify({
            'success': True,
            'customers': customers
        })

    except Exception as e:
        logger.error(f"Error getting QBR customers: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@qbr_bp.route('/api/qbr/<customer_name>/data', methods=['GET'])
@jwt_required()
def get_qbr_data(customer_name):
    """
    Get all QBR metrics for a customer and quarter
    customer_name: The customer name from BillToName (used as identifier)
    Query params: quarter (e.g., 'Q3-2025')
    Returns: Complete QBR dashboard data
    """
    try:
        quarter_param = request.args.get('quarter', 'Q4-2025')

        # Parse quarter
        parts = quarter_param.split('-')
        quarter = parts[0]  # 'Q3'
        year = int(parts[1])  # 2025

        qbr_service = get_qbr_service()

        # Get date range
        start_date, end_date = qbr_service.get_quarter_date_range(quarter, year)

        # customer_name IS the identifier (from BillToName)
        # No need to query Customer table - we use BillToName directly
        customer = {
            'customer_number': customer_name,
            'customer_name': customer_name
        }

        # Get all metrics (all queries use BillToName)
        fleet_overview = qbr_service.get_fleet_overview(customer_name, start_date, end_date)
        fleet_health = qbr_service.get_fleet_health(customer_name, end_date)
        service_performance = qbr_service.get_service_performance(customer_name, start_date, end_date)
        service_costs = qbr_service.get_service_costs(customer_name, start_date, end_date)
        parts_rentals = qbr_service.get_parts_rentals(customer_name, start_date, end_date)
        value_delivered = qbr_service.get_value_delivered(customer_name, start_date, end_date, service_costs, parts_rentals)
        recommendations = qbr_service.generate_recommendations(customer_name, fleet_health, service_costs)

        return jsonify({
            'success': True,
            'data': {
                'customer': customer,
                'quarter': f'{quarter} {year}',
                'date_range': {
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': end_date.strftime('%Y-%m-%d')
                },
                'fleet_overview': fleet_overview,
                'fleet_health': fleet_health,
                'service_performance': service_performance,
                'service_costs': service_costs,
                'parts_rentals': parts_rentals,
                'value_delivered': value_delivered,
                'recommendations': recommendations
            }
        })

    except Exception as e:
        logger.error(f"Error getting QBR data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@qbr_bp.route('/api/qbr/<customer_name>/save', methods=['POST'])
@jwt_required()
def save_qbr(customer_name):
    """
    Save QBR session with manual inputs
    customer_name: The customer name from BillToName (used as identifier)
    Body: {quarter, meeting_date, business_priorities, custom_recommendations, action_items, status}
    Returns: QBR ID
    """
    try:
        data = request.get_json()
        current_user = get_jwt_identity()

        qbr_service = get_qbr_service()

        # Generate QBR ID using customer name
        quarter = data.get('quarter', 'Q4 2025')

        # Parse quarter
        parts = quarter.split(' ')
        quarter_str = parts[0]  # 'Q3'
        fiscal_year = int(parts[1]) if len(parts) > 1 else 2025

        # Prepare QBR data for saving
        qbr_data = {
            'customer_number': customer_name,  # Using customer name as identifier
            'customer_name': customer_name,
            'quarter': quarter,
            'meeting_date': data.get('meeting_date'),
            'status': data.get('status', 'draft'),
            'notes': data.get('notes'),
            'business_priorities': data.get('business_priorities', []),
            'recommendations': data.get('custom_recommendations', []),
            'action_items': data.get('action_items', [])
        }

        # Save to PostgreSQL
        qbr_id = qbr_service.save_qbr_session(qbr_data, current_user)

        logger.info(f"QBR session created: {qbr_id} for {customer_name}")

        return jsonify({
            'success': True,
            'qbr_id': qbr_id,
            'message': 'QBR saved successfully',
            'data': {
                'customer_number': customer_name,
                'customer_name': customer_name,
                'quarter': quarter,
                'fiscal_year': fiscal_year,
                'created_by': current_user,
                'business_priorities': data.get('business_priorities', []),
                'recommendations': data.get('custom_recommendations', []),
                'action_items': data.get('action_items', [])
            }
        })

    except Exception as e:
        logger.error(f"Error saving QBR: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@qbr_bp.route('/api/qbr/<qbr_id>/export', methods=['POST'])
@jwt_required()
def export_qbr(qbr_id):
    """
    Export QBR to PowerPoint
    Returns: PPTX file download
    """
    try:
        # Get QBR data from request body (includes all dashboard data)
        data = request.get_json() or {}

        # Import generator (will be created in Phase 4)
        try:
            from src.services.pptx_generator import PPTXGenerator

            # Get template path
            template_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'templates',
                'BMH_QBR_Template.pptx'
            )

            if not os.path.exists(template_path):
                return jsonify({
                    'success': False,
                    'error': 'PowerPoint template not found'
                }), 404

            # Generate output path
            output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp')
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f'{qbr_id}.pptx')

            # Generate PowerPoint
            generator = PPTXGenerator(template_path)
            generator.generate_qbr_presentation(data, output_path)

            # Return file
            return send_file(
                output_path,
                mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
                as_attachment=True,
                download_name=f'{qbr_id}.pptx'
            )

        except ImportError:
            # Generator not yet implemented
            return jsonify({
                'success': True,
                'message': 'PowerPoint export will be implemented in Phase 4',
                'qbr_id': qbr_id
            })

    except Exception as e:
        logger.error(f"Error exporting QBR: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@qbr_bp.route('/api/qbr/sessions', methods=['GET'])
@jwt_required()
def get_qbr_sessions():
    """
    Get list of saved QBR sessions from PostgreSQL
    Query params: customer_number (optional), status (optional)
    """
    try:
        customer_number = request.args.get('customer_number')
        status = request.args.get('status')

        qbr_service = get_qbr_service()
        sessions = qbr_service.get_qbr_sessions_list(customer_number, status)

        return jsonify({
            'success': True,
            'sessions': sessions
        })

    except Exception as e:
        logger.error(f"Error getting QBR sessions: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@qbr_bp.route('/api/qbr/sessions/<qbr_id>', methods=['GET'])
@jwt_required()
def get_qbr_session(qbr_id):
    """
    Get a specific QBR session with all related data
    """
    try:
        qbr_service = get_qbr_service()
        session = qbr_service.get_qbr_session(qbr_id)

        if not session:
            return jsonify({
                'success': False,
                'error': 'QBR session not found'
            }), 404

        return jsonify({
            'success': True,
            'session': session
        })

    except Exception as e:
        logger.error(f"Error getting QBR session: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
