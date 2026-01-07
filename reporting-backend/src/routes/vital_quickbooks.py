"""
VITAL QuickBooks Integration Routes
Provides OAuth flow and API endpoints for QuickBooks financial data
"""
from flask import Blueprint, jsonify, request, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
import os
import json

logger = logging.getLogger(__name__)

vital_quickbooks_bp = Blueprint('vital_quickbooks', __name__)

# QuickBooks OAuth credentials - must be set in environment variables
QB_CLIENT_ID = os.environ.get('QB_CLIENT_ID')
QB_CLIENT_SECRET = os.environ.get('QB_CLIENT_SECRET')
QB_REDIRECT_URI = os.environ.get('QB_REDIRECT_URI', 
    'https://softbasereports-production.up.railway.app/api/vital/quickbooks/callback')

def get_quickbooks_service():
    """Get QuickBooks service instance"""
    from src.services.quickbooks_service import QuickBooksService
    return QuickBooksService(
        client_id=QB_CLIENT_ID,
        client_secret=QB_CLIENT_SECRET,
        redirect_uri=QB_REDIRECT_URI
    )

def is_vital_user():
    """Check if current user belongs to VITAL organization"""
    try:
        from src.models.user import User, Organization
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.organization_id:
            return False
        
        org = Organization.query.get(user.organization_id)
        if org and org.name:
            return 'vital' in org.name.lower()
        return False
    except Exception as e:
        logger.error(f"Error checking VITAL user: {str(e)}")
        return False

def get_vital_org():
    """Get VITAL organization"""
    try:
        from src.models.user import User, Organization
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user and user.organization_id:
            return Organization.query.get(user.organization_id)
        return None
    except Exception as e:
        logger.error(f"Error getting VITAL org: {str(e)}")
        return None

def get_qb_tokens():
    """Get stored QuickBooks tokens for VITAL"""
    try:
        org = get_vital_org()
        if not org:
            return None
        
        settings = {}
        if hasattr(org, 'settings') and org.settings:
            try:
                settings = json.loads(org.settings) if isinstance(org.settings, str) else org.settings
            except:
                settings = {}
        
        return settings.get('quickbooks', {})
    except Exception as e:
        logger.error(f"Error getting QB tokens: {str(e)}")
        return None

def save_qb_tokens(tokens, realm_id):
    """Save QuickBooks tokens for VITAL organization"""
    try:
        from src.models.user import db
        org = get_vital_org()
        if not org:
            return False
        
        settings = {}
        if hasattr(org, 'settings') and org.settings:
            try:
                settings = json.loads(org.settings) if isinstance(org.settings, str) else org.settings
            except:
                settings = {}
        
        settings['quickbooks'] = {
            'access_token': tokens.get('access_token'),
            'refresh_token': tokens.get('refresh_token'),
            'realm_id': realm_id,
            'expires_at': tokens.get('expires_at'),
            'connected': True
        }
        
        org.settings = json.dumps(settings)
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Error saving QB tokens: {str(e)}")
        return False


# ==================== OAuth Endpoints ====================

@vital_quickbooks_bp.route('/api/vital/quickbooks/connect', methods=['GET'])
@jwt_required()
def quickbooks_connect():
    """Initiate QuickBooks OAuth flow"""
    try:
        if not is_vital_user():
            return jsonify({'error': 'Access denied. VITAL users only.'}), 403
        
        if not QB_CLIENT_ID or not QB_CLIENT_SECRET:
            return jsonify({'error': 'QuickBooks not configured'}), 500
        
        qb_service = get_quickbooks_service()
        auth_url = qb_service.get_authorization_url(state='vital_qb_connect')
        
        return jsonify({
            'authorization_url': auth_url,
            'message': 'Redirect user to authorization_url to connect QuickBooks'
        })
    except Exception as e:
        logger.error(f"Error initiating QB connect: {str(e)}")
        return jsonify({'error': str(e)}), 500


