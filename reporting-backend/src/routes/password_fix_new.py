"""One-time password hash fix endpoint"""
from flask import Blueprint, jsonify
from flask_cors import cross_origin
from src.models.user import db, User
from werkzeug.security import generate_password_hash

password_fix_bp = Blueprint('password_fix', __name__)

@password_fix_bp.route('/api/admin/fix-password-hashes', methods=['POST'])
@cross_origin()
def fix_password_hashes():
    """One-time fix for broken password hashes"""
    try:
        results = []
        
        # Users to fix and their new passwords
        users_to_fix = {
            'elebow@bmhmn.com': 'admin123',
            'jchristensen@bmhmn.com': 'admin123'
        }
        
        for email, new_password in users_to_fix.items():
            user = User.query.filter_by(email=email).first()
            if user:
                # Generate proper bcrypt hash
                new_hash = generate_password_hash(new_password)
                old_hash_preview = user.password_hash[:50] + '...' if user.password_hash else 'None'
                
                # Update the password hash
                user.password_hash = new_hash
                
                # Test the new hash works
                if user.check_password(new_password):
                    results.append({
                        'email': email,
                        'status': 'success',
                        'old_hash_preview': old_hash_preview,
                        'new_hash_preview': new_hash[:50] + '...',
                        'validation': 'passed'
                    })
                else:
                    results.append({
                        'email': email,
                        'status': 'failed',
                        'error': 'Hash validation failed'
                    })
            else:
                results.append({
                    'email': email,
                    'status': 'not_found'
                })
        
        # Commit all changes
        db.session.commit()
        
        return jsonify({
            'message': 'Password hashes updated',
            'results': results,
            'new_credentials': {email: 'admin123' for email in users_to_fix.keys()}
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': f'Failed to update password hashes: {str(e)}'
        }), 500