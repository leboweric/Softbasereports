"""
Initialize RBAC (Role-Based Access Control) system
Run this script to set up default roles, permissions, and departments
"""
from src.models.user import db
from src.models.rbac import Role, Permission, Department, DEFAULT_ROLES, DEFAULT_PERMISSIONS

def init_rbac(app=None):
    """Initialize RBAC system with default roles and permissions"""
    
    # If app context is provided, use it
    if app:
        with app.app_context():
            _create_rbac_data()
    else:
        _create_rbac_data()

def _create_rbac_data():
    """Create default RBAC data"""
    
    # Create default departments
    departments = [
        {'name': 'Parts', 'code': 'PRT', 'description': 'Parts department'},
        {'name': 'Service', 'code': 'SVC', 'description': 'Service department'},
        {'name': 'Rental', 'code': 'RNT', 'description': 'Rental department'},
        {'name': 'Accounting', 'code': 'ACC', 'description': 'Accounting department'},
        {'name': 'Sales', 'code': 'SLS', 'description': 'Sales department'},
    ]
    
    print("Creating departments...")
    for dept_data in departments:
        dept = Department.query.filter_by(code=dept_data['code']).first()
        if not dept:
            dept = Department(**dept_data)
            db.session.add(dept)
            print(f"  Created department: {dept_data['name']}")
        else:
            print(f"  Department exists: {dept_data['name']}")
    
    db.session.commit()
    
    # Create default permissions
    print("\nCreating permissions...")
    created_permissions = {}
    for perm_data in DEFAULT_PERMISSIONS:
        perm = Permission.query.filter_by(name=perm_data['name']).first()
        if not perm:
            perm = Permission(**perm_data)
            db.session.add(perm)
            print(f"  Created permission: {perm_data['name']}")
        else:
            print(f"  Permission exists: {perm_data['name']}")
        created_permissions[perm_data['name']] = perm
    
    db.session.commit()
    
    # Create default roles with permissions
    print("\nCreating roles...")
    for role_data in DEFAULT_ROLES:
        role = Role.query.filter_by(name=role_data['name']).first()
        if not role:
            role = Role(
                name=role_data['name'],
                description=role_data['description'],
                department=role_data['department'],
                level=role_data['level']
            )
            db.session.add(role)
            db.session.flush()  # Get the role ID
            
            # Assign permissions
            for perm_pattern in role_data['permissions']:
                if perm_pattern == '*':
                    # Assign all permissions
                    role.permissions = list(created_permissions.values())
                elif perm_pattern.endswith('*'):
                    # Wildcard permissions (e.g., 'view_*')
                    prefix = perm_pattern[:-1]
                    for perm_name, perm in created_permissions.items():
                        if perm_name.startswith(prefix):
                            role.permissions.append(perm)
                else:
                    # Specific permission
                    if perm_pattern in created_permissions:
                        role.permissions.append(created_permissions[perm_pattern])
            
            print(f"  Created role: {role_data['name']} with {len(role.permissions)} permissions")
        else:
            print(f"  Role exists: {role_data['name']}")
    
    db.session.commit()
    print("\nRBAC initialization complete!")

def assign_role_to_user(user, role_name):
    """Assign a role to a user"""
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        raise ValueError(f"Role '{role_name}' not found")
    
    if role not in user.roles:
        user.roles.append(role)
        db.session.commit()
        return True
    return False

def remove_role_from_user(user, role_name):
    """Remove a role from a user"""
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        raise ValueError(f"Role '{role_name}' not found")
    
    if role in user.roles:
        user.roles.remove(role)
        db.session.commit()
        return True
    return False

def migrate_existing_users():
    """Migrate existing users to new RBAC system"""
    from src.models.user import User
    
    print("\nMigrating existing users to RBAC...")
    users = User.query.all()
    
    for user in users:
        # Skip if user already has roles
        if user.roles:
            print(f"  User {user.username} already has roles")
            continue
        
        # Assign role based on legacy 'role' field
        if user.role == 'admin':
            assign_role_to_user(user, 'Super Admin')
            print(f"  Assigned 'Super Admin' to {user.username}")
        elif user.role == 'manager':
            assign_role_to_user(user, 'Leadership')
            print(f"  Assigned 'Leadership' to {user.username}")
        else:
            assign_role_to_user(user, 'Read Only')
            print(f"  Assigned 'Read Only' to {user.username}")
    
    db.session.commit()
    print("User migration complete!")

if __name__ == '__main__':
    # Run standalone
    from src.main import app
    init_rbac(app)
    
    # Optionally migrate existing users
    with app.app_context():
        migrate_existing_users()