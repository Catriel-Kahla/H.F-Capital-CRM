"""
Lead Scoring System

Implements sophisticated multi-signal lead scoring algorithm based on:
1. Session count (engagement)
2. Job title hierarchy (buying power)
3. Team adoption signals (multiple users per enterprise domain)
4. Enterprise domain indicators
5. Email type signals
"""

from django.db.models import Q, Count
import re


# Free email providers list
FREE_EMAIL_DOMAINS = {
    'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
    'aol.com', 'mail.com', 'yandex.com', 'protonmail.com',
    'icloud.com', 'mail.ru', 'qq.com', '163.com',
    'gmx.com', 'web.de', 'live.com', 'msn.com',
    'inbox.com', 'zoho.com', 'fastmail.com', 'tutanota.com',
    'hotmail.co.uk', 'yahoo.co.uk', 'myyahoo.com',
}

# Job title scoring hierarchy
JOB_TITLE_SCORES = {
    'ciso': 20,
    'cto': 20,
    'chief information': 20,
    'chief technology': 20,
    'vp': 15,
    'vice president': 15,
    'director': 15,
    'manager': 10,
    'senior': 8,
    'engineer': 5,
    'developer': 5,
    'analyst': 5,
    'specialist': 5,
}


def is_free_email_domain(email: str) -> bool:
    """Check if email is from a free email provider."""
    if not email or '@' not in email:
        return False
    domain = email.split('@')[1].lower()
    return domain in FREE_EMAIL_DOMAINS


def extract_domain(email: str) -> str:
    """Extract domain from email address."""
    if not email or '@' not in email:
        return None
    return email.split('@')[1].lower()


def get_job_title_score(job_title: str) -> int:
    """Calculate score based on job title."""
    if not job_title:
        return 0
    
    job_title_lower = job_title.lower()
    
    # Check for CISO/CTO first (highest priority)
    if 'ciso' in job_title_lower or 'chief information' in job_title_lower:
        return 20
    if 'cto' in job_title_lower or 'chief technology' in job_title_lower:
        return 20
    
    # Check for VP/Director
    if 'vp ' in job_title_lower or 'vice president' in job_title_lower:
        return 15
    if 'director' in job_title_lower:
        return 15
    
    # Check for Manager
    if 'manager' in job_title_lower:
        return 10
    
    # Check for Senior
    if 'senior' in job_title_lower:
        return 8
    
    # Default for IC roles
    for keyword in ['engineer', 'developer', 'analyst', 'specialist']:
        if keyword in job_title_lower:
            return 5
    
    return 0


def count_users_per_domain(lead_domain: str) -> dict:
    """
    Count unique users per enterprise domain (excluding free email providers).
    
    Returns:
        dict: {domain: user_count, ...} for enterprise domains only
    """
    from leads.models import Lead
    
    # Get all leads
    all_leads = Lead.objects.filter(company__domain=lead_domain)
    
    users_per_domain = {}
    for lead in all_leads:
        email_domain = extract_domain(lead.email)
        
        # Only count if NOT a free email domain
        if email_domain and not is_free_email_domain(lead.email):
            if email_domain not in users_per_domain:
                users_per_domain[email_domain] = set()
            users_per_domain[email_domain].add(lead.email)
    
    # Convert sets to counts
    return {domain: len(emails) for domain, emails in users_per_domain.items()}


def calculate_lead_score(lead) -> tuple:
    """
    Calculate lead score and stage based on multiple signals.
    
    Returns:
        tuple: (score: int, stage: str)
    """
    score = 0
    
    # Signal 1: Base Score - Session Count (0-50 points)
    # 1 session = 1 point (max 50)
    if lead.session_count:
        session_score = min(lead.session_count, 50)
        score += session_score
    
    # Signal 2: Product Adoption - Months of Usage
    # 6+ months of usage = +25 bonus
    # Estimated from session count: ~10 sessions per month
    if lead.session_count and lead.session_count >= 60:
        score += 25
    
    # Signal 3: Team Adoption Signal - Users Per Domain (most important)
    # 2+ unique users on same ENTERPRISE domain = +30 bonus
    try:
        domain_user_counts = count_users_per_domain(lead.company.domain)
        
        # Check if this lead's email domain has 2+ users
        email_domain = extract_domain(lead.email)
        if email_domain and email_domain in domain_user_counts:
            if domain_user_counts[email_domain] >= 2:
                score += 30
    except Exception:
        # If counting fails, skip this signal
        pass
    
    # Signal 4: Job Title Hierarchy (5-20 points)
    if lead.pdl_job_title:
        score += get_job_title_score(lead.pdl_job_title)
    
    # Signal 5: Gmail Qualified Adjustment (+5 points)
    # Applied when using Gmail but with other positive signals
    if is_free_email_domain(lead.email) and lead.email.endswith('@gmail.com'):
        if score > 0:  # Only if there are other positive signals
            score += 5
    
    # Signal 6: Enterprise Domain Bonus (+30 points)
    # Using corporate domain (not free email provider)
    if not is_free_email_domain(lead.email):
        score += 30
    
    # Signal 7: ASN / Corporate IP Signals (future enhancement)
    # +20 points if corporate IP detected
    # (can be added when IP enrichment is implemented)
    
    # Signal 8: Mimecast Email Security (+15 points)
    # (can be added when email security data is available)
    
    # Signal 9: Free Email Penalty (-10 points)
    if is_free_email_domain(lead.email) and not lead.email.endswith('@gmail.com'):
        score -= 10
    
    # Clamp score between 0-100
    score = max(0, min(100, score))
    
    # Map score to stage
    if score >= 80:
        stage = 'enterprise'
    elif score >= 60:
        stage = 'very_high'
    elif score >= 40:
        stage = 'high'
    elif score >= 20:
        stage = 'medium'
    else:
        stage = 'low'
    
    return score, stage


def auto_calculate_score_and_stage(lead):
    """
    Automatically calculate and update lead score and stage.
    Call this in the Lead.save() method.
    """
    score, stage = calculate_lead_score(lead)
    lead.lead_score = score
    lead.lead_stage = stage
