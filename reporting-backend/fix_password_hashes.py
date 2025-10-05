#!/usr/bin/env python3
"""
Fix password hashes for elebow and jchristensen to eliminate temp-login need
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from src.models.user import db, User
from src.main import app
from werkzeug.security import generate_password_hash

def fix_password_hashes():
    """Update password hashes for problematic users"""
    with app.app_context():
        print("=== FIXING PASSWORD HASHES ===")
        
        # Users to fix and their new passwords
        users_to_fix = {
            'elebow@bmhmn.com': 'admin123',  # Using admin123 as the new password
            'jchristensen@bmhmn.com': 'admin123'  # Using admin123 as the new password
        }
        
        for email, new_password in users_to_fix.items():
            user = User.query.filter_by(email=email).first()
            if user:
                # Generate proper bcrypt hash
                new_hash = generate_password_hash(new_password)
                old_hash = user.password_hash
                
                print(f"\n👤 Updating {email}:")
                print(f"   Old hash: {old_hash[:50]}...")
                print(f"   New hash: {new_hash[:50]}...")
                
                # Update the password hash
                user.password_hash = new_hash
                
                # Test the new hash works
                if user.check_password(new_password):
                    print(f"   ✅ Hash validation works!")
                else:
                    print(f"   ❌ Hash validation failed!")
                    continue
                    
            else:
                print(f"❌ User {email} not found")
                continue
        
        # Commit all changes
        try:
            db.session.commit()
            print("\n✅ All password hashes updated successfully!")
            print("📋 New login credentials:")
            for email in users_to_fix.keys():
                print(f"   {email}: admin123")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error committing changes: {e}")

if __name__ == '__main__':
    fix_password_hashes()