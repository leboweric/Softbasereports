"""
VITAL Anonymous Questions Database Model
Stores anonymous employee questions for HR review and trend analysis
"""

from datetime import datetime
from src.extensions import db


class AnonymousQuestion(db.Model):
    """Model for storing anonymous employee questions"""
    
    __tablename__ = 'vital_anonymous_questions'
    
    id = db.Column(db.String(36), primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False, default='Other')
    anonymous_id = db.Column(db.String(12), nullable=True)  # Hashed user ID for tracking
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, addressed, archived
    admin_notes = db.Column(db.Text, nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    
    # Index for faster queries
    __table_args__ = (
        db.Index('idx_vital_questions_category', 'category'),
        db.Index('idx_vital_questions_status', 'status'),
        db.Index('idx_vital_questions_submitted', 'submitted_at'),
    )
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'question_text': self.question_text,
            'category': self.category,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'status': self.status,
            'admin_notes': self.admin_notes,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None
        }
    
    def __repr__(self):
        return f'<AnonymousQuestion {self.id[:8]}... [{self.category}]>'


class TrendAnalysis(db.Model):
    """Model for storing AI-generated trend analyses"""
    
    __tablename__ = 'vital_trend_analyses'
    
    id = db.Column(db.String(36), primary_key=True)
    analysis_date = db.Column(db.DateTime, default=datetime.utcnow)
    period_days = db.Column(db.Integer, default=30)
    total_questions = db.Column(db.Integer, default=0)
    trends_json = db.Column(db.Text, nullable=True)  # JSON string of trends
    actions_json = db.Column(db.Text, nullable=True)  # JSON string of suggested actions
    sentiment_json = db.Column(db.Text, nullable=True)  # JSON string of sentiment analysis
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        import json
        return {
            'id': self.id,
            'analysis_date': self.analysis_date.isoformat() if self.analysis_date else None,
            'period_days': self.period_days,
            'total_questions': self.total_questions,
            'trends': json.loads(self.trends_json) if self.trends_json else [],
            'suggested_actions': json.loads(self.actions_json) if self.actions_json else [],
            'sentiment': json.loads(self.sentiment_json) if self.sentiment_json else {}
        }
    
    def __repr__(self):
        return f'<TrendAnalysis {self.analysis_date.strftime("%Y-%m-%d")} ({self.total_questions} questions)>'
