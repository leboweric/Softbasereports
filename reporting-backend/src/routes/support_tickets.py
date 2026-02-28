from flask import Blueprint, request, jsonify, Response, make_response, g
from src.models.user import db
from src.models.support_ticket import SupportTicket, SupportTicketAttachment, SupportTicketComment
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from datetime import datetime
import os
import json
import io

support_tickets_bp = Blueprint('support_tickets', __name__)

# ==================== HELPERS ====================


def get_current_user_org_id():
    """Get the current authenticated user's organization_id from g context or JWT.
    Returns None if not authenticated (public endpoints).
    Returns organization_id for org-scoped filtering.
    Super Admins (org_id exists but they have Super Admin role) still see only their org tickets
    unless we add a special bypass later.
    """
    # First try g.current_user set by before_request middleware
    if hasattr(g, 'current_user') and g.current_user:
        return g.current_user.organization_id
    
    # Fallback: try JWT
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id:
            from src.models.user import User
            user = User.query.get(int(user_id))
            if user:
                return user.organization_id
    except Exception:
        pass
    
    return None

def generate_ticket_number():
    """Generate a unique ticket number in format TKT-YYYY-NNNN"""
    year = datetime.utcnow().year
    prefix = f'TKT-{year}-'
    count = SupportTicket.query.filter(
        SupportTicket.ticket_number.like(f'{prefix}%')
    ).count()
    return f'{prefix}{str(count + 1).zfill(4)}'


def get_sendgrid_client():
    """Get SendGrid client if configured"""
    try:
        import sendgrid
    except ImportError:
        print('SendGrid not installed, skipping email')
        return None, None, None

    api_key = os.environ.get('SENDGRID_API_KEY')
    if not api_key:
        print('SENDGRID_API_KEY not configured, skipping email')
        return None, None, None

    from_email = os.environ.get('SENDGRID_FROM_EMAIL', 'noreply@aiop.one')
    sg = sendgrid.SendGridAPIClient(api_key=api_key)
    return sg, from_email, api_key


def send_ticket_notifications(ticket, attachment_count=0):
    """Send email notifications via SendGrid"""
    sg, from_email, api_key = get_sendgrid_client()
    if not sg:
        return

    try:
        from sendgrid.helpers.mail import Mail
    except ImportError:
        return

    admin_email = 'eric@profitbuildernetwork.com'

    type_label = {
        'bug': 'Bug Report',
        'enhancement': 'Enhancement Request',
        'question': 'Question'
    }.get(ticket.type, ticket.type)

    attachment_info = ''
    if attachment_count > 0:
        attachment_info = f'<tr><td style="padding: 8px 0;"><strong>Attachments:</strong></td><td style="padding: 8px 0;">{attachment_count} file(s) attached</td></tr>'

    # Admin notification email
    admin_html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <div style="background: #1a1a2e; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
        <h2 style="margin: 0;">New Support Ticket: {ticket.ticket_number}</h2>
        <p style="margin: 5px 0 0; opacity: 0.8;">AIOP.one Platform</p>
      </div>
      
      <div style="background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb;">
        <table style="width: 100%;">
          <tr>
            <td style="padding: 8px 0;"><strong>Type:</strong></td>
            <td style="padding: 8px 0;">{type_label}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0;"><strong>Subject:</strong></td>
            <td style="padding: 8px 0;">{ticket.subject}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0;"><strong>Submitted By:</strong></td>
            <td style="padding: 8px 0;">{ticket.submitted_by_name or 'Unknown'} ({ticket.submitted_by_email or 'No email'})</td>
          </tr>
          <tr>
            <td style="padding: 8px 0;"><strong>Page URL:</strong></td>
            <td style="padding: 8px 0;">{ticket.page_url or 'Not provided'}</td>
          </tr>
          {attachment_info}
        </table>
      </div>
      
      <div style="padding: 20px; border: 1px solid #e5e7eb; border-top: none;">
        <h3 style="margin-top: 0;">Message:</h3>
        <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; white-space: pre-wrap;">
{ticket.message}
        </div>
      </div>
      
      <div style="padding: 15px; background: #f9fafb; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
        <p style="margin: 0; color: #6b7280; font-size: 12px;">
          Submitted via AIOP.one on {ticket.created_at.strftime('%Y-%m-%d %H:%M:%S') if ticket.created_at else 'N/A'}
        </p>
      </div>
    </div>
    """

    try:
        message = Mail(
            from_email=from_email,
            to_emails=admin_email,
            subject=f'[{ticket.ticket_number}] {type_label}: {ticket.subject}',
            html_content=admin_html
        )
        if ticket.submitted_by_email:
            message.reply_to = ticket.submitted_by_email
        sg.send(message)
        print(f'Ticket notification sent to admin: {ticket.ticket_number}')
    except Exception as e:
        print(f'Error sending admin notification: {e}')

    # Confirmation email to user
    if ticket.submitted_by_email:
        user_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <div style="background: #1a1a2e; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0;">We've Received Your Request</h2>
            <p style="margin: 5px 0 0; opacity: 0.8;">AIOP.one Platform</p>
          </div>
          
          <div style="padding: 20px; border: 1px solid #e5e7eb;">
            <p>Thank you for contacting us! Your {type_label.lower()} has been submitted and assigned ticket number:</p>
            
            <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0;">
              <span style="font-size: 24px; font-weight: bold; color: #1a1a2e;">{ticket.ticket_number}</span>
            </div>
            
            <p><strong>Subject:</strong> {ticket.subject}</p>
            {f'<p><strong>Attachments:</strong> {attachment_count} file(s) received</p>' if attachment_count > 0 else ''}
            
            <p>We'll review your request and get back to you as soon as possible.</p>
          </div>
          
          <div style="padding: 15px; background: #f9fafb; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
            <p style="margin: 0; color: #6b7280; font-size: 12px;">
              This is an automated confirmation. Please do not reply to this email.
            </p>
          </div>
        </div>
        """

        try:
            message = Mail(
                from_email=from_email,
                to_emails=ticket.submitted_by_email,
                subject=f'Ticket {ticket.ticket_number} Received - {ticket.subject}',
                html_content=user_html
            )
            sg.send(message)
            print(f'Confirmation email sent to user: {ticket.submitted_by_email}')
        except Exception as e:
            print(f'Error sending user confirmation: {e}')


