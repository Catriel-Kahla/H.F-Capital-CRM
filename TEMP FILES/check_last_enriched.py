"""
Check the last enriched leads to see where we stopped.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from browserling_leads.db import get_session
from browserling_leads.models import Lead
from sqlalchemy import func


def check_enrichment_progress():
    """Check enrichment progress and find where we stopped."""
    
    with get_session() as session:
        # Total leads
        total_leads = session.query(func.count(Lead.email)).scalar()
        
        # Enriched leads (with PDL data)
        enriched_count = session.query(func.count(Lead.email)).filter(
            Lead.pdl_first_name.isnot(None)
        ).scalar()
        
        # Not enriched
        not_enriched = total_leads - enriched_count
        
        print("="*80)
        print("📊 ENRICHMENT PROGRESS")
        print("="*80)
        print(f"\nTotal leads:           {total_leads}")
        print(f"✅ Enriched:           {enriched_count} ({enriched_count/total_leads*100:.1f}%)")
        print(f"❌ Not enriched:       {not_enriched} ({not_enriched/total_leads*100:.1f}%)")
        
        # Last 10 enriched leads (most recently enriched)
        print(f"\n📝 LAST 10 ENRICHED LEADS:")
        print("-"*80)
        last_enriched = session.query(Lead).filter(
            Lead.pdl_first_name.isnot(None)
        ).order_by(Lead.updated_at.desc()).limit(10).all()
        
        for i, lead in enumerate(last_enriched, 1):
            name = f"{lead.pdl_first_name or ''} {lead.pdl_last_name or ''}".strip() or "N/A"
            print(f"{i:2}. {lead.email:40} | {name:25} | {lead.updated_at}")
        
        # First 10 NOT enriched leads
        print(f"\n❌ FIRST 10 NOT ENRICHED LEADS:")
        print("-"*80)
        not_enriched_leads = session.query(Lead).filter(
            Lead.pdl_first_name.is_(None)
        ).limit(10).all()
        
        for i, lead in enumerate(not_enriched_leads, 1):
            print(f"{i:2}. {lead.email:40} | Domain: {lead.domain:30}")
        
        print("\n" + "="*80)


if __name__ == "__main__":
    check_enrichment_progress()
