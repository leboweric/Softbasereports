"""
VITAL Anonymous Questions Service
Provides anonymous question submission and AI-powered trend analysis
Uses Claude AI (via OpenAI-compatible API) for trend identification and action suggestions
"""

import os
import logging
import json
from datetime import datetime, timedelta
from openai import OpenAI
import hashlib
import uuid

logger = logging.getLogger(__name__)


class VitalAnonymousQuestionsService:
    """Service class for VITAL Anonymous Questions feature"""
    
    # Question categories for classification
    CATEGORIES = [
        "Benefits & Compensation",
        "Work-Life Balance",
        "Career Development",
        "Management & Leadership",
        "Company Culture",
        "Policies & Procedures",
        "Workplace Environment",
        "Team Dynamics",
        "Communication",
        "Other"
    ]
    
    def __init__(self, db_session=None):
        """Initialize with database session and AI client"""
        self.db_session = db_session
        
        # Initialize OpenAI-compatible client for Claude
        self.ai_client = OpenAI()  # Uses OPENAI_API_KEY env var
        self.ai_model = "gpt-4.1-mini"  # Available model
    
    def _generate_anonymous_id(self, user_id):
        """Generate a consistent anonymous ID for a user (for tracking without identifying)"""
        # Use a hash that's consistent but not reversible
        salt = os.environ.get('ANONYMOUS_SALT', 'vital-anonymous-2024')
        combined = f"{salt}:{user_id}"
        return hashlib.sha256(combined.encode()).hexdigest()[:12]
    
    def submit_question(self, question_text, user_id=None, category=None):
        """Submit an anonymous question"""
        try:
            from src.models.vital_questions import AnonymousQuestion
            
            # Generate anonymous tracking ID if user is logged in
            anonymous_id = self._generate_anonymous_id(user_id) if user_id else None
            
            # Auto-categorize if not provided
            if not category:
                category = self._categorize_question(question_text)
            
            # Create question record
            question = AnonymousQuestion(
                id=str(uuid.uuid4()),
                question_text=question_text,
                category=category,
                anonymous_id=anonymous_id,
                submitted_at=datetime.utcnow(),
                status='pending'
            )
            
            self.db_session.add(question)
            self.db_session.commit()
            
            logger.info(f"Anonymous question submitted: {question.id}")
            
            return {
                "success": True,
                "question_id": question.id,
                "category": category,
                "message": "Your question has been submitted anonymously."
            }
        except Exception as e:
            logger.error(f"Error submitting question: {str(e)}")
            if self.db_session:
                self.db_session.rollback()
            raise
    
    def _categorize_question(self, question_text):
        """Use AI to categorize a question"""
        try:
            prompt = f"""Categorize the following anonymous employee question into exactly ONE of these categories:
{', '.join(self.CATEGORIES)}

Question: "{question_text}"

Respond with ONLY the category name, nothing else."""

            response = self.ai_client.chat.completions.create(
                model=self.ai_model,
                messages=[
                    {"role": "system", "content": "You are an HR assistant that categorizes employee questions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.3
            )
            
            category = response.choices[0].message.content.strip()
            
            # Validate category
            if category in self.CATEGORIES:
                return category
            else:
                # Find closest match
                for cat in self.CATEGORIES:
                    if cat.lower() in category.lower() or category.lower() in cat.lower():
                        return cat
                return "Other"
        except Exception as e:
            logger.warning(f"AI categorization failed: {str(e)}, defaulting to 'Other'")
            return "Other"
    
    def get_questions(self, status=None, category=None, days=30, limit=100):
        """Get anonymous questions with optional filters"""
        try:
            from src.models.vital_questions import AnonymousQuestion
            
            query = AnonymousQuestion.query
            
            # Apply filters
            if status:
                query = query.filter(AnonymousQuestion.status == status)
            
            if category:
                query = query.filter(AnonymousQuestion.category == category)
            
            if days:
                cutoff = datetime.utcnow() - timedelta(days=days)
                query = query.filter(AnonymousQuestion.submitted_at >= cutoff)
            
            # Order by newest first
            query = query.order_by(AnonymousQuestion.submitted_at.desc())
            
            if limit:
                query = query.limit(limit)
            
            questions = query.all()
            
            return {
                "total": len(questions),
                "questions": [q.to_dict() for q in questions]
            }
        except Exception as e:
            logger.error(f"Error getting questions: {str(e)}")
            raise
    
    def get_question_stats(self, days=30):
        """Get statistics about questions"""
        try:
            from src.models.vital_questions import AnonymousQuestion
            from sqlalchemy import func
            
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            # Total questions
            total = AnonymousQuestion.query.filter(
                AnonymousQuestion.submitted_at >= cutoff
            ).count()
            
            # By category
            category_counts = self.db_session.query(
                AnonymousQuestion.category,
                func.count(AnonymousQuestion.id)
            ).filter(
                AnonymousQuestion.submitted_at >= cutoff
            ).group_by(AnonymousQuestion.category).all()
            
            # By status
            status_counts = self.db_session.query(
                AnonymousQuestion.status,
                func.count(AnonymousQuestion.id)
            ).filter(
                AnonymousQuestion.submitted_at >= cutoff
            ).group_by(AnonymousQuestion.status).all()
            
            # Questions per week
            weekly_counts = []
            for i in range(4):
                week_start = datetime.utcnow() - timedelta(days=(i+1)*7)
                week_end = datetime.utcnow() - timedelta(days=i*7)
                count = AnonymousQuestion.query.filter(
                    AnonymousQuestion.submitted_at >= week_start,
                    AnonymousQuestion.submitted_at < week_end
                ).count()
                weekly_counts.append({
                    "week": f"Week {i+1}",
                    "count": count
                })
            
            return {
                "period_days": days,
                "total_questions": total,
                "by_category": [{"category": cat, "count": count} for cat, count in category_counts],
                "by_status": [{"status": status, "count": count} for status, count in status_counts],
                "weekly_trend": list(reversed(weekly_counts))
            }
        except Exception as e:
            logger.error(f"Error getting question stats: {str(e)}")
            raise
    
    def analyze_trends(self, days=30):
        """Use AI to analyze trends in questions and suggest actions"""
        try:
            # Get recent questions
            questions_data = self.get_questions(days=days, limit=200)
            questions = questions_data.get('questions', [])
            
            if len(questions) < 3:
                return {
                    "analysis_date": datetime.utcnow().isoformat(),
                    "period_days": days,
                    "total_questions_analyzed": len(questions),
                    "message": "Not enough questions to identify meaningful trends. At least 3 questions are needed.",
                    "trends": [],
                    "suggested_actions": []
                }
            
            # Prepare questions for analysis
            questions_text = "\n".join([
                f"- [{q['category']}] {q['question_text']}" 
                for q in questions
            ])
            
            # Get category distribution
            category_summary = {}
            for q in questions:
                cat = q.get('category', 'Other')
                category_summary[cat] = category_summary.get(cat, 0) + 1
            
            category_text = "\n".join([
                f"- {cat}: {count} questions" 
                for cat, count in sorted(category_summary.items(), key=lambda x: x[1], reverse=True)
            ])
            
            prompt = f"""As an HR analytics expert, analyze the following anonymous employee questions submitted over the past {days} days.

CATEGORY DISTRIBUTION:
{category_text}

QUESTIONS:
{questions_text}

Please provide:

1. **KEY TRENDS** (identify 3-5 main themes or concerns emerging from these questions)
   For each trend, explain:
   - What the trend is
   - How many questions relate to it
   - Why this might be a concern

2. **SUGGESTED ACTIONS** (provide 3-5 specific, actionable recommendations for HR)
   For each action, explain:
   - What to do
   - Why it addresses the identified trends
   - Priority level (High/Medium/Low)

3. **SENTIMENT ANALYSIS**
   - Overall employee sentiment based on questions
   - Areas of particular concern
   - Any positive themes

Format your response as JSON with this structure:
{{
    "trends": [
        {{"trend": "...", "question_count": N, "description": "...", "concern_level": "High/Medium/Low"}}
    ],
    "suggested_actions": [
        {{"action": "...", "rationale": "...", "priority": "High/Medium/Low", "addresses_trends": ["..."]}}
    ],
    "sentiment": {{
        "overall": "Positive/Neutral/Concerned/Negative",
        "key_concerns": ["..."],
        "positive_themes": ["..."]
    }}
}}"""

            response = self.ai_client.chat.completions.create(
                model=self.ai_model,
                messages=[
                    {"role": "system", "content": "You are an expert HR analytics consultant who helps organizations understand employee concerns and improve workplace culture. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                # Handle potential markdown code blocks
                if ai_response.startswith("```"):
                    ai_response = ai_response.split("```")[1]
                    if ai_response.startswith("json"):
                        ai_response = ai_response[4:]
                
                analysis = json.loads(ai_response)
            except json.JSONDecodeError:
                logger.warning("AI response was not valid JSON, using raw text")
                analysis = {
                    "trends": [{"trend": "Analysis available", "description": ai_response, "concern_level": "Medium"}],
                    "suggested_actions": [],
                    "sentiment": {"overall": "Unknown", "key_concerns": [], "positive_themes": []}
                }
            
            return {
                "analysis_date": datetime.utcnow().isoformat(),
                "period_days": days,
                "total_questions_analyzed": len(questions),
                "category_distribution": category_summary,
                **analysis
            }
        except Exception as e:
            logger.error(f"Error analyzing trends: {str(e)}")
            raise
    
    def update_question_status(self, question_id, status, admin_notes=None):
        """Update the status of a question (for HR admin)"""
        try:
            from src.models.vital_questions import AnonymousQuestion
            
            question = AnonymousQuestion.query.get(question_id)
            if not question:
                raise ValueError(f"Question not found: {question_id}")
            
            valid_statuses = ['pending', 'reviewed', 'addressed', 'archived']
            if status not in valid_statuses:
                raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
            
            question.status = status
            if admin_notes:
                question.admin_notes = admin_notes
            question.reviewed_at = datetime.utcnow()
            
            self.db_session.commit()
            
            return {
                "success": True,
                "question_id": question_id,
                "new_status": status
            }
        except Exception as e:
            logger.error(f"Error updating question status: {str(e)}")
            if self.db_session:
                self.db_session.rollback()
            raise
    
    def get_dashboard_data(self, days=30):
        """Get comprehensive dashboard data for Anonymous Questions"""
        try:
            stats = self.get_question_stats(days=days)
            recent = self.get_questions(days=7, limit=10)
            
            # Get pending questions count
            pending = self.get_questions(status='pending', days=days)
            
            return {
                "stats": stats,
                "recent_questions": recent.get('questions', []),
                "pending_count": pending.get('total', 0),
                "last_updated": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting dashboard data: {str(e)}")
            raise
