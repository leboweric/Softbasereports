from src.models.user import db
from datetime import datetime


class SupportTicket(db.Model):
    __tablename__ = 'support_ticket'

    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(20), unique=True, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'bug', 'enhancement', 'question'
    status = db.Column(db.String(20), default='open')  # 'open', 'in_progress', 'resolved', 'closed'
    priority = db.Column(db.String(20), default='medium')  # 'low', 'medium', 'high', 'critical'
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    page_url = db.Column(db.String(500), nullable=True)
    submitted_by = db.Column(db.Integer, nullable=True)
    submitted_by_name = db.Column(db.String(100), nullable=True)
    submitted_by_email = db.Column(db.String(255), nullable=True)
    organization_id = db.Column(db.Integer, nullable=True)
    resolved_by = db.Column(db.String(100), nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)

    # Relationship to attachments
    attachments = db.relationship('SupportTicketAttachment', backref='ticket', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'ticket_number': self.ticket_number,
            'type': self.type,
            'status': self.status,
            'priority': self.priority,
            'subject': self.subject,
            'message': self.message,
            'page_url': self.page_url,
            'submitted_by': self.submitted_by,
            'submitted_by_name': self.submitted_by_name,
            'submitted_by_email': self.submitted_by_email,
            'organization_id': self.organization_id,
            'resolved_by': self.resolved_by,
            'resolution_notes': self.resolution_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'attachments': [a.to_dict() for a in self.attachments] if self.attachments else []
        }


class SupportTicketAttachment(db.Model):
    __tablename__ = 'support_ticket_attachment'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('support_ticket.id', ondelete='CASCADE'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    mimetype = db.Column(db.String(100), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'mimetype': self.mimetype,
            'size': self.size,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
