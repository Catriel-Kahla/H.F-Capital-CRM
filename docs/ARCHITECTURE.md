# Architecture

## Project Structure

```
Browserling CRM/
├── crm_project/       # Django project (settings, urls, wsgi)
├── crm/               # Home, import, AI enrichment
├── leads/             # Leads, companies, tags, scoring, Mailchimp
├── companies/         # Company CRUD, notes
├── templates/         # Shared + app templates
├── docs/              # Project documentation
└── docs/skills/       # Project skills for AI context
```

## Apps

| App | Responsibility |
|-----|----------------|
| `crm` | Home, CSV import, AI enrichment UI |
| `leads` | Lead/Company models, scoring, enrichment, Mailchimp, tags |
| `companies` | Company views, notes, recalculate scores |

## Models (leads app)

- **Lead** – One per email. FK to Company. Fields: email, lead_score, lead_stage, hierarchical_level, pdl_* (enrichment), tags (M2M to LeadTag).
- **Company** – One per domain (PK). Fields: domain, company_name, industry, pdl_* (funding), notes.
- **CompanyNote** – FK to Company. body, created_at, updated_at.
- **LeadTag** – Tags for leads. M2M on Lead.

## URL Structure

- `/` – Home
- `/leads/` – Lead list, CRUD, bulk actions
- `/companies/` – Company list, detail
- `/companies/<domain>/notes/` – Company notes
- `/admin/` – Django admin

## Key Files

- `leads/models.py` – Lead, Company, CompanyNote, LeadTag
- `leads/scoring.py` – Auto score/stage calculation
- `leads/enrichment.py` – DuckDuckGo + Gemini/OpenAI enrichment
- `leads/mailchimp_utils.py` – Mailchimp upsert, tags
