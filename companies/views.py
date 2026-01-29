from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from leads.models import Company
from leads.forms import CompanyForm
from leads.enrichment import enrich_company
import os


def company_list(request):
    """View to list all companies"""
    companies = Company.objects.all()
    search_query = request.GET.get('search', '').strip()
    
    # Filter by search query if provided
    if search_query:
        companies = companies.filter(
            company_name__icontains=search_query
        ) | companies.filter(
            domain__icontains=search_query
        )
    
    companies = companies.order_by('-company_name')
    
    # Estadísticas
    total_companies = companies.count()
    with_linkedin = companies.exclude(linkedin__isnull=True).exclude(linkedin='').count()
    
    context = {
        'companies': companies,
        'total_companies': total_companies,
        'with_linkedin': with_linkedin,
        'search_query': search_query,
    }
    return render(request, 'companies/company_list.html', context)


def company_detail(request, pk):
    """View to see company details (read-only)"""
    company = get_object_or_404(Company, domain=pk)
    return render(request, 'companies/company_detail.html', {'company': company})


def company_create(request):
    """View to create a new company"""
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Company created successfully.')
            return redirect('companies:company_list')
    else:
        form = CompanyForm()
    return render(request, 'companies/company_form.html', {'form': form, 'title': 'Create Company'})


def company_update(request, pk):
    """View to edit a company"""
    company = get_object_or_404(Company, domain=pk)
    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, 'Company updated successfully.')
            return redirect('companies:company_list')
    else:
        form = CompanyForm(instance=company)
    return render(request, 'companies/company_form.html', {'form': form, 'title': 'Edit Company'})


def company_delete(request, pk):
    """View to delete a company"""
    company = get_object_or_404(Company, domain=pk)
    if request.method == 'POST':
        company_name = company.company_name
        company.delete()
        messages.success(request, f'Company "{company_name}" deleted successfully.')
        return redirect('companies:company_list')
    return render(request, 'companies/company_confirm_delete.html', {'company': company})


def company_enrich(request):
    """Enrich companies using AI with optional re-enrichment."""
    enable_enrichment = os.getenv("GENAI_API_KEY") and os.getenv("OPENAI_API_KEY")
    if not enable_enrichment:
        messages.error(request, 'AI enrichment is disabled. Add GENAI_API_KEY and OPENAI_API_KEY to keys.env to enable.')
        return redirect('companies:company_list')

    mode = request.GET.get('mode', 'empty')
    overwrite = mode == 'all'

    companies = Company.objects.all()
    if not overwrite:
        companies = companies.filter(
            Q(work_website__isnull=True) | Q(work_website='') |
            Q(linkedin__isnull=True) | Q(linkedin='') |
            Q(company_name__isnull=True) | Q(company_name='') |
            Q(industry__isnull=True) | Q(industry='') |
            Q(company_size__isnull=True) |
            Q(hq_country__isnull=True) | Q(hq_country='') |
            Q(org_type__isnull=True) | Q(org_type='') |
            Q(tech_stack__isnull=True) | Q(tech_stack='') |
            Q(street__isnull=True) | Q(street='') |
            Q(city__isnull=True) | Q(city='') |
            Q(state__isnull=True) | Q(state='') |
            Q(postal_code__isnull=True) | Q(postal_code='') |
            Q(country__isnull=True) | Q(country='') |
            Q(work_phone__isnull=True) | Q(work_phone='') |
            Q(facebook__isnull=True) | Q(facebook='')
        )

    total = companies.count()
    if total == 0:
        messages.info(request, 'No companies need enrichment.')
        return redirect('companies:company_list')

    enriched = 0
    skipped = 0
    errors = 0

    fields = [
        'work_website', 'linkedin', 'company_name', 'industry', 'company_size',
        'hq_country', 'org_type', 'tech_stack', 'street', 'city', 'state',
        'postal_code', 'country', 'work_phone', 'facebook'
    ]

    for company in companies:
        try:
            enriched_data = enrich_company(company.domain, verbose=False)
            if not enriched_data:
                errors += 1
                continue

            updated = False
            for field in fields:
                value = enriched_data.get(field)
                if value is None or value == '':
                    continue
                current = getattr(company, field)
                if overwrite or not current:
                    setattr(company, field, value)
                    updated = True

            if updated:
                company.save()
                enriched += 1
            else:
                skipped += 1
        except Exception:
            errors += 1
            continue

    msg = f'Company enrichment completed. Enriched {enriched} company(s).'
    if skipped:
        msg += f' Skipped {skipped}.'
    if errors:
        msg += f' {errors} error(s) occurred.'
    messages.success(request, msg)

    return redirect('companies:company_list')
