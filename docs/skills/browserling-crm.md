---
name: browserling-crm
description: Django CRM for Browserling. Use when working on leads, companies, scoring, AI enrichment, Mailchimp, or CSV import in this project.
---

# Browserling CRM

## Project Overview

Django CRM with leads, companies, AI enrichment (DuckDuckGo + Gemini/OpenAI), lead scoring, and Mailchimp integration.

## Structure

- **crm** – Home, CSV import, AI enrichment UI
- **leads** – Lead/Company models, scoring, enrichment, Mailchimp, LeadTag
- **companies** – Company CRUD, notes

## Models (leads app)

- **Lead** – email (PK), company (FK by domain), lead_score, lead_stage, pdl_*, tags (M2M LeadTag)
- **Company** – domain (PK), company_name, pdl_*, etc.
- **CompanyNote** – FK Company, body
- **LeadTag** – name, M2M on Lead

## Conventions

- Company PK is `domain` (not id). Use `to_field='domain'` on FKs.
- Lead scoring auto-runs on save via `leads/scoring.py`.
- Enrichment: `leads/enrichment.py` – DuckDuckGo → Gemini/OpenAI.
- Env: `keys.env` with GENAI_API_KEY, OPENAI_API_KEY, MAILCHIMP_*.

## Key Paths

- `leads/models.py`, `leads/scoring.py`, `leads/enrichment.py`, `leads/mailchimp_utils.py`
- `docs/` – ARCHITECTURE.md, INTEGRATIONS.md, DEVELOPMENT.md
