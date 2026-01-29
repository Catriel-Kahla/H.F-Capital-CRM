from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import StreamingHttpResponse
from leads.models import Lead, Company
from leads.enrichment import enrich_company, enrich_lead
import csv
import io
import os
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from django.urls import reverse


def home(request):
    """Vista para la página de inicio"""
    return render(request, 'crm/home.html')


def ai_enrichment(request):
    """Simplified AI enrichment view for companies and leads."""
    enrichment_enabled = bool(os.getenv("GENAI_API_KEY") and os.getenv("OPENAI_API_KEY"))

    # Compute counts for UI
    companies_needing_enrichment = Company.objects.filter(
        work_website__isnull=True
    ).exclude(
        domain__in=['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com']
    )
    companies_count = companies_needing_enrichment.count()

    leads_to_enrich_q = (
        Lead.objects.filter(pdl_first_name__isnull=True)
        | Lead.objects.filter(pdl_last_name__isnull=True)
        | Lead.objects.filter(pdl_job_title__isnull=True)
        | Lead.objects.filter(pdl_linkedin_url__isnull=True)
    )
    leads_to_enrich = leads_to_enrich_q.distinct()
    leads_count = leads_to_enrich.count()

    # Handle POST actions synchronously (keeps view simple and sync)
    if request.method == 'POST':
        if 'enrich_companies' in request.POST:
            if not enrichment_enabled:
                messages.error(request, 'AI enrichment is disabled. Add GENAI_API_KEY and OPENAI_API_KEY to keys.env to enable.')
                return redirect('crm:ai_enrichment')

            enriched = 0
            errors = 0

            # Enrich companies in parallel (5 workers)
            def _enrich_one(company):
                try:
                    enriched_data = enrich_company(company.domain, verbose=False)
                    if enriched_data:
                        if enriched_data.get('work_website'):
                            company.work_website = enriched_data['work_website']
                        if enriched_data.get('company_name'):
                            company.company_name = enriched_data['company_name']
                        if enriched_data.get('linkedin'):
                            company.linkedin = enriched_data['linkedin']
                        company.save()
                        return {'success': True, 'company': company}
                    return {'success': False, 'company': company}
                except Exception as e:
                    return {'success': False, 'company': company, 'error': str(e)}

            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_company = {executor.submit(_enrich_one, c): c for c in companies_needing_enrichment}
                for future in as_completed(future_to_company):
                    try:
                        result = future.result()
                        if result.get('success'):
                            enriched += 1
                        else:
                            # treat missing data as not-enriched
                            if result.get('error'):
                                errors += 1
                    except Exception:
                        errors += 1

            messages.success(request, f'AI-enriched {enriched} companies. {errors} errors.')
            return redirect('crm:ai_enrichment')

        if 'enrich_leads' in request.POST:
            if not enrichment_enabled:
                messages.error(request, 'AI enrichment is disabled. Add GENAI_API_KEY and OPENAI_API_KEY to keys.env to enable.')
                return redirect('crm:ai_enrichment')

            enriched = 0
            errors = 0
            for lead in leads_to_enrich:
                try:
                    result = enrich_lead(lead, verbose=False, overwrite=True)
                    if result and not result.get('skipped'):
                        enriched += 1
                    elif result is None:
                        errors += 1
                except Exception:
                    errors += 1

            messages.success(request, f'AI-enriched {enriched} leads. {errors} errors.')
            return redirect('crm:ai_enrichment')

    return render(request, 'crm/ai_enrichment.html', {
        'enrichment_enabled': enrichment_enabled,
        'companies_count': companies_count,
        'leads_count': leads_count,
    })


def enrichment_progress(request):
    """API endpoint to get enrichment progress"""
    from django.http import JsonResponse
    
    progress = request.session.get('enrichment_progress', {
        'total': 0,
        'current': 0,
        'enriched': 0,
        'errors': 0,
        'current_company': '',
        'status': 'idle',
        'logs': []
    })
    
    # Only return last 20 logs to avoid too much data
    if len(progress.get('logs', [])) > 20:
        progress['logs'] = progress['logs'][-20:]
    
    return JsonResponse(progress)