def send_resolution_email(ticket, fix_summary, testing_instructions):
    """Send resolution email to ticket submitter with action buttons"""
    sg, from_email, api_key = get_sendgrid_client()
    if not sg:
        return

    try:
        from sendgrid.helpers.mail import Mail
    except ImportError:
        return

    if not ticket.submitted_by_email:
        print(f'No email address for ticket {ticket.ticket_number}, skipping resolution email')
        return

    app_url = os.environ.get('APP_URL', 'https://app.aiop.one')

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Ticket Resolved</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
      
      <div style="background: linear-gradient(135deg, #059669 0%, #10b981 100%); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 28px;">Your Ticket Has Been Resolved!</h1>
        <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0; font-size: 16px;">
          Ticket #{ticket.ticket_number}
        </p>
      </div>
      
      <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
        
        <p style="font-size: 16px; margin-bottom: 20px;">Hi {ticket.submitted_by_name or 'there'},</p>
        
        <p style="font-size: 16px; margin-bottom: 20px;">
          Great news! We've resolved your support ticket. Here are the details:
        </p>
        
        <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #059669;">
          <p style="margin: 0 0 10px 0; font-weight: 600; color: #059669;">Your Ticket:</p>
          <p style="margin: 0 0 5px 0;"><strong>Subject:</strong> {ticket.subject}</p>
          <p style="margin: 0;"><strong>Ticket Number:</strong> {ticket.ticket_number}</p>
        </div>
        
        <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2563eb;">
          <p style="margin: 0 0 10px 0; font-weight: 600; color: #2563eb;">
            What Was Fixed:
          </p>
          <p style="margin: 0; white-space: pre-wrap;">{fix_summary}</p>
        </div>
        
        {f'''<div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #7c3aed;">
          <p style="margin: 0 0 10px 0; font-weight: 600; color: #7c3aed;">
            How to Test:
          </p>
          <p style="margin: 0; white-space: pre-wrap;">{testing_instructions}</p>
        </div>''' if testing_instructions else ''}
        
        <p style="font-size: 16px; margin: 20px 0;">
          Please test the fix and let us know if everything is working correctly.
        </p>
        
        <div style="text-align: center; margin: 30px 0;">
          <a href="{app_url}/hub?ticket_close={ticket.ticket_number}" 
             style="display: inline-block; background: #059669; color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 6px rgba(5, 150, 105, 0.3); margin: 5px;">
            Mark as Closed
          </a>
          <a href="{app_url}/hub?ticket_followup={ticket.ticket_number}" 
             style="display: inline-block; background: #d97706; color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 6px rgba(217, 119, 6, 0.3); margin: 5px;">
            Add Follow-up Comment
          </a>
        </div>
        
        <p style="font-size: 14px; color: #666; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
          <strong>Need help?</strong> Reply to this email or visit the support portal.
        </p>
        
        <p style="font-size: 14px; color: #666; margin-top: 10px;">
          Resolved by: <strong>AI First Operations Support Team</strong><br>
          Ticket Number: <strong>{ticket.ticket_number}</strong>
        </p>
        
      </div>
      
    </body>
    </html>
    """

    try:
        message = Mail(
            from_email=from_email,
            to_emails=ticket.submitted_by_email,
            subject=f'[{ticket.ticket_number}] Resolved - {ticket.subject}',
            html_content=html_content
        )
        # CC admin
        from sendgrid.helpers.mail import Cc
        message.add_cc(Cc('eric@profitbuildernetwork.com'))
        message.reply_to = 'eric@profitbuildernetwork.com'
        sg.send(message)
        print(f'Resolution email sent for ticket {ticket.ticket_number}')
    except Exception as e:
        print(f'Error sending resolution email for ticket {ticket.ticket_number}: {e}')


def send_comment_notification_email(ticket, comment_message):
    """Send email to ticket submitter when a comment is added requesting more information"""
    sg, from_email, api_key = get_sendgrid_client()
    if not sg:
        return

    try:
        from sendgrid.helpers.mail import Mail
    except ImportError:
        return

    if not ticket.submitted_by_email:
        print(f'No email address for ticket {ticket.ticket_number}, skipping comment notification email')
        return

    app_url = os.environ.get('APP_URL', 'https://app.aiop.one')

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Support Ticket Update</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
      
      <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 28px;">Support Ticket Update</h1>
      </div>
      
      <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
        
        <p style="font-size: 16px; margin-bottom: 20px;">Hi {ticket.submitted_by_name or 'there'},</p>
        
        <p style="font-size: 16px; margin-bottom: 20px;">
          We've reviewed your support ticket and need some additional information to help resolve your issue.
        </p>
        
        <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea;">
          <p style="margin: 0 0 10px 0; font-weight: 600; color: #667eea;">Your Ticket:</p>
          <p style="margin: 0 0 5px 0;"><strong>Subject:</strong> {ticket.subject}</p>
          <p style="margin: 0;"><strong>Ticket Number:</strong> {ticket.ticket_number}</p>
        </div>
        
        <div style="background: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107;">
          <p style="margin: 0 0 10px 0; font-weight: 600; color: #856404;">
            Additional Information Needed
          </p>
          <p style="margin: 0; white-space: pre-wrap; color: #856404;">{comment_message}</p>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
          <a href="{app_url}/hub?ticket_followup={ticket.ticket_number}" 
             style="display: inline-block; background: #667eea; color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);">
            Respond to This Ticket
          </a>
        </div>
        
        <p style="font-size: 14px; color: #666; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
          <strong>Need help?</strong> Reply to this email or visit the support portal.
        </p>
        
        <p style="font-size: 14px; color: #666; margin-top: 10px;">
          AI First Operations Support Team<br>
          Ticket Number: <strong>{ticket.ticket_number}</strong>
        </p>
        
      </div>
      
    </body>
    </html>
    """

    try:
        message = Mail(
            from_email=from_email,
            to_emails=ticket.submitted_by_email,
            subject=f'[{ticket.ticket_number}] Additional Information Needed - {ticket.subject}',
            html_content=html_content
        )
        from sendgrid.helpers.mail import Cc
        message.add_cc(Cc('eric@profitbuildernetwork.com'))
        message.reply_to = 'eric@profitbuildernetwork.com'
        sg.send(message)
        print(f'Comment notification email sent for ticket {ticket.ticket_number}')
    except Exception as e:
        print(f'Error sending comment notification email for ticket {ticket.ticket_number}: {e}')