@vital_quickbooks_bp.route('/api/vital/quickbooks/callback', methods=['GET'])
def quickbooks_callback():
    """Handle QuickBooks OAuth callback"""
    try:
        code = request.args.get('code')
        realm_id = request.args.get('realmId')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            logger.error(f"QuickBooks OAuth error: {error}")
            # Redirect to frontend with error
            return redirect(f"https://aiop.one/vital-quickbooks?error={error}")
        
        if not code or not realm_id:
            return redirect("https://aiop.one/vital-quickbooks?error=missing_params")
        
        qb_service = get_quickbooks_service()
        tokens = qb_service.exchange_code_for_tokens(code)
        
        # Store tokens - we need to get the org differently since no JWT in callback
        # For now, store in environment or use a temporary storage
        # In production, you'd use a state parameter to identify the user
        
        # Store tokens temporarily in environment (not ideal, but works for POC)
        os.environ['VITAL_QB_ACCESS_TOKEN'] = tokens.get('access_token', '')
        os.environ['VITAL_QB_REFRESH_TOKEN'] = tokens.get('refresh_token', '')
        os.environ['VITAL_QB_REALM_ID'] = realm_id
        
        logger.info(f"QuickBooks connected successfully for realm: {realm_id}")
        
        # Redirect to frontend success page
        return redirect(f"https://aiop.one/vital-quickbooks?connected=true&realm={realm_id}")
    
    except Exception as e:
        logger.error(f"Error in QB callback: {str(e)}")
        return redirect(f"https://aiop.one/vital-quickbooks?error={str(e)}")


@vital_quickbooks_bp.route('/api/vital/quickbooks/disconnect', methods=['POST'])
@jwt_required()
def quickbooks_disconnect():
    """Disconnect QuickBooks"""
    try:
        if not is_vital_user():
            return jsonify({'error': 'Access denied. VITAL users only.'}), 403
        
        # Clear stored tokens
        os.environ.pop('VITAL_QB_ACCESS_TOKEN', None)
        os.environ.pop('VITAL_QB_REFRESH_TOKEN', None)
        os.environ.pop('VITAL_QB_REALM_ID', None)
        
        return jsonify({
            'success': True,
            'message': 'QuickBooks disconnected successfully'
        })
    except Exception as e:
        logger.error(f"Error disconnecting QB: {str(e)}")
        return jsonify({'error': str(e)}), 500


