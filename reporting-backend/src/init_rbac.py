"""
Auto-initialize RBAC roles and permissions on application startup
"""
from src.models.rbac import Role, Permission, db
from sqlalchemy.exc import IntegrityError

def initialize_parts_user_role():
    """Create Parts User role if it doesn't exist"""
    try:
        # Check if role already exists
        existing_role = Role.query.filter_by(name='Parts User').first()
        if existing_role:
            print("✅ Parts User role already exists")
            return existing_role
        
        print("🔧 Creating Parts User role...")
        
        # Create the role
        parts_user_role = Role(
            name='Parts User',
            description='Restricted access to specific Parts reports and Minitrac only',
            department='Parts',
            level=2
        )
        
        # Define required permissions with their details
        required_permissions = [
            {
                'name': 'view_parts_work_orders',
                'resource': 'parts',
                'action': 'view_work_orders',
                'description': 'View Parts work orders report'
            },
            {
                'name': 'view_parts_inventory_location',
                'resource': 'parts',
                'action': 'view_inventory_location',
                'description': 'View Parts inventory by location report'
            },
            {
                'name': 'view_parts_stock_alerts',
                'resource': 'parts',
                'action': 'view_stock_alerts',
                'description': 'View Parts stock alerts report'
            },
            {
                'name': 'view_parts_forecast',
                'resource': 'parts',
                'action': 'view_forecast',
                'description': 'View Parts forecast report'
            },
            {
                'name': 'view_minitrac',
                'resource': 'minitrac',
                'action': 'view',
                'description': 'View Minitrac equipment data'
            },
            {
                'name': 'export_minitrac',
                'resource': 'minitrac',
                'action': 'export',
                'description': 'Export Minitrac data'
            }
        ]
        
        # Create/get permissions and add to role
        for perm_data in required_permissions:
            permission = Permission.query.filter_by(name=perm_data['name']).first()
            if not permission:
                # Create permission if it doesn't exist
                permission = Permission(
                    name=perm_data['name'],
                    resource=perm_data['resource'],
                    action=perm_data['action'],
                    description=perm_data['description']
                )
                db.session.add(permission)
                print(f"  📝 Created permission: {perm_data['name']}")
            else:
                print(f"  ✓ Permission exists: {perm_data['name']}")
            
            parts_user_role.permissions.append(permission)
        
        db.session.add(parts_user_role)
        db.session.commit()
        
        print("✅ Parts User role created successfully with all permissions")
        print(f"   📋 Role: {parts_user_role.name}")
        print(f"   🏢 Department: {parts_user_role.department}")
        print(f"   📊 Level: {parts_user_role.level}")
        print(f"   🔐 Permissions: {len(parts_user_role.permissions)}")
        
        return parts_user_role
        
    except IntegrityError as e:
        db.session.rollback()
        print(f"⚠️  Role creation failed (may already exist): {e}")
        return Role.query.filter_by(name='Parts User').first()
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating Parts User role: {e}")
        raise

def initialize_accounting_user_role():
    """Create or update Accounting User role with proper permissions"""
    try:
        # Check if role already exists
        existing_role = Role.query.filter_by(name='Accounting User').first()

        if existing_role:
            print("✅ Accounting User role already exists, checking permissions...")
            accounting_user_role = existing_role
        else:
            print("🔧 Creating Accounting User role...")
            accounting_user_role = Role(
                name='Accounting User',
                description='View-only access to accounting data',
                department='Accounting',
                level=2
            )
            db.session.add(accounting_user_role)

        # Define required permissions with their details
        required_permissions = [
            {
                'name': 'view_accounting',
                'resource': 'accounting',
                'action': 'view',
                'description': 'View accounting reports and data'
            },
            {
                'name': 'view_commissions',
                'resource': 'commissions',
                'action': 'view',
                'description': 'View sales commission reports'
            },
            {
                'name': 'view_ar',
                'resource': 'ar',
                'action': 'view',
                'description': 'View accounts receivable reports'
            },
            {
                'name': 'export_accounting',
                'resource': 'accounting',
                'action': 'export',
                'description': 'Export accounting data'
            },
            {
                'name': 'view_dashboard',
                'resource': 'dashboard',
                'action': 'view',
                'description': 'View main dashboard'
            }
        ]

        # Create/get permissions and add to role
        for perm_data in required_permissions:
            permission = Permission.query.filter_by(name=perm_data['name']).first()
            if not permission:
                # Create permission if it doesn't exist
                permission = Permission(
                    name=perm_data['name'],
                    resource=perm_data['resource'],
                    action=perm_data['action'],
                    description=perm_data['description']
                )
                db.session.add(permission)
                print(f"  📝 Created permission: {perm_data['name']}")
            else:
                print(f"  ✓ Permission exists: {perm_data['name']}")

            # Add permission to role if not already assigned
            if permission not in accounting_user_role.permissions:
                accounting_user_role.permissions.append(permission)
                print(f"  🔗 Linked permission: {perm_data['name']} to Accounting User")

        db.session.commit()

        print("✅ Accounting User role initialized successfully with all permissions")
        print(f"   📋 Role: {accounting_user_role.name}")
        print(f"   🏢 Department: {accounting_user_role.department}")
        print(f"   📊 Level: {accounting_user_role.level}")
        print(f"   🔐 Permissions: {len(accounting_user_role.permissions)}")

        return accounting_user_role

    except IntegrityError as e:
        db.session.rollback()
        print(f"⚠️  Accounting User role creation failed (may already exist): {e}")
        return Role.query.filter_by(name='Accounting User').first()
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating Accounting User role: {e}")
        raise

