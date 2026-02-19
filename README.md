# crm-django

## Version History

Version | Date       | Author          | Description
-------------------------------------------------------------
0.3.2   | 2026-02-19 | Catriel Kahla   | Non-stable subversion
0.3.1   | 2026-02-17 | Jonathan Nelson | Non-stable subversion
0.3.0   | 2026-02-10 | Catriel Kahla   | Non-stable release
0.2.0   | 2026-01-29 | Catriel Kahla   | Non-stable release
0.1.0   | 2026-01-19 | Catriel Kahla   | Initial non-stable release

---
## Version 0.3.2 – Subversion

### Leads List (UI + UX)
- Added a **Job Title** column to `/leads`.
- Reordered columns to: **Name**, **Job Title**, **Email**, Company, Score, Stage (checkbox first).
- Removed the **Status** column from the `/leads` list table.
- Added **column sorting** by clicking header titles:
  - Name, Job Title, Email, Company: A→Z
  - Score, Stage: max→min
  - Active sort shows a small arrow icon in the header.
- Added **pagination** to `/leads` (10 leads per page) with Previous/Next and a **Go to page** number input.
- Pagination and sorting preserve existing search/company filters.

### Lead Details (Tabs)
- Lead details view now uses **Fomantic tabs**: Personal, Company, Scoring, Activity, CRM, System Dates.

### Companies List (UI + UX)
- Added sortable headers and **pagination (10 per page)** to `/companies`.
- Domain column is now clickable and opens the company website in a new tab.

### Company Details (Tabs)
- Company details view now uses **Fomantic tabs** (Basic Information, Address, Contact & Social, CRM, Funding, System Dates).
- Added a **Linked Leads** tab showing all leads related to the company.

### Branding
- Added an **SVG favicon/app icon** using `static/img/Space Ship Logo SVG.svg` (favicon + shortcut icon + Apple touch icon).


------------------------------------------------------------

## Version 0.3.1 – Subversion

### UI Refresh (Flat Design)
- Updated UI to a flat design with a light blue accent via the `--light-blue` CSS variable.
- Uses vanilla Fomantic UI styling with a box-shadow override.
- Companies and leads pages now use a flatter layout (no segments for the main list layout), with `ui table` and basic buttons.

### Companies List Improvements
- Company name links to the company detail page with a "Show details" tooltip.
- Leads column: fixed reverse relation reference (`lead_set` → `leads`).
- Leads count now shows as a clickable "X leads" link that navigates to a filtered leads list.

### Leads List Improvements
- Lead email/name links to lead detail with a "Show details" tooltip; removed the View icon from action buttons.
- Striped leads table.
- Active status now renders as a green basic label.
- Mailchimp/tag actions grouped into segments with icons.
- Added `?company=domain` filter:
  - Shows a "Leads for [Company]" subheader
  - Includes a "Show all" link
  - Search preserves the active company filter

### Assets & Icons
- Added brand logo to static assets.
- LinkedIn icon uses the Fomantic `grey` class for a muted appearance.

### Dependencies
- Updated `requirements.txt` dependencies and compatibility.

------------------------------------------------------------

## Version 0.3.0 – Non-stable

### Lead Tag System (Email Tagging)
- Added a structured tag system for **leads (emails)**.
- New DB model: `LeadTag` + a `Lead.tags` Many-to-Many relationship.
- Tags are shown on `/leads` and can be used for bulk actions.

### Bulk Actions in `/leads`
- Select multiple leads via checkboxes.
- **Apply tag to selected**: type a tag name (ex: `enterprise`, `webinar-2026`) and apply it to the selected emails.
- **Send selected to Mailchimp**: sends selected emails; existing CRM tags are also pushed as **Mailchimp audience tags**.
- **Send all leads with tag to Mailchimp**: pick a tag and send all leads that have that tag.

### Search by Tags
- The search input in `/leads` now matches tag names too (in addition to name/email/company).

### Mailchimp Notes
- Mailchimp integration uses the environment variables:
  - `MAILCHIMP_API_KEY`
  - `MAILCHIMP_SERVER_PREFIX`
  - `MAILCHIMP_AUDIENCE_ID`
