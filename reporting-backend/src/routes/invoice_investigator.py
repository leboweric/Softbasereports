"""
Invoice Investigator - Show ALL fields for invoice 110000014
"""
from flask import Blueprint, Response, request
from flask_jwt_extended import jwt_required
from src.utils.tenant_utils import get_tenant_db
import json

from flask_jwt_extended import get_jwt_identity
from src.models.user import User

def get_tenant_schema():
    """Get the database schema for the current user's organization"""
    try:
        user_id = get_jwt_identity()
        if user_id:
            user = User.query.get(int(user_id))
            if user and user.organization and user.organization.database_schema:
                return user.organization.database_schema
        return 'ben002'  # Fallback
    except:
        return 'ben002'



invoice_investigator_bp = Blueprint('invoice_investigator', __name__)

@invoice_investigator_bp.route('/api/investigate-invoice', methods=['GET'])
def investigate_invoice():
    """Show ALL fields from a specific invoice - No auth required for debugging"""
    try:
        db = get_tenant_db()
        schema = get_tenant_schema()
        invoice_no = request.args.get('invoice_no', '110000014')

        # Get the invoice
        query = f"SELECT * FROM {schema}.InvoiceReg WHERE InvoiceNo = '{invoice_no}'"
        invoice = db.execute_query(query)

        if not invoice:
            return Response(f"<h1>Invoice {invoice_no} not found</h1>", mimetype='text/html')

        invoice_data = invoice[0]

        # Get related Dept info
        sale_dept = invoice_data.get('SaleDept')
        dept_data = None
        if sale_dept:
            dept_query = f"SELECT * FROM {schema}.Dept WHERE Dept = {sale_dept}"
            dept_result = db.execute_query(dept_query)
            if dept_result:
                dept_data = dept_result[0]

        # Get all salesmen with the same SaleGroup
        salesmen_data = []
        if dept_data and dept_data.get('SaleGroup'):
            salesmen_query = f"SELECT * FROM {schema}.Salesman WHERE SalesGroup = {dept_data['SaleGroup']}"
            salesmen_data = db.execute_query(salesmen_query)

        # Get Customer info
        bill_to = invoice_data.get('BillTo')
        customer_data = None
        if bill_to:
            customer_query = f"SELECT * FROM {schema}.Customer WHERE Number = '{bill_to}'"
            customer_result = db.execute_query(customer_query)
            if customer_result:
                customer_data = customer_result[0]

        # Get WO info (join on WONo = InvoiceNo)
        wo_query = f"SELECT * FROM {schema}.WO WHERE WONo = {invoice_no}"
        wo_data = db.execute_query(wo_query)

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Invoice {invoice_no} Investigation</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #4CAF50;
            margin-top: 30px;
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
            width: 30%;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .highlight {{
            background: #ffeb3b !important;
            font-weight: bold;
        }}
        .section {{
            margin: 30px 0;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 8px;
            border-left: 4px solid #4CAF50;
        }}
        .alert {{
            padding: 15px;
            background: #ff5722;
            color: white;
            border-radius: 4px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Invoice Investigation: {invoice_no}</h1>

        <div class="section">
            <h2>📄 Invoice Fields (ALL {len(invoice_data)} fields)</h2>
            <table>
                <tr><th>Field Name</th><th>Value</th></tr>
                {''.join([f'<tr{"class=highlight" if "sale" in key.lower() or "dept" in key.lower() or "rep" in key.lower() or "man" in key.lower() else ""}><td>{key}</td><td>{value}</td></tr>' for key, value in invoice_data.items()])}
            </table>
        </div>

        {f'''<div class="section">
            <h2>🏢 Related Dept {sale_dept}</h2>
            <table>
                <tr><th>Field Name</th><th>Value</th></tr>
                {''.join([f'<tr{"class=highlight" if "group" in key.lower() or "sale" in key.lower() else ""}><td>{key}</td><td>{value}</td></tr>' for key, value in dept_data.items()])}
            </table>
        </div>''' if dept_data else ''}

        {f'''<div class="section">
            <h2>👥 All Salesmen with SaleGroup {dept_data.get("SaleGroup") if dept_data else "?"}</h2>
            <div class="alert">⚠️ PROBLEM: Multiple salesmen have the same SaleGroup! This is why the query returns the wrong person.</div>
            <table>
                <tr><th>Number</th><th>Name</th><th>SalesGroup</th></tr>
                {''.join([f'<tr><td>{s.get("Number")}</td><td><strong>{s.get("Name")}</strong></td><td>{s.get("SalesGroup")}</td></tr>' for s in salesmen_data])}
            </table>
        </div>''' if salesmen_data else ''}

        {f'''<div class="section">
            <h2>👤 Customer {bill_to}</h2>
            <table>
                <tr><th>Field Name</th><th>Value</th></tr>
                {''.join([f'<tr{"class=highlight" if "salesman" in key.lower() else ""}><td>{key}</td><td>{value}</td></tr>' for key, value in customer_data.items()])}
            </table>
        </div>''' if customer_data else ''}

        {f'''<div class="section">
            <h2>🛠️ Work Order (WO) Records for WONo = {invoice_no}</h2>
            <div class="alert">✅ Found {len(wo_data)} WO record(s). The commission report uses WO.Salesman field.</div>
            <table>
                <tr><th>Field Name</th><th>Value</th></tr>
                {''.join([f'<tr{"class=highlight" if "salesman" in key.lower() or "wono" in key.lower() else ""}><td>{key}</td><td>{value}</td></tr>' for key, value in wo_data[0].items()])}
            </table>
        </div>''' if wo_data and len(wo_data) > 0 else '<div class="section"><h2>🛠️ Work Order (WO) Records</h2><div class="alert">⚠️ No WO record found with WONo = ' + invoice_no + '</div></div>'}

        <div class="section">
            <h2>🔎 Investigation Summary</h2>
            <p><strong>Invoice:</strong> {invoice_no}</p>
            <p><strong>SaleDept:</strong> {sale_dept}</p>
            <p><strong>Dept SaleGroup:</strong> {dept_data.get("SaleGroup") if dept_data else "N/A"}</p>
            <p><strong>Number of salesmen with this SaleGroup:</strong> {len(salesmen_data)}</p>
            <p><strong>Customer Default Salesman:</strong> {customer_data.get("Salesman1") if customer_data else "N/A"}</p>
            <p><strong>WO Salesman:</strong> {wo_data[0].get("Salesman") if wo_data and len(wo_data) > 0 else "N/A (No WO record)"}</p>
            <p><strong>Number of WO records:</strong> {len(wo_data) if wo_data else 0}</p>
        </div>
    </div>
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
    <h1>Error Investigating Invoice</h1>
    <pre>{str(e)}</pre>
</body>
</html>
"""
        return Response(error_html, mimetype='text/html', status=500)
