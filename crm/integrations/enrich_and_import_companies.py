"""
Script to enrich companies from CSV and save to database.

Integrates with AI_enrichement.py workflow:
1. Reads browserling_leads_final-500.csv
2. Extracts unique email domains
3. Uses DuckDuckGo + Gemini + ChatGPT to find website, LinkedIn and company info
4. Saves enriched data to database

Usage:
    python crm/integrations/enrich_and_import_companies.py --limit 5
    python crm/integrations/enrich_and_import_companies.py --domain microsoft.com
"""

import sys
import argparse
import time
from pathlib import Path
from click import prompt
import pandas as pd
from ddgs import DDGS
from google import genai
from openai import OpenAI
from dotenv import load_dotenv
import os
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from browserling_leads.db import get_session
from browserling_leads.models import Company
from datetime import datetime

load_dotenv("keys.env")

# Configure AI clients
GENAI_API_KEY = os.getenv("GENAI_API_KEY")
client = genai.Client(api_key=GENAI_API_KEY)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
gpt_client = OpenAI(api_key=OPENAI_API_KEY)

# Free email domains to skip
FREE_EMAIL_DOMAINS = {
    'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com',
    'icloud.com', 'mail.com', 'protonmail.com', 'proton.me', 'gmx.com',
    'yandex.com', 'zoho.com', 'tutanota.com', 'myyahoo.com', 'live.com',
    'msn.com', 'hotmail.co.uk', 'live.co.uk',
}


def extract_domain(email):
    """Extract domain from email address."""
    if not email or '@' not in email:
        return None
    return email.split('@')[1].lower()


def collect_candidates(domain: str, search_type="website", max_results: int = 6):
    """Search for URLs using DuckDuckGo (same as AI_enrichement.py)."""
    company_name = domain.split('.')[0].replace('-', ' ').title()
    
    if search_type == "website":
        queries = [
            f"{company_name} official site",
            f"{company_name} company website",
            f"{company_name} homepage"
        ]
    elif search_type == "linkedin":
        queries = [
            f"{company_name} official LinkedIn page",
            f"{company_name} LinkedIn company profile",
            f"{company_name} site:linkedin.com"
        ]
    else:
        raise ValueError("Tipo de búsqueda no reconocido")

    urls = []
    with DDGS() as ddgs:
        for q in queries:
            try:
                for r in ddgs.text(q, max_results=max_results):
                    href = r.get("href") or r.get("link")
                    title = r.get("title", "")
                    if not href:
                        continue
                    urls.append({"title": title, "url": href, "query": q})
                time.sleep(0.2)
            except Exception as e:
                print(f"    ⚠️  Search error: {e}")
                continue

    # Remove duplicates
    seen = set()
    dedup = []
    for item in urls:
        u = item["url"]
        if u in seen:
            continue
        seen.add(u)
        dedup.append(item)
    return dedup


def select_best_with_gemini(domain: str, candidates: list, kind="website"):
    """Gemini selects the best URL from candidates."""
    if not candidates:
        return None

    company_name = domain.split('.')[0].title()
    urls_text = "\n".join([f"- {c['title']} ({c['url']})" for c in candidates])
    prompt = f"""You are selecting the best URL for a company.
Company: {company_name} (domain: {domain})
Type: {kind}

Candidates:
{urls_text}

Choose the most likely official URL from the list above.
Respond with ONLY the URL, nothing else. No explanations, no additional text.
If none match, respond with the first URL from the list.
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        text = response.text.strip()
        
        # Extract only the URL from the response (remove explanations)
        # Look for lines that start with http:// or https://
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('http://') or line.startswith('https://'):
                return line
        
        # If no URL found, try to extract from the text
        import re
        urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', text)
        if urls:
            return urls[0]
        
        return text  # Fallback to original text if no URL extracted
    except Exception as e:
        print(f"    ⚠️  Gemini error: {e}")
        return None


def get_company_info_with_gpt(domain: str, website: str, linkedin: str):
    """Use ChatGPT to extract company information."""
    company_name = domain.split('.')[0].replace('-', ' ').title()
    
    prompt = f"""Based on the domain "{domain}", extract comprehensive company information.

Website: {website or 'Unknown'}
LinkedIn: {linkedin or 'Unknown'}

Return ONLY a JSON object with this exact structure (use null for unknown fields):
{{
    "company_name": "Official company name",
    "industry": "Industry/sector",
    "company_size": estimated_employee_count_as_integer_or_null,
    "hq_country": "Country code like US, UK, CA",
    "org_type": "one of: private, public, gov, edu, nonprofit",
    "tech_stack": "Brief technologies description",
    "street": "Street address if available",
    "city": "City name",
    "state": "State/Province",
    "postal_code": "Postal/ZIP code",
    "country": "Full country name",
    "work_phone": "Phone number with country code",
    "facebook": "Facebook page URL if known"
}}

