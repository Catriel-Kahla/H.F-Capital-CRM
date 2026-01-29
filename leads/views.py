from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Avg
from .models import Lead, Company
from .forms import LeadForm, CompanyForm
from .enrichment import enrich_lead
import os


def lead_list(request):
    """View to list all leads"""
    leads = Lead.objects.select_related('company').all()
    search_query = request.GET.get('search', '').strip()
    
    # Filter by search query if provided
    if search_query:
        leads = leads.filter(
            pdl_first_name__icontains=search_query
        ) | leads.filter(
            pdl_last_name__icontains=search_query
        ) | leads.filter(
            email__icontains=search_query
        ) | leads.filter(
            company__company_name__icontains=search_query
        ) | leads.filter(
            company__domain__icontains=search_query
        )
    
    avg_score = leads.aggregate(avg=Avg('lead_score'))['avg']
    if avg_score is not None:
        avg_score = round(avg_score, 1)
    else:
        avg_score = '--'
    
    return render(request, 'leads/lead_list.html', {
        'leads': leads,
        'search_query': search_query,
        'avg_score': avg_score,
    })


def lead_detail(request, pk):
    """View to see lead details (read-only)"""
    lead = get_object_or_404(Lead, pk=pk)
    return render(request, 'leads/lead_detail.html', {'lead': lead})


def lead_create(request):
    """View to create a new lead"""
    if request.method == 'POST':
        form = LeadForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lead created successfully.')
            return redirect('leads:lead_list')
    else:
        form = LeadForm()
    return render(request, 'leads/lead_form.html', {'form': form, 'title': 'Create Lead'})


def lead_update(request, pk):
    """View to update an existing lead"""
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lead updated successfully.')
            return redirect('leads:lead_list')
    else:
        form = LeadForm(instance=lead)
    return render(request, 'leads/lead_form.html', {'form': form, 'title': 'Edit Lead'})


def lead_delete(request, pk):
    """View to delete a lead"""
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        lead.delete()
        messages.success(request, 'Lead deleted successfully.')
        return redirect('leads:lead_list')
    return render(request, 'leads/lead_confirm_delete.html', {'lead': lead})


def company_create(request):
    """View to create a new company"""
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Company created successfully.')
            return redirect('leads:lead_create')
    else:
        form = CompanyForm()
    return render(request, 'leads/company_form.html', {'form': form, 'title': 'Create Company'})


def clear_leads(request):
    """View to clear all leads and companies"""
    if request.method == 'POST':
        leads_count = Lead.objects.count()
        companies_count = Company.objects.count()
        
        Lead.objects.all().delete()
        Company.objects.all().delete()
        
        messages.success(request, f'Successfully deleted {leads_count} leads and {companies_count} companies.')
        return redirect('leads:lead_list')
    
    return redirect('leads:lead_list')


def lead_enrich(request):
    """Enrich leads using AI with optional re-enrichment."""
    enable_enrichment = os.getenv("GENAI_API_KEY") and os.getenv("OPENAI_API_KEY")
    if not enable_enrichment:
        messages.error(request, 'AI enrichment is disabled. Add GENAI_API_KEY and OPENAI_API_KEY to keys.env to enable.')
        return redirect('leads:lead_list')

    mode = request.GET.get('mode', 'empty')
    overwrite = mode == 'all'

    leads = Lead.objects.select_related('company').all()
    if not overwrite:
        leads = leads.filter(
            Q(pdl_first_name__isnull=True) | Q(pdl_first_name='') |
            Q(pdl_last_name__isnull=True) | Q(pdl_last_name='') |
            Q(pdl_job_title__isnull=True) | Q(pdl_job_title='') |
            Q(pdl_linkedin_url__isnull=True) | Q(pdl_linkedin_url='')
        )

    total = leads.count()
    if total == 0:
        messages.info(request, 'No leads need enrichment.')
        return redirect('leads:lead_list')

    enriched = 0
    skipped = 0
    errors = 0

    for lead in leads:
        try:
            result = enrich_lead(lead, verbose=False, overwrite=overwrite)
            if result and result.get('skipped'):
                skipped += 1
            elif result:
                enriched += 1
            else:
                errors += 1
        except Exception:
            errors += 1
            continue

    msg = f'Lead enrichment completed. Enriched {enriched} lead(s).'
    if skipped:
        msg += f' Skipped {skipped}.'
    if errors:
        msg += f' {errors} error(s) occurred.'
    messages.success(request, msg)

    return redirect('leads:lead_list')
