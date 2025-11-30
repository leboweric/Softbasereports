"""
Database initialization script for Currie Cloud Platform.
Run this to create all database tables.
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from src.models.database import db
from src.models.core import Dealer, User, Role, ERPConnection, DataSyncJob
from src.models.financial import ReportingPeriod, DepartmentFinancial, ExpenseAllocation, OperationalMetric

def init_database():
    """Initialize database tables and seed initial data."""
    app = create_app()

    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Tables created successfully!")

        # Check if we need to seed initial data
        if not Role.query.first():
            print("Seeding initial roles...")
            roles = [
                Role(name='super_admin', description='Full platform access'),
                Role(name='currie_admin', description='Currie staff administrator'),
                Role(name='currie_analyst', description='Currie analyst - view all dealers'),
                Role(name='dealer_admin', description='Dealer administrator'),
                Role(name='dealer_user', description='Dealer standard user'),
            ]
            for role in roles:
                db.session.add(role)
            db.session.commit()
            print("Roles seeded!")

        # Create default super admin if none exists
        if not User.query.filter_by(email='admin@currie.com').first():
            print("Creating default admin user...")
            from werkzeug.security import generate_password_hash
            super_admin_role = Role.query.filter_by(name='super_admin').first()
            admin = User(
                email='admin@currie.com',
                password_hash=generate_password_hash('changeme123'),
                name='System Admin',
                user_type='currie_admin',
                is_active=True
            )
            if super_admin_role:
                admin.roles.append(super_admin_role)
            db.session.add(admin)
            db.session.commit()
            print("Default admin created: admin@currie.com / changeme123")
            print("IMPORTANT: Change this password immediately!")

        print("\nDatabase initialization complete!")
        print("Tables created:")
        for table in db.metadata.tables.keys():
            print(f"  - {table}")

if __name__ == '__main__':
    init_database()
