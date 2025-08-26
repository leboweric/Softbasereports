#!/usr/bin/env python3
"""
Apply permission decorators to all department routes
This script will be used to automatically update all routes with proper RBAC permissions
"""

import os
import re

# Permission mapping for each department
PERMISSION_MAP = {
    '/departments/service': 'view_service',
    '/departments/parts': 'view_parts',
    '/departments/rental': 'view_rental',
    '/departments/accounting': 'view_accounting',
    '/departments/work-order': 'view_dashboard',  # General work order endpoints
}

# Special routes that should have different permissions
SPECIAL_PERMISSIONS = {
    '/departments/accounting/sales-commission': 'view_commissions',
    '/departments/accounting/ar-': 'view_ar',
    '/departments/accounting/ap-': 'view_accounting',
    '/departments/service/awaiting-invoice': 'edit_service',
    '/departments/parts/awaiting-invoice': 'edit_parts',
}

def get_permission_for_route(route):
    """Determine the appropriate permission for a route"""
    # Check special permissions first
    for pattern, permission in SPECIAL_PERMISSIONS.items():
        if pattern in route:
            return permission
    
    # Check general department permissions
    for pattern, permission in PERMISSION_MAP.items():
        if route.startswith(pattern):
            return permission
    
    # Default to view_dashboard for unmatched routes
    return 'view_dashboard'

def update_route_decorators(file_path):
    """Update a Python file to use permission decorators"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if auth_decorators is imported
    if 'from src.utils.auth_decorators import' not in content:
        # Add import at the top of imports section
        import_line = 'from src.utils.auth_decorators import require_permission, require_department\n'
        
        # Find where to insert (after other imports)
        import_pattern = r'(from src\..*?import.*?\n)'
        matches = list(re.finditer(import_pattern, content))
        if matches:
            last_import = matches[-1]
            insert_pos = last_import.end()
            content = content[:insert_pos] + import_line + content[insert_pos:]
        else:
            # Insert after the main imports
            insert_pos = content.find('\nimport') 
            if insert_pos == -1:
                insert_pos = content.find('\nfrom')
            if insert_pos != -1:
                # Find the end of import block
                lines = content[insert_pos:].split('\n')
                import_end = 0
                for i, line in enumerate(lines):
                    if line and not line.startswith(('import', 'from', '#')) and not line.strip() == '':
                        import_end = i
                        break
                insert_pos = insert_pos + sum(len(l) + 1 for l in lines[:import_end])
                content = content[:insert_pos] + import_line + content[insert_pos:]
    
    # Pattern to find route decorators with jwt_required
    route_pattern = r"(@reports_bp\.route\('/departments/.*?'\s*(?:,.*?)?\))\s*\n\s*@jwt_required\(\)"
    
    def replace_decorator(match):
        route_decorator = match.group(1)
        # Extract the route path
        route_match = re.search(r"'/departments/(.*?)'", route_decorator)
        if route_match:
            full_route = f'/departments/{route_match.group(1)}'
            permission = get_permission_for_route(full_route)
            return f"{route_decorator}\n    @require_permission('{permission}')"
        return match.group(0)
    
    # Replace all occurrences
    updated_content = re.sub(route_pattern, replace_decorator, content)
    
    # Write back if changes were made
    if updated_content != content:
        with open(file_path, 'w') as f:
            f.write(updated_content)
        return True
    return False

def main():
    """Update all department route files"""
    backend_dir = '/Users/ericlebow/Library/CloudStorage/OneDrive-PBN/Software Projects/Softbasereports/reporting-backend'
    routes_dir = os.path.join(backend_dir, 'src', 'routes')
    
    files_to_update = [
        'department_reports.py',
        'rental_comprehensive_research.py',
        'rental_shipto_research.py',
        'rental_shipto_simple.py',
        'rental_customer_solution.py',
        'rental_deep_search.py',
        'rental_diagnosis.py',
        'control_number_reports.py',
        'control_number_research.py',
        'accounting_reports.py',
    ]
    
    updated_files = []
    for filename in files_to_update:
        file_path = os.path.join(routes_dir, filename)
        if os.path.exists(file_path):
            if update_route_decorators(file_path):
                updated_files.append(filename)
                print(f"Updated {filename}")
            else:
                print(f"No changes needed for {filename}")
        else:
            print(f"File not found: {filename}")
    
    print(f"\nTotal files updated: {len(updated_files)}")
    if updated_files:
        print("Files updated:", ', '.join(updated_files))

if __name__ == '__main__':
    main()