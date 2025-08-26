"""Temporary password fix endpoint"""
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from werkzeug.security import generate_password_hash
from src.models.user import db, User

password_fix_bp = Blueprint('password_fix', __name__)

@password_fix_bp.route('/api/fix-passwords', methods=['POST'])
@cross_origin()
def fix_passwords():
    """Fix password hashes for users"""
    try:
        # Update specific users with proper bcrypt hash for 'abc123'
        users_to_fix = ['elebow@bmhmn.com', 'jchristensen@bmhmn.com']
        
        for username in users_to_fix:
            user = User.query.filter_by(username=username).first()
            if user:
                # Generate proper hash for abc123
                user.set_password('abc123')
                db.session.commit()
                print(f"Fixed password for {username}")
        
        return jsonify({'message': 'Passwords fixed successfully'}), 200
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@password_fix_bp.route('/api/test-login', methods=['GET'])
@cross_origin()
def test_login():
    """Test endpoint to check if server is working"""
    return jsonify({'message': 'Server is working'}), 200