def initialize_specific_permissions():
    """Ensure the specific Parts permissions exist"""
    try:
        permissions_to_create = [
            {
                'name': 'view_parts_work_orders',
                'resource': 'parts',
                'action': 'view_work_orders',
                'description': 'View Parts work orders report'
            },
            {
                'name': 'view_parts_inventory_location',
                'resource': 'parts',
                'action': 'view_inventory_location',
                'description': 'View Parts inventory by location report'
            },
            {
                'name': 'view_parts_stock_alerts',
                'resource': 'parts',
                'action': 'view_stock_alerts',
                'description': 'View Parts stock alerts report'
            },
            {
                'name': 'view_parts_forecast',
                'resource': 'parts',
                'action': 'view_forecast',
                'description': 'View Parts forecast report'
            }
        ]
        
        for perm_data in permissions_to_create:
            existing_perm = Permission.query.filter_by(name=perm_data['name']).first()
            if not existing_perm:
                permission = Permission(**perm_data)
                db.session.add(permission)
                print(f"  📝 Created permission: {perm_data['name']}")
        
        db.session.commit()
        print("✅ Specific Parts permissions initialized")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating specific permissions: {e}")
        raise

def initialize_core_roles():
    """Create all core roles from RBAC config"""
    from src.config.rbac_config import ROLE_PERMISSIONS
    
    try:
        for role_name, role_config in ROLE_PERMISSIONS.items():
            # Check if role already exists
            existing_role = Role.query.filter_by(name=role_name).first()
            if existing_role:
                print(f"✅ {role_name} role already exists")
                continue
            
            print(f"🔧 Creating {role_name} role...")
            
            # Create the role
            role = Role(
                name=role_name,
                description=f"Auto-generated {role_name} role",
                department='All' if role_name in ['Super Admin', 'Leadership'] else 'Various',
                level=1 if role_name == 'Super Admin' else 2
            )
            
            db.session.add(role)
            print(f"✅ {role_name} role created successfully")
        
        db.session.commit()
        print("✅ All core roles initialized")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating core roles: {e}")
        raise

def assign_super_admin_to_existing_admin_users():
    """Assign Super Admin role to users with legacy admin role"""
    try:
        from src.models.user import User
        
        # Get Super Admin role
        super_admin_role = Role.query.filter_by(name='Super Admin').first()
        if not super_admin_role:
            print("⚠️ Super Admin role not found, skipping user assignment")
            return
        
        # Find users with legacy admin role who don't have any RBAC roles
        admin_users = User.query.filter_by(role='admin').all()
        for user in admin_users:
            if not user.roles:  # User has no RBAC roles assigned
                user.roles.append(super_admin_role)
                print(f"✅ Assigned Super Admin role to {user.username}")
        
        db.session.commit()
        print("✅ Super Admin roles assigned to legacy admin users")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error assigning Super Admin roles: {e}")
        raise

def initialize_all_rbac():
    """Initialize all RBAC roles and permissions"""
    print("🔧 Initializing RBAC system...")

    try:
        # First ensure specific permissions exist
        initialize_specific_permissions()

        # Create all core roles from RBAC config
        initialize_core_roles()

        # Create the Parts User role (legacy)
        initialize_parts_user_role()

        # Create/update the Accounting User role with proper permissions
        initialize_accounting_user_role()

        # Assign Super Admin to existing admin users
        assign_super_admin_to_existing_admin_users()

        print("✅ RBAC initialization complete")
        
    except Exception as e:
        print(f"❌ RBAC initialization failed: {e}")
        # Don't crash the app if RBAC init fails
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # For testing purposes
    from src.main import create_app
    app = create_app()
    with app.app_context():
        initialize_all_rbac()