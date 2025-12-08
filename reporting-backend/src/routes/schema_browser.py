"""
Interactive Database Schema Browser
Generates a comprehensive HTML page showing all database schema information
"""
from flask import Blueprint, Response
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService
import json

schema_browser_bp = Blueprint('schema_browser', __name__)

@schema_browser_bp.route('/api/schema-browser', methods=['GET'])
@jwt_required()
def schema_browser():
    """Generate comprehensive interactive schema browser HTML page"""
    try:
        db = AzureSQLService()

        # Get all tables
        tables_query = """
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'ben002'
        ORDER BY TABLE_NAME
        """
        tables = db.execute_query(tables_query)

        # For each table, get columns, PKs, FKs, and sample data
        schema_data = {}

        for table in tables:
            table_name = table['TABLE_NAME']

            # Get columns
            columns_query = """
            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'ben002' AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
            """
            columns = db.execute_query(columns_query, [table_name])

            # Get row count
            try:
                count_query = f"SELECT COUNT(*) as cnt FROM ben002.[{table_name}]"
                count = db.execute_query(count_query)[0]['cnt']
            except:
                count = 0

            # Get sample data (first 3 rows)
            try:
                sample_query = f"SELECT TOP 3 * FROM ben002.[{table_name}]"
                sample = db.execute_query(sample_query)
            except:
                sample = []

            # Get foreign keys
            try:
                fk_query = """
                SELECT
                    COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS ColumnName,
                    OBJECT_NAME(fk.referenced_object_id) AS ReferencedTable,
                    COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS ReferencedColumn
                FROM sys.foreign_keys AS fk
                INNER JOIN sys.foreign_key_columns AS fkc ON fk.object_id = fkc.constraint_object_id
                WHERE OBJECT_NAME(fk.parent_object_id) = %s
                """
                foreign_keys = db.execute_query(fk_query, [table_name])
            except:
                foreign_keys = []

            schema_data[table_name] = {
                'columns': columns,
                'row_count': count,
                'sample_data': sample,
                'foreign_keys': foreign_keys
            }

        # Generate HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Database Schema Browser</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .search-box {{
            margin: 20px 0;
            padding: 12px;
            width: 100%;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }}
        .table-list {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 10px;
            margin: 20px 0;
        }}
        .table-item {{
            padding: 10px;
            background: #f0f0f0;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .table-item:hover {{
            background: #4CAF50;
            color: white;
            transform: translateY(-2px);
        }}
        .table-detail {{
            display: none;
            margin: 20px 0;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 8px;
            border: 2px solid #4CAF50;
        }}
        .table-detail.active {{
            display: block;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #4CAF50;
            color: white;
            font-weight: bold;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .fk-badge {{
            display: inline-block;
            padding: 4px 8px;
            background: #2196F3;
            color: white;
            border-radius: 4px;
            font-size: 12px;
            margin: 2px;
        }}
        .row-count {{
            color: #666;
            font-style: italic;
        }}
        .close-btn {{
            float: right;
            background: #f44336;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
        }}
        .json-data {{
            background: #272822;
            color: #f8f8f2;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            max-height: 400px;
            overflow-y: auto;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🗄️ Database Schema Browser - ben002</h1>
        <input type="text" id="searchBox" class="search-box" placeholder="Search tables..." onkeyup="filterTables()">

        <div class="table-list" id="tableList">
            {''.join([f'<div class="table-item" onclick="showTable(\'{name}\')">{name} <span class="row-count">({data["row_count"]} rows)</span></div>' for name, data in schema_data.items()])}
        </div>

        {''.join([f'''
        <div class="table-detail" id="table-{name}">
            <button class="close-btn" onclick="closeTable()">Close</button>
            <h2>{name}</h2>
            <p class="row-count">Total Rows: {data["row_count"]}</p>

            <h3>Columns ({len(data["columns"])})</h3>
            <table>
                <tr>
                    <th>Column Name</th>
                    <th>Data Type</th>
                    <th>Max Length</th>
                    <th>Nullable</th>
                </tr>
                {''.join([f'''<tr>
                    <td>{col["COLUMN_NAME"]}</td>
                    <td>{col["DATA_TYPE"]}</td>
                    <td>{col.get("CHARACTER_MAXIMUM_LENGTH", "-")}</td>
                    <td>{col["IS_NULLABLE"]}</td>
                </tr>''' for col in data["columns"]])}
            </table>

            {f'''<h3>Foreign Keys ({len(data["foreign_keys"])})</h3>
            <div>
                {''.join([f'<span class="fk-badge">{fk["ColumnName"]} → {fk["ReferencedTable"]}.{fk["ReferencedColumn"]}</span>' for fk in data["foreign_keys"]])}
            </div>''' if data["foreign_keys"] else ''}

            <h3>Sample Data (First 3 Rows)</h3>
            <div class="json-data">{json.dumps(data["sample_data"], indent=2, default=str)}</div>
        </div>
        ''' for name, data in schema_data.items()])}
    </div>

    <script>
        var schemaData = {json.dumps(schema_data, default=str)};

        function showTable(tableName) {{
            // Hide all tables
            document.querySelectorAll('.table-detail').forEach(el => el.classList.remove('active'));
            // Show selected table
            document.getElementById('table-' + tableName).classList.add('active');
            // Scroll to top of detail
            document.getElementById('table-' + tableName).scrollIntoView({{ behavior: 'smooth' }});
        }}

        function closeTable() {{
            document.querySelectorAll('.table-detail').forEach(el => el.classList.remove('active'));
        }}

        function filterTables() {{
            var input = document.getElementById('searchBox');
            var filter = input.value.toUpperCase();
            var items = document.getElementsByClassName('table-item');

            for (var i = 0; i < items.length; i++) {{
                var txtValue = items[i].textContent || items[i].innerText;
                if (txtValue.toUpperCase().indexOf(filter) > -1) {{
                    items[i].style.display = "";
                }} else {{
                    items[i].style.display = "none";
                }}
            }}
        }}
    </script>
</body>
</html>
"""

        return Response(html, mimetype='text/html')

    except Exception as e:
        error_html = f"""
<!DOCTYPE html>
<html>
<head><title>Error</title></head>
<body>
    <h1>Error Loading Schema</h1>
    <pre>{str(e)}</pre>
</body>
</html>
"""
        return Response(error_html, mimetype='text/html', status=500)