@vital_quickbooks_bp.route('/api/vital/quickbooks/status', methods=['GET'])
@jwt_required()
def quickbooks_status():
    """Check QuickBooks connection status"""
    try:
        if not is_vital_user():
            return jsonify({'error': 'Access denied. VITAL users only.'}), 403
        
        access_token = os.environ.get('VITAL_QB_ACCESS_TOKEN')
        realm_id = os.environ.get('VITAL_QB_REALM_ID')
        
        if access_token and realm_id:
            return jsonify({
                'connected': True,
                'realm_id': realm_id,
                'message': 'QuickBooks is connected'
            })
        else:
            return jsonify({
                'connected': False,
                'message': 'QuickBooks is not connected'
            })
    except Exception as e:
        logger.error(f"Error checking QB status: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ==================== Financial Data Endpoints ====================

@vital_quickbooks_bp.route('/api/vital/quickbooks/dashboard', methods=['GET'])
@jwt_required()
def quickbooks_dashboard():
    """Get QuickBooks financial dashboard data"""
    try:
        if not is_vital_user():
            return jsonify({'error': 'Access denied. VITAL users only.'}), 403
        
        access_token = os.environ.get('VITAL_QB_ACCESS_TOKEN')
        realm_id = os.environ.get('VITAL_QB_REALM_ID')
        
        if not access_token or not realm_id:
            return jsonify({
                'error': 'QuickBooks not connected',
                'connected': False
            }), 400
        
        qb_service = get_quickbooks_service()
        dashboard_data = qb_service.get_financial_dashboard(access_token, realm_id)
        
        return jsonify({
            'success': True,
            'data': dashboard_data
        })
    except Exception as e:
        logger.error(f"Error getting QB dashboard: {str(e)}")
        return jsonify({'error': str(e)}), 500


@vital_quickbooks_bp.route('/api/vital/quickbooks/profit-loss', methods=['GET'])
@jwt_required()
def quickbooks_profit_loss():
    """Get Profit & Loss report"""
    try:
        if not is_vital_user():
            return jsonify({'error': 'Access denied. VITAL users only.'}), 403
        
        access_token = os.environ.get('VITAL_QB_ACCESS_TOKEN')
        realm_id = os.environ.get('VITAL_QB_REALM_ID')
        
        if not access_token or not realm_id:
            return jsonify({'error': 'QuickBooks not connected'}), 400
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        qb_service = get_quickbooks_service()
        pl_data = qb_service.get_profit_and_loss(access_token, realm_id, start_date, end_date)
        
        return jsonify({
            'success': True,
            'data': pl_data
        })
    except Exception as e:
        logger.error(f"Error getting P&L: {str(e)}")
        return jsonify({'error': str(e)}), 500


@vital_quickbooks_bp.route('/api/vital/quickbooks/balance-sheet', methods=['GET'])
@jwt_required()
def quickbooks_balance_sheet():
    """Get Balance Sheet report"""
    try:
        if not is_vital_user():
            return jsonify({'error': 'Access denied. VITAL users only.'}), 403
        
        access_token = os.environ.get('VITAL_QB_ACCESS_TOKEN')
        realm_id = os.environ.get('VITAL_QB_REALM_ID')
        
        if not access_token or not realm_id:
            return jsonify({'error': 'QuickBooks not connected'}), 400
        
        qb_service = get_quickbooks_service()
        bs_data = qb_service.get_balance_sheet(access_token, realm_id)
        
        return jsonify({
            'success': True,
            'data': bs_data
        })
    except Exception as e:
        logger.error(f"Error getting Balance Sheet: {str(e)}")
        return jsonify({'error': str(e)}), 500


@vital_quickbooks_bp.route('/api/vital/quickbooks/ar-aging', methods=['GET'])
@jwt_required()
def quickbooks_ar_aging():
    """Get Accounts Receivable Aging report"""
    try:
        if not is_vital_user():
            return jsonify({'error': 'Access denied. VITAL users only.'}), 403
        
        access_token = os.environ.get('VITAL_QB_ACCESS_TOKEN')
        realm_id = os.environ.get('VITAL_QB_REALM_ID')
        
        if not access_token or not realm_id:
            return jsonify({'error': 'QuickBooks not connected'}), 400
        
        qb_service = get_quickbooks_service()
        ar_data = qb_service.get_ar_aging_summary(access_token, realm_id)
        
        return jsonify({
            'success': True,
            'data': ar_data
        })
    except Exception as e:
        logger.error(f"Error getting AR Aging: {str(e)}")
        return jsonify({'error': str(e)}), 500


@vital_quickbooks_bp.route('/api/vital/quickbooks/company', methods=['GET'])
@jwt_required()
def quickbooks_company():
    """Get company information"""
    try:
        if not is_vital_user():
            return jsonify({'error': 'Access denied. VITAL users only.'}), 403
        
        access_token = os.environ.get('VITAL_QB_ACCESS_TOKEN')
        realm_id = os.environ.get('VITAL_QB_REALM_ID')
        
        if not access_token or not realm_id:
            return jsonify({'error': 'QuickBooks not connected'}), 400
        
        qb_service = get_quickbooks_service()
        company_data = qb_service.get_company_info(access_token, realm_id)
        
        return jsonify({
            'success': True,
            'data': company_data
        })
    except Exception as e:
        logger.error(f"Error getting company info: {str(e)}")
        return jsonify({'error': str(e)}), 500


@vital_quickbooks_bp.route('/api/vital/quickbooks/invoices', methods=['GET'])
@jwt_required()
def quickbooks_invoices():
    """Get recent invoices"""
    try:
        if not is_vital_user():
            return jsonify({'error': 'Access denied. VITAL users only.'}), 403
        
        access_token = os.environ.get('VITAL_QB_ACCESS_TOKEN')
        realm_id = os.environ.get('VITAL_QB_REALM_ID')
        
        if not access_token or not realm_id:
            return jsonify({'error': 'QuickBooks not connected'}), 400
        
        limit = request.args.get('limit', 50, type=int)
        
        qb_service = get_quickbooks_service()
        invoices = qb_service.get_invoices(access_token, realm_id, limit)
        
        return jsonify({
            'success': True,
            'data': invoices,
            'count': len(invoices)
        })
    except Exception as e:
        logger.error(f"Error getting invoices: {str(e)}")
        return jsonify({'error': str(e)}), 500
