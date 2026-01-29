from django import forms
from .models import Lead, Company


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['domain', 'company_name', 'industry', 'company_size', 'hq_country', 'org_type']
        widgets = {
            'domain': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'example.com'}),
            'company_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Company Name'}),
            'industry': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Technology, Finance, etc.'}),
            'company_size': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '50'}),
            'hq_country': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'USA'}),
            'org_type': forms.Select(attrs={'class': 'form-input'}, choices=[
                ('', 'Select Type'),
                ('public', 'Public'),
                ('private', 'Private'),
                ('gov', 'Government'),
                ('edu', 'Education'),
                ('nonprofit', 'Non-Profit'),
            ]),
        }


class LeadForm(forms.ModelForm):
    # Read-only fields for display (auto-calculated)
    lead_score = forms.IntegerField(
        disabled=True,
        required=False,
        label="Lead Score (Auto-calculated)"
    )
    lead_stage = forms.CharField(
        disabled=True,
        required=False,
        label="Lead Stage (Auto-calculated)"
    )
    
    class Meta:
        model = Lead
        fields = [
            'email', 'company', 'pdl_first_name', 'pdl_last_name', 
            'pdl_job_title', 'hierarchical_level',
            'email_status', 'crm_owner', 'is_candidate_enterprise',
            'lead_score', 'lead_stage'  # Display only (disabled)
        ]
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'email@example.com'}),
            'company': forms.Select(attrs={'class': 'form-input'}),
            'pdl_first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'First Name'}),
            'pdl_last_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Last Name'}),
            'pdl_job_title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Job Title'}),
            'hierarchical_level': forms.Select(attrs={'class': 'form-input'}),
            'email_status': forms.Select(attrs={'class': 'form-input'}),
            'crm_owner': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Owner Email'}),
            'is_candidate_enterprise': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values for read-only fields
        if self.instance and self.instance.pk:
            self.fields['lead_score'].initial = self.instance.lead_score
            self.fields['lead_stage'].initial = self.instance.get_lead_stage_display() or 'Not assigned'
            # Style read-only fields
            self.fields['lead_score'].widget.attrs.update({
                'class': 'form-input',
                'style': 'background-color: #f5f5f5; cursor: not-allowed;'
            })
            self.fields['lead_stage'].widget.attrs.update({
                'class': 'form-input',
                'style': 'background-color: #f5f5f5; cursor: not-allowed;'
            })
