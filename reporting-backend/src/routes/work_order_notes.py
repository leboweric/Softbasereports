from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.postgres_service import get_postgres_db
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

notes_bp = Blueprint('notes', __name__, url_prefix='/api/work-orders')

@notes_bp.route('/notes', methods=['GET'])
@jwt_required()
def get_notes():
    """Get all notes or notes for specific work orders"""
    try:
        db = get_postgres_db()
        
        # Check if specific work orders are requested
        wo_numbers = request.args.get('wo_numbers')
        
        if wo_numbers:
            # Get notes for specific work orders
            wo_list = wo_numbers.split(',')
            placeholders = ','.join(['%s'] * len(wo_list))
            query = f"""
                SELECT id, wo_number, note, created_at, updated_at, created_by, updated_by
                FROM work_order_notes
                WHERE wo_number IN ({placeholders})
                ORDER BY updated_at DESC
            """
            notes = db.execute_query(query, wo_list)
        else:
            # Get all notes
            query = """
                SELECT id, wo_number, note, created_at, updated_at, created_by, updated_by
                FROM work_order_notes
                ORDER BY updated_at DESC
                LIMIT 1000
            """
            notes = db.execute_query(query)
        
        # Convert datetime objects to strings
        for note in notes:
            if note.get('created_at'):
                note['created_at'] = note['created_at'].isoformat()
            if note.get('updated_at'):
                note['updated_at'] = note['updated_at'].isoformat()
        
        return jsonify(notes), 200
        
    except Exception as e:
        logger.error(f"Error fetching notes: {str(e)}")
        return jsonify({'error': 'Failed to fetch notes'}), 500

@notes_bp.route('/notes/<wo_number>', methods=['GET'])
@jwt_required()
def get_note_by_wo(wo_number):
    """Get note for a specific work order"""
    try:
        db = get_postgres_db()
        
        query = """
            SELECT id, wo_number, note, created_at, updated_at, created_by, updated_by
            FROM work_order_notes
            WHERE wo_number = %s
            ORDER BY updated_at DESC
            LIMIT 1
        """
        
        result = db.execute_query(query, [wo_number])
        
        if result:
            note = result[0]
            if note.get('created_at'):
                note['created_at'] = note['created_at'].isoformat()
            if note.get('updated_at'):
                note['updated_at'] = note['updated_at'].isoformat()
            return jsonify(note), 200
        else:
            return jsonify(None), 200
            
    except Exception as e:
        logger.error(f"Error fetching note for WO {wo_number}: {str(e)}")
        return jsonify({'error': 'Failed to fetch note'}), 500

@notes_bp.route('/notes', methods=['POST'])
@jwt_required()
def create_or_update_note():
    """Create or update a note for a work order"""
    try:
        db = get_postgres_db()
        data = request.get_json()
        
        wo_number = data.get('wo_number')
        note_text = data.get('note', '')
        user = get_jwt_identity()
        
        if not wo_number:
            return jsonify({'error': 'Work order number is required'}), 400
        
        # Check if note already exists
        existing = db.execute_query(
            "SELECT id FROM work_order_notes WHERE wo_number = %s",
            [wo_number]
        )
        
        if existing:
            # Update existing note
            query = """
                UPDATE work_order_notes
                SET note = %s, updated_at = CURRENT_TIMESTAMP, updated_by = %s
                WHERE wo_number = %s
                RETURNING id, wo_number, note, created_at, updated_at, created_by, updated_by
            """
            result = db.execute_insert_returning(query, [note_text, user, wo_number])
        else:
            # Create new note
            query = """
                INSERT INTO work_order_notes (wo_number, note, created_by, updated_by)
                VALUES (%s, %s, %s, %s)
                RETURNING id, wo_number, note, created_at, updated_at, created_by, updated_by
            """
            result = db.execute_insert_returning(query, [wo_number, note_text, user, user])
        
        if result:
            if result.get('created_at'):
                result['created_at'] = result['created_at'].isoformat()
            if result.get('updated_at'):
                result['updated_at'] = result['updated_at'].isoformat()
            return jsonify(result), 200
        else:
            return jsonify({'error': 'Failed to save note'}), 500
            
    except Exception as e:
        logger.error(f"Error creating/updating note: {str(e)}")
        return jsonify({'error': 'Failed to save note'}), 500

@notes_bp.route('/notes/<int:note_id>', methods=['PUT'])
@jwt_required()
def update_note(note_id):
    """Update a specific note by ID"""
    try:
        db = get_postgres_db()
        data = request.get_json()
        
        note_text = data.get('note', '')
        user = get_jwt_identity()
        
        query = """
            UPDATE work_order_notes
            SET note = %s, updated_at = CURRENT_TIMESTAMP, updated_by = %s
            WHERE id = %s
            RETURNING id, wo_number, note, created_at, updated_at, created_by, updated_by
        """
        
        result = db.execute_insert_returning(query, [note_text, user, note_id])
        
        if result:
            if result.get('created_at'):
                result['created_at'] = result['created_at'].isoformat()
            if result.get('updated_at'):
                result['updated_at'] = result['updated_at'].isoformat()
            return jsonify(result), 200
        else:
            return jsonify({'error': 'Note not found'}), 404
            
    except Exception as e:
        logger.error(f"Error updating note {note_id}: {str(e)}")
        return jsonify({'error': 'Failed to update note'}), 500

@notes_bp.route('/notes/<int:note_id>', methods=['DELETE'])
@jwt_required()
def delete_note(note_id):
    """Delete a specific note by ID"""
    try:
        db = get_postgres_db()
        
        query = "DELETE FROM work_order_notes WHERE id = %s"
        rowcount = db.execute_update(query, [note_id])
        
        if rowcount > 0:
            return jsonify({'message': 'Note deleted successfully'}), 200
        else:
            return jsonify({'error': 'Note not found'}), 404
            
    except Exception as e:
        logger.error(f"Error deleting note {note_id}: {str(e)}")
        return jsonify({'error': 'Failed to delete note'}), 500

@notes_bp.route('/notes/batch', methods=['POST'])
@jwt_required()
def get_notes_batch():
    """Get notes for multiple work orders in a single request"""
    try:
        db = get_postgres_db()
        data = request.get_json()
        
        wo_numbers = data.get('wo_numbers', [])
        
        if not wo_numbers:
            return jsonify({}), 200
        
        placeholders = ','.join(['%s'] * len(wo_numbers))
        query = f"""
            SELECT wo_number, note, updated_at, updated_by
            FROM work_order_notes
            WHERE wo_number IN ({placeholders})
        """
        
        results = db.execute_query(query, wo_numbers)
        
        # Convert to dict keyed by wo_number for easy lookup
        notes_dict = {}
        for row in results:
            notes_dict[row['wo_number']] = {
                'note': row['note'],
                'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None,
                'updated_by': row['updated_by']
            }
        
        return jsonify(notes_dict), 200
        
    except Exception as e:
        logger.error(f"Error fetching batch notes: {str(e)}")
        return jsonify({'error': 'Failed to fetch notes'}), 500