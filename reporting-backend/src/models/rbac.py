"""
Role-Based Access Control (RBAC) models for Softbase Reports
"""
from datetime import datetime
from src.models.user import db

# Association table for many-to-many relationship between users and roles
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id', ondelete='CASCADE'), primary_key=True),
    db.Column('assigned_at', db.DateTime, default=datetime.utcnow),
    db.Column('assigned_by', db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'))
)

# Association table for many-to-many relationship between roles and permissions
role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'), primary_key=True)
)

class Role(db.Model):
    """Role model - defines user roles like Admin, Parts Manager, Service Tech, etc."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # Removed unique constraint - roles can have same name in different orgs
    description = db.Column(db.String(255))
    department = db.Column(db.String(50))  # Parts, Service, Rental, Accounting, etc.
    level = db.Column(db.Integer, default=1)  # 1=User, 5=Manager, 10=Admin
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=True)  # Null = system-wide role
    
    # Add unique constraint on name + organization_id
    __table_args__ = (db.UniqueConstraint('name', 'organization_id', name='uq_role_name_org'),)
    
    # Relationships
    permissions = db.relationship('Permission', secondary=role_permissions, 
                                 backref=db.backref('roles', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Role {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'department': self.department,
            'level': self.level,
            'is_active': self.is_active,
            'organization_id': self.organization_id,
            'permissions': [p.to_dict() for p in self.permissions]
        }
    
    def has_permission(self, permission_name):
        """Check if role has a specific permission"""
        return any(p.name == permission_name for p in self.permissions)

class Permission(db.Model):
    """Permission model - defines specific permissions like 'view_parts', 'edit_invoices', etc."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  # e.g., 'view_parts', 'edit_commissions'
    resource = db.Column(db.String(50), nullable=False)  # e.g., 'parts', 'service', 'dashboard'
    action = db.Column(db.String(50), nullable=False)  # e.g., 'view', 'create', 'edit', 'delete'
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Permission {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'resource': self.resource,
            'action': self.action,
            'description': self.description
        }

