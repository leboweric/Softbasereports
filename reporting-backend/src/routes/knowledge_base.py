from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.azure_sql_service import AzureSQLService
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

knowledge_base_bp = Blueprint('knowledge_base', __name__)

@knowledge_base_bp.route('/api/knowledge-base/articles', methods=['GET'])
@jwt_required()
def get_articles():
    """
    Get all knowledge base articles with optional search and filtering.
    """
    try:
        db = AzureSQLService()
        
        # Get query parameters
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        equipment_make = request.args.get('equipment_make', '')
        
        # Build query with filters
        query = """
        SELECT 
            Id,
            Title,
            EquipmentMake,
            EquipmentModel,
            IssueCategory,
            Symptoms,
            RootCause,
            Solution,
            RelatedWONumbers,
            ImageUrls,
            CreatedBy,
            CreatedDate,
            UpdatedBy,
            UpdatedDate,
            ViewCount
        FROM ben002.KnowledgeBase
        WHERE 1=1
        """
        
        params = []
        
        # Add search filter (searches across multiple fields)
        if search:
            query += """
            AND (
                Title LIKE %s
                OR Symptoms LIKE %s
                OR RootCause LIKE %s
                OR Solution LIKE %s
                OR EquipmentMake LIKE %s
                OR EquipmentModel LIKE %s
            )
            """
            search_param = f'%{search}%'
            params.extend([search_param] * 6)
        
        # Add category filter
        if category:
            query += " AND IssueCategory = %s"
            params.append(category)
        
        # Add equipment make filter
        if equipment_make:
            query += " AND EquipmentMake = %s"
            params.append(equipment_make)
        
        query += " ORDER BY UpdatedDate DESC, CreatedDate DESC"
        
        results = db.execute_query(query, params if params else None)
        
        if not results:
            return jsonify({'articles': []})
        
        articles = []
        for row in results:
            articles.append({
                'id': row['Id'],
                'title': row['Title'],
                'equipmentMake': row['EquipmentMake'],
                'equipmentModel': row['EquipmentModel'],
                'issueCategory': row['IssueCategory'],
                'symptoms': row['Symptoms'],
                'rootCause': row['RootCause'],
                'solution': row['Solution'],
                'relatedWONumbers': row['RelatedWONumbers'],
                'imageUrls': row['ImageUrls'].split(',') if row['ImageUrls'] else [],
                'createdBy': row['CreatedBy'],
                'createdDate': row['CreatedDate'].isoformat() if row['CreatedDate'] else None,
                'updatedBy': row['UpdatedBy'],
                'updatedDate': row['UpdatedDate'].isoformat() if row['UpdatedDate'] else None,
                'viewCount': row['ViewCount'] or 0
            })
        
        return jsonify({'articles': articles})
        
    except Exception as e:
        logger.error(f"Failed to fetch knowledge base articles: {str(e)}")
        return jsonify({'error': str(e)}), 500