def ai_enrichment_stream(request):
    """Streaming endpoint that runs company enrichment in parallel and streams progress as HTML/JS.
    Opens in a new browser window/tab so the main UI remains responsive.
    """
    enrichment_enabled = bool(os.getenv("GENAI_API_KEY") and os.getenv("OPENAI_API_KEY"))
    if not enrichment_enabled:
        return StreamingHttpResponse("<html><body><h3>AI enrichment is disabled.</h3></body></html>", content_type='text/html')

    companies = list(Company.objects.filter(
        work_website__isnull=True
    ).exclude(domain__in=['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com']))

    total = len(companies)

    def stream():
        yield "<!doctype html><html><head><meta charset='utf-8'><title>AI Enrichment Progress</title>"
        yield "<style>body{font-family:Segoe UI,Arial;margin:16px} .progress{width:100%;height:22px;background:#eee;border-radius:4px;overflow:hidden} .bar{height:100%;background:#4caf50;width:0%}</style>"
        yield "</head><body>"
        yield f"<h2>AI Enrichment — {total} companies</h2>"
        yield "<div class='progress'><div id='bar' class='bar'></div></div>"
        yield "<div id='log' style='margin-top:12px;font-family:monospace;white-space:pre-wrap'></div>"

        if total == 0:
            yield "<script>document.getElementById('log').textContent = 'No companies to enrich.';</script>"
            yield "</body></html>"
            return

        enriched = 0
        errors = 0

        def _enrich_one(company):
            try:
                enriched_data = enrich_company(company.domain, verbose=False)
                if enriched_data:
                    if enriched_data.get('work_website'):
                        company.work_website = enriched_data['work_website']
                    if enriched_data.get('company_name'):
                        company.company_name = enriched_data['company_name']
                    if enriched_data.get('linkedin'):
                        company.linkedin = enriched_data['linkedin']
                    company.save()
                    return {'success': True, 'domain': company.domain, 'name': company.company_name}
                return {'success': False, 'domain': company.domain}
            except Exception as e:
                return {'success': False, 'domain': company.domain, 'error': str(e)}

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_company = {executor.submit(_enrich_one, c): c for c in companies}
            completed = 0
            for future in as_completed(future_to_company):
                completed += 1
                try:
                    res = future.result()
                    if res.get('success'):
                        enriched += 1
                        msg = f"✅ Enriched {res.get('name') or res.get('domain')}"
                    else:
                        if res.get('error'):
                            errors += 1
                            msg = f"❌ Error {res.get('domain')}: {res.get('error')}"
                        else:
                            msg = f"⚠️ Skipped {res.get('domain')} (no data)"
                except Exception as e:
                    errors += 1
                    msg = f"❌ Exception: {str(e)}"

                percent = int((completed / total) * 100)
                # send progress update and log line (use json.dumps to safely escape content)
                safe_msg = json.dumps(msg + "\n")
                yield f"<script>document.getElementById('bar').style.width='{percent}%'; document.getElementById('log').textContent += {safe_msg};</script>"

        # final summary
        yield f"<script>document.getElementById('log').textContent += '---\nCompleted: {enriched}/{total} enriched, {errors} errors.\n';</script>"
        yield "</body></html>"

    return StreamingHttpResponse(stream(), content_type='text/html; charset=utf-8')


