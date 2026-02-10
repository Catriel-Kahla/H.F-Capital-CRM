"""
Script to check detailed information for a specific lead.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from browserling_leads.db import get_session
from browserling_leads.models import Lead
import argparse


def check_lead(email: str):
    """Check all fields for a specific lead."""
    with get_session() as session:
        lead = session.get(Lead, email)
        
        if not lead:
            print(f"❌ Lead not found: {email}")
            return
        
        print("=" * 80)
        print(f"📧 LEAD DETAILS: {email}")
        print("=" * 80)
        print()
        
        # Basic info
        print("📋 BASIC INFORMATION:")
        print(f"  Email:                    {lead.email}")
        print(f"  Domain:                   {lead.domain}")
        print(f"  Email Status:             {lead.email_status}")
        print(f"  Is Free Email:            {lead.is_free_email}")
        print(f"  Is Candidate Enterprise:  {lead.is_candidate_enterprise}")
        print()
        
        # Personal info
        print("👤 PERSONAL INFORMATION:")
        print(f"  PDL First Name:           {lead.pdl_first_name}")
        print(f"  PDL Last Name:            {lead.pdl_last_name}")
        print(f"  PDL LinkedIn URL:         {lead.pdl_linkedin_url}")
        print(f"  PDL Job Title:            {lead.pdl_job_title}")
        print(f"  PDL Job Last Verified:    {lead.pdl_job_last_verified}")
        print()
        
        # Scoring
        print("⭐ SCORING:")
        print(f"  Lead Score:               {lead.lead_score}")
        print(f"  Lead Stage:               {lead.lead_stage}")
        print(f"  Hierarchical Level:       {lead.hierarchical_level}")
        print()
        
        # Campaign
        print("📢 CAMPAIGN:")
        print(f"  Campaign Segment:         {lead.campaign_segment}")
        print(f"  CRM Owner:                {lead.crm_owner}")
        print(f"  Last Contacted Date:      {lead.last_contacted_date}")
        print()
        
        # Activity
        print("📊 ACTIVITY:")
        print(f"  Session Count:            {lead.session_count}")
        print(f"  Signup Date:              {lead.signup_date}")
        print(f"  First Seen:               {lead.first_seen}")
        print(f"  Last Active:              {lead.last_active}")
        print()
        
        # Timestamps
        print("🕐 TIMESTAMPS:")
        print(f"  Created At:               {lead.created_at}")
        print(f"  Updated At:               {lead.updated_at}")
        print()
        
        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Check detailed lead information")
    parser.add_argument("email", help="Email address of the lead to check")
    args = parser.parse_args()
    
    check_lead(args.email)


if __name__ == "__main__":
    main()
