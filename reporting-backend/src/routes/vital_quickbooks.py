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

# Store tokens in memory for POC (will persist across requests but not restarts)
# In production, use database or Redis
_qb_tokens = {
    'access_token': os.environ.get('VITAL_QB_ACCESS_TOKEN', ''),
    'refresh_token': os.environ.get('VITAL_QB_REFRESH_TOKEN', ''),
    'realm_id': os.environ.get('VITAL_QB_REALM_ID', '9130348352184736')  # Default to VITAL's realm
}

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
    """Get stored QuickBooks tokens"""
    global _qb_tokens
    return _qb_tokens

def save_qb_tokens(access_token, refresh_token, realm_id):
    """Save QuickBooks tokens"""
    global _qb_tokens
    _qb_tokens['access_token'] = access_token
    _qb_tokens['refresh_token'] = refresh_token
    _qb_tokens['realm_id'] = realm_id
    logger.info(f"Saved QB tokens for realm: {realm_id}")


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
            return redirect(f"https://aiop.one/vital-quickbooks?error={error}")
        
        if not code or not realm_id:
            return redirect("https://aiop.one/vital-quickbooks?error=missing_params")
        
        qb_service = get_quickbooks_service()
        tokens = qb_service.exchange_code_for_tokens(code)
        
        access_token = tokens.get('access_token', '')
        refresh_token = tokens.get('refresh_token', '')
        
        # Log tokens for debugging (first 50 chars only for security)
        logger.info(f"QB OAuth Success - Realm: {realm_id}")
        logger.info(f"QB Access Token (first 50 chars): {access_token[:50] if access_token else 'None'}...")
        logger.info(f"QB Refresh Token (first 50 chars): {refresh_token[:50] if refresh_token else 'None'}...")
        logger.info(f"QB Full tokens received - access: {len(access_token)} chars, refresh: {len(refresh_token)} chars")
        
        # IMPORTANT: Print full tokens to logs for manual env var setup
        # Remove this in production!
        print(f"=== VITAL QB TOKENS ===")
        print(f"VITAL_QB_ACCESS_TOKEN={access_token}")
        print(f"VITAL_QB_REFRESH_TOKEN={refresh_token}")
        print(f"VITAL_QB_REALM_ID={realm_id}")
        print(f"=======================")
        
        # Save tokens to memory (persists across requests)
        save_qb_tokens(access_token, refresh_token, realm_id)
        
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
        global _qb_tokens
        _qb_tokens = {'access_token': '', 'refresh_token': '', 'realm_id': ''}
        
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
        
        tokens = get_qb_tokens()
        access_token = tokens.get('access_token')
        realm_id = tokens.get('realm_id')
        
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
        
        tokens = get_qb_tokens()
        access_token = tokens.get('access_token')
        refresh_token = tokens.get('refresh_token')
        realm_id = tokens.get('realm_id')
        
        logger.info(f"QB Dashboard request - has access_token: {bool(access_token)}, has refresh_token: {bool(refresh_token)}, realm_id: {realm_id}")
        
        if not realm_id:
            return jsonify({
                'error': 'QuickBooks not connected',
                'connected': False
            }), 400
        
        qb_service = get_quickbooks_service()
        
        # If no access token but we have refresh token, try to refresh first
        if not access_token and refresh_token:
            logger.info("No access token, attempting to refresh using refresh token...")
            try:
                new_tokens = qb_service.refresh_access_token(refresh_token)
                access_token = new_tokens.get('access_token', '')
                new_refresh = new_tokens.get('refresh_token', refresh_token)
                save_qb_tokens(access_token, new_refresh, realm_id)
                logger.info(f"Token refresh successful, new access token length: {len(access_token)}")
                # Log for manual env var update
                print(f"=== REFRESHED QB TOKENS ===")
                print(f"VITAL_QB_ACCESS_TOKEN={access_token}")
                print(f"VITAL_QB_REFRESH_TOKEN={new_refresh}")
                print(f"===========================")
            except Exception as refresh_error:
                logger.error(f"Initial token refresh failed: {str(refresh_error)}")
                return jsonify({
                    'error': 'QuickBooks token expired. Please reconnect.',
                    'connected': False,
                    'needs_reconnect': True
                }), 401
        
        if not access_token:
            return jsonify({
                'error': 'QuickBooks not connected',
                'connected': False
            }), 400
        
        # Try to get dashboard data
        try:
            dashboard_data = qb_service.get_financial_dashboard(access_token, realm_id)
            return jsonify({
                'success': True,
                'data': dashboard_data
            })
        except Exception as api_error:
            error_str = str(api_error)
            logger.error(f"API error: {error_str}")
            
            # Check if it's an auth error (401)
            if '401' in error_str or 'Unauthorized' in error_str:
                if refresh_token:
                    logger.info("Got 401, attempting token refresh...")
                    try:
                        new_tokens = qb_service.refresh_access_token(refresh_token)
                        new_access = new_tokens.get('access_token', '')
                        new_refresh = new_tokens.get('refresh_token', refresh_token)
                        save_qb_tokens(new_access, new_refresh, realm_id)
                        logger.info(f"Token refresh successful after 401")
                        # Log for manual env var update
                        print(f"=== REFRESHED QB TOKENS ===")
                        print(f"VITAL_QB_ACCESS_TOKEN={new_access}")
                        print(f"VITAL_QB_REFRESH_TOKEN={new_refresh}")
                        print(f"===========================")
                        # Retry with new token
                        dashboard_data = qb_service.get_financial_dashboard(new_access, realm_id)
                        return jsonify({
                            'success': True,
                            'data': dashboard_data
                        })
                    except Exception as refresh_error:
                        logger.error(f"Token refresh failed after 401: {str(refresh_error)}")
                        return jsonify({
                            'error': 'QuickBooks token expired and refresh failed. Please reconnect.',
                            'connected': False,
                            'needs_reconnect': True
                        }), 401
                else:
                    return jsonify({
                        'error': 'QuickBooks token expired. Please reconnect.',
                        'connected': False,
                        'needs_reconnect': True
                    }), 401
            else:
                raise api_error
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
        
        tokens = get_qb_tokens()
        access_token = tokens.get('access_token')
        realm_id = tokens.get('realm_id')
        
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
        
        tokens = get_qb_tokens()
        access_token = tokens.get('access_token')
        realm_id = tokens.get('realm_id')
        
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
        
        tokens = get_qb_tokens()
        access_token = tokens.get('access_token')
        realm_id = tokens.get('realm_id')
        
        if not access_token or not realm_id:
            return jsonify({'error': 'QuickBooks not connected'}), 400
        
        qb_service = get_quickbooks_service()
        ar_data = qb_service.get_ar_aging(access_token, realm_id)
        
        return jsonify({
            'success': True,
            'data': ar_data
        })
    except Exception as e:
        logger.error(f"Error getting AR Aging: {str(e)}")
        return jsonify({'error': str(e)}), 500
