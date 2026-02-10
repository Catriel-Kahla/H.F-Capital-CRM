"""
Enrich leads using AI (Gemini/ChatGPT) and DuckDuckGo search.
Alternative to People Data Labs for when API credits are exhausted.

Usage:
    # Enrich specific lead
    python scripts/enrich_leads_with_ai.py --email mukeshkumar.balwani@aujas.com --dry-run
    
    # Enrich first 10 leads without PDL data
    python scripts/enrich_leads_with_ai.py --limit 10
    
    # Enrich all unenriched leads
    python scripts/enrich_leads_with_ai.py --limit 999999
"""

import sys
import argparse
import time
from pathlib import Path
import os
import json
from dotenv import load_dotenv
from ddgs import DDGS
from google import genai
from openai import OpenAI
from datetime import datetime

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from browserling_leads.db import get_session
from browserling_leads.models import Lead

# Load environment variables
load_dotenv("keys.env")

# Configure AI clients
GENAI_API_KEY = os.getenv("GENAI_API_KEY")
gemini_client = genai.Client(api_key=GENAI_API_KEY)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
gpt_client = OpenAI(api_key=OPENAI_API_KEY)


def search_person_with_ddgs(email: str, max_results: int = 10):
    """Search for person information using DuckDuckGo."""
    # Extract name parts from email if possible
    local_part = email.split('@')[0]
    
    # Common email patterns: firstname.lastname, firstnamelastname, flastname, etc.
    queries = [
        f"{email}",
        f"{email} LinkedIn",
        f"{local_part} LinkedIn profile",
        f'"{email}" professional profile',
    ]
    
    results = []
    with DDGS() as ddgs:
        for query in queries:
            try:
                for r in ddgs.text(query, max_results=max_results):
                    href = r.get("href") or r.get("link")
                    title = r.get("title", "")
                    snippet = r.get("body", "")
                    if href:
                        results.append({
                            "title": title,
                            "url": href,
                            "snippet": snippet,
                            "query": query
                        })
                time.sleep(0.3)
            except Exception as e:
                print(f"    ⚠️  Search error for '{query}': {e}")
                continue
    
    # Remove duplicates
    seen = set()
    dedup = []
    for item in results:
        u = item["url"]
        if u not in seen:
            seen.add(u)
            dedup.append(item)
    
    return dedup


def extract_linkedin_url(results: list) -> str:
    """Extract LinkedIn URL from search results."""
    for result in results:
        url = result.get("url", "")
        if "linkedin.com/in/" in url:
            # Clean up LinkedIn URL
            if "?" in url:
                url = url.split("?")[0]
            return url
    return None


def enrich_lead_with_ai(email: str, search_results: list, use_model="gemini"):
    """Use AI to extract person information from search results."""
    
    if not search_results:
        return None
    
    # Prepare context from search results
    context = ""
    for i, result in enumerate(search_results[:10], 1):
        context += f"\n{i}. Title: {result.get('title', '')}\n"
        context += f"   URL: {result.get('url', '')}\n"
        context += f"   Snippet: {result.get('snippet', '')}\n"
    
    prompt = f"""Analyze the following search results about a professional with email: {email}

Search Results:
{context}

Extract and return ONLY a JSON object with the following information:
{{
    "first_name": "extracted first name or null",
    "last_name": "extracted last name or null",
    "job_title": "current job title or null",
    "linkedin_url": "LinkedIn profile URL or null (must be linkedin.com/in/...)",
    "confidence": "high/medium/low based on data quality"
}}

Instructions:
- Carefully analyze ALL search results for any mentions of names, job titles, or professional information
- Look for patterns: titles often contain person names, snippets mention job roles
- If you find a LinkedIn URL like "linkedin.com/in/john-smith-123", extract the name from it (john smith)
- Names in URLs use hyphens instead of spaces (john-smith = John Smith)
- Search result titles and snippets often contain "Name - Job Title at Company"
- Be thorough but accurate - extract what you can find
- Return ONLY valid JSON, no explanations
- Use null only when you truly cannot find any information
- For linkedin_url, include any linkedin.com/in/... URL you find
"""

    try:
        if use_model == "gemini":
            response = gemini_client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=prompt
            )
            text = response.text.strip()
        else:  # chatgpt
            response = gpt_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert data extraction assistant. You excel at finding names, job titles, and professional information from search results. Be thorough and extract all available information. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3  # Slightly higher for better inference
            )
            text = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
            text = text.strip()
        
        # Parse JSON
        data = json.loads(text)
        return data
        
    except Exception as e:
        print(f"    ⚠️  AI extraction error: {e}")
        return None


