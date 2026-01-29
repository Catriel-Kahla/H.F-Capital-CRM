from django.db import models
from django.utils import timezone
from .scoring import auto_calculate_score_and_stage


class Company(models.Model):
    """Company model - one per domain."""

    domain = models.CharField(max_length=255, primary_key=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    industry = models.CharField(max_length=255, blank=True, null=True)
    company_size = models.IntegerField(blank=True, null=True)
    hq_country = models.CharField(max_length=100, blank=True, null=True)
    org_type = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text="public, private, gov, edu, nonprofit"
    )
    tech_stack = models.TextField(blank=True, null=True)
    domain_confidence_score = models.FloatField(blank=True, null=True)
    
    # Address fields
    street = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    
    # Contact and social fields
    work_phone = models.CharField(max_length=50, blank=True, null=True)
    work_website = models.CharField(max_length=255, blank=True, null=True)
    linkedin = models.CharField(max_length=255, blank=True, null=True)
    facebook = models.CharField(max_length=255, blank=True, null=True)
    
    # CRM fields
    owned_by = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Owner name or email"
    )
    contact_type = models.CharField(max_length=100, blank=True, null=True)
    tags = models.TextField(
        blank=True, 
        null=True,
        help_text="Comma-separated tags"
    )
    last_contacted = models.DateTimeField(blank=True, null=True)
    
    # PDL funding fields (People Data Labs)
    pdl_total_funding_raised = models.FloatField(blank=True, null=True)
    pdl_latest_funding_stage = models.CharField(max_length=100, blank=True, null=True)
    pdl_last_funding_date = models.DateTimeField(blank=True, null=True)
    pdl_number_funding_rounds = models.IntegerField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'companies'
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'

    def __str__(self):
        return f"{self.company_name or self.domain}"

    def __repr__(self):
        return f"<Company(domain={self.domain!r}, company_name={self.company_name!r})>"


class Lead(models.Model):
    """Lead model - one per email."""

    # Lead stages choices
    LEAD_STAGE_CHOICES = [
        ('low', 'Low Priority'),
        ('medium', 'Medium Priority'),
        ('high', 'High Priority'),
        ('very_high', 'Very High Priority'),
        ('enterprise', 'Enterprise Target'),
    ]
    
    # Hierarchical level choices
    HIERARCHICAL_LEVEL_CHOICES = [
        ('low', 'Low Level'),
        ('medium', 'Medium Level'),
        ('high', 'High Level'),
        ('unknown', 'Unknown'),
    ]
    
    # Email status choices
    EMAIL_STATUS_CHOICES = [
        ('active', 'Active'),
        ('bounced', 'Bounced'),
        ('unsubscribed', 'Unsubscribed'),
    ]

    email = models.CharField(max_length=255, primary_key=True)
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE,
        to_field='domain',
        db_column='domain',
        related_name='leads'
    )
    signup_date = models.DateTimeField(blank=True, null=True)
    session_count = models.IntegerField(blank=True, null=True)
    is_free_email = models.BooleanField(default=False)
    is_candidate_enterprise = models.BooleanField(default=False)
    lead_score = models.IntegerField(default=0)
    lead_stage = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        choices=LEAD_STAGE_CHOICES
    )
    hierarchical_level = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=HIERARCHICAL_LEVEL_CHOICES
    )
    campaign_segment = models.CharField(max_length=255, blank=True, null=True)
    email_status = models.CharField(
        max_length=50,
        default='active',
        choices=EMAIL_STATUS_CHOICES
    )
    crm_owner = models.CharField(max_length=255, blank=True, null=True)
    first_seen = models.DateTimeField(blank=True, null=True)
    last_active = models.DateTimeField(blank=True, null=True)
    last_contacted_date = models.DateTimeField(blank=True, null=True)
    
    # PDL enrichment fields (People Data Labs)
    pdl_first_name = models.CharField(max_length=100, blank=True, null=True)
    pdl_last_name = models.CharField(max_length=100, blank=True, null=True)
    pdl_job_title = models.CharField(max_length=255, blank=True, null=True)
    pdl_linkedin_url = models.CharField(max_length=255, blank=True, null=True)
    pdl_job_last_verified = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'leads'
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
        ordering = ['-created_at']

    def __str__(self):
        name = f"{self.pdl_first_name or ''} {self.pdl_last_name or ''}".strip()
        return name if name else self.email

    def __repr__(self):
        return f"<Lead(email={self.email!r}, domain={self.company_id!r}, lead_score={self.lead_score})>"

    def save(self, *args, **kwargs):
        """Override save to automatically calculate score and stage."""
        # Auto-calculate lead score and stage based on lead data
        auto_calculate_score_and_stage(self)
        super().save(*args, **kwargs)