Return ONLY the JSON, no additional text."""

    try:
        response = gpt_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = response.choices[0].message.content.strip()
        
        # Remove markdown if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text
            if response_text.startswith("json"):
                response_text = response_text[4:].strip()
        
        data = json.loads(response_text)
        return data
    except Exception as e:
        print(f"    ⚠️  GPT error: {e}")
        return None


def save_company_to_db(domain, enriched_data, website, linkedin):
    """Save enriched company data to database."""
    with get_session() as session:
        # Check if company already exists
        existing = session.query(Company).filter_by(domain=domain).first()
        
        if existing:
            print(f"  ℹ️  Company {domain} already exists - updating")
            company = existing
        else:
            company = Company(domain=domain)
            session.add(company)
        
        # Calculate domain confidence score
        # Free email domains: 0.5, Corporate domains: 1.0
        if domain in FREE_EMAIL_DOMAINS:
            company.domain_confidence_score = 0.5
        else:
            company.domain_confidence_score = 1.0
        
        # Save website and LinkedIn
        if website:
            company.work_website = website
        if linkedin:
            company.linkedin = linkedin
        
        # Update fields if enriched data is available
        if enriched_data:
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
            # Note: domain_confidence_score is calculated above based on domain type, not from AI
            
            # Address fields
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
            
            # Contact fields
            if enriched_data.get('work_phone'):
                company.work_phone = enriched_data['work_phone']
            if enriched_data.get('facebook'):
                company.facebook = enriched_data['facebook']
        
        company.updated_at = datetime.utcnow()
        session.commit()
        
        return company


def main():
    parser = argparse.ArgumentParser(description="Enrich companies from CSV and save to database")
    parser.add_argument("--csv", default="browserling_leads_final-500 .csv", help="Input CSV file")
    parser.add_argument("--limit", type=int, default=5, help="Number of companies to process")
    parser.add_argument("--domain", type=str, help="Process only this specific domain")
    args = parser.parse_args()
    
    print(f"🚀 Starting company enrichment process")
    print(f"📁 Reading CSV: {args.csv}")
    
    # Read CSV
    df = pd.read_csv(args.csv)
    
    # Extract unique domains from emails
    df['domain'] = df['email'].apply(extract_domain)
    unique_domains = df['domain'].dropna().unique()
    
    # Keep all domains (both business and free email domains)
    # Free email domains will get domain_confidence_score = 0.5
    # Business domains will get domain_confidence_score = 1.0
    domains_to_process = list(unique_domains)
    
    # If specific domain requested, process only that one
    if args.domain:
        if args.domain in domains_to_process:
            domains_to_process = [args.domain]
            print(f"🎯 Processing only specific domain: {args.domain}")
        else:
            print(f"❌ Domain '{args.domain}' not found in CSV")
            return
    
    free_email_count = len([d for d in domains_to_process if d in FREE_EMAIL_DOMAINS])
    business_count = len(domains_to_process) - free_email_count
    print(f"📊 Found {len(domains_to_process)} total domains ({business_count} business, {free_email_count} free email)")
    print(f"🎯 Processing {min(args.limit, len(domains_to_process))} companies")
    print("=" * 60)
    
    processed = 0
    enriched = 0
    errors = 0
    
    for domain in domains_to_process[:args.limit]:
        processed += 1
        print(f"\n[{processed}/{min(args.limit, len(domains_to_process))}] 🔎 Processing: {domain}")
        
        # Check if it's a free email domain
        is_free_email = domain in FREE_EMAIL_DOMAINS
        
        if is_free_email:
            print(f"  ⚠️  Free email domain - saving with confidence score 0.5")
            try:
                company = save_company_to_db(domain, None, None, None)
                print(f"  ✓ Saved to database")
                processed += 1
            except Exception as e:
                print(f"  ❌ Error saving: {e}")
                errors += 1
            continue
        
        try:
            # Search for website
            print(f"  🔍 Searching for website...")
            web_candidates = collect_candidates(domain, "website")
            best_website = select_best_with_gemini(domain, web_candidates, "website") if web_candidates else None
            if best_website:
                print(f"  🌐 Website: {best_website}")
            
            # Search for LinkedIn
            print(f"  🔍 Searching for LinkedIn...")
            linkedin_candidates = collect_candidates(domain, "linkedin")
            best_linkedin = select_best_with_gemini(domain, linkedin_candidates, "linkedin") if linkedin_candidates else None
            if best_linkedin:
                print(f"  💼 LinkedIn: {best_linkedin}")
            
            # Get company info with GPT
            print(f"  🤖 Enriching with AI...")
            enriched_data = get_company_info_with_gpt(domain, best_website, best_linkedin)
            
            if enriched_data and enriched_data.get('company_name'):
                print(f"  ✓ Enriched: {enriched_data.get('company_name')}")
                enriched += 1
            else:
                print(f"  ⚠️  AI returned limited data")
            
            # Save to database
            print(f"  💾 Saving to database...")
            company = save_company_to_db(domain, enriched_data, best_website, best_linkedin)
            print(f"  ✅ Saved: {company.domain} - {company.company_name or 'No name'}")
            
            # Delay to avoid rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"  ❌ Error processing {domain}: {e}")
            errors += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Enrichment process completed!")
    print(f"  Total processed: {processed}")
    print(f"  Successfully enriched: {enriched}")
    print(f"  Errors: {errors}")


if __name__ == "__main__":
    main()