@knowledge_base_bp.route('/api/knowledge-base/articles/<int:article_id>', methods=['GET'])
@jwt_required()
def get_article(article_id):
    """
    Get a single knowledge base article by ID and increment view count.
    """
    try:
        db = AzureSQLService()
        
        # Get article
        query = """
        SELECT 
            Id,
            Title,
            EquipmentMake,
            EquipmentModel,
            IssueCategory,
            Symptoms,
            RootCause,
            Solution,
            RelatedWONumbers,
            ImageUrls,
            CreatedBy,
            CreatedDate,
            UpdatedBy,
            UpdatedDate,
            ViewCount
        FROM ben002.KnowledgeBase
        WHERE Id = %s
        """
        
        results = db.execute_query(query, [article_id])
        
        if not results:
            return jsonify({'error': 'Article not found'}), 404
        
        row = results[0]
        
        # Increment view count
        update_query = """
        UPDATE ben002.KnowledgeBase
        SET ViewCount = ISNULL(ViewCount, 0) + 1
        WHERE Id = %s
        """
        db.execute_query(update_query, [article_id])
        
        article = {
            'id': row['Id'],
            'title': row['Title'],
            'equipmentMake': row['EquipmentMake'],
            'equipmentModel': row['EquipmentModel'],
            'issueCategory': row['IssueCategory'],
            'symptoms': row['Symptoms'],
            'rootCause': row['RootCause'],
            'solution': row['Solution'],
            'relatedWONumbers': row['RelatedWONumbers'],
            'imageUrls': row['ImageUrls'].split(',') if row['ImageUrls'] else [],
            'createdBy': row['CreatedBy'],
            'createdDate': row['CreatedDate'].isoformat() if row['CreatedDate'] else None,
            'updatedBy': row['UpdatedBy'],
            'updatedDate': row['UpdatedDate'].isoformat() if row['UpdatedDate'] else None,
            'viewCount': (row['ViewCount'] or 0) + 1
        }
        
        return jsonify({'article': article})
        
    except Exception as e:
        logger.error(f"Failed to fetch article {article_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@knowledge_base_bp.route('/api/knowledge-base/articles', methods=['POST'])
@jwt_required()
def create_article():
    """
    Create a new knowledge base article (admin only).
    """
    try:
        current_user = get_jwt_identity()
        data = request.json
        
        # Validate required fields
        required_fields = ['title', 'symptoms', 'rootCause', 'solution', 'issueCategory']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        db = AzureSQLService()
        
        # Insert article
        query = """
        INSERT INTO ben002.KnowledgeBase (
            Title,
            EquipmentMake,
            EquipmentModel,
            IssueCategory,
            Symptoms,
            RootCause,
            Solution,
            RelatedWONumbers,
            ImageUrls,
            CreatedBy,
            CreatedDate,
            ViewCount
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, GETDATE(), 0);
        SELECT SCOPE_IDENTITY() as Id;
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
        
        result = db.execute_query(query, params)
        
        if result:
            new_id = int(result[0]['Id'])
            return jsonify({
                'message': 'Article created successfully',
                'id': new_id
            }), 201
        else:
            return jsonify({'error': 'Failed to create article'}), 500
        
    except Exception as e:
        logger.error(f"Failed to create article: {str(e)}")
        return jsonify({'error': str(e)}), 500


@knowledge_base_bp.route('/api/knowledge-base/articles/<int:article_id>', methods=['PUT'])
@jwt_required()
def update_article(article_id):
    """
    Update an existing knowledge base article (admin only).
    """
    try:
        current_user = get_jwt_identity()
        data = request.json
        
        db = AzureSQLService()
        
        # Update article
        query = """
        UPDATE ben002.KnowledgeBase
        SET 
            Title = %s,
            EquipmentMake = %s,
            EquipmentModel = %s,
            IssueCategory = %s,
            Symptoms = %s,
            RootCause = %s,
            Solution = %s,
            RelatedWONumbers = %s,
            ImageUrls = %s,
            UpdatedBy = %s,
            UpdatedDate = GETDATE()
        WHERE Id = %s
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
            current_user,
            article_id
        ]
        
        db.execute_query(query, params)
        
        return jsonify({'message': 'Article updated successfully'})
        
    except Exception as e:
        logger.error(f"Failed to update article {article_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@knowledge_base_bp.route('/api/knowledge-base/articles/<int:article_id>', methods=['DELETE'])
@jwt_required()
def delete_article(article_id):
    """
    Delete a knowledge base article (admin only).
    """
    try:
        db = AzureSQLService()
        
        query = "DELETE FROM ben002.KnowledgeBase WHERE Id = %s"
        db.execute_query(query, [article_id])
        
        return jsonify({'message': 'Article deleted successfully'})
        
    except Exception as e:
        logger.error(f"Failed to delete article {article_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@knowledge_base_bp.route('/api/knowledge-base/categories', methods=['GET'])
@jwt_required()
def get_categories():
    """
    Get all unique issue categories.
    """
    try:
        db = AzureSQLService()
        
        query = """
        SELECT DISTINCT IssueCategory
        FROM ben002.KnowledgeBase
        WHERE IssueCategory IS NOT NULL AND IssueCategory != ''
        ORDER BY IssueCategory
        """
        
        results = db.execute_query(query)
        
        categories = [row['IssueCategory'] for row in results] if results else []
        
        return jsonify({'categories': categories})
        
    except Exception as e:
        logger.error(f"Failed to fetch categories: {str(e)}")
        return jsonify({'error': str(e)}), 500


@knowledge_base_bp.route('/api/knowledge-base/equipment-makes', methods=['GET'])
@jwt_required()
def get_equipment_makes():
    """
    Get all unique equipment makes.
    """
    try:
        db = AzureSQLService()
        
        query = """
        SELECT DISTINCT EquipmentMake
        FROM ben002.KnowledgeBase
        WHERE EquipmentMake IS NOT NULL AND EquipmentMake != ''
        ORDER BY EquipmentMake
        """
        
        results = db.execute_query(query)
        
        makes = [row['EquipmentMake'] for row in results] if results else []
        
        return jsonify({'makes': makes})
        
    except Exception as e:
        logger.error(f"Failed to fetch equipment makes: {str(e)}")
        return jsonify({'error': str(e)}), 500