# ==================== PUBLIC ROUTES ====================

@support_tickets_bp.route('/api/support-tickets/submit', methods=['POST'])
def submit_ticket():
    """Submit a new support ticket (with optional file attachments)"""
    try:
        # Handle both JSON and FormData
        if request.content_type and 'multipart/form-data' in request.content_type:
            ticket_type = request.form.get('type')
            subject = request.form.get('subject')
            message = request.form.get('message')
            page_url = request.form.get('page_url')
            user_data = request.form.get('user')
            if user_data and isinstance(user_data, str):
                try:
                    user_data = json.loads(user_data)
                except json.JSONDecodeError:
                    user_data = None
            files = request.files.getlist('attachments')
        else:
            data = request.get_json() or {}
            ticket_type = data.get('type')
            subject = data.get('subject')
            message = data.get('message')
            page_url = data.get('page_url')
            user_data = data.get('user')
            files = []

        # Validate required fields
        if not ticket_type or not subject or not message:
            return jsonify({'error': 'Type, subject, and message are required'}), 400

        if ticket_type not in ('bug', 'enhancement', 'question'):
            return jsonify({'error': 'Type must be bug, enhancement, or question'}), 400

        # Create ticket
        ticket = SupportTicket(
            ticket_number=generate_ticket_number(),
            type=ticket_type,
            subject=subject,
            message=message,
            page_url=page_url,
            submitted_by=user_data.get('id') if user_data else None,
            submitted_by_name=user_data.get('name') or user_data.get('username') if user_data else None,
            submitted_by_email=user_data.get('email') if user_data else None,
            organization_id=user_data.get('organization_id') if user_data else None
        )
        db.session.add(ticket)
        db.session.flush()  # Get the ticket ID

        # Save attachments
        attachment_count = 0
        for f in files:
            if f and f.filename:
                attachment = SupportTicketAttachment(
                    ticket_id=ticket.id,
                    filename=f.filename,
                    mimetype=f.content_type or 'application/octet-stream',
                    size=0,
                    data=f.read()
                )
                attachment.size = len(attachment.data)
                db.session.add(attachment)
                attachment_count += 1

        db.session.commit()
        print(f'Ticket {ticket.ticket_number} created with {attachment_count} attachment(s)')

        # Send email notifications (non-blocking)
        try:
            send_ticket_notifications(ticket, attachment_count)
        except Exception as e:
            print(f'Email notification error (non-blocking): {e}')

        return jsonify({
            'success': True,
            'ticket_number': ticket.ticket_number,
            'message': 'Your ticket has been submitted successfully. You will receive a confirmation email shortly.'
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f'Error submitting ticket: {e}')
        return jsonify({'error': 'Failed to submit ticket'}), 500


# ==================== ADMIN ROUTES ====================

@support_tickets_bp.route('/api/support-tickets', methods=['GET'])
def get_all_tickets():
    """Get all tickets with optional filters - scoped by organization"""
    try:
        status = request.args.get('status')
        ticket_type = request.args.get('type')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)

        query = SupportTicket.query

        # Organization scoping - only show tickets from the user's organization
        org_id = get_current_user_org_id()
        if org_id:
            query = query.filter(SupportTicket.organization_id == org_id)

        if status:
            query = query.filter(SupportTicket.status == status)
        if ticket_type:
            query = query.filter(SupportTicket.type == ticket_type)

        total = query.count()

        # Order: open first, then by priority, then by date
        tickets = query.order_by(
            db.case(
                (SupportTicket.status == 'open', 1),
                (SupportTicket.status == 'in_progress', 2),
                (SupportTicket.status == 'resolved', 3),
                (SupportTicket.status == 'closed', 4),
                else_=5
            ),
            db.case(
                (SupportTicket.priority == 'critical', 1),
                (SupportTicket.priority == 'high', 2),
                (SupportTicket.priority == 'medium', 3),
                (SupportTicket.priority == 'low', 4),
                else_=5
            ),
            SupportTicket.created_at.desc()
        ).limit(limit).offset(offset).all()

        return jsonify({
            'tickets': [t.to_dict() for t in tickets],
            'total': total
        })

    except Exception as e:
        print(f'Error fetching tickets: {e}')
        return jsonify({'error': 'Failed to fetch tickets'}), 500


