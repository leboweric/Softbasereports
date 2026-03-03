"""
Error Logs API - Captures and exposes application errors via API
Provides /api/admin/logs endpoint for querying recent errors without Railway dashboard access.

Uses an in-memory ring buffer (deque) to store recent errors. This means:
- No database migration needed
- Errors are lost on app restart (acceptable for debugging)
- Configurable max entries (default 500)
- Zero performance impact on normal requests

For the automated support bot, this enables error investigation during ticket processing.
"""
import os
import sys
import traceback
import logging
from datetime import datetime, timedelta
from collections import deque
from threading import Lock
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps

error_logs_bp = Blueprint('error_logs', __name__)

# ==================== IN-MEMORY ERROR STORE ====================

MAX_LOG_ENTRIES = int(os.environ.get('MAX_ERROR_LOG_ENTRIES', '500'))
_error_log = deque(maxlen=MAX_LOG_ENTRIES)
_log_lock = Lock()
_log_id_counter = 0


def _next_id():
    global _log_id_counter
    _log_id_counter += 1
    return _log_id_counter


def capture_error(error, context=None):
    """
    Capture an error into the in-memory log.
    
    Args:
        error: The exception object or error message string
        context: Optional dict with additional context (endpoint, method, user_id, org_id, etc.)
    """
    with _log_lock:
        entry = {
            'id': _next_id(),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'error_type': type(error).__name__ if isinstance(error, Exception) else 'Error',
            'message': str(error),
            'traceback': traceback.format_exc() if isinstance(error, Exception) and sys.exc_info()[2] else None,
            'endpoint': None,
            'method': None,
            'url': None,
            'user_id': None,
            'org_id': None,
            'status_code': None,
            'request_data': None,
        }
        
        # Merge context
        if context:
            entry.update({k: v for k, v in context.items() if k in entry})
        
        # Try to capture request context if available
        try:
            if request:
                entry['endpoint'] = entry.get('endpoint') or request.endpoint
                entry['method'] = entry.get('method') or request.method
                entry['url'] = entry.get('url') or request.url
                # Capture query params but not sensitive data
                if request.args:
                    entry['request_data'] = dict(request.args)
        except RuntimeError:
            pass  # Outside request context
        
        _error_log.append(entry)
        return entry


def capture_request_error(error, status_code=500):
    """
    Capture an error with full request context. Call this from error handlers.
    """
    context = {
        'status_code': status_code,
    }
    
    try:
        from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
            if user_id:
                context['user_id'] = int(user_id)
                from flask import g
                if hasattr(g, 'tenant_id'):
                    context['org_id'] = g.tenant_id
        except Exception:
            pass
    except ImportError:
        pass
    
    return capture_error(error, context)


def get_recent_errors(limit=50, since_hours=None, error_type=None, endpoint_filter=None, status_code=None):
    """
    Query recent errors from the in-memory log.
    
    Args:
        limit: Max number of entries to return (default 50)
        since_hours: Only return errors from the last N hours
        error_type: Filter by error type (e.g., 'ValueError', 'KeyError')
        endpoint_filter: Filter by endpoint substring
        status_code: Filter by HTTP status code
    
    Returns:
        List of error entries, newest first
    """
    with _log_lock:
        entries = list(_error_log)
    
    # Newest first
    entries.reverse()
    
    # Apply filters
    if since_hours:
        cutoff = datetime.utcnow() - timedelta(hours=since_hours)
        cutoff_str = cutoff.isoformat() + 'Z'
        entries = [e for e in entries if e['timestamp'] >= cutoff_str]
    
    if error_type:
        entries = [e for e in entries if error_type.lower() in (e.get('error_type') or '').lower()]
    
    if endpoint_filter:
        entries = [e for e in entries if endpoint_filter.lower() in (e.get('endpoint') or e.get('url') or '').lower()]
    
    if status_code:
        entries = [e for e in entries if e.get('status_code') == status_code]
    
    return entries[:limit]


def get_error_summary():
    """
    Get a summary of error counts by type and endpoint.
    """
    with _log_lock:
        entries = list(_error_log)
    
    if not entries:
        return {
            'total_errors': 0,
            'by_type': {},
            'by_endpoint': {},
            'by_status_code': {},
            'oldest_entry': None,
            'newest_entry': None,
        }
    
    by_type = {}
    by_endpoint = {}
    by_status = {}
    
    for e in entries:
        # Count by type
        etype = e.get('error_type', 'Unknown')
        by_type[etype] = by_type.get(etype, 0) + 1
        
        # Count by endpoint
        ep = e.get('endpoint') or e.get('url') or 'Unknown'
        by_endpoint[ep] = by_endpoint.get(ep, 0) + 1
        
        # Count by status code
        sc = e.get('status_code')
        if sc:
            by_status[str(sc)] = by_status.get(str(sc), 0) + 1
    
    return {
        'total_errors': len(entries),
        'buffer_capacity': MAX_LOG_ENTRIES,
        'by_type': dict(sorted(by_type.items(), key=lambda x: x[1], reverse=True)),
        'by_endpoint': dict(sorted(by_endpoint.items(), key=lambda x: x[1], reverse=True)[:20]),
        'by_status_code': by_status,
        'oldest_entry': entries[0]['timestamp'] if entries else None,
        'newest_entry': entries[-1]['timestamp'] if entries else None,
    }


# ==================== FLASK ERROR HANDLER INTEGRATION ====================

