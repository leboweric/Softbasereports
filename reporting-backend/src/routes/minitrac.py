"""
Minitrac historical data API endpoints
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.services.postgres_service import PostgreSQLService
import logging

logger = logging.getLogger(__name__)

minitrac_bp = Blueprint('minitrac', __name__)

@minitrac_bp.route('/api/minitrac/search', methods=['GET'])
@jwt_required()
def search_equipment():
    """
    Search Minitrac equipment data
    Supports full-text search and various filters
    """
    try:
        # Get search parameters
        search_term = request.args.get('search', '').strip()
        category = request.args.get('category', '').strip()
        status = request.args.get('status', '').strip()
        customer = request.args.get('customer', '').strip()
        make = request.args.get('make', '').strip()
        model = request.args.get('model', '').strip()
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        # Build query
        query_parts = []
        params = []
        
        base_query = """
            SELECT 
                id,
                unit_num,
                category,
                grp,
                serial,
                make,
                model,
                year,
                unit_desc,
                status,
                ship_name,
                ship_cust,
                bill_cust,
                last_invc_date,
                contr_thru_date,
                net_book_val,
                ytd_income,
                ytd_expense,
                curr_meter_read,
                eng_make,
                eng_model
            FROM minitrac_equipment
            WHERE 1=1
        """
        
        # Add search conditions
        if search_term:
            query_parts.append("""
                AND (
                    unit_num ILIKE %s OR
                    serial ILIKE %s OR
                    make ILIKE %s OR
                    model ILIKE %s OR
                    unit_desc ILIKE %s OR
                    ship_name ILIKE %s OR
                    eng_serial ILIKE %s
                )
            """)
            search_pattern = f'%{search_term}%'
            params.extend([search_pattern] * 7)
        
        if category:
            query_parts.append("AND category = %s")
            params.append(category)
        
        if status:
            query_parts.append("AND status = %s")
            params.append(status)
        
        if customer:
            query_parts.append("AND (ship_name ILIKE %s OR ship_cust ILIKE %s OR bill_cust ILIKE %s)")
            customer_pattern = f'%{customer}%'
            params.extend([customer_pattern] * 3)
        
        if make:
            query_parts.append("AND make ILIKE %s")
            params.append(f'%{make}%')
        
        if model:
            query_parts.append("AND model ILIKE %s")
            params.append(f'%{model}%')
        
        # Count total results
        count_query = f"SELECT COUNT(*) as total FROM minitrac_equipment WHERE 1=1 {''.join(query_parts)}"
        
        # Add ordering and pagination
        query = base_query + ''.join(query_parts) + " ORDER BY unit_num LIMIT %s OFFSET %s"
        params.extend([per_page, (page - 1) * per_page])
        
        # Execute queries
        pg_service = PostgreSQLService()
        with pg_service.get_connection() as conn:
            if conn is None:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor()
            
            # Get total count
            cursor.execute(count_query, params[:-2])  # Exclude pagination params
            total_count = cursor.fetchone()['total']
            
            # Get results
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            cursor.close()
        
        return jsonify({
            'success': True,
            'data': results,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'total_pages': (total_count + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        logger.error(f"Error searching Minitrac data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@minitrac_bp.route('/api/minitrac/equipment/<unit_num>', methods=['GET'])
@jwt_required()
def get_equipment_detail(unit_num):
    """Get detailed information for a specific equipment unit"""
    try:
        pg_service = PostgreSQLService()
        with pg_service.get_connection() as conn:
            if conn is None:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor()
            
            # Get all fields for the unit
            cursor.execute("""
                SELECT * FROM minitrac_equipment 
                WHERE unit_num = %s
            """, (unit_num,))
            
            result = cursor.fetchone()
            cursor.close()
            
            if not result:
                return jsonify({'error': 'Equipment not found'}), 404
            
            return jsonify({
                'success': True,
                'data': result
            })
            
    except Exception as e:
        logger.error(f"Error getting equipment detail: {str(e)}")
        return jsonify({'error': str(e)}), 500

@minitrac_bp.route('/api/minitrac/filters', methods=['GET'])
@jwt_required()
def get_filter_options():
    """Get available filter options for dropdowns"""
    try:
        pg_service = PostgreSQLService()
        with pg_service.get_connection() as conn:
            if conn is None:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor()
            
            # Get unique values for filters
            filters = {}
            
            # Categories
            cursor.execute("SELECT DISTINCT category FROM minitrac_equipment WHERE category IS NOT NULL ORDER BY category")
            filters['categories'] = [row['category'] for row in cursor.fetchall()]
            
            # Status
            cursor.execute("SELECT DISTINCT status FROM minitrac_equipment WHERE status IS NOT NULL ORDER BY status")
            filters['statuses'] = [row['status'] for row in cursor.fetchall()]
            
            # Makes
            cursor.execute("SELECT DISTINCT make FROM minitrac_equipment WHERE make IS NOT NULL ORDER BY make")
            filters['makes'] = [row['make'] for row in cursor.fetchall()]
            
            # Groups
            cursor.execute("SELECT DISTINCT grp FROM minitrac_equipment WHERE grp IS NOT NULL ORDER BY grp")
            filters['groups'] = [row['grp'] for row in cursor.fetchall()]
            
            cursor.close()
            
            return jsonify({
                'success': True,
                'filters': filters
            })
            
    except Exception as e:
        logger.error(f"Error getting filter options: {str(e)}")
        return jsonify({'error': str(e)}), 500

@minitrac_bp.route('/api/minitrac/export', methods=['GET'])
@jwt_required()
def export_search_results():
    """Export search results to CSV format"""
    try:
        # Get search parameters (same as search endpoint)
        search_term = request.args.get('search', '').strip()
        category = request.args.get('category', '').strip()
        status = request.args.get('status', '').strip()
        customer = request.args.get('customer', '').strip()
        make = request.args.get('make', '').strip()
        model = request.args.get('model', '').strip()
        
        # Build query without pagination
        query_parts = []
        params = []
        
        base_query = """
            SELECT 
                unit_num as "Unit #",
                category as "Category",
                serial as "Serial",
                make as "Make",
                model as "Model",
                year as "Year",
                unit_desc as "Description",
                status as "Status",
                ship_name as "Customer",
                ship_cust as "Ship To",
                bill_cust as "Bill To",
                last_invc_date as "Last Invoice",
                contr_thru_date as "Contract Thru",
                net_book_val as "Book Value",
                ytd_income as "YTD Income",
                ytd_expense as "YTD Expense",
                curr_meter_read as "Current Meter"
            FROM minitrac_equipment
            WHERE 1=1
        """
        
        # Add search conditions (same as search endpoint)
        if search_term:
            query_parts.append("""
                AND (
                    unit_num ILIKE %s OR
                    serial ILIKE %s OR
                    make ILIKE %s OR
                    model ILIKE %s OR
                    unit_desc ILIKE %s OR
                    ship_name ILIKE %s OR
                    eng_serial ILIKE %s
                )
            """)
            search_pattern = f'%{search_term}%'
            params.extend([search_pattern] * 7)
        
        if category:
            query_parts.append("AND category = %s")
            params.append(category)
        
        if status:
            query_parts.append("AND status = %s")
            params.append(status)
        
        if customer:
            query_parts.append("AND (ship_name ILIKE %s OR ship_cust ILIKE %s OR bill_cust ILIKE %s)")
            customer_pattern = f'%{customer}%'
            params.extend([customer_pattern] * 3)
        
        if make:
            query_parts.append("AND make ILIKE %s")
            params.append(f'%{make}%')
        
        if model:
            query_parts.append("AND model ILIKE %s")
            params.append(f'%{model}%')
        
        query = base_query + ''.join(query_parts) + " ORDER BY unit_num"
        
        # Execute query
        pg_service = PostgreSQLService()
        with pg_service.get_connection() as conn:
            if conn is None:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
        
        # Convert to CSV format
        import csv
        import io
        
        output = io.StringIO()
        if results:
            writer = csv.DictWriter(output, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        
        return output.getvalue(), 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename=minitrac_export.csv'
        }
        
    except Exception as e:
        logger.error(f"Error exporting Minitrac data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@minitrac_bp.route('/api/minitrac/stats', methods=['GET'])
@jwt_required()
def get_statistics():
    """Get summary statistics for Minitrac data"""
    try:
        pg_service = PostgreSQLService()
        with pg_service.get_connection() as conn:
            if conn is None:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor()
            
            # Get various statistics
            stats = {}
            
            # Total equipment count
            cursor.execute("SELECT COUNT(*) as total FROM minitrac_equipment")
            stats['total_equipment'] = cursor.fetchone()['total']
            
            # By status
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM minitrac_equipment 
                WHERE status IS NOT NULL 
                GROUP BY status
            """)
            stats['by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # By category
            cursor.execute("""
                SELECT category, COUNT(*) as count 
                FROM minitrac_equipment 
                WHERE category IS NOT NULL 
                GROUP BY category
                ORDER BY count DESC
                LIMIT 10
            """)
            stats['top_categories'] = [{'category': row['category'], 'count': row['count']} for row in cursor.fetchall()]
            
            # Total values
            cursor.execute("""
                SELECT 
                    SUM(net_book_val) as total_book_value,
                    SUM(ytd_income) as total_ytd_income,
                    SUM(ytd_expense) as total_ytd_expense,
                    SUM(atd_income) as total_atd_income,
                    SUM(atd_expense) as total_atd_expense
                FROM minitrac_equipment
            """)
            values = cursor.fetchone()
            stats['financials'] = {
                'total_book_value': float(values['total_book_value'] or 0),
                'total_ytd_income': float(values['total_ytd_income'] or 0),
                'total_ytd_expense': float(values['total_ytd_expense'] or 0),
                'total_atd_income': float(values['total_atd_income'] or 0),
                'total_atd_expense': float(values['total_atd_expense'] or 0)
            }
            
            cursor.close()
            
            return jsonify({
                'success': True,
                'stats': stats
            })
            
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        return jsonify({'error': str(e)}), 500