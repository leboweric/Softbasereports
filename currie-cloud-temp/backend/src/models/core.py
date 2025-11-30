"""
Currie Cloud Platform - Core Data Models

This module defines the multi-tenant data model for the platform:
- Dealers (tenants)
- Users (belong to dealers or Currie corporate)
- ERP Connections (how dealers connect to their systems)
- Data Sync Jobs (tracking data imports)
"""
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from .database import db


# Association table for user roles
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)


class Dealer(db.Model):
    """
    Dealer organization - the primary tenant in the system.
    Each dealer has their own users, ERP connections, and financial data.
    """
    __tablename__ = 'dealers'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))

    # Basic info
    name = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(50), unique=True)  # e.g., "DEALER001"

    # Contact
    contact_name = db.Column(db.String(255))
    contact_email = db.Column(db.String(255))
    contact_phone = db.Column(db.String(50))

    # Address
    address = db.Column(db.String(255))
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    zip_code = db.Column(db.String(20))

    # Subscription
    subscription_tier = db.Column(db.String(50), default='basic')  # basic, professional, enterprise
    subscription_status = db.Column(db.String(20), default='active')  # active, suspended, cancelled
    subscription_start = db.Column(db.DateTime)
    subscription_end = db.Column(db.DateTime)

    # ERP System info
    erp_system = db.Column(db.String(50))  # 'softbase_evolution', 'dis_cai', 'e_emphasys', etc.

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    users = db.relationship('User', backref='dealer', lazy='dynamic')
    erp_connections = db.relationship('ERPConnection', backref='dealer', lazy='dynamic')
    financial_data = db.relationship('DepartmentFinancial', backref='dealer', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'name': self.name,
            'code': self.code,
            'erp_system': self.erp_system,
            'subscription_tier': self.subscription_tier,
            'subscription_status': self.subscription_status,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class User(db.Model):
    """
    User accounts - can belong to a dealer or be Currie corporate users.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))

    # Authentication
    email = db.Column(db.String(255), unique=True, nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # Profile
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))

    # Tenant association (NULL for Currie corporate users)
    dealer_id = db.Column(db.Integer, db.ForeignKey('dealers.id'), nullable=True)

    # User type
    user_type = db.Column(db.String(20), default='dealer')  # 'dealer', 'currie_admin', 'currie_analyst'

    # Status
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    roles = db.relationship('Role', secondary=user_roles, backref='users')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'dealer_id': self.dealer_id,
            'user_type': self.user_type,
            'is_active': self.is_active,
            'roles': [r.name for r in self.roles],
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class Role(db.Model):
    """User roles for access control."""
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))

    # Permissions stored as JSON array
    permissions = db.Column(db.JSON, default=list)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'permissions': self.permissions
        }


class ERPConnection(db.Model):
    """
    ERP/DMS connection configuration for a dealer.
    Stores encrypted credentials and connection details.
    """
    __tablename__ = 'erp_connections'

    id = db.Column(db.Integer, primary_key=True)
    dealer_id = db.Column(db.Integer, db.ForeignKey('dealers.id'), nullable=False)

    # Connection type
    erp_type = db.Column(db.String(50), nullable=False)  # 'softbase_evolution', etc.
    connection_method = db.Column(db.String(50))  # 'direct_db', 'api', 'sftp', 'agent'

    # Connection details (encrypted)
    server = db.Column(db.String(255))
    database = db.Column(db.String(255))
    username = db.Column(db.String(255))
    password_encrypted = db.Column(db.Text)  # Encrypted with platform key

    # API-based connections
    api_endpoint = db.Column(db.String(500))
    api_key_encrypted = db.Column(db.Text)

    # SFTP-based connections
    sftp_host = db.Column(db.String(255))
    sftp_path = db.Column(db.String(500))

    # Status
    is_active = db.Column(db.Boolean, default=True)
    last_sync = db.Column(db.DateTime)
    last_sync_status = db.Column(db.String(50))  # 'success', 'failed', 'partial'
    last_sync_message = db.Column(db.Text)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'dealer_id': self.dealer_id,
            'erp_type': self.erp_type,
            'connection_method': self.connection_method,
            'server': self.server,
            'database': self.database,
            'is_active': self.is_active,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'last_sync_status': self.last_sync_status
        }


class DataSyncJob(db.Model):
    """
    Tracks data synchronization jobs from ERP systems.
    """
    __tablename__ = 'data_sync_jobs'

    id = db.Column(db.Integer, primary_key=True)
    dealer_id = db.Column(db.Integer, db.ForeignKey('dealers.id'), nullable=False)
    erp_connection_id = db.Column(db.Integer, db.ForeignKey('erp_connections.id'))

    # Job details
    job_type = db.Column(db.String(50))  # 'full', 'incremental', 'manual'
    status = db.Column(db.String(50))  # 'pending', 'running', 'completed', 'failed'

    # Period being synced
    period_start = db.Column(db.Date)
    period_end = db.Column(db.Date)

    # Results
    records_processed = db.Column(db.Integer, default=0)
    records_created = db.Column(db.Integer, default=0)
    records_updated = db.Column(db.Integer, default=0)
    errors = db.Column(db.JSON, default=list)

    # Timestamps
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    dealer = db.relationship('Dealer', backref='sync_jobs')

    def to_dict(self):
        return {
            'id': self.id,
            'dealer_id': self.dealer_id,
            'job_type': self.job_type,
            'status': self.status,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'records_processed': self.records_processed,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