def register_error_handlers(app):
    """
    Register global error handlers on the Flask app to automatically capture errors.
    Call this in main.py after creating the app.
    """
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Catch all unhandled exceptions"""
        # Don't capture 404s as errors (too noisy)
        status_code = getattr(e, 'code', 500)
        if status_code == 404:
            return jsonify({'error': 'Not found'}), 404
        
        capture_request_error(e, status_code=status_code)
        
        # Log to stdout as well (for Railway logs)
        print(f"[ErrorLog] {type(e).__name__}: {str(e)}", file=sys.stderr)
        
        # Return appropriate response
        if status_code >= 500:
            return jsonify({
                'error': 'Internal server error',
                'error_type': type(e).__name__,
                'message': str(e)
            }), 500
        else:
            return jsonify({
                'error': str(e),
                'error_type': type(e).__name__
            }), status_code
    
    @app.errorhandler(500)
    def handle_500(e):
        capture_request_error(e, status_code=500)
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500
    
    @app.errorhandler(422)
    def handle_422(e):
        capture_request_error(e, status_code=422)
        return jsonify({'error': 'Unprocessable entity', 'message': str(e)}), 422


# ==================== LOGGING HANDLER (captures Python logging errors) ====================

class ErrorLogHandler(logging.Handler):
    """
    Python logging handler that captures ERROR and CRITICAL level logs
    into the in-memory error store.
    """
    
    def emit(self, record):
        if record.levelno >= logging.ERROR:
            context = {
                'endpoint': getattr(record, 'endpoint', None),
                'error_type': record.levelname,
            }
            if record.exc_info and record.exc_info[1]:
                capture_error(record.exc_info[1], context)
            else:
                capture_error(Exception(record.getMessage()), context)


def attach_logging_handler():
    """Attach the ErrorLogHandler to the root logger."""
    handler = ErrorLogHandler()
    handler.setLevel(logging.ERROR)
    logging.getLogger().addHandler(handler)


# ==================== API ROUTES ====================

def require_admin_or_bot():
    """Decorator to require admin permissions or bot service account"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def wrapper(*args, **kwargs):
            current_user_id = get_jwt_identity()
            from src.models.user import User
            user = User.query.get(int(current_user_id))
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Allow admin users
            is_admin = False
            try:
                from src.services.permission_service import PermissionService
                is_admin = PermissionService.user_has_permission(user, 'user_management', 'view')
            except Exception:
                is_admin = getattr(user, 'is_admin', False)
            
            # Allow the support bot service account
            is_bot = getattr(user, 'username', '') == 'aiop-support-bot'
            
            if not is_admin and not is_bot:
                return jsonify({'error': 'Admin or bot access required'}), 403
            
            return f(*args, **kwargs)
        return wrapper
    return decorator


@error_logs_bp.route('/api/admin/logs', methods=['GET'])
@require_admin_or_bot()
def get_logs():
    """
    Get recent application error logs.
    
    Query params:
        limit (int): Max entries to return (default 50, max 200)
        since_hours (float): Only errors from last N hours
        error_type (str): Filter by error type (e.g., 'ValueError')
        endpoint (str): Filter by endpoint substring
        status_code (int): Filter by HTTP status code
    
    Returns:
        JSON with errors array and metadata
    """
    limit = min(int(request.args.get('limit', 50)), 200)
    since_hours = request.args.get('since_hours', type=float)
    error_type = request.args.get('error_type')
    endpoint_filter = request.args.get('endpoint')
    status_code = request.args.get('status_code', type=int)
    
    errors = get_recent_errors(
        limit=limit,
        since_hours=since_hours,
        error_type=error_type,
        endpoint_filter=endpoint_filter,
        status_code=status_code
    )
    
    return jsonify({
        'errors': errors,
        'count': len(errors),
        'filters_applied': {
            'limit': limit,
            'since_hours': since_hours,
            'error_type': error_type,
            'endpoint': endpoint_filter,
            'status_code': status_code,
        }
    })


@error_logs_bp.route('/api/admin/logs/summary', methods=['GET'])
@require_admin_or_bot()
def get_logs_summary():
    """
    Get a summary of error counts grouped by type, endpoint, and status code.
    Useful for quick health checks.
    """
    summary = get_error_summary()
    return jsonify(summary)


@error_logs_bp.route('/api/admin/logs/clear', methods=['POST'])
@require_admin_or_bot()
def clear_logs():
    """
    Clear all error logs from the in-memory buffer.
    Useful after deploying a fix to start fresh.
    """
    with _log_lock:
        _error_log.clear()
    
    return jsonify({
        'success': True,
        'message': 'Error logs cleared'
    })


@error_logs_bp.route('/api/admin/logs/health', methods=['GET'])
@require_admin_or_bot()
def get_health():
    """
    Quick health check endpoint that returns error rate info.
    No detailed error data — just counts for monitoring.
    """
    with _log_lock:
        total = len(_error_log)
        
        # Count errors in last hour
        one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat() + 'Z'
        recent = sum(1 for e in _error_log if e['timestamp'] >= one_hour_ago)
        
        # Count errors in last 24 hours
        one_day_ago = (datetime.utcnow() - timedelta(hours=24)).isoformat() + 'Z'
        last_24h = sum(1 for e in _error_log if e['timestamp'] >= one_day_ago)
    
    return jsonify({
        'status': 'healthy' if recent < 10 else 'degraded' if recent < 50 else 'critical',
        'total_buffered': total,
        'buffer_capacity': MAX_LOG_ENTRIES,
        'errors_last_hour': recent,
        'errors_last_24h': last_24h,
        'server_time': datetime.utcnow().isoformat() + 'Z',
    })
