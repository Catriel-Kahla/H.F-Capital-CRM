from django.shortcuts import render
from django.views.decorators.http import require_GET

@require_GET
def changelog(request):
    changelog_entries = [
        {
            "date": "2026-01-28",
            "content": "<b>Version 0.2.0 – Non-stable</b><br>\n\
<ul>\n\
<li><b>UI/UX improvements.</b></li>\n\
<li><b>Search & Filtering:</b> Company and lead search, filter by name, domain or email.</li>\n\
<li><b>AI Lead Enrichment:</b> AI enrichment during CSV upload, real-time progress, job title/LinkedIn extraction.</li>\n\
<li><b>Automated Lead Scoring:</b> Multi-signal algorithm (session count, adoption, job title, domain, etc.), auto-calculated on save, read-only in UI, management command for bulk updates.</li>\n\
<li><b>Bug Fixes:</b> CSV import button, new lead button, Gemini AI model update, cancel button, search UX, clickable links, non-editable score/stage.</li>\n\
</ul>"
        },
        {
            "date": "2026-01-19",
            "content": "<b>Version 0.1.0 – Non-stable</b><br>\n\
<ul>\n\
<li>Initial Django CRM foundation with AI-powered enrichment (DuckDuckGo, Gemini, OpenAI).</li>\n\
<li>Comprehensive models for leads and companies, with enrichment and scoring fields.</li>\n\
<li>Bulk CSV import, CRUD for leads/companies, admin customizations, template system, and utility scripts.</li>\n\
</ul>"
        },
    ]
    return render(request, 'crm/changelog.html', {"changelog_entries": changelog_entries})
