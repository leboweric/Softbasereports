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
                kb.id,
                kb.title,
                kb.equipment_make,
                kb.equipment_model,
                kb.issue_category,
                kb.symptoms,
                kb.root_cause,
                kb.solution,
                kb.related_wo_numbers,
                kb.image_urls,
                kb.created_by,
                kb.created_date,
                kb.updated_by,
                kb.updated_date,
                kb.view_count,
                COUNT(att.id) as attachment_count
            FROM knowledge_base kb
            LEFT JOIN kb_attachments att ON kb.id = att.article_id
            WHERE 1=1
        """
        params = []
        
        # Add search filter
        if search:
            query += """ AND (
                kb.title ILIKE %s OR
                kb.symptoms ILIKE %s OR
                kb.root_cause ILIKE %s OR
                kb.solution ILIKE %s OR
                kb.equipment_make ILIKE %s OR
                kb.equipment_model ILIKE %s
            )"""
            search_param = f'%{search}%'
            params.extend([search_param] * 6)
        
        # Add category filter
        if category:
            query += " AND kb.issue_category = %s"
            params.append(category)
        
        # Add equipment make filter
        if equipment_make:
            query += " AND kb.equipment_make = %s"
            params.append(equipment_make)
        
        query += """
            GROUP BY kb.id, kb.title, kb.equipment_make, kb.equipment_model, 
                     kb.issue_category, kb.symptoms, kb.root_cause, kb.solution, 
                     kb.related_wo_numbers, kb.image_urls, kb.created_by, kb.created_date, 
                     kb.updated_by, kb.updated_date, kb.view_count
            ORDER BY kb.created_date DESC
        """
        
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
                'viewCount': article['view_count'] or 0,
                'attachmentCount': article['attachment_count'] or 0
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
    """Get all unique equipment makes from Softbase Equipment table"""
    try:
        from src.services.azure_sql_service import AzureSQLService
        
        azure_db = AzureSQLService()
        query = """
            SELECT DISTINCT Make
            FROM ben002.Equipment
            WHERE Make IS NOT NULL AND Make != ''
            ORDER BY Make
        """
        
        results = azure_db.execute_query(query)
        makes = [row['Make'] for row in results] if results else []
        return jsonify({'makes': makes}), 200
        
    except Exception as e:
        logger.error(f"Error fetching equipment makes: {str(e)}")
        return jsonify({'error': str(e)}), 500

@knowledge_base_bp.route('/api/knowledge-base/equipment-models', methods=['GET'])
@jwt_required()
def get_equipment_models():
    """Get all unique equipment models from Softbase Equipment table, optionally filtered by make"""
    try:
        from src.services.azure_sql_service import AzureSQLService
        
        make = request.args.get('make', '')
        azure_db = AzureSQLService()
        
        if make:
            # Filter models by make
            query = """
                SELECT DISTINCT Model
                FROM ben002.Equipment
                WHERE Make = %s
                  AND Model IS NOT NULL 
                  AND Model != ''
                ORDER BY Model
            """
            results = azure_db.execute_query(query, [make])
        else:
            # Get all models
            query = """
                SELECT DISTINCT Model
                FROM ben002.Equipment
                WHERE Model IS NOT NULL AND Model != ''
                ORDER BY Model
            """
            results = azure_db.execute_query(query)
        
        models = [row['Model'] for row in results] if results else []
        return jsonify({'models': models}), 200
        
    except Exception as e:
        logger.error(f"Error fetching equipment models: {str(e)}")
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

@knowledge_base_bp.route('/api/knowledge-base/work-orders/search', methods=['GET'])
@jwt_required()
def search_work_orders():
    """Search work orders by keywords in descriptions and notes"""
    try:
        from src.services.azure_sql_service import get_azure_sql_service
        azure_sql = get_azure_sql_service()
        
        # Get search parameters
        search = request.args.get('search', '')
        equipment_make = request.args.get('equipment_make', '')
        customer = request.args.get('customer', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        limit = int(request.args.get('limit', 100))
        
        # Build query
        query = """
            SELECT TOP (@limit)
                wo.WONumber,
                wo.Customer,
                wo.Make,
                wo.Model,
                wo.SerialNumber,
                wo.UnitNumber,
                wo.Description,
                wo.Resolution,
                wo.DateClosed,
                wo.TechnicianName,
                wo.Status
            FROM ben002.WO wo
            WHERE 1=1
        """
        
        params = {'limit': limit}
        
        # Add search filter for Description and Resolution
        if search:
            query += """
                AND (
                    wo.Description LIKE @search OR
                    wo.Resolution LIKE @search
                )
            """
            params['search'] = f'%{search}%'
        
        # Add equipment make filter
        if equipment_make:
            query += " AND wo.Make = @equipment_make"
            params['equipment_make'] = equipment_make
        
        # Add customer filter
        if customer:
            query += " AND wo.Customer LIKE @customer"
            params['customer'] = f'%{customer}%'
        
        # Add date range filters
        if date_from:
            query += " AND wo.DateClosed >= @date_from"
            params['date_from'] = date_from
        
        if date_to:
            query += " AND wo.DateClosed <= @date_to"
            params['date_to'] = date_to
        
        # Only show closed work orders with descriptions
        query += """
            AND wo.Status = 'Closed'
            AND (wo.Description IS NOT NULL OR wo.Resolution IS NOT NULL)
            ORDER BY wo.DateClosed DESC
        """
        
        work_orders = azure_sql.execute_query(query, params)
        
        # Convert to camelCase for frontend
        result = []
        for wo in work_orders:
            result.append({
                'woNumber': wo['WONumber'],
                'customer': wo['Customer'],
                'make': wo['Make'],
                'model': wo['Model'],
                'serialNumber': wo['SerialNumber'],
                'unitNumber': wo['UnitNumber'],
                'description': wo['Description'],
                'resolution': wo['Resolution'],
                'dateClosed': wo['DateClosed'].isoformat() if wo['DateClosed'] else None,
                'technicianName': wo['TechnicianName'],
                'status': wo['Status']
            })
        
        return jsonify({
            'workOrders': result,
            'count': len(result)
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching work orders: {str(e)}")
        return jsonify({'error': str(e)}), 500
