from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.support_ticket import SupportTicket, SupportTicketAttachment
from datetime import datetime
import os
import json

support_tickets_bp = Blueprint('support_tickets', __name__)

# ==================== HELPERS ====================

def generate_ticket_number():
    """Generate a unique ticket number in format TKT-YYYY-NNNN"""
    year = datetime.utcnow().year
    prefix = f'TKT-{year}-'
    count = SupportTicket.query.filter(
        SupportTicket.ticket_number.like(f'{prefix}%')
    ).count()
    return f'{prefix}{str(count + 1).zfill(4)}'


def send_ticket_notifications(ticket, attachment_count=0):
    """Send email notifications via SendGrid"""
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent
    except ImportError:
        print('SendGrid not installed, skipping email notifications')
        return

    api_key = os.environ.get('SENDGRID_API_KEY')
    if not api_key:
        print('SENDGRID_API_KEY not configured, skipping email notifications')
        return

    from_email = os.environ.get('SENDGRID_FROM_EMAIL', 'noreply@molinops.com')
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
        sg = sendgrid.SendGridAPIClient(api_key=api_key)
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
                    size=0,  # Will update after reading
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
    """Get all tickets with optional filters"""
    try:
        status = request.args.get('status')
        ticket_type = request.args.get('type')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)

        query = SupportTicket.query

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
    """Get ticket statistics"""
    try:
        total = SupportTicket.query.count()
        open_count = SupportTicket.query.filter_by(status='open').count()
        in_progress = SupportTicket.query.filter_by(status='in_progress').count()
        resolved = SupportTicket.query.filter_by(status='resolved').count()
        closed = SupportTicket.query.filter_by(status='closed').count()

        by_type = db.session.query(
            SupportTicket.type,
            db.func.count(SupportTicket.id)
        ).group_by(SupportTicket.type).all()

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
    """Get a single ticket by ID"""
    try:
        ticket = SupportTicket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        return jsonify(ticket.to_dict())
    except Exception as e:
        print(f'Error fetching ticket: {e}')
        return jsonify({'error': 'Failed to fetch ticket'}), 500


@support_tickets_bp.route('/api/support-tickets/<int:ticket_id>', methods=['PUT'])
def update_ticket(ticket_id):
    """Update ticket status, priority, or resolution notes"""
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

        if 'resolution_notes' in data:
            ticket.resolution_notes = data['resolution_notes']

        if 'resolved_by' in data:
            ticket.resolved_by = data['resolved_by']

        ticket.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify(ticket.to_dict())

    except Exception as e:
        db.session.rollback()
        print(f'Error updating ticket: {e}')
        return jsonify({'error': 'Failed to update ticket'}), 500
