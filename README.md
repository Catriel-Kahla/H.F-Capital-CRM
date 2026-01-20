# crm-django

## Version History

Version | Date       | Author         | Description
------------------------------------------------------------
0.1.0   | 2026-01-19 | Catriel Kahla  | Initial non-stable release

---

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

#### **3. CSV Import System** 
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
- **Average Score Calculation** - Lead scoring aggregation functionality not implemented
- **Database Clear Operation** - Currently clears entire database instead of selective deletion

#### **Code Quality Issues**
- **Unused Functions** - Home page ([crm/views.py](crm/views.py)) contains functions that need cleanup
- **Mixed Language Comments** - Some Spanish comments mixed with English code

#### **Missing Features**
- Lead editing interface needs debugging
- Analytics dashboard for lead scoring
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
