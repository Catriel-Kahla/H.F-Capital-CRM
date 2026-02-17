# Integrations

## AI Enrichment (leads/enrichment.py)

- **DuckDuckGo** – Search for company URLs, LinkedIn
- **Gemini** (google-genai) – Select best URL, extract job title/name/LinkedIn
- **OpenAI** – Fallback for extraction

**Env vars**: `GENAI_API_KEY`, `OPENAI_API_KEY` (in `keys.env`)

**Flow**: CSV import → DuckDuckGo search → AI selects best URL → AI extracts person data → save to Lead/Company.

## Lead Scoring (leads/scoring.py)

Auto-calculated on Lead save. Signals:

- Session count, job title hierarchy, team adoption (multiple leads per domain)
- Enterprise domain, free vs work email

Stages: low → medium → high → very_high → enterprise.

## Mailchimp (leads/mailchimp_utils.py)

- **Env vars**: `MAILCHIMP_API_KEY`, `MAILCHIMP_SERVER_PREFIX`, `MAILCHIMP_AUDIENCE_ID`
- **Actions**: Upsert members, apply CRM tags as Mailchimp audience tags
- **Bulk**: Send selected leads or all leads with a tag to Mailchimp
