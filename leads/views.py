from .mailchimp_utils import add_lead_to_mailchimp
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Avg, Case, IntegerField, Q, Value, When
from django.db.models.functions import Coalesce, Lower
from .models import Lead, Company, LeadTag
from .forms import LeadForm, CompanyForm
from .enrichment import enrich_lead
import os


def lead_list(request):
    """View to list all leads"""
    leads = Lead.objects.select_related('company').prefetch_related('tags').all()
    search_query = request.GET.get('search', '').strip()
    company_domain = request.GET.get('company', '').strip()
    sort_key = (request.GET.get('sort') or '').strip().lower()
    sort_dir = (request.GET.get('dir') or '').strip().lower()
    page_number = request.GET.get('page', '').strip()
    
    # Filter by company domain if provided
    if company_domain:
        leads = leads.filter(company__domain=company_domain)
    
    # Filter by search query if provided
    if search_query:
        leads = leads.filter(
            Q(pdl_first_name__icontains=search_query)
            | Q(pdl_last_name__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(company__company_name__icontains=search_query)
            | Q(company__domain__icontains=search_query)
            | Q(tags__name__icontains=search_query)
        ).distinct()
    
    avg_score = leads.aggregate(avg=Avg('lead_score'))['avg']
    if avg_score is not None:
        avg_score = round(avg_score, 1)
    else:
        avg_score = '--'

    total_leads = leads.count()

    # Sorting (safe allow-list)
    allowed_sort_keys = {'name', 'job_title', 'email', 'company', 'score', 'stage'}
    if sort_key not in allowed_sort_keys:
        sort_key = ''

    def _default_dir_for(key: str) -> str:
        return 'desc' if key in {'score', 'stage'} else 'asc'

    # Per requested UX: each column has a fixed direction
    # - name/job_title/email/company: A→Z
    # - score/stage: max→min
    if sort_key:
        sort_dir = _default_dir_for(sort_key)

    if sort_key:
        prefix = '-' if sort_dir == 'desc' else ''

        if sort_key == 'name':
            leads = leads.annotate(
                first_name_sort=Lower(Coalesce('pdl_first_name', Value(''))),
                last_name_sort=Lower(Coalesce('pdl_last_name', Value(''))),
            ).order_by(
                f'{prefix}first_name_sort',
                f'{prefix}last_name_sort',
                'email',
            )
        elif sort_key == 'job_title':
            leads = leads.annotate(
                job_title_sort=Lower(Coalesce('pdl_job_title', Value(''))),
            ).order_by(
                f'{prefix}job_title_sort',
                'email',
            )
        elif sort_key == 'email':
            leads = leads.annotate(
                email_sort=Lower('email'),
            ).order_by(
                f'{prefix}email_sort',
            )
        elif sort_key == 'company':
            leads = leads.annotate(
                company_sort=Lower(Coalesce('company__company_name', 'company__domain')),
            ).order_by(
                f'{prefix}company_sort',
                'email',
            )
        elif sort_key == 'score':
            leads = leads.order_by(f'{prefix}lead_score', 'email')
        elif sort_key == 'stage':
            leads = leads.annotate(
                stage_rank=Case(
                    When(lead_stage='low', then=Value(0)),
                    When(lead_stage='medium', then=Value(1)),
                    When(lead_stage='high', then=Value(2)),
                    When(lead_stage='very_high', then=Value(3)),
                    When(lead_stage='enterprise', then=Value(4)),
                    default=Value(-1),
                    output_field=IntegerField(),
                ),
            ).order_by(f'{prefix}stage_rank', 'email')

    # Prebuild sort URLs for header links (preserve current filters/search)
    def build_sort_url(key: str) -> str:
        params = request.GET.copy()
        default_dir = _default_dir_for(key)
        params['sort'] = key
        params['dir'] = default_dir
        params.pop('page', None)
        return '?' + params.urlencode()

    # Pagination (10 per page)
    paginator = Paginator(leads, 10)
    page_obj = paginator.get_page(page_number or 1)

    params_wo_page = request.GET.copy()
    params_wo_page.pop('page', None)
    querystring = params_wo_page.urlencode()

    def build_page_url(page: int) -> str:
        params = params_wo_page.copy()
        params['page'] = str(page)
        return '?' + params.urlencode()

    pagination_params: list[tuple[str, str]] = []
    for key, values in params_wo_page.lists():
        for value in values:
            pagination_params.append((key, value))
    
    all_tags = LeadTag.objects.all().order_by('name')
    filter_company = None
    if company_domain:
        filter_company = Company.objects.filter(domain=company_domain).first()

    return render(request, 'leads/lead_list.html', {
        'leads': page_obj,
        'all_tags': all_tags,
        'search_query': search_query,
        'avg_score': avg_score,
        'filter_company': filter_company,
        'total_leads': total_leads,
        'page_obj': page_obj,
        'querystring': querystring,
        'page_prev_url': build_page_url(page_obj.previous_page_number()) if page_obj.has_previous() else None,
        'page_next_url': build_page_url(page_obj.next_page_number()) if page_obj.has_next() else None,
        'pagination_params': pagination_params,
        'sort_key': sort_key,
        'sort_dir': sort_dir,
        'sort_urls': {
            'name': build_sort_url('name'),
            'job_title': build_sort_url('job_title'),
            'email': build_sort_url('email'),
            'company': build_sort_url('company'),
            'score': build_sort_url('score'),
            'stage': build_sort_url('stage'),
        },
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


from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect
def send_to_mailchimp(request):
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_leads')
        if not selected_ids:
            messages.error(request, 'No leads selected.')
            return redirect('leads:lead_list')
        from .models import Lead
        leads = Lead.objects.filter(pk__in=selected_ids)
        success, failed = 0, 0
        for lead in leads:
            # Push any existing CRM tags as Mailchimp audience tags too
            tag_names = list(lead.tags.values_list('name', flat=True))
            result = add_lead_to_mailchimp(
                lead.email,
                getattr(lead, 'pdl_first_name', ''),
                getattr(lead, 'pdl_last_name', ''),
                tag_names=tag_names,
            )
            if 'error' in result:
                failed += 1
            else:
                success += 1
        if success:
            messages.success(request, f'{success} leads sent to Mailchimp.')
        if failed:
            messages.error(request, f'{failed} leads failed to send.')
        return redirect('leads:lead_list')
    return redirect('leads:lead_list')


def bulk_apply_tag(request):
    if request.method != 'POST':
        return redirect('leads:lead_list')

    selected_ids = request.POST.getlist('selected_leads')
    tag_name = (request.POST.get('tag_name') or '').strip()

    if not selected_ids:
        messages.error(request, 'No leads selected.')
        return redirect('leads:lead_list')

    if not tag_name:
        messages.error(request, 'Tag name is required.')
        return redirect('leads:lead_list')

    tag, _ = LeadTag.objects.get_or_create(name=tag_name.strip().lower())
    leads = Lead.objects.filter(pk__in=selected_ids)

    updated = 0
    for lead in leads:
        lead.tags.add(tag)
        updated += 1

    messages.success(request, f'Applied tag "{tag.name}" to {updated} lead(s).')
    return redirect('leads:lead_list')


def send_tag_to_mailchimp(request):
    if request.method != 'POST':
        return redirect('leads:lead_list')

    tag_id = request.POST.get('tag_id')
    if not tag_id:
        messages.error(request, 'Please choose a tag.')
        return redirect('leads:lead_list')

    tag = get_object_or_404(LeadTag, pk=tag_id)
    leads = Lead.objects.filter(tags=tag)

    if not leads.exists():
        messages.info(request, f'No leads found with tag "{tag.name}".')
        return redirect('leads:lead_list')

    success, failed = 0, 0
    for lead in leads:
        result = add_lead_to_mailchimp(
            lead.email,
            getattr(lead, 'pdl_first_name', ''),
            getattr(lead, 'pdl_last_name', ''),
            tag_names=[tag.name],
        )
        if 'error' in result:
            failed += 1
        else:
            success += 1

    if success:
        messages.success(request, f'{success} tagged lead(s) sent to Mailchimp (tag: {tag.name}).')
    if failed:
        messages.error(request, f'{failed} tagged lead(s) failed to send to Mailchimp.')

    return redirect('leads:lead_list')


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