- Members are **upserted** (won't fail if already exists) and tags are applied via Mailchimp's member tags endpoint.

### UI/UX Improvements
- The Actions column now uses compact icon-only buttons for view, edit, and delete.
- Leads Stage column; new style at labels.
- A new "Name" column has been added to the leads list, displaying the lead's name and last name together.

### Company Notes System
- Added a per-company notes system to track explanations and workflow history.
- Route: `/companies/<domain>/notes/` (domain matches the existing company URL identifier).
- Full CRUD:
  - List + add note on the notes page
  - Edit: `/companies/<domain>/notes/<note_id>/edit/`
  - Delete: `/companies/<domain>/notes/<note_id>/delete/`
- New DB model: `CompanyNote` (FK to `Company`, `body`, `created_at`, `updated_at`).
- Django admin: `CompanyNote` is registered for browsing/search.
- Tests: `companies` app includes coverage for create/edit/delete and cross-company access protection.

------------------------------------------------------------

## Version 0.2.0 – Non-stable

### Overview
This release adds search, improves CSV import flow, enables AI lead enrichment during CSV uploads, and implements automated lead scoring with multi-signal intelligence.

### Features

#### **4. UI/UX Improvements & Codebase Cleanup**
- Home page: Removed Reports card and AI Enrichment button, added AI Enrichment card
- Leads list: Improved button alignment and sizing, removed enrichment buttons from lists
- Alerts: Now auto-hide after a few seconds for better UX
- "Recalculate Score" button restricted to leads only (not companies)
- Company detail view: Fixed rendering errors
- .gitignore: Added TEMP FILES/ and removed obsolete files
- Deleted demo, test, and unused scripts and documentation

#### **1. Lead Search & Filtering**
- Company search in /companies (filters by company name and domain)
- Lead search in /leads (filters by first name, last name, email, company name, and company domain)
- Clean search UI with clear button to reset filters
- Filter leads by score, stage, and other criteria

#### **2. AI Lead Enrichment**
- AI lead enrichment during CSV upload (DuckDuckGo + Gemini/OpenAI)
- Real-time progress tracking
- Support for job title, first/last name, and LinkedIn URL extraction

#### **3. Automated Lead Scoring System** ⭐ NEW
**Sophisticated multi-signal lead scoring algorithm** based on enterprise intelligence signals:

**Scoring Signals (0-100 scale):**
- **Session Count** (0-50 pts): 1 point per user engagement session
- **Product Adoption** (+25 pts): 6+ months of usage bonus
- **Team Adoption** (+30 pts): 2+ users from same enterprise domain ⭐ CORE
- **Job Title** (5-20 pts): CISO/CTO (20), VP/Director (15), Manager (10), Senior (8), IC (5)
- **Enterprise Domain** (+30 pts): Corporate domain vs. free email
- **Gmail Qualified** (+5 pts): Quality Gmail users with positive signals
- **Free Email Penalty** (-10 pts): Reduces score for personal emails

**Automatic Lead Stages (based on score):**
- 0-19: Low Priority
- 20-39: Medium Priority  
- 40-59: High Priority
- 60-79: Very High Priority
- 80-100: Enterprise Target

**Features:**
- ✅ Scores calculated automatically on every lead save
- ✅ Stages auto-updated based on score
- ✅ Read-only display in forms (no manual override)
- ✅ Management command: `python manage.py recalculate_scores`
- ✅ Admin list filtering and sorting by score/stage
- ✅ Team adoption signal detects multi-user companies

**Management Command Usage:**
```bash
# Recalculate all leads
python manage.py recalculate_scores

# Filter by stage
python manage.py recalculate_scores --stage very_high

# Specific email
python manage.py recalculate_scores --email user@example.com

# Limit records
python manage.py recalculate_scores --limit 100
```

### Fixed bugs
- **CSV Import Button**: Fixed "📥 Import CSV" button not being clickable (added cursor: pointer CSS)
- **New Lead Button**: Fixed "New Lead" button error by correcting URL reference from `leads:company_create` to `companies:company_create`
- **Gemini AI Model**: Updated from deprecated `gemini-2.0-flash-exp` to current stable `gemini-2.5-flash`, resolving 404 errors during AI enrichment
- **Cancel Button**: Fixed incorrect URL in CSV import cancel button from `leads:home` to `crm:home`
- **Search UX**: Removed intrusive search result alert messages for cleaner user experience
- **Clickable Links**: Added cursor: pointer to all clickable buttons and feature cards for better visual feedback
- Lead score and stage now non-editable (auto-calculated only)
- **Company Detail View**: Fixed errors when viewing company details
- **Button Alignment**: Fixed action button layout in leads list
- **Enrichment Buttons**: Removed from leads and companies lists
- **Alert Auto-hide**: Alerts now disappear automatically
- **Obsolete Files**: Removed demo, test, and unused files

------------------------------------------------------------

## Version 0.1.0 – Non-stable

### Overview
This initial release establishes the foundation of a Django-based Customer Relationship Management (CRM) system with AI-powered data enrichment capabilities. The system includes comprehensive models for managing leads and companies, with automated enrichment using DuckDuckGo search, Google Gemini, and OpenAI ChatGPT.

### Database Models

#### **Company Model** (in `leads` app):
  - domain (primary key)
  - company_name
  - industry
  - company_size
  - hq_country
  - org_type (public, private, gov, edu, nonprofit)
  - tech_stack
  - domain_confidence_score
  - street
  - city 
  - state
  - postal_code 
  - country     
  - work_phone
  - work_website
  - linkedin
  - facebook
  - owned_by
  - contact_type
  - tags
  - last_contacted
  - pdl_total_funding_raised
  - pdl_latest_funding_stage
  - pdl_last_funding_date
  - pdl_number_funding_rounds
  - created_at
  - updated_at

#### **Lead Model** (in `leads` app):
  - email (primary key)
  - company (ForeignKey to Company)
  - signup_date
  - session_count
  - is_free_email
  - is_candidate_enterprise
  - lead_score
  - lead_stage (low, medium, high, very_high, enterprise)
  - hierarchical_level (low, medium, high, unknown)
  - campaign_segment
  - email_status (active, bounced, unsubscribed)
  - crm_owner
  - first_seen
  - last_active
  - last_contacted_date
  - pdl_first_name
  - pdl_last_name
  - pdl_job_title
  - pdl_linkedin_url
  - pdl_job_last_verified
  - created_at
  - updated_at

### Core Features & Functions

#### **1. Project Structure**
Django project organized into specialized apps:
- **`crm_project`** - Main project configuration with settings, URLs, and WSGI/ASGI setup
- **`crm`** - Home app containing core CRM functions including CSV import and AI enrichment
- **`leads`** - Lead management with CRUD operations, enrichment utilities, and form handling
- **companies`** - Company management with CRUD operations and statistics tracking

#### **2. AI-Powered Data Enrichment**
Advanced company enrichment system using multiple AI providers:
- **`enrich_company()`** - Main enrichment function in [leads/enrichment.py](leads/enrichment.py)
  - **DuckDuckGo Search Integration**: Automatically searches for company websites and LinkedIn profiles
  - **Google Gemini AI**: Selects the best matching URLs from search results using AI decision-making
  - **OpenAI ChatGPT**: Validates and confirms final selections for accuracy
  - **Multi-threaded Processing**: Concurrent enrichment with progress tracking and error handling
  - **Real-time Progress Dashboard**: Streaming HTTP response showing live enrichment status

#### **3. Automated Lead Scoring System** ⭐ NEW
Multi-signal lead scoring algorithm ([leads/scoring.py](leads/scoring.py)):
- **`calculate_lead_score()`** - Comprehensive scoring function using 7 signals:
  - Session count (engagement metric)
  - Product adoption months bonus
  - Team adoption detection (2+ users per enterprise domain)
  - Job title hierarchy recognition (CISO/CTO through Individual Contributor)
  - Enterprise domain detection (vs. free email)
  - Gmail qualified adjustment
  - Free email penalty
- **`auto_calculate_score_and_stage()`** - Automatic calculation on Lead.save()
- **Automatic stage mapping** - Maps score to pipeline stage (Low → Enterprise Target)
- **Team adoption signal** - Enterprise intelligence: identifies companies with multi-user adoption
- **Management command** - `python manage.py recalculate_scores` for bulk operations
- All scoring **read-only in UI** - No manual override possible

#### **4. CSV Import System** 
Bulk data import with validation ([crm/views.py](crm/views.py)):
- **`import_csv()`** - Upload CSV files containing lead and company data
  - Validates CSV format and required fields (email, domain)
  - Creates or updates Company records based on domain
  - Creates Lead records with foreign key relationships
  - Optional AI enrichment during import process
  - Real-time progress updates with statistics
  - Error handling and detailed logging

#### **4. Lead Management Functions**
Complete CRUD operations for leads ([leads/views.py](leads/views.py)):
- **`lead_list()`** - Display all leads with company relationships
- **`lead_detail()`** - View detailed lead information (read-only)
- **`lead_create()`** - Create new leads with form validation
- **`lead_update()`** - Update existing lead information
- **`lead_delete()`** - Delete leads with confirmation
- **`clear_leads()`** - Bulk deletion of all leads and companies

#### **5. Company Management Functions**
Full company lifecycle management ([companies/views.py](companies/views.py)):
- **`company_list()`** - Display all companies with statistics (total, LinkedIn profiles)
- **`company_detail()`** - View detailed company information
- **`company_create()`** - Create new companies with validation
- **`company_update()`** - Edit company details
- **`company_delete()`** - Delete companies (cascades to associated leads)

#### **6. Django Admin Customizations**
Enhanced admin interface with custom actions ([leads/admin.py](leads/admin.py)):
- **CompanyAdmin**:
  - Custom list display with key fields
  - Filtering by industry, organization type, and country
  - `view_details()` action - Read-only detailed view with organized field groups
  - Search functionality across domain, name, and industry
- **LeadAdmin**:
  - List display with full name, company, score, and stage
  - Inline editing of lead score and stage
  - Filtering by stage, hierarchy level, email status
  - `view_details()` action - Comprehensive lead information display

#### **7. Forms & Data Validation**
Custom Django forms for data entry ([leads/forms.py](leads/forms.py)):
- **LeadForm** - Lead creation and editing with field validation
- **CompanyForm** - Company data entry with business rules

#### **8. Template System**
Responsive HTML templates with Bootstrap styling:
- **Base template** - [templates/base.html](templates/base.html) with navigation
- **Lead templates** - List, detail, create/edit, and delete confirmation views
- **Company templates** - Full CRUD interface templates
- **CRM templates** - Home page, CSV import interface, AI enrichment dashboard
- **Admin templates** - Custom detail view template for enhanced admin interface

### Technical Implementation Details

#### **Environment Configuration**
- Uses `.env` file ([keys.env](keys.env)) for API keys:
  - `GENAI_API_KEY` - Google Gemini API access
  - `OPENAI_API_KEY` - OpenAI ChatGPT access
- AI enrichment automatically disabled if API keys not present

#### **Database Design**
- SQLite database ([db.sqlite3](db.sqlite3)) for development
- Foreign key relationships with CASCADE deletion
- Automatic timestamps (created_at, updated_at)
- Choice fields for lead stages, hierarchical levels, email status

#### **External Integrations**
- **DuckDuckGo Search** - Web scraping for company information discovery
- **Google Gemini 2.0 Flash** - AI-powered URL selection and validation
- **OpenAI GPT** - Secondary validation and enrichment
- **People Data Labs (PDL)** - Prepared fields for future PDL API integration

#### **Utilities & Scripts**
- **`create_admin.py`** - Automated superuser creation script for development
- **URL Routing** - Modular URL configuration across all apps
- **Migrations** - Database schema version control

---

### Known Issues & Limitations

#### **Functional Issues**
- **Lead Editing Not Working** - `lead_update()` function exists but may have form validation issues
- **Database Clear Operation** - Currently clears entire database instead of selective deletion

#### **Code Quality Issues**
- **Unused Functions** - Home page ([crm/views.py](crm/views.py)) contains functions that need cleanup
- **Mixed Language Comments** - Some Spanish comments mixed with English code

#### **Missing Features**
- Lead editing interface needs debugging
- Analytics dashboard for lead scoring trends
- Selective database management (clear by filters)
- People Data Labs API integration (fields prepared but not connected)
- User authentication and permissions system
- Email campaign functionality
- Export functionality (CSV, Excel)

---

### Future Roadmap
- Fix lead editing functionality
- Implement proper lead scoring analytics
- Integrate People Data Labs API for enrichment
- Add export capabilities
- Create reporting and analytics dashboard
- Email campaign management
- API endpoints for external integrations
