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

def initialize_all_rbac():
    """Initialize all RBAC roles and permissions"""
    print("🔧 Initializing RBAC system...")
    
    try:
        # First ensure specific permissions exist
        initialize_specific_permissions()
        
        # Then create the Parts User role
        initialize_parts_user_role()
        
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