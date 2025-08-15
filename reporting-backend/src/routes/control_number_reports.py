from flask import jsonify, request
from flask_jwt_extended import jwt_required
from datetime import datetime
from src.services.azure_sql_service import AzureSQLService
from src.routes.reports import reports_bp
import logging

logger = logging.getLogger(__name__)

@reports_bp.route('/departments/accounting/control-serial-mapping', methods=['GET'])
@jwt_required()
def get_control_serial_mapping():
    """Get report mapping Control Numbers to Serial Numbers with equipment details"""
    try:
        logger.info("Starting control number to serial number mapping report")
        db = AzureSQLService()
        
        # Get all equipment with control numbers or serial numbers
        mapping_query = """
        SELECT 
            e.ControlNo,
            e.SerialNo,
            e.UnitNo,
            e.Make,
            e.Model,
            e.ModelYear,
            e.Location,
            e.CustomerNo,
            c.Name as CustomerName,
            e.RentalStatus,
            e.Cost,
            e.Sell,
            e.CreatedDate,
            CASE 
                WHEN e.ControlNo IS NOT NULL AND e.ControlNo != '' THEN 'Assigned'
                ELSE 'Not Assigned'
            END as ControlStatus,
            -- Get last work order for this equipment
            wo.LastWONo,
            wo.LastWODate,
            -- Get last invoice
            inv.LastInvoiceNo,
            inv.LastInvoiceDate,
            -- Check if in GL
            CASE 
                WHEN gl.ControlNo IS NOT NULL THEN 'Yes'
                ELSE 'No'
            END as InGLSystem
        FROM ben002.Equipment e
        LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
        -- Get most recent work order
        LEFT JOIN (
            SELECT ControlNo, 
                   MAX(WONo) as LastWONo,
                   MAX(OpenDate) as LastWODate
            FROM ben002.WO
            WHERE ControlNo IS NOT NULL AND ControlNo != ''
            GROUP BY ControlNo
        ) wo ON e.ControlNo = wo.ControlNo
        -- Get most recent invoice
        LEFT JOIN (
            SELECT ControlNo,
                   MAX(InvoiceNo) as LastInvoiceNo,
                   MAX(InvoiceDate) as LastInvoiceDate
            FROM ben002.InvoiceReg
            WHERE ControlNo IS NOT NULL AND ControlNo != ''
            GROUP BY ControlNo
        ) inv ON e.ControlNo = inv.ControlNo
        -- Check if exists in GL
        LEFT JOIN (
            SELECT DISTINCT ControlNo
            FROM ben002.GLDetail
            WHERE ControlNo IS NOT NULL AND ControlNo != ''
        ) gl ON e.ControlNo = gl.ControlNo
        WHERE e.SerialNo IS NOT NULL
        ORDER BY 
            CASE WHEN e.ControlNo IS NULL OR e.ControlNo = '' THEN 1 ELSE 0 END,
            e.ControlNo,
            e.SerialNo
        """
        
        result = db.execute_query(mapping_query)
        
        if not result:
            return jsonify({
                'equipment': [],
                'summary': {
                    'total_equipment': 0,
                    'with_control_numbers': 0,
                    'without_control_numbers': 0,
                    'with_gl_entries': 0,
                    'percentage_assigned': 0
                }
            })
        
        # Process results
        equipment = []
        with_control = 0
        without_control = 0
        with_gl = 0
        
        for row in result:
            control_no = row.get('ControlNo', '')
            has_control = control_no and control_no.strip() != ''
            
            if has_control:
                with_control += 1
            else:
                without_control += 1
                
            if row.get('InGLSystem') == 'Yes':
                with_gl += 1
            
            equipment.append({
                'control_number': control_no if control_no else 'NOT ASSIGNED',
                'serial_number': row.get('SerialNo', ''),
                'unit_number': row.get('UnitNo', ''),
                'make': row.get('Make', ''),
                'model': row.get('Model', ''),
                'model_year': row.get('ModelYear', ''),
                'location': row.get('Location', ''),
                'customer_number': row.get('CustomerNo', ''),
                'customer_name': row.get('CustomerName', ''),
                'rental_status': row.get('RentalStatus', ''),
                'cost': float(row.get('Cost', 0) or 0),
                'sell_price': float(row.get('Sell', 0) or 0),
                'created_date': row.get('CreatedDate').strftime('%Y-%m-%d') if row.get('CreatedDate') else None,
                'control_status': row.get('ControlStatus', ''),
                'last_wo_number': row.get('LastWONo', ''),
                'last_wo_date': row.get('LastWODate').strftime('%Y-%m-%d') if row.get('LastWODate') else None,
                'last_invoice_no': row.get('LastInvoiceNo', ''),
                'last_invoice_date': row.get('LastInvoiceDate').strftime('%Y-%m-%d') if row.get('LastInvoiceDate') else None,
                'in_gl_system': row.get('InGLSystem', 'No')
            })
        
        total = len(equipment)
        percentage_assigned = round((with_control / total * 100), 1) if total > 0 else 0
        
        summary = {
            'total_equipment': total,
            'with_control_numbers': with_control,
            'without_control_numbers': without_control,
            'with_gl_entries': with_gl,
            'percentage_assigned': percentage_assigned
        }
        
        logger.info(f"Found {total} equipment records: {with_control} with control numbers, {without_control} without")
        
        return jsonify({
            'equipment': equipment,
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"Error in control-serial mapping report: {str(e)}")
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/departments/accounting/control-number-summary', methods=['GET'])
@jwt_required()
def get_control_number_summary():
    """Get summary statistics for control number usage across the system"""
    try:
        logger.info("Starting control number summary report")
        db = AzureSQLService()
        
        # Get usage statistics
        summary_query = """
        SELECT 
            'Equipment' as TableName,
            COUNT(*) as TotalRecords,
            COUNT(DISTINCT ControlNo) as UniqueControlNos,
            COUNT(CASE WHEN ControlNo IS NOT NULL AND ControlNo != '' THEN 1 END) as RecordsWithControlNo
        FROM ben002.Equipment
        WHERE SerialNo IS NOT NULL
        
        UNION ALL
        
        SELECT 
            'Work Orders' as TableName,
            COUNT(*) as TotalRecords,
            COUNT(DISTINCT ControlNo) as UniqueControlNos,
            COUNT(CASE WHEN ControlNo IS NOT NULL AND ControlNo != '' THEN 1 END) as RecordsWithControlNo
        FROM ben002.WO
        
        UNION ALL
        
        SELECT 
            'Invoices' as TableName,
            COUNT(*) as TotalRecords,
            COUNT(DISTINCT ControlNo) as UniqueControlNos,
            COUNT(CASE WHEN ControlNo IS NOT NULL AND ControlNo != '' THEN 1 END) as RecordsWithControlNo
        FROM ben002.InvoiceReg
        
        UNION ALL
        
        SELECT 
            'GL Entries' as TableName,
            COUNT(*) as TotalRecords,
            COUNT(DISTINCT ControlNo) as UniqueControlNos,
            COUNT(CASE WHEN ControlNo IS NOT NULL AND ControlNo != '' THEN 1 END) as RecordsWithControlNo
        FROM ben002.GLDetail
        """
        
        usage_result = db.execute_query(summary_query)
        
        # Get control number changes history
        changes_query = """
        SELECT TOP 100
            ControlNo,
            SerialNo,
            UnitNo,
            OldControlNo,
            NewControlNo,
            ChangeDate,
            ChangedBy
        FROM ben002.EQControlNoChange
        ORDER BY ChangeDate DESC
        """
        
        changes_result = db.execute_query(changes_query)
        
        # Format results
        usage_stats = []
        if usage_result:
            for row in usage_result:
                usage_stats.append({
                    'table_name': row.get('TableName', ''),
                    'total_records': row.get('TotalRecords', 0),
                    'unique_control_numbers': row.get('UniqueControlNos', 0),
                    'records_with_control_no': row.get('RecordsWithControlNo', 0),
                    'percentage_with_control': round(
                        (row.get('RecordsWithControlNo', 0) / row.get('TotalRecords', 1) * 100), 1
                    ) if row.get('TotalRecords', 0) > 0 else 0
                })
        
        recent_changes = []
        if changes_result:
            for row in changes_result:
                recent_changes.append({
                    'control_number': row.get('ControlNo', ''),
                    'serial_number': row.get('SerialNo', ''),
                    'unit_number': row.get('UnitNo', ''),
                    'old_control_no': row.get('OldControlNo', ''),
                    'new_control_no': row.get('NewControlNo', ''),
                    'change_date': row.get('ChangeDate').strftime('%Y-%m-%d %H:%M') if row.get('ChangeDate') else None,
                    'changed_by': row.get('ChangedBy', '')
                })
        
        # Get next control number from Company table
        next_control_query = """
        SELECT NextControlNo
        FROM ben002.Company
        """
        
        next_control_result = db.execute_query(next_control_query)
        next_control_no = next_control_result[0].get('NextControlNo') if next_control_result else None
        
        return jsonify({
            'usage_statistics': usage_stats,
            'recent_changes': recent_changes,
            'next_control_number': next_control_no
        })
        
    except Exception as e:
        logger.error(f"Error in control number summary: {str(e)}")
        return jsonify({'error': str(e)}), 500