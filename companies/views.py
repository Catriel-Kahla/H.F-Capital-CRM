from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, IntegerField, Q, Value
from django.db.models.functions import Coalesce, Lower
from leads.models import Company, CompanyNote, Lead
from leads.forms import CompanyForm, CompanyNoteForm
from leads.enrichment import enrich_company
import os


def company_list(request):
    """View to list all companies"""
    companies = Company.objects.all()
    search_query = request.GET.get('search', '').strip()
    sort_key = (request.GET.get('sort') or '').strip().lower()
    sort_dir = (request.GET.get('dir') or '').strip().lower()
    page_number = (request.GET.get('page') or '').strip()
    
    # Filter by search query if provided
    if search_query:
        companies = companies.filter(
            Q(company_name__icontains=search_query)
            | Q(domain__icontains=search_query)
        )
    
    # Estadísticas (based on the filtered queryset, not paginated)
    total_companies = companies.count()
    with_linkedin = companies.exclude(linkedin__isnull=True).exclude(linkedin='').count()

    # Sorting (safe allow-list)
    allowed_sort_keys = {'name', 'domain', 'industry', 'size', 'leads'}
    if sort_key not in allowed_sort_keys:
        sort_key = ''

    def _default_dir_for(key: str) -> str:
        return 'desc' if key in {'size', 'leads'} else 'asc'

    # Per requested UX: each column has a fixed direction
    if sort_key:
        sort_dir = _default_dir_for(sort_key)

    # Always annotate leads_count so the template doesn't do N+1 queries
    companies = companies.annotate(leads_count=Count('leads'))

    if sort_key:
        prefix = '-' if sort_dir == 'desc' else ''
        if sort_key == 'name':
            companies = companies.annotate(
                name_sort=Lower(Coalesce('company_name', 'domain')),
            ).order_by(f'{prefix}name_sort', 'domain')
        elif sort_key == 'domain':
            companies = companies.annotate(domain_sort=Lower('domain')).order_by(f'{prefix}domain_sort')
        elif sort_key == 'industry':
            companies = companies.annotate(
                industry_sort=Lower(Coalesce('industry', Value(''))),
            ).order_by(f'{prefix}industry_sort', 'domain')
        elif sort_key == 'size':
            companies = companies.annotate(
                size_sort=Coalesce('company_size', Value(-1), output_field=IntegerField()),
            ).order_by(f'{prefix}size_sort', 'domain')
        elif sort_key == 'leads':
            companies = companies.order_by(f'{prefix}leads_count', 'domain')
    else:
        # Keep existing default behavior
        companies = companies.order_by('-company_name')

    # Pagination (10 per page)
    paginator = Paginator(companies, 10)
    page_obj = paginator.get_page(page_number or 1)

    params_wo_page = request.GET.copy()
    params_wo_page.pop('page', None)

    def build_page_url(page: int) -> str:
        params = params_wo_page.copy()
        params['page'] = str(page)
        return '?' + params.urlencode()

    pagination_params: list[tuple[str, str]] = []
    for key, values in params_wo_page.lists():
        for value in values:
            pagination_params.append((key, value))

    # Prebuild sort URLs for header links (preserve current filters/search)
    def build_sort_url(key: str) -> str:
        params = request.GET.copy()
        params.pop('page', None)
        params['sort'] = key
        params['dir'] = _default_dir_for(key)
        return '?' + params.urlencode()
    
    context = {
        'companies': page_obj,
        'total_companies': total_companies,
        'with_linkedin': with_linkedin,
        'search_query': search_query,
        'sort_key': sort_key,
        'sort_dir': sort_dir,
        'sort_urls': {
            'name': build_sort_url('name'),
            'domain': build_sort_url('domain'),
            'industry': build_sort_url('industry'),
            'size': build_sort_url('size'),
            'leads': build_sort_url('leads'),
        },
        'page_obj': page_obj,
        'page_prev_url': build_page_url(page_obj.previous_page_number()) if page_obj.has_previous() else None,
        'page_next_url': build_page_url(page_obj.next_page_number()) if page_obj.has_next() else None,
        'pagination_params': pagination_params,
    }
    return render(request, 'companies/company_list.html', context)


def company_detail(request, pk):
    """View to see company details (read-only)"""
    company = get_object_or_404(Company, domain=pk)
    linked_leads = (
        Lead.objects.filter(company=company)
        .prefetch_related('tags')
        .order_by('-lead_score', 'email')
    )
    return render(
        request,
        'companies/company_detail.html',
        {
            'company': company,
            'linked_leads': linked_leads,
        },
    )


def company_notes(request, pk):
    """List and create notes for a company."""
    company = get_object_or_404(Company, domain=pk)
    notes = CompanyNote.objects.filter(company=company).order_by('-created_at')

    if request.method == 'POST':
        form = CompanyNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.company = company
            note.save()
            messages.success(request, 'Note added successfully.')
            return redirect('companies:company_notes', pk=company.domain)
    else:
        form = CompanyNoteForm()

    context = {
        'company': company,
        'notes': notes,
        'form': form,
    }
    return render(request, 'companies/company_notes.html', context)


def company_note_update(request, pk, note_id):
    """Edit a note for a company."""
    company = get_object_or_404(Company, domain=pk)
    note = get_object_or_404(CompanyNote, id=note_id, company=company)

    if request.method == 'POST':
        form = CompanyNoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            messages.success(request, 'Note updated successfully.')
            return redirect('companies:company_notes', pk=company.domain)
    else:
        form = CompanyNoteForm(instance=note)

    context = {
        'company': company,
        'note': note,
        'form': form,
        'title': 'Edit Note',
    }
    return render(request, 'companies/company_note_form.html', context)


def company_note_delete(request, pk, note_id):
    """Delete a note for a company."""
    company = get_object_or_404(Company, domain=pk)
    note = get_object_or_404(CompanyNote, id=note_id, company=company)

    if request.method == 'POST':
        note.delete()
        messages.success(request, 'Note deleted successfully.')
        return redirect('companies:company_notes', pk=company.domain)

    context = {
        'company': company,
        'note': note,
    }
    return render(request, 'companies/company_note_confirm_delete.html', context)


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