def import_csv(request):
    """Vista para importar leads desde CSV con enriquecimiento AI"""
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        
        # Validate file type
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a valid CSV file.')
            return redirect('crm:import_csv')
        
        # Validate file size (10MB max)
        if csv_file.size > 10 * 1024 * 1024:
            messages.error(request, 'File size must be less than 10MB.')
            return redirect('crm:import_csv')
        
        # Check if AI enrichment is enabled
        enable_enrichment = os.getenv("GENAI_API_KEY") and os.getenv("OPENAI_API_KEY")
        
        try:
            # Read and decode CSV
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            # Convert to list to get total count
            rows = list(reader)
            total_rows = len(rows)
            
            print("\n" + "="*60)
            print(f"📥 STARTING CSV IMPORT: {total_rows} rows to process")
            print("="*60 + "\n")
            
            created_companies = 0
            enriched_companies = 0
            created_leads = 0
            enriched_leads = 0
            skipped_leads = 0
            errors = []
            
            # Track unique domains to enrich
            domains_to_enrich = set()
            
            for row_num, row in enumerate(rows, start=1):
                try:
                    email = row.get('email', '').strip()
                    
                    if not email or '@' not in email:
                        skipped_leads += 1
                        print(f"  [{row_num}/{total_rows}] ⚠️  Skipped invalid email")
                        continue
                    
                    # Extract domain from email
                    domain = email.split('@')[1].lower()
                    domains_to_enrich.add(domain)
                    
                    # Get or create company (without enrichment yet)
                    company, company_created = Company.objects.get_or_create(
                        domain=domain,
                        defaults={
                            'company_name': row.get('company_name', '').strip() or None,
                            'domain_confidence_score': 1.0 if domain not in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com'] else 0.5
                        }
                    )
                    
                    if company_created:
                        created_companies += 1
                        print(f"  [{row_num}/{total_rows}] 🏢 Created company: {domain}")
                    
                    # Check if lead already exists
                    if Lead.objects.filter(email=email).exists():
                        skipped_leads += 1
                        print(f"  [{row_num}/{total_rows}] ⏭️  Skipped duplicate: {email}")
                        continue
                    
                    # Create lead
                    lead = Lead(
                        email=email,
                        company=company,
                        pdl_first_name=row.get('first_name', '').strip() or None,
                        pdl_last_name=row.get('last_name', '').strip() or None,
                        pdl_job_title=row.get('job_title', '').strip() or None,
                        lead_score=int(row.get('lead_score', 0)) if row.get('lead_score') else 0,
                        is_free_email=domain in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com'],
                    )
                    lead.save()
                    created_leads += 1
                    
                    lead_name = f"{lead.pdl_first_name or ''} {lead.pdl_last_name or ''}".strip() or email
                    print(f"  [{row_num}/{total_rows}] ✅ Created lead: {lead_name}")

                    if enable_enrichment:
                        print(f"  [{row_num}/{total_rows}] 🤖 Enriching lead with AI...")
                        enriched_data = enrich_lead(lead, verbose=True)
                        if enriched_data:
                            enriched_leads += 1
                            print(f"  [{row_num}/{total_rows}] ✅ Lead enriched")
                        else:
                            print(f"  [{row_num}/{total_rows}] ⚠️  Lead enrichment skipped or failed")
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    print(f"  [{row_num}/{total_rows}] ❌ Error: {str(e)}")
                    continue
            
            print("\n" + "="*60)
            print(f"📊 CSV IMPORT COMPLETED")
            print(f"  Created: {created_leads} leads, {created_companies} companies")
            print(f"  Skipped: {skipped_leads} duplicates")
            print("="*60 + "\n")
            
            # Enrich companies with AI if enabled
            if enable_enrichment and domains_to_enrich:
                # Filter out free email domains
                business_domains = [d for d in domains_to_enrich if d not in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com']]
                total_to_enrich = len(business_domains)
                
                print("\n" + "="*60)
                print(f"🤖 STARTING AI ENRICHMENT: {total_to_enrich} companies")
                print("="*60 + "\n")
                
                for idx, domain in enumerate(business_domains, start=1):
                    try:
                        company = Company.objects.get(domain=domain)
                        
                        # Skip if already enriched
                        if company.work_website and company.company_name:
                            print(f"  [{idx}/{total_to_enrich}] ⏭️  Already enriched: {domain}")
                            continue
                        
                        # Enrich with AI
                        print(f"\n  [{idx}/{total_to_enrich}] 🔍 Enriching: {domain}")
                        enriched_data = enrich_company(domain, verbose=True)
                        
                        # Update company with enriched data
                        if enriched_data.get('work_website'):
                            company.work_website = enriched_data['work_website']
                        if enriched_data.get('linkedin'):
                            company.linkedin = enriched_data['linkedin']
                        if enriched_data.get('company_name'):
                            company.company_name = enriched_data['company_name']
                        if enriched_data.get('industry'):
                            company.industry = enriched_data['industry']
                        if enriched_data.get('company_size'):
                            company.company_size = enriched_data['company_size']
                        if enriched_data.get('hq_country'):
                            company.hq_country = enriched_data['hq_country']
                        if enriched_data.get('org_type'):
                            company.org_type = enriched_data['org_type']
                        if enriched_data.get('tech_stack'):
                            company.tech_stack = enriched_data['tech_stack']
                        if enriched_data.get('street'):
                            company.street = enriched_data['street']
                        if enriched_data.get('city'):
                            company.city = enriched_data['city']
                        if enriched_data.get('state'):
                            company.state = enriched_data['state']
                        if enriched_data.get('postal_code'):
                            company.postal_code = enriched_data['postal_code']
                        if enriched_data.get('country'):
                            company.country = enriched_data['country']
                        if enriched_data.get('work_phone'):
                            company.work_phone = enriched_data['work_phone']
                        if enriched_data.get('facebook'):
                            company.facebook = enriched_data['facebook']
                        
                        company.save()
                        enriched_companies += 1
                        print(f"  ✅ [{idx}/{total_to_enrich}] Saved: {company.company_name or domain}\n")
                        
                    except Exception as e:
                        print(f"  ❌ [{idx}/{total_to_enrich}] Error enriching {domain}: {e}\n")
                        continue
                
                print("="*60)
                print(f"🎉 AI ENRICHMENT COMPLETED: {enriched_companies}/{total_to_enrich} companies enriched")
                print("="*60 + "\n")
            
            # Show results
            success_msg = f'Import completed! Created {created_leads} leads and {created_companies} companies.'
            if enable_enrichment and enriched_companies > 0:
                success_msg += f' AI-enriched {enriched_companies} companies.'
            if enable_enrichment and enriched_leads > 0:
                success_msg += f' AI-enriched {enriched_leads} leads.'
            success_msg += f' Skipped {skipped_leads} duplicates.'
            
            messages.success(request, success_msg)
            
            if errors:
                messages.warning(request, f'{len(errors)} errors occurred during import.')
            
            if not enable_enrichment:
                messages.info(request, 'AI enrichment disabled. Add GENAI_API_KEY and OPENAI_API_KEY to .env to enable.')
            
            return redirect('leads:lead_list')
            
        except Exception as e:
            messages.error(request, f'Error processing CSV: {str(e)}')
            return redirect('crm:import_csv')
    
    # Check if enrichment is configured
    enrichment_enabled = bool(os.getenv("GENAI_API_KEY") and os.getenv("OPENAI_API_KEY"))
    
    return render(request, 'crm/import_csv.html', {'enrichment_enabled': enrichment_enabled})
