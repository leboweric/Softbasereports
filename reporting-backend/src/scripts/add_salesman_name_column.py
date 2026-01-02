"""
Script to add salesman_name column to users table.
This should be run once to migrate existing database.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Flask
from src.models.user import db

def add_salesman_name_column():
    """Add salesman_name column to users table if it doesn't exist"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        # Check if column exists
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('user')]
        
        if 'salesman_name' not in columns:
            print("Adding salesman_name column to user table...")
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE "user" ADD COLUMN salesman_name VARCHAR(100)'))
                conn.commit()
            print("✅ Column added successfully!")
        else:
            print("✅ salesman_name column already exists")

if __name__ == '__main__':
    add_salesman_name_column()
