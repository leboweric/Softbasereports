"""
Sentiment Analysis Service
Analyzes satisfaction comments and feedback from case data
Uses keyword-based sentiment analysis with option for LLM enhancement
"""
import re
from collections import Counter
from datetime import datetime, timedelta

# Sentiment keyword dictionaries
POSITIVE_KEYWORDS = [
    'excellent', 'great', 'amazing', 'wonderful', 'fantastic', 'outstanding',
    'helpful', 'professional', 'caring', 'supportive', 'understanding',
    'recommend', 'satisfied', 'happy', 'pleased', 'grateful', 'thankful',
    'awesome', 'perfect', 'best', 'love', 'appreciate', 'kind', 'friendly',
    'responsive', 'thorough', 'knowledgeable', 'effective', 'efficient',
    'comfortable', 'safe', 'listened', 'heard', 'validated', 'empathetic'
]

NEGATIVE_KEYWORDS = [
    'terrible', 'awful', 'horrible', 'bad', 'poor', 'worst', 'disappointed',
    'frustrating', 'frustrated', 'unhelpful', 'unprofessional', 'rude',
    'slow', 'delayed', 'waiting', 'wait', 'long', 'never', 'didn\'t',
    'couldn\'t', 'wouldn\'t', 'problem', 'issue', 'complaint', 'difficult',
    'confusing', 'confused', 'unclear', 'unavailable', 'unresponsive',
    'ignored', 'dismissive', 'rushed', 'impersonal', 'cold', 'uncaring'
]

NEUTRAL_KEYWORDS = [
    'okay', 'ok', 'fine', 'average', 'adequate', 'acceptable', 'standard',
    'normal', 'typical', 'expected', 'satisfactory', 'decent', 'fair'
]

# Topic categories for feedback
TOPIC_KEYWORDS = {
    'wait_time': ['wait', 'waiting', 'delayed', 'delay', 'slow', 'long time', 'took forever', 'hours', 'days'],
    'provider_quality': ['counselor', 'therapist', 'provider', 'coach', 'professional', 'clinician', 'doctor'],
    'communication': ['communication', 'response', 'respond', 'call back', 'email', 'contact', 'reach', 'available'],
    'scheduling': ['schedule', 'appointment', 'booking', 'reschedule', 'cancel', 'availability', 'time slot'],
    'platform': ['app', 'website', 'portal', 'system', 'technology', 'login', 'access', 'online'],
    'service_quality': ['service', 'help', 'support', 'care', 'treatment', 'session', 'experience'],
    'billing': ['bill', 'billing', 'charge', 'cost', 'payment', 'insurance', 'coverage', 'fee'],
    'confidentiality': ['confidential', 'privacy', 'private', 'secure', 'anonymous', 'discreet']
}


def analyze_sentiment(text):
    """
    Analyze sentiment of a single text string
    Returns: dict with sentiment score, label, and matched keywords
    """
    if not text or not isinstance(text, str):
        return {'score': 0, 'label': 'neutral', 'positive_matches': [], 'negative_matches': []}
    
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)
    
    positive_matches = [w for w in POSITIVE_KEYWORDS if w in text_lower]
    negative_matches = [w for w in NEGATIVE_KEYWORDS if w in text_lower]
    
    positive_count = len(positive_matches)
    negative_count = len(negative_matches)
    
    # Calculate sentiment score (-1 to 1)
    total = positive_count + negative_count
    if total == 0:
        score = 0
        label = 'neutral'
    else:
        score = (positive_count - negative_count) / total
        if score > 0.2:
            label = 'positive'
        elif score < -0.2:
            label = 'negative'
        else:
            label = 'neutral'
    
    return {
        'score': round(score, 2),
        'label': label,
        'positive_matches': positive_matches,
        'negative_matches': negative_matches
    }


def extract_topics(text):
    """
    Extract topics mentioned in feedback text
    Returns: list of topic categories found
    """
    if not text or not isinstance(text, str):
        return []
    
    text_lower = text.lower()
    found_topics = []
    
    for topic, keywords in TOPIC_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                found_topics.append(topic)
                break
    
    return found_topics


def analyze_feedback_batch(feedbacks):
    """
    Analyze a batch of feedback comments
    Returns: aggregated sentiment analysis results
    """
    results = {
        'total_analyzed': 0,
        'sentiment_distribution': {'positive': 0, 'neutral': 0, 'negative': 0},
        'average_score': 0,
        'topic_frequency': Counter(),
        'top_positive_keywords': Counter(),
        'top_negative_keywords': Counter(),
        'sample_positive': [],
        'sample_negative': [],
        'trend_data': []
    }
    
    scores = []
    
    for feedback in feedbacks:
        if not feedback.get('comment'):
            continue
        
        results['total_analyzed'] += 1
        
        # Analyze sentiment
        sentiment = analyze_sentiment(feedback['comment'])
        scores.append(sentiment['score'])
        results['sentiment_distribution'][sentiment['label']] += 1
        
        # Track keywords
        for kw in sentiment['positive_matches']:
            results['top_positive_keywords'][kw] += 1
        for kw in sentiment['negative_matches']:
            results['top_negative_keywords'][kw] += 1
        
        # Extract topics
        topics = extract_topics(feedback['comment'])
        for topic in topics:
            results['topic_frequency'][topic] += 1
        
        # Collect samples
        if sentiment['label'] == 'positive' and len(results['sample_positive']) < 5:
            results['sample_positive'].append({
                'comment': feedback['comment'][:200],
                'score': sentiment['score'],
                'date': feedback.get('date'),
                'satisfaction': feedback.get('satisfaction')
            })
        elif sentiment['label'] == 'negative' and len(results['sample_negative']) < 5:
            results['sample_negative'].append({
                'comment': feedback['comment'][:200],
                'score': sentiment['score'],
                'date': feedback.get('date'),
                'satisfaction': feedback.get('satisfaction')
            })
    
    # Calculate average score
    if scores:
        results['average_score'] = round(sum(scores) / len(scores), 2)
    
    # Convert counters to sorted lists
    results['top_positive_keywords'] = [
        {'keyword': k, 'count': v} 
        for k, v in results['top_positive_keywords'].most_common(10)
    ]
    results['top_negative_keywords'] = [
        {'keyword': k, 'count': v} 
        for k, v in results['top_negative_keywords'].most_common(10)
    ]
    results['topic_frequency'] = [
        {'topic': k.replace('_', ' ').title(), 'count': v}
        for k, v in results['topic_frequency'].most_common()
    ]
    
    return results


def calculate_sentiment_trend(feedbacks_by_date):
    """
    Calculate sentiment trend over time
    feedbacks_by_date: dict with date keys and list of feedbacks as values
    Returns: list of trend data points
    """
    trend = []
    
    for date, feedbacks in sorted(feedbacks_by_date.items()):
        if not feedbacks:
            continue
        
        scores = []
        sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
        
        for feedback in feedbacks:
            if feedback.get('comment'):
                sentiment = analyze_sentiment(feedback['comment'])
                scores.append(sentiment['score'])
                sentiment_counts[sentiment['label']] += 1
        
        if scores:
            trend.append({
                'date': date,
                'average_score': round(sum(scores) / len(scores), 2),
                'count': len(scores),
                'positive': sentiment_counts['positive'],
                'neutral': sentiment_counts['neutral'],
                'negative': sentiment_counts['negative']
            })
    
    return trend
