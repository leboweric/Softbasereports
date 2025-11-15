"""
Knowledge Base API Routes
Manages technical troubleshooting articles for service technicians
Stores data in PostgreSQL (Railway)
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from src.services.postgres_service import get_postgres_db
from src.services.permission_service import PermissionService

logger = logging.getLogger(__name__)

knowledge_base_bp = Blueprint('knowledge_base', __name__)

# Get PostgreSQL service
postgres_db = get_postgres_db()

def is_admin():
    """Check if current user has admin permissions"""
    # RBAC disabled - allow all authenticated users
    return True

@knowledge_base_bp.route('/api/knowledge-base/articles', methods=['GET'])
@jwt_required()
def get_articles():
    """Get all knowledge base articles with optional filtering"""
    try:
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        equipment_make = request.args.get('equipment_make', '')
        
        # Build query with filters
        query = """
            SELECT 
                id,
                title,
                equipment_make,
                equipment_model,
                issue_category,
                symptoms,
                root_cause,
                solution,
                related_wo_numbers,
                image_urls,
                created_by,
                created_date,
                updated_by,
                updated_date,
                view_count
            FROM knowledge_base
            WHERE 1=1
        """
        params = []
        
        # Add search filter
        if search:
            query += """ AND (
                title ILIKE %s OR
                symptoms ILIKE %s OR
                root_cause ILIKE %s OR
                solution ILIKE %s OR
                equipment_make ILIKE %s OR
                equipment_model ILIKE %s
            )"""
            search_param = f'%{search}%'
            params.extend([search_param] * 6)
        
        # Add category filter
        if category:
            query += " AND issue_category = %s"
            params.append(category)
        
        # Add equipment make filter
        if equipment_make:
            query += " AND equipment_make = %s"
            params.append(equipment_make)
        
        query += " ORDER BY created_date DESC"
        
        articles = postgres_db.execute_query(query, params if params else None)
        
        # Convert to camelCase for frontend
        result = []
        for article in articles:
            result.append({
                'id': article['id'],
                'title': article['title'],
                'equipmentMake': article['equipment_make'],
                'equipmentModel': article['equipment_model'],
                'issueCategory': article['issue_category'],
                'symptoms': article['symptoms'],
                'rootCause': article['root_cause'],
                'solution': article['solution'],
                'relatedWONumbers': article['related_wo_numbers'],
                'imageUrls': article['image_urls'].split(',') if article['image_urls'] else [],
                'createdBy': article['created_by'],
                'createdDate': article['created_date'].isoformat() if article['created_date'] else None,
                'updatedBy': article['updated_by'],
                'updatedDate': article['updated_date'].isoformat() if article['updated_date'] else None,
                'viewCount': article['view_count'] or 0
            })
        
        return jsonify({'articles': result}), 200
        
    except Exception as e:
        logger.error(f"Error fetching articles: {str(e)}")
        return jsonify({'error': str(e)}), 500

@knowledge_base_bp.route('/api/knowledge-base/articles/<int:article_id>', methods=['GET'])
@jwt_required()
def get_article(article_id):
    """Get a single article and increment view count"""
    try:
        # Increment view count
        update_query = """
            UPDATE knowledge_base 
            SET view_count = view_count + 1
            WHERE id = %s
        """
        postgres_db.execute_update(update_query, [article_id])
        
        # Get article
        query = """
            SELECT 
                id,
                title,
                equipment_make,
                equipment_model,
                issue_category,
                symptoms,
                root_cause,
                solution,
                related_wo_numbers,
                image_urls,
                created_by,
                created_date,
                updated_by,
                updated_date,
                view_count
            FROM knowledge_base
            WHERE id = %s
        """
        
        articles = postgres_db.execute_query(query, [article_id])
        
        if not articles:
            return jsonify({'error': 'Article not found'}), 404
        
        article = articles[0]
        result = {
            'id': article['id'],
            'title': article['title'],
            'equipmentMake': article['equipment_make'],
            'equipmentModel': article['equipment_model'],
            'issueCategory': article['issue_category'],
            'symptoms': article['symptoms'],
            'rootCause': article['root_cause'],
            'solution': article['solution'],
            'relatedWONumbers': article['related_wo_numbers'],
            'imageUrls': article['image_urls'].split(',') if article['image_urls'] else [],
            'createdBy': article['created_by'],
            'createdDate': article['created_date'].isoformat() if article['created_date'] else None,
            'updatedBy': article['updated_by'],
            'updatedDate': article['updated_date'].isoformat() if article['updated_date'] else None,
            'viewCount': article['view_count'] or 0
        }
        
        return jsonify({'article': result}), 200
        
    except Exception as e:
        logger.error(f"Error fetching article: {str(e)}")
        return jsonify({'error': str(e)}), 500

@knowledge_base_bp.route('/api/knowledge-base/articles', methods=['POST'])
@jwt_required()
def create_article():
    """Create a new knowledge base article"""
    try:
        
        data = request.json
        current_user = get_jwt_identity()
        
        # Validate required fields
        required_fields = ['title', 'issueCategory', 'symptoms', 'rootCause', 'solution']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        query = """
            INSERT INTO knowledge_base (
                title, equipment_make, equipment_model, issue_category,
                symptoms, root_cause, solution, related_wo_numbers,
                image_urls, created_by
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """
        
        params = [
            data['title'],
            data.get('equipmentMake', ''),
            data.get('equipmentModel', ''),
            data['issueCategory'],
            data['symptoms'],
            data['rootCause'],
            data['solution'],
            data.get('relatedWONumbers', ''),
            ','.join(data.get('imageUrls', [])),
            current_user
        ]
        
        result = postgres_db.execute_insert_returning(query, params)
        
        if result:
            return jsonify({
                'message': 'Article created successfully',
                'id': result['id']
            }), 201
        else:
            return jsonify({'error': 'Failed to create article'}), 500
        
    except Exception as e:
        logger.error(f"Error creating article: {str(e)}")
        return jsonify({'error': str(e)}), 500

@knowledge_base_bp.route('/api/knowledge-base/articles/<int:article_id>', methods=['PUT'])
@jwt_required()
def update_article(article_id):
    """Update an existing article"""
    try:
        
        data = request.json
        current_user = get_jwt_identity()
        
        query = """
            UPDATE knowledge_base SET
                title = %s,
                equipment_make = %s,
                equipment_model = %s,
                issue_category = %s,
                symptoms = %s,
                root_cause = %s,
                solution = %s,
                related_wo_numbers = %s,
                image_urls = %s,
                updated_by = %s,
                updated_date = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        params = [
            data.get('title'),
            data.get('equipmentMake', ''),
            data.get('equipmentModel', ''),
            data.get('issueCategory'),
            data.get('symptoms'),
            data.get('rootCause'),
            data.get('solution'),
            data.get('relatedWONumbers', ''),
            ','.join(data.get('imageUrls', [])),
            current_user,
            article_id
        ]
        
        rows_affected = postgres_db.execute_update(query, params)
        
        if rows_affected > 0:
            return jsonify({'message': 'Article updated successfully'}), 200
        else:
            return jsonify({'error': 'Article not found'}), 404
        
    except Exception as e:
        logger.error(f"Error updating article: {str(e)}")
        return jsonify({'error': str(e)}), 500

@knowledge_base_bp.route('/api/knowledge-base/articles/<int:article_id>', methods=['DELETE'])
@jwt_required()
def delete_article(article_id):
    """Delete an article"""
    try:
        
        query = "DELETE FROM knowledge_base WHERE id = %s"
        rows_affected = postgres_db.execute_update(query, [article_id])
        
        if rows_affected > 0:
            return jsonify({'message': 'Article deleted successfully'}), 200
        else:
            return jsonify({'error': 'Article not found'}), 404
        
    except Exception as e:
        logger.error(f"Error deleting article: {str(e)}")
        return jsonify({'error': str(e)}), 500

@knowledge_base_bp.route('/api/knowledge-base/categories', methods=['GET'])
@jwt_required()
def get_categories():
    """Get all unique issue categories"""
    try:
        query = """
            SELECT DISTINCT issue_category 
            FROM knowledge_base 
            WHERE issue_category IS NOT NULL AND issue_category != ''
            ORDER BY issue_category
        """
        
        categories = postgres_db.execute_query(query)
        result = [cat['issue_category'] for cat in categories] if categories else []
        return jsonify({'categories': result}), 200
        
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        return jsonify({'error': str(e)}), 500

@knowledge_base_bp.route('/api/knowledge-base/equipment-makes', methods=['GET'])
@jwt_required()
def get_equipment_makes():
    """Get all unique equipment makes"""
    try:
        query = """
            SELECT DISTINCT equipment_make 
            FROM knowledge_base 
            WHERE equipment_make IS NOT NULL AND equipment_make != ''
            ORDER BY equipment_make
        """
        
        makes = postgres_db.execute_query(query)
        result = [make['equipment_make'] for make in makes] if makes else []
        return jsonify({'makes': result}), 200
        
    except Exception as e:
        logger.error(f"Error fetching equipment makes: {str(e)}")
        return jsonify({'error': str(e)}), 500

@knowledge_base_bp.route('/api/knowledge-base/articles/<int:article_id>/attachments', methods=['POST'])
@jwt_required()
def upload_attachment(article_id):
    """Upload a file attachment to an article"""
    try:
        current_user = get_jwt_identity()
        
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read file data
        file_data = file.read()
        file_size = len(file_data)
        
        # Limit file size to 10MB
        if file_size > 10 * 1024 * 1024:
            return jsonify({'error': 'File size exceeds 10MB limit'}), 400
        
        # Insert attachment
        query = """
            INSERT INTO kb_attachments (
                article_id, filename, file_data, file_size, mime_type, uploaded_by
            ) VALUES (
                %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """
        
        params = [
            article_id,
            file.filename,
            file_data,
            file_size,
            file.content_type or 'application/octet-stream',
            current_user
        ]
        
        result = postgres_db.execute_insert_returning(query, params)
        
        if result:
            return jsonify({
                'message': 'Attachment uploaded successfully',
                'id': result['id'],
                'filename': file.filename,
                'size': file_size
            }), 201
        else:
            return jsonify({'error': 'Failed to upload attachment'}), 500
        
    except Exception as e:
        logger.error(f"Error uploading attachment: {str(e)}")
        return jsonify({'error': str(e)}), 500

@knowledge_base_bp.route('/api/knowledge-base/articles/<int:article_id>/attachments', methods=['GET'])
@jwt_required()
def get_attachments(article_id):
    """Get all attachments for an article (metadata only, no file data)"""
    try:
        query = """
            SELECT 
                id, filename, file_size, mime_type, uploaded_by, uploaded_date
            FROM kb_attachments
            WHERE article_id = %s
            ORDER BY uploaded_date DESC
        """
        
        attachments = postgres_db.execute_query(query, [article_id])
        
        result = []
        for att in attachments:
            result.append({
                'id': att['id'],
                'filename': att['filename'],
                'fileSize': att['file_size'],
                'mimeType': att['mime_type'],
                'uploadedBy': att['uploaded_by'],
                'uploadedDate': att['uploaded_date'].isoformat() if att['uploaded_date'] else None
            })
        
        return jsonify({'attachments': result}), 200
        
    except Exception as e:
        logger.error(f"Error fetching attachments: {str(e)}")
        return jsonify({'error': str(e)}), 500

@knowledge_base_bp.route('/api/knowledge-base/attachments/<int:attachment_id>', methods=['GET'])
@jwt_required()
def download_attachment(attachment_id):
    """Download a specific attachment"""
    try:
        from flask import send_file
        import io
        
        query = """
            SELECT filename, file_data, mime_type
            FROM kb_attachments
            WHERE id = %s
        """
        
        attachments = postgres_db.execute_query(query, [attachment_id])
        
        if not attachments:
            return jsonify({'error': 'Attachment not found'}), 404
        
        attachment = attachments[0]
        
        # Create file-like object from binary data
        file_data = io.BytesIO(attachment['file_data'])
        
        return send_file(
            file_data,
            mimetype=attachment['mime_type'],
            as_attachment=True,
            download_name=attachment['filename']
        )
        
    except Exception as e:
        logger.error(f"Error downloading attachment: {str(e)}")
        return jsonify({'error': str(e)}), 500

@knowledge_base_bp.route('/api/knowledge-base/attachments/<int:attachment_id>', methods=['DELETE'])
@jwt_required()
def delete_attachment(attachment_id):
    """Delete an attachment"""
    try:
        query = "DELETE FROM kb_attachments WHERE id = %s"
        rows_affected = postgres_db.execute_update(query, [attachment_id])
        
        if rows_affected > 0:
            return jsonify({'message': 'Attachment deleted successfully'}), 200
        else:
            return jsonify({'error': 'Attachment not found'}), 404
        
    except Exception as e:
        logger.error(f"Error deleting attachment: {str(e)}")
        return jsonify({'error': str(e)}), 500
