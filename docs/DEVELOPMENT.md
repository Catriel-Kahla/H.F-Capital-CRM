# Development

## Environment

Create `keys.env` in project root:

```
GENAI_API_KEY=...
OPENAI_API_KEY=...
MAILCHIMP_API_KEY=...
MAILCHIMP_SERVER_PREFIX=us21
MAILCHIMP_AUDIENCE_ID=...
```

## Run

```powershell
.\start.ps1
# or
python manage.py runserver
```

## Dependencies

See `requirements.txt`. Key packages:

- Django, djangorestframework
- duckduckgo-search, google-genai, openai
- python-dotenv, mailchimp-marketing

## Database

- SQLite: `db.sqlite3`
- Migrations: `python manage.py migrate`

## Production

- Set `DJANGO_PRODUCTION=True` (start.ps1 does this on server)
- See `DEPLOY.md` for nginx, deployment
