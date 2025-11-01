#!/usr/bin/env python3
"""
Migration script to add multi-tenant fields to the organization table.
Run this script to update your database schema.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import app
from src.models.user import db
import sqlite3

def migrate():
    """Add new multi-tenant fields to organization table"""
    
    # Get the database path from the app config
    with app.app_context():
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        print(f"📊 Migrating database: {db_path}")
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Check which columns already exist
            cursor.execute("PRAGMA table_info(organization)")
            existing_columns = [col[1] for col in cursor.fetchall()]
            print(f"✅ Existing columns: {existing_columns}")
            
            # Add new columns if they don't exist
            new_columns = [
                ("platform_type", "VARCHAR(20)"),
                ("db_server", "VARCHAR(255)"),
                ("db_name", "VARCHAR(255)"),
                ("db_username", "VARCHAR(255)"),
                ("db_password_encrypted", "TEXT"),
                ("subscription_tier", "VARCHAR(50) DEFAULT 'basic'"),
                ("max_users", "INTEGER DEFAULT 5")
            ]
            
            for col_name, col_type in new_columns:
                if col_name not in existing_columns:
                    try:
                        cursor.execute(f"ALTER TABLE organization ADD COLUMN {col_name} {col_type}")
                        print(f"✅ Added column: {col_name}")
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" in str(e):
                            print(f"⚠️  Column {col_name} already exists, skipping...")
                        else:
                            raise
                else:
                    print(f"⚠️  Column {col_name} already exists, skipping...")
            
            # Commit the changes
            conn.commit()
            print("\n✅ Migration completed successfully!")
            
            # Verify the schema
            cursor.execute("PRAGMA table_info(organization)")
            final_columns = cursor.fetchall()
            print("\n📋 Final table structure:")
            for col in final_columns:
                print(f"  - {col[1]}: {col[2]}")
                
        except Exception as e:
            conn.rollback()
            print(f"\n❌ Migration failed: {e}")
            raise
        finally:
            conn.close()

if __name__ == "__main__":
    migrate()