class Department(db.Model):
    """Department model - organizational structure"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)  # e.g., 'PRT', 'SVC', 'RNT'
    description = db.Column(db.String(255))
    manager_role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Department {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'is_active': self.is_active
        }

# Default roles and permissions setup
DEFAULT_ROLES = [
    {
        'name': 'Super Admin',
        'description': 'Full system access',
        'department': None,
        'level': 10,
        'permissions': ['*']  # All permissions
    },
    {
        'name': 'Leadership',
        'description': 'Executive level access to all departments',
        'department': None,
        'level': 9,
        'permissions': ['view_*', 'export_*']  # View and export everything
    },
    {
        'name': 'Accounting Manager',
        'description': 'Full access to accounting and financial data',
        'department': 'Accounting',
        'level': 5,
        'permissions': ['view_accounting', 'edit_accounting', 'view_commissions', 'edit_commissions', 
                       'view_ar', 'export_accounting', 'view_dashboard']
    },
    {
        'name': 'Parts Manager',
        'description': 'Full access to parts department',
        'department': 'Parts',
        'level': 5,
        'permissions': ['view_parts', 'edit_parts', 'view_inventory', 'edit_inventory', 
                       'export_parts', 'view_dashboard']
    },
    {
        'name': 'Service Manager',
        'description': 'Full access to service department',
        'department': 'Service',
        'level': 5,
        'permissions': ['view_service', 'edit_service', 'view_technicians', 'edit_work_orders',
                       'export_service', 'view_dashboard']
    },
    {
        'name': 'Rental Manager',
        'description': 'Full access to rental department',
        'department': 'Rental',
        'level': 5,
        'permissions': ['view_rental', 'edit_rental', 'view_equipment', 'edit_equipment',
                       'export_rental', 'view_dashboard']
    },
    {
        'name': 'Parts Staff',
        'description': 'View-only access to parts data',
        'department': 'Parts',
        'level': 1,
        'permissions': ['view_parts', 'view_inventory']
    },
    {
        'name': 'Parts User',
        'description': 'Restricted access to specific Parts reports and Minitrac only',
        'department': 'Parts',
        'level': 2,
        'permissions': ['view_parts_work_orders', 'view_parts_inventory_location', 
                       'view_parts_stock_alerts', 'view_parts_forecast', 'view_minitrac', 'export_minitrac']
    },
    {
        'name': 'Service Tech',
        'description': 'View service work orders and update status',
        'department': 'Service',
        'level': 1,
        'permissions': ['view_service', 'edit_own_work_orders']
    },
    {
        'name': 'Sales Rep',
        'description': 'View own commission data',
        'department': 'Sales',
        'level': 1,
        'permissions': ['view_own_commissions', 'view_own_customers']
    },
    {
        'name': 'Accounting User',
        'description': 'View-only access to accounting data',
        'department': 'Accounting',
        'level': 2,
        'permissions': ['view_accounting', 'view_commissions', 'view_ar', 'export_accounting', 'view_dashboard']
    },
    {
        'name': 'Read Only',
        'description': 'View-only access to authorized areas',
        'department': None,
        'level': 0,
        'permissions': ['view_dashboard']
    }
]

DEFAULT_PERMISSIONS = [
    # Dashboard
    {'name': 'view_dashboard', 'resource': 'dashboard', 'action': 'view', 
     'description': 'View main dashboard'},
    
    # Parts Department
    {'name': 'view_parts', 'resource': 'parts', 'action': 'view',
     'description': 'View parts reports and data'},
    {'name': 'edit_parts', 'resource': 'parts', 'action': 'edit',
     'description': 'Edit parts data'},
    {'name': 'view_inventory', 'resource': 'inventory', 'action': 'view',
     'description': 'View inventory levels'},
    {'name': 'edit_inventory', 'resource': 'inventory', 'action': 'edit',
     'description': 'Adjust inventory levels'},
    {'name': 'export_parts', 'resource': 'parts', 'action': 'export',
     'description': 'Export parts data'},
    
    # Service Department
    {'name': 'view_service', 'resource': 'service', 'action': 'view',
     'description': 'View service reports and work orders'},
    {'name': 'edit_service', 'resource': 'service', 'action': 'edit',
     'description': 'Edit service data'},
    {'name': 'view_technicians', 'resource': 'technicians', 'action': 'view',
     'description': 'View technician performance'},
    {'name': 'edit_work_orders', 'resource': 'work_orders', 'action': 'edit',
     'description': 'Edit work orders'},
    {'name': 'edit_own_work_orders', 'resource': 'work_orders', 'action': 'edit_own',
     'description': 'Edit only own work orders'},
    {'name': 'export_service', 'resource': 'service', 'action': 'export',
     'description': 'Export service data'},
    
    # Rental Department
    {'name': 'view_rental', 'resource': 'rental', 'action': 'view',
     'description': 'View rental reports'},
    {'name': 'edit_rental', 'resource': 'rental', 'action': 'edit',
     'description': 'Edit rental data'},
    {'name': 'view_equipment', 'resource': 'equipment', 'action': 'view',
     'description': 'View equipment status'},
    {'name': 'edit_equipment', 'resource': 'equipment', 'action': 'edit',
     'description': 'Edit equipment data'},
    {'name': 'export_rental', 'resource': 'rental', 'action': 'export',
     'description': 'Export rental data'},
    
    # Accounting Department
    {'name': 'view_accounting', 'resource': 'accounting', 'action': 'view',
     'description': 'View accounting reports'},
    {'name': 'edit_accounting', 'resource': 'accounting', 'action': 'edit',
     'description': 'Edit accounting data'},
    {'name': 'view_commissions', 'resource': 'commissions', 'action': 'view',
     'description': 'View all commission data'},
    {'name': 'edit_commissions', 'resource': 'commissions', 'action': 'edit',
     'description': 'Edit commission calculations'},
    {'name': 'view_own_commissions', 'resource': 'commissions', 'action': 'view_own',
     'description': 'View only own commission data'},
    {'name': 'view_ar', 'resource': 'accounts_receivable', 'action': 'view',
     'description': 'View AR aging reports'},
    {'name': 'export_accounting', 'resource': 'accounting', 'action': 'export',
     'description': 'Export accounting data'},
    
    # Customer Management
    {'name': 'view_customers', 'resource': 'customers', 'action': 'view',
     'description': 'View all customers'},
    {'name': 'view_own_customers', 'resource': 'customers', 'action': 'view_own',
     'description': 'View only assigned customers'},
    {'name': 'edit_customers', 'resource': 'customers', 'action': 'edit',
     'description': 'Edit customer data'},
    
    # System Administration
    {'name': 'view_users', 'resource': 'users', 'action': 'view',
     'description': 'View user list'},
    {'name': 'edit_users', 'resource': 'users', 'action': 'edit',
     'description': 'Edit user accounts'},
    {'name': 'manage_roles', 'resource': 'roles', 'action': 'manage',
     'description': 'Manage user roles and permissions'},
    
    # Database Access
    {'name': 'view_database_explorer', 'resource': 'database', 'action': 'view',
     'description': 'Access database explorer'},
    {'name': 'execute_queries', 'resource': 'database', 'action': 'execute',
     'description': 'Execute custom SQL queries'},
    
    # AI Features
    {'name': 'use_ai_query', 'resource': 'ai', 'action': 'query',
     'description': 'Use AI query assistant'},
    {'name': 'use_report_creator', 'resource': 'reports', 'action': 'create',
     'description': 'Create custom reports'},
    
    # Minitrac
    {'name': 'view_minitrac', 'resource': 'minitrac', 'action': 'view',
     'description': 'View Minitrac equipment data'},
    {'name': 'export_minitrac', 'resource': 'minitrac', 'action': 'export',
     'description': 'Export Minitrac data'},
    
    # Parts - Specific Report Permissions
    {'name': 'view_parts_work_orders', 'resource': 'parts', 'action': 'view_work_orders',
     'description': 'View Parts work orders report'},
    {'name': 'view_parts_inventory_location', 'resource': 'parts', 'action': 'view_inventory_location',
     'description': 'View Parts inventory by location report'},
    {'name': 'view_parts_stock_alerts', 'resource': 'parts', 'action': 'view_stock_alerts',
     'description': 'View Parts stock alerts report'},
    {'name': 'view_parts_forecast', 'resource': 'parts', 'action': 'view_forecast',
     'description': 'View Parts forecast report'}
]