@support_tickets_bp.route('/api/support-tickets/stats', methods=['GET'])
def get_ticket_stats():
    """Get ticket statistics - scoped by organization"""
    try:
        # Organization scoping
        org_id = get_current_user_org_id()
        base_query = SupportTicket.query
        if org_id:
            base_query = base_query.filter(SupportTicket.organization_id == org_id)

        total = base_query.count()
        open_count = base_query.filter(SupportTicket.status == 'open').count()
        in_progress = base_query.filter(SupportTicket.status == 'in_progress').count()
        resolved = base_query.filter(SupportTicket.status == 'resolved').count()
        closed = base_query.filter(SupportTicket.status == 'closed').count()

        type_query = db.session.query(
            SupportTicket.type,
            db.func.count(SupportTicket.id)
        )
        if org_id:
            type_query = type_query.filter(SupportTicket.organization_id == org_id)
        by_type = type_query.group_by(SupportTicket.type).all()

        return jsonify({
            'total': total,
            'open': open_count,
            'in_progress': in_progress,
            'resolved': resolved,
            'closed': closed,
            'by_type': [{'type': t, 'count': c} for t, c in by_type]
        })

    except Exception as e:
        print(f'Error fetching ticket stats: {e}')
        return jsonify({'error': 'Failed to fetch ticket stats'}), 500


@support_tickets_bp.route('/api/support-tickets/<int:ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    """Get a single ticket by ID with comments"""
    try:
        ticket = SupportTicket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        return jsonify(ticket.to_dict(include_comments=True))
    except Exception as e:
        print(f'Error fetching ticket: {e}')
        return jsonify({'error': 'Failed to fetch ticket'}), 500


@support_tickets_bp.route('/api/support-tickets/<int:ticket_id>/with-comments', methods=['GET'])
def get_ticket_with_comments(ticket_id):
    """Get a single ticket by ID with all comments included"""
    try:
        ticket = SupportTicket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        return jsonify(ticket.to_dict(include_comments=True))
    except Exception as e:
        print(f'Error fetching ticket with comments: {e}')
        return jsonify({'error': 'Failed to fetch ticket'}), 500


@support_tickets_bp.route('/api/support-tickets/<int:ticket_id>', methods=['PUT'])
def update_ticket(ticket_id):
    """Update ticket status, priority, type, or resolution notes"""
    try:
        ticket = SupportTicket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404

        data = request.get_json() or {}

        if 'status' in data:
            if data['status'] not in ('open', 'in_progress', 'resolved', 'closed'):
                return jsonify({'error': 'Invalid status'}), 400
            ticket.status = data['status']
            if data['status'] in ('resolved', 'closed'):
                ticket.resolved_at = datetime.utcnow()

        if 'priority' in data:
            if data['priority'] not in ('low', 'medium', 'high', 'critical'):
                return jsonify({'error': 'Invalid priority'}), 400
            ticket.priority = data['priority']

        if 'type' in data:
            if data['type'] not in ('bug', 'enhancement', 'question'):
                return jsonify({'error': 'Invalid type'}), 400
            ticket.type = data['type']

        if 'resolution_notes' in data:
            ticket.resolution_notes = data['resolution_notes']

        if 'resolved_by' in data:
            ticket.resolved_by = data['resolved_by']

        ticket.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify(ticket.to_dict(include_comments=True))

    except Exception as e:
        db.session.rollback()
        print(f'Error updating ticket: {e}')
        return jsonify({'error': 'Failed to update ticket'}), 500


# ==================== COMMENTS ====================

@support_tickets_bp.route('/api/support-tickets/<int:ticket_id>/comments', methods=['GET'])
def get_comments(ticket_id):
    """Get all comments for a ticket"""
    try:
        ticket = SupportTicket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404

        comments = SupportTicketComment.query.filter_by(
            ticket_id=ticket_id
        ).order_by(SupportTicketComment.created_at.asc()).all()

        return jsonify({
            'comments': [c.to_dict() for c in comments]
        })

    except Exception as e:
        print(f'Error fetching comments: {e}')
        return jsonify({'error': 'Failed to fetch comments'}), 500


@support_tickets_bp.route('/api/support-tickets/<int:ticket_id>/comments', methods=['POST'])
def add_comment(ticket_id):
    """Add a comment to a ticket"""
    try:
        ticket = SupportTicket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404

        data = request.get_json() or {}
        message_text = data.get('message')
        if not message_text:
            return jsonify({'error': 'Message is required'}), 400

        comment_type = data.get('comment_type', 'user_comment')
        if comment_type not in ('user_comment', 'system_resolution', 'system_note', 'initial_submission'):
            return jsonify({'error': 'Invalid comment_type'}), 400

        comment = SupportTicketComment(
            ticket_id=ticket_id,
            comment_type=comment_type,
            message=message_text,
            created_by_name=data.get('created_by_name'),
            created_by_email=data.get('created_by_email'),
            created_by_user_id=data.get('created_by_user_id'),
            is_internal=data.get('is_internal', False)
        )
        db.session.add(comment)

        # Update ticket metadata
        ticket.last_comment_at = datetime.utcnow()
        ticket.last_comment_by = data.get('created_by_name') or 'Unknown'
        ticket.updated_at = datetime.utcnow()

        # Auto-reopen if user adds a comment to a resolved/closed ticket
        if comment_type == 'user_comment' and ticket.status in ('resolved', 'closed'):
            ticket.status = 'open'
            ticket.reopened_count = (ticket.reopened_count or 0) + 1
            ticket.resolved_at = None

        db.session.commit()

        # Send comment notification email if admin/system is requesting more info
        if comment_type == 'system_note' and not data.get('is_internal', False):
            try:
                send_comment_notification_email(ticket, message_text)
            except Exception as e:
                print(f'Comment notification email error (non-blocking): {e}')

        return jsonify(comment.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        print(f'Error adding comment: {e}')
        return jsonify({'error': 'Failed to add comment'}), 500


# ==================== ATTACHMENTS ====================

@support_tickets_bp.route('/api/support-tickets/<int:ticket_id>/attachments', methods=['GET'])
def get_attachments(ticket_id):
    """Get attachment metadata for a ticket"""
    try:
        ticket = SupportTicket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404

        attachments = SupportTicketAttachment.query.filter_by(
            ticket_id=ticket_id
        ).all()

        return jsonify({
            'attachments': [a.to_dict() for a in attachments]
        })

    except Exception as e:
        print(f'Error fetching attachments: {e}')
        return jsonify({'error': 'Failed to fetch attachments'}), 500


@support_tickets_bp.route('/api/support-tickets/<int:ticket_id>/attachments/<int:attachment_id>/download', methods=['GET'])
def download_attachment(ticket_id, attachment_id):
    """Download an attachment file"""
    try:
        attachment = SupportTicketAttachment.query.filter_by(
            id=attachment_id,
            ticket_id=ticket_id
        ).first()

        if not attachment:
            return jsonify({'error': 'Attachment not found'}), 404

        response = make_response(attachment.data)
        response.headers['Content-Type'] = attachment.mimetype
        response.headers['Content-Disposition'] = f'inline; filename="{attachment.filename}"'
        response.headers['Content-Length'] = attachment.size
        return response

    except Exception as e:
        print(f'Error downloading attachment: {e}')
        return jsonify({'error': 'Failed to download attachment'}), 500


# ==================== RESOLVE & CLOSE ====================

@support_tickets_bp.route('/api/support-tickets/<int:ticket_id>/resolve', methods=['POST'])
def resolve_ticket(ticket_id):
    """Resolve a ticket with fix summary and testing instructions, and send resolution email"""
    try:
        ticket = SupportTicket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404

        data = request.get_json() or {}
        fix_summary = data.get('fix_summary', '') or data.get('resolution_notes', '')
        testing_instructions = data.get('testing_instructions', '')
        resolved_by = data.get('resolved_by', 'Support Team')

        if not fix_summary:
            return jsonify({'error': 'fix_summary or resolution_notes is required'}), 400

        # Add resolution comment
        resolution_message = f"**Fix Summary:**\n{fix_summary}"
        if testing_instructions:
            resolution_message += f"\n\n**How to Test:**\n{testing_instructions}"

        comment = SupportTicketComment(
            ticket_id=ticket_id,
            comment_type='system_resolution',
            message=resolution_message,
            created_by_name=resolved_by,
            is_internal=False
        )
        db.session.add(comment)

        # Update ticket
        ticket.status = 'resolved'
        ticket.resolved_at = datetime.utcnow()
        ticket.resolved_by = resolved_by
        ticket.resolution_notes = fix_summary
        ticket.last_comment_at = datetime.utcnow()
        ticket.last_comment_by = resolved_by
        ticket.updated_at = datetime.utcnow()

        db.session.commit()

        # Send resolution email
        try:
            send_resolution_email(ticket, fix_summary, testing_instructions)
        except Exception as e:
            print(f'Resolution email error (non-blocking): {e}')

        return jsonify({
            'success': True,
            'ticket': ticket.to_dict(include_comments=True)
        })

    except Exception as e:
        db.session.rollback()
        print(f'Error resolving ticket: {e}')
        return jsonify({'error': 'Failed to resolve ticket'}), 500


@support_tickets_bp.route('/api/support-tickets/<int:ticket_id>/close', methods=['POST'])
def close_ticket(ticket_id):
    """Close a resolved ticket (user confirms fix worked)"""
    try:
        ticket = SupportTicket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404

        ticket.status = 'closed'
        ticket.updated_at = datetime.utcnow()
        if not ticket.resolved_at:
            ticket.resolved_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'ticket': ticket.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        print(f'Error closing ticket: {e}')
        return jsonify({'error': 'Failed to close ticket'}), 500