def enrich_lead(email: str, dry_run=False, ai_model="gemini", force=False):
    """Enrich a single lead using AI and DuckDuckGo."""
    
    print(f"\n{'='*80}")
    print(f"📧 Processing: {email}")
    print(f"{'='*80}")
    
    # Check if already enriched (unless force=True)
    if not force:
        with get_session() as session:
            lead = session.get(Lead, email)
            if lead and lead.pdl_first_name:
                print(f"⏭️  SKIPPED - Already enriched (use --force to re-enrich)")
                print(f"   Current data: {lead.pdl_first_name} {lead.pdl_last_name} | {lead.pdl_job_title}")
                return {"skipped": True}
    
    # Search for person information
    print("🔍 Searching with DuckDuckGo...")
    search_results = search_person_with_ddgs(email)
    
    if not search_results:
        print("❌ No search results found")
        return None
    
    print(f"✅ Found {len(search_results)} search results")
    
    # Extract LinkedIn URL
    linkedin_url = extract_linkedin_url(search_results)
    if linkedin_url:
        print(f"🔗 LinkedIn found: {linkedin_url}")
    
    # Use AI to extract information
    print(f"🤖 Extracting data with {ai_model.upper()}...")
    ai_data = enrich_lead_with_ai(email, search_results, use_model=ai_model)
    
    if not ai_data:
        print("❌ AI extraction failed")
        return None
    
    # Display extracted data
    print(f"\n📊 EXTRACTED DATA:")
    print(f"  First Name:     {ai_data.get('first_name', 'N/A')}")
    print(f"  Last Name:      {ai_data.get('last_name', 'N/A')}")
    print(f"  Job Title:      {ai_data.get('job_title', 'N/A')}")
    print(f"  LinkedIn:       {ai_data.get('linkedin_url', 'N/A')}")
    print(f"  Confidence:     {ai_data.get('confidence', 'N/A')}")
    
    if dry_run:
        print("\n🔍 DRY RUN - No database update")
        return ai_data
    
    # Update database
    with get_session() as session:
        lead = session.get(Lead, email)
        if not lead:
            print(f"❌ Lead not found in database: {email}")
            return None
        
        # Update fields
        if ai_data.get('first_name'):
            lead.pdl_first_name = ai_data['first_name']
        if ai_data.get('last_name'):
            lead.pdl_last_name = ai_data['last_name']
        if ai_data.get('job_title'):
            lead.pdl_job_title = ai_data['job_title']
        if ai_data.get('linkedin_url'):
            lead.pdl_linkedin_url = ai_data['linkedin_url']
        
        lead.pdl_job_last_verified = datetime.utcnow()
        lead.updated_at = datetime.utcnow()
        
        session.commit()
        print("✅ Database updated")
    
    return ai_data


def main():
    parser = argparse.ArgumentParser(description="Enrich leads using AI and DuckDuckGo")
    parser.add_argument("--email", type=str, help="Specific email to enrich")
    parser.add_argument("--limit", type=int, default=10, help="Number of leads to enrich")
    parser.add_argument("--dry-run", action="store_true", help="Show data without updating database")
    parser.add_argument("--ai-model", type=str, default="gemini", choices=["gemini", "chatgpt"], help="AI model to use")
    parser.add_argument("--force", action="store_true", help="Force re-enrichment of already enriched leads")
    args = parser.parse_args()
    
    print("="*80)
    print("🤖 AI-POWERED LEAD ENRICHMENT")
    print("Using: DuckDuckGo + " + args.ai_model.upper())
    print("="*80)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No database updates")
    
    if args.force:
        print("⚠️  FORCE MODE - Will re-enrich already enriched leads")
    
    print()
    
    # Get leads to process
    with get_session() as session:
        if args.email:
            # Process specific email
            leads = [session.get(Lead, args.email)]
            if not leads[0]:
                print(f"❌ Lead not found: {args.email}")
                return
        else:
            # Get unenriched leads only (unless force=True)
            query = session.query(Lead)
            if not args.force:
                query = query.filter(Lead.pdl_first_name.is_(None))
            leads = query.limit(args.limit).all()
        
        lead_emails = [lead.email for lead in leads if lead]
    
    print(f"📊 Processing {len(lead_emails)} lead(s)\n")
    
    # Process each lead
    stats = {"success": 0, "failed": 0, "skipped": 0, "total": len(lead_emails)}
    
    for i, email in enumerate(lead_emails, 1):
        print(f"\n[{i}/{stats['total']}]")
        try:
            result = enrich_lead(email, dry_run=args.dry_run, ai_model=args.ai_model, force=args.force)
            if result and result.get("skipped"):
                stats["skipped"] += 1
            elif result:
                stats["success"] += 1
            else:
                stats["failed"] += 1
            
            # Rate limiting
            if i < stats['total']:
                time.sleep(2)  # Wait 2 seconds between requests
                
        except Exception as e:
            print(f"❌ Error: {e}")
            stats["failed"] += 1
            continue
    
    # Summary
    print(f"\n{'='*80}")
    print(f"📊 ENRICHMENT SUMMARY")
    print(f"{'='*80}")
    print(f"Total processed: {stats['total']}")
    print(f"✅ Success: {stats['success']}")
    print(f"⏭️  Skipped: {stats['skipped']}")
    print(f"❌ Failed: {stats['failed']}")
    if stats['total'] > 0:
        print(f"Success rate: {stats['success']/stats['total']*100:.1f}%")
    print()


if __name__ == "__main__":
    main()
