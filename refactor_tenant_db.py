#!/usr/bin/env python3
"""
Refactoring script to update all route files to use tenant-specific database connections.

This script:
1. Replaces AzureSQLService() calls with get_tenant_db() calls
2. Updates imports accordingly
3. Handles module-level sql_service instances
"""

import os
import re
from pathlib import Path

ROUTES_DIR = Path("/home/ubuntu/SoftbaseCode/reporting-backend/src/routes")

def refactor_file(filepath):
    """Refactor a single file to use get_tenant_db()"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    changes = []
    
    # Track if we need to add the tenant_utils import
    needs_tenant_import = False
    has_tenant_import = 'from src.utils.tenant_utils import' in content
    
    # Pattern 1: Replace standalone import of AzureSQLService
    # from src.services.azure_sql_service import AzureSQLService
    if 'from src.services.azure_sql_service import AzureSQLService' in content:
        # Check if it's the only import from that module
        if re.search(r'from src\.services\.azure_sql_service import AzureSQLService\s*$', content, re.MULTILINE):
            content = re.sub(
                r'from src\.services\.azure_sql_service import AzureSQLService\s*\n',
                '',
                content
            )
            needs_tenant_import = True
            changes.append("Removed AzureSQLService import")
    
    # Pattern 2: Replace inline imports
    # from src.services.azure_sql_service import AzureSQLService
    # db = AzureSQLService()
    content = re.sub(
        r'from src\.services\.azure_sql_service import AzureSQLService\s*\n\s*db = AzureSQLService\(\)',
        'from src.utils.tenant_utils import get_tenant_db\n        db = get_tenant_db()',
        content
    )
    if content != original_content:
        changes.append("Replaced inline import+instantiation")
    
    # Pattern 3: Replace db = AzureSQLService() with db = get_tenant_db()
    if 'db = AzureSQLService()' in content:
        content = content.replace('db = AzureSQLService()', 'db = get_tenant_db()')
        needs_tenant_import = True
        changes.append("Replaced db = AzureSQLService()")
    
    # Pattern 4: Replace sql_service = AzureSQLService() at module level
    # This is trickier - we need to make it a function call
    if re.search(r'^sql_service = AzureSQLService\(\)\s*$', content, re.MULTILINE):
        # Replace module-level instantiation with a lazy getter
        content = re.sub(
            r'^sql_service = AzureSQLService\(\)\s*$',
            '# sql_service is now obtained via get_tenant_db() for multi-tenant support\n_sql_service = None\ndef get_sql_service():\n    return get_tenant_db()',
            content,
            flags=re.MULTILINE
        )
        # Also replace uses of sql_service with get_sql_service()
        # But be careful not to replace the definition
        needs_tenant_import = True
        changes.append("Converted module-level sql_service to lazy getter")
    
    # Pattern 5: Replace azure_db = AzureSQLService() 
    if 'azure_db = AzureSQLService()' in content:
        content = content.replace('azure_db = AzureSQLService()', 'azure_db = get_tenant_db()')
        needs_tenant_import = True
        changes.append("Replaced azure_db = AzureSQLService()")
    
    # Pattern 6: Replace azure_sql = AzureSQLService()
    if 'azure_sql = AzureSQLService()' in content:
        content = content.replace('azure_sql = AzureSQLService()', 'azure_sql = get_tenant_db()')
        needs_tenant_import = True
        changes.append("Replaced azure_sql = AzureSQLService()")
    
    # Pattern 7: Replace sql_service = AzureSQLService() (inline, not module level)
    if re.search(r'\s+sql_service = AzureSQLService\(\)', content):
        content = re.sub(r'(\s+)sql_service = AzureSQLService\(\)', r'\1sql_service = get_tenant_db()', content)
        needs_tenant_import = True
        changes.append("Replaced inline sql_service = AzureSQLService()")
    
    # Pattern 8: Replace get_db() functions that return AzureSQLService()
    if 'def get_db():' in content and 'return AzureSQLService()' in content:
        content = re.sub(
            r'def get_db\(\):\s*\n\s*""".*?"""\s*\n\s*return AzureSQLService\(\)',
            'def get_db():\n    """Get database connection"""\n    return get_tenant_db()',
            content,
            flags=re.DOTALL
        )
        needs_tenant_import = True
        changes.append("Updated get_db() to use get_tenant_db()")
    
    # Add the tenant_utils import if needed and not already present
    if needs_tenant_import and not has_tenant_import:
        # Find a good place to add the import (after other imports)
        if 'from src.utils.tenant_utils import get_tenant_schema' in content:
            # Already has tenant_utils import, just add get_tenant_db
            content = content.replace(
                'from src.utils.tenant_utils import get_tenant_schema',
                'from src.utils.tenant_utils import get_tenant_schema, get_tenant_db'
            )
            changes.append("Added get_tenant_db to existing tenant_utils import")
        elif 'from flask_jwt_extended import' in content:
            # Add after flask_jwt_extended import
            content = re.sub(
                r'(from flask_jwt_extended import[^\n]+\n)',
                r'\1from src.utils.tenant_utils import get_tenant_db\n',
                content,
                count=1
            )
            changes.append("Added tenant_utils import after flask_jwt_extended")
        elif 'from flask import' in content:
            # Add after flask import
            content = re.sub(
                r'(from flask import[^\n]+\n)',
                r'\1from src.utils.tenant_utils import get_tenant_db\n',
                content,
                count=1
            )
            changes.append("Added tenant_utils import after flask")
        else:
            # Add at the top after other imports
            lines = content.split('\n')
            import_end = 0
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    import_end = i + 1
            lines.insert(import_end, 'from src.utils.tenant_utils import get_tenant_db')
            content = '\n'.join(lines)
            changes.append("Added tenant_utils import at end of imports")
    
    # Write back if changed
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        return changes
    
    return []

def main():
    """Main function to refactor all route files"""
    print("Starting refactoring...")
    
    total_files = 0
    modified_files = 0
    
    for filepath in ROUTES_DIR.glob('*.py'):
        if filepath.name.startswith('__'):
            continue
        
        total_files += 1
        changes = refactor_file(filepath)
        
        if changes:
            modified_files += 1
            print(f"\n{filepath.name}:")
            for change in changes:
                print(f"  - {change}")
    
    print(f"\n\nSummary:")
    print(f"  Total files scanned: {total_files}")
    print(f"  Files modified: {modified_files}")

if __name__ == '__main__':
    main()
