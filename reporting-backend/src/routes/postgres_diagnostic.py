from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from src.services.postgres_service import get_postgres_db
import os
import logging

logger = logging.getLogger(__name__)

postgres_diagnostic_bp = Blueprint('postgres_diagnostic', __name__, url_prefix='/api/postgres')

@postgres_diagnostic_bp.route('/diagnostic', methods=['GET'])
@jwt_required()
def postgres_diagnostic():
    """Diagnostic endpoint to check PostgreSQL connection and create tables"""
    try:
        results = {
            'env_vars_found': {},
            'connection_status': 'unknown',
            'tables_created': False,
            'existing_tables': [],
            'error': None
        }
        
        # Check environment variables
        results['env_vars_found']['POSTGRES_URL'] = 'POSTGRES_URL' in os.environ
        results['env_vars_found']['DATABASE_URL'] = 'DATABASE_URL' in os.environ
        results['env_vars_found']['POSTGRES_PRIVATE_URL'] = 'POSTGRES_PRIVATE_URL' in os.environ
        
        # Log which variable we're using (without exposing the actual value)
        if os.environ.get('POSTGRES_URL'):
            logger.info("Using POSTGRES_URL for connection")
        elif os.environ.get('DATABASE_URL'):
            logger.info("Using DATABASE_URL for connection")
        elif os.environ.get('POSTGRES_PRIVATE_URL'):
            logger.info("Using POSTGRES_PRIVATE_URL for connection")
        else:
            logger.warning("No PostgreSQL connection string found in environment")
            results['error'] = "No PostgreSQL connection string found in environment variables"
            return jsonify(results), 200
        
        # Try to get the database connection
        db = get_postgres_db()
        
        if not db:
            results['connection_status'] = 'failed'
            results['error'] = 'Could not initialize database connection'
            return jsonify(results), 200
        
        # Check if we can connect
        try:
            test_query = "SELECT version()"
            version_result = db.execute_query(test_query)
            if version_result:
                results['connection_status'] = 'connected'
                results['postgres_version'] = version_result[0].get('version', 'unknown')
            else:
                results['connection_status'] = 'failed'
                results['error'] = 'Could not execute test query'
        except Exception as e:
            results['connection_status'] = 'failed'
            results['error'] = f'Connection test failed: {str(e)}'
            return jsonify(results), 200
        
        # Check existing tables
        try:
            tables_query = """
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY tablename
            """
            tables_result = db.execute_query(tables_query)
            if tables_result:
                results['existing_tables'] = [t['tablename'] for t in tables_result]
        except Exception as e:
            results['error'] = f'Could not list tables: {str(e)}'
        
        # Try to create the work_order_notes table
        try:
            if db.create_tables():
                results['tables_created'] = True
                results['message'] = 'Tables created successfully'
                
                # Verify the table was created
                verify_query = """
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'work_order_notes'
                    AND table_schema = 'public'
                    ORDER BY ordinal_position
                """
                columns = db.execute_query(verify_query)
                if columns:
                    results['work_order_notes_columns'] = [
                        {'name': col['column_name'], 'type': col['data_type']} 
                        for col in columns
                    ]
            else:
                results['tables_created'] = False
                results['error'] = 'Failed to create tables'
        except Exception as e:
            results['tables_created'] = False
            results['error'] = f'Table creation failed: {str(e)}'
        
        return jsonify(results), 200
        
    except Exception as e:
        logger.error(f"Diagnostic error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@postgres_diagnostic_bp.route('/force-create-tables', methods=['POST'])
@jwt_required()
def force_create_tables():
    """Force create the work_order_notes table"""
    try:
        db = get_postgres_db()
        
        if not db:
            return jsonify({'error': 'Could not connect to database'}), 500
        
        # Force create the table
        create_query = """
        DROP TABLE IF EXISTS work_order_notes CASCADE;
        
        CREATE TABLE work_order_notes (
            id SERIAL PRIMARY KEY,
            wo_number VARCHAR(50) NOT NULL,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(100),
            updated_by VARCHAR(100)
        );
        
        CREATE INDEX IF NOT EXISTS idx_wo_number ON work_order_notes(wo_number);
        """
        
        with db.get_connection() as conn:
            if conn:
                with conn.cursor() as cursor:
                    cursor.execute(create_query)
                    conn.commit()
                    
                    # Verify it was created
                    cursor.execute("""
                        SELECT COUNT(*) as count 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'work_order_notes'
                    """)
                    result = cursor.fetchone()
                    
                    if result and result['count'] > 0:
                        return jsonify({
                            'success': True,
                            'message': 'Table created successfully'
                        }), 200
                    else:
                        return jsonify({
                            'success': False,
                            'error': 'Table creation could not be verified'
                        }), 500
            else:
                return jsonify({'error': 'No database connection'}), 500
                
    except Exception as e:
        logger.error(f"Force create error: {str(e)}")
        return jsonify({'error': str(e)}), 500