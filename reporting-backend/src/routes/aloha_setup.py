"""
One-time setup route for Aloha Holdings tenant
This can be called once to set up the organization and users, then removed.
Aloha Holdings is a Hawaii-based holding company with 3 subsidiaries:
  - Sandia Plastics
  - Kauai Exclusive
  - Hawaii Care & Cleaning
Each subsidiary runs its own SAP ERP system.
"""
from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash
from datetime import datetime
from src.models.user import db, Organization, User
from src.models.rbac import Role
import json

aloha_setup_bp = Blueprint('aloha_setup', __name__)


@aloha_setup_bp.route('/setup-aloha', methods=['POST'])
def setup_aloha():
    """
    One-time setup for Aloha Holdings organization and users.
    Call this endpoint once to create the tenant.
    """
    try:
        # Check if Aloha Holdings already exists
        org = Organization.query.filter_by(name='Aloha Holdings').first()
        org_created = False
        
        if not org:
            # Default SAP data source configuration for 3 subsidiaries
            default_settings = {
                'data_sources': {
                    'sap_sandia_plastics': {
                        'name': 'Sandia Plastics',
                        'connected': False,
                        'system_type': '',  # S/4HANA, Business One, ECC, ByDesign
                        'connection_method': '',  # odata, rfc, db_direct, api, service_layer
                        'host': '',
                        'port': '',
                        'client': '',
                        'system_number': '',
                        'username': '',
                        'password': '',
                        'company_db': '',  # For SAP Business One
                    },
                    'sap_kauai_exclusive': {
                        'name': 'Kauai Exclusive',
                        'connected': False,
                        'system_type': '',
                        'connection_method': '',
                        'host': '',
                        'port': '',
                        'client': '',
                        'system_number': '',
                        'username': '',
                        'password': '',
                        'company_db': '',
                    },
                    'sap_hawaii_care': {
                        'name': 'Hawaii Care & Cleaning',
                        'connected': False,
                        'system_type': '',
                        'connection_method': '',
                        'host': '',
                        'port': '',
                        'client': '',
                        'system_number': '',
                        'username': '',
                        'password': '',
                        'company_db': '',
                    }
                }
            }
            
            org = Organization(
                name='Aloha Holdings',
                platform_type='sap',
                subscription_status='active',
                fiscal_year_start_month=1,
                is_active=True,
                settings=json.dumps(default_settings)
            )
            db.session.add(org)
            db.session.flush()
            org_created = True
        
        # Get or create Aloha roles
        aloha_admin_role = Role.query.filter_by(name='Aloha Admin').first()
        if not aloha_admin_role:
            aloha_admin_role = Role(
                name='Aloha Admin',
                description='Aloha Holdings administrator with full access to all subsidiary data',
                department='Administration',
                organization_id=org.id,
                is_active=True
            )
            db.session.add(aloha_admin_role)
            db.session.flush()
        
        aloha_user_role = Role.query.filter_by(name='Aloha User').first()
        if not aloha_user_role:
            aloha_user_role = Role(
                name='Aloha User',
                description='Aloha Holdings standard user with view access to subsidiary data',
                department='Operations',
                organization_id=org.id,
                is_active=True
            )
            db.session.add(aloha_user_role)
            db.session.flush()
        
        # Initial admin user (Eric LeBow for setup/testing)
        aloha_users = [
            {'first_name': 'Eric', 'last_name': 'LeBow', 'email': 'elebow@aloha.com', 'is_admin': True},
            {'first_name': 'J', 'last_name': 'Foos', 'email': 'jfoos@aloha.com', 'is_admin': True},
            {'first_name': 'C', 'last_name': 'Shannon', 'email': 'cshannon@aloha.com', 'is_admin': True},
        ]
        
        temp_password = 'abc123'
        created_users = []
        skipped_users = []
        
        for user_data in aloha_users:
            existing_user = User.query.filter_by(email=user_data['email'].lower()).first()
            if existing_user:
                skipped_users.append(f"{user_data['first_name']} {user_data['last_name']} ({user_data['email']}) - already exists in org {existing_user.organization_id}")
                continue
            
            user = User(
                username=user_data['email'].lower(),
                email=user_data['email'].lower(),
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                password_hash=generate_password_hash(temp_password),
                organization_id=org.id,
                is_active=True,
                role='admin' if user_data['is_admin'] else 'user'
            )
            
            if user_data['is_admin'] and aloha_admin_role:
                user.roles.append(aloha_admin_role)
            elif aloha_user_role:
                user.roles.append(aloha_user_role)
            
            db.session.add(user)
            created_users.append(f"{user_data['first_name']} {user_data['last_name']} ({user_data['email']})")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Aloha Holdings setup complete',
            'organization': {
                'id': org.id,
                'name': org.name,
                'platform_type': org.platform_type,
                'created': org_created
            },
            'subsidiaries': [
                'Sandia Plastics',
                'Kauai Exclusive',
                'Hawaii Care & Cleaning'
            ],
            'roles_created': [
                'Aloha Admin' if aloha_admin_role else None,
                'Aloha User' if aloha_user_role else None
            ],
            'users_created': created_users,
            'users_skipped': skipped_users,
            'temp_password': temp_password,
            'next_steps': [
                'Configure SAP connection for Sandia Plastics',
                'Configure SAP connection for Kauai Exclusive',
                'Configure SAP connection for Hawaii Care & Cleaning',
                'Add actual users via User Management',
                'Set up ETL jobs for SAP data extraction'
            ]
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
