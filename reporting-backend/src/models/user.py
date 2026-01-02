from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# Import this after db is defined to avoid circular import
from src.models.rbac import user_roles

class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    
    # Legacy Softbase API fields (keep for backward compatibility)
    softbase_api_key = db.Column(db.String(255), nullable=True)
    softbase_endpoint = db.Column(db.String(255), nullable=True)
    
    # Multi-tenant database connection fields
    platform_type = db.Column(db.String(20), nullable=True)  # 'evolution' or 'legacy'
    db_server = db.Column(db.String(255), nullable=True)
    db_name = db.Column(db.String(255), nullable=True)
    db_username = db.Column(db.String(255), nullable=True)
    db_password_encrypted = db.Column(db.Text, nullable=True)
    
    # Stripe subscription management
    stripe_customer_id = db.Column(db.String(255), nullable=True)
    stripe_subscription_id = db.Column(db.String(255), nullable=True)
    subscription_status = db.Column(db.String(50), default='trialing')  # 'trialing', 'active', 'past_due', 'canceled', 'unpaid'
    subscription_ends_at = db.Column(db.DateTime, nullable=True)  # When current period ends or when access expires after cancellation
    trial_ends_at = db.Column(db.DateTime, nullable=True)  # End of free trial period

    # Legacy fields (keeping for backward compatibility)
    subscription_tier = db.Column(db.String(50), default='basic')  # Deprecated - all paid users get full access
    max_users = db.Column(db.Integer, default=5)  # Deprecated - no user limits
    
    # Fiscal year configuration
    fiscal_year_start_month = db.Column(db.Integer, default=11)  # 1-12, where 1=January, 11=November
    
    # Organization settings (JSON for flexible config storage)
    settings = db.Column(db.Text, nullable=True)  # JSON string for data source configs, etc.
    logo_url = db.Column(db.String(255), nullable=True) # URL for organization logo
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship
    users = db.relationship('User', backref='organization', lazy=True)

    def __repr__(self):
        return f'<Organization {self.name}>'

    def has_active_subscription(self):
        """Check if organization has an active paid subscription or valid trial"""
        if self.subscription_status in ['active', 'trialing']:
            return True
        # Allow access if past_due but within grace period (subscription_ends_at not yet passed)
        if self.subscription_status == 'past_due' and self.subscription_ends_at:
            return datetime.utcnow() < self.subscription_ends_at
        return False

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'platform_type': self.platform_type,
            'subscription_status': self.subscription_status,
            'subscription_ends_at': self.subscription_ends_at.isoformat() if self.subscription_ends_at else None,
            'trial_ends_at': self.trial_ends_at.isoformat() if self.trial_ends_at else None,
            'has_active_subscription': self.has_active_subscription(),
            'fiscal_year_start_month': self.fiscal_year_start_month,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'logo_url': self.logo_url
            # Note: Database credentials and Stripe IDs are intentionally NOT included for security
        }

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(80), nullable=True)
    last_name = db.Column(db.String(80), nullable=True)
    role = db.Column(db.String(50), default='user')  # DEPRECATED - use roles relationship
    # department_id = db.Column(db.Integer, db.ForeignKey('department.id', ondelete='SET NULL'), nullable=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    salesman_name = db.Column(db.String(100), nullable=True)  # Links user to Softbase salesman for commission reports
    
    # Relationships
    roles = db.relationship('Role', secondary=user_roles, 
                           backref=db.backref('users', lazy='dynamic'),
                           primaryjoin="User.id==user_roles.c.user_id",
                           secondaryjoin="Role.id==user_roles.c.role_id")
    # department = db.relationship('Department', backref='users', lazy='select')

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_admin(self):
        """Check if user has admin role (legacy support + new RBAC)"""
        if self.role == 'admin':  # Legacy check
            return True
        return any(r.name in ['Super Admin', 'Leadership'] for r in self.roles)
    
    def has_role(self, role_name):
        """Check if user has a specific role"""
        return any(r.name == role_name for r in self.roles)
    
    def has_permission(self, permission_name):
        """Check if user has a specific permission through any of their roles"""
        # Super Admin has all permissions
        if any(r.name == 'Super Admin' for r in self.roles):
            return True
        
        # Check if permission name includes wildcard
        if permission_name.startswith('view_') and any(r.name == 'Leadership' for r in self.roles):
            return True  # Leadership can view everything
        
        # Check specific permissions
        for role in self.roles:
            if role.has_permission(permission_name):
                return True
        return False
    
    def has_any_permission(self, *permission_names):
        """Check if user has any of the specified permissions"""
        return any(self.has_permission(p) for p in permission_names)
    
    def has_all_permissions(self, *permission_names):
        """Check if user has all of the specified permissions"""
        return all(self.has_permission(p) for p in permission_names)
    
    def can_access_department(self, department_name):
        """Check if user can access a specific department"""
        # Super Admin and Leadership can access all
        if any(r.name in ['Super Admin', 'Leadership'] for r in self.roles):
            return True
        
        # Check if user has role in that department
        return any(r.department == department_name for r in self.roles)
    
    def get_accessible_departments(self):
        """Get list of departments user can access"""
        if any(r.name in ['Super Admin', 'Leadership'] for r in self.roles):
            return ['Dashboard', 'Parts', 'Service', 'Rental', 'Accounting', 'Database', 'AI']
        
        departments = set(['Dashboard'])  # Everyone can see dashboard
        for role in self.roles:
            if role.department:
                departments.add(role.department)
        return list(departments)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role,  # Keep for legacy
            'roles': [r.to_dict() for r in self.roles],
            'department': None,  # Temporarily disabled
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active,
            'salesman_name': self.salesman_name,
            'accessible_departments': self.get_accessible_departments(),
            'is_admin': self.is_admin,
            'organization': self.organization.to_dict() if self.organization else None
        }

class ReportTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    query_config = db.Column(db.Text, nullable=False)  # JSON string with query parameters
    chart_config = db.Column(db.Text, nullable=True)   # JSON string with chart configuration
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<ReportTemplate {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'organization_id': self.organization_id,
            'created_by': self.created_by,
            'query_config': self.query_config,
            'chart_config': self.chart_config,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }
