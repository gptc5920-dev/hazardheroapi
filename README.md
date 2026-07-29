# Hazard Hero REST API

Django REST Framework and MySQL backend for two clients: an anonymous,
read-only Citizen application and a JWT-protected Administrator/Responder
application. The only account role is `administrator_responder`.

## Deployment

The repository includes a hardened multi-stage `Dockerfile`, a MySQL-backed
`compose.yaml`, automatic migration startup, persistent media support, and a
database-aware health check at `/health/`. A `nixpacks.toml` fallback supports
platforms configured with Nixpacks. See [DEPLOYMENT.md](DEPLOYMENT.md) for the
production environment, Coolify, HTTPS, first-user, backup, and rollout steps.

## XAMPP/MySQL setup

Start MySQL in XAMPP and create a UTF-8 database named `hazard_hero`. The local
defaults are `root`, blank password, `127.0.0.1:3306`. Copy `.env.example` to
`.env` and change these values if your installation differs.

```powershell
cd C:\Users\nagoy\Downloads\hazard_hero\backend
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py loaddata fixtures/sample_data.json
python manage.py seed_sample_translations
python manage.py runserver
```

`createsuperuser` produces an active, verified account with the fixed
`administrator_responder` role.

## API entry points

- Public Citizen API: `http://127.0.0.1:8000/api/citizen/`
- Protected Responder API: `http://127.0.0.1:8000/api/responder/`
- Swagger UI: `http://127.0.0.1:8000/api/docs/`
- ReDoc: `http://127.0.0.1:8000/api/redoc/`
- OpenAPI schema: `http://127.0.0.1:8000/api/schema/`

Citizen modules are `go-bag`, `guidelines`, `evacuation-centers`,
`emergency-contacts`, and `alerts`. They accept only GET, HEAD, and OPTIONS and
use dedicated serializers that omit audit and responder fields.

## Citizen languages and translations

Exactly three languages are seeded by migration: English (`en`, always active
and default), Filipino (`fil`), and Bisaya (`ceb`). Citizens select a language
anonymously with `?language=en|fil|ceb`; published content falls back from the
requested language to English and then the original record. Every localized
record reports `requested_language`, `returned_language`, and `used_fallback`.

Responder translation routes include `go-bag-translations`,
`guideline-translations`, `guideline-media-translations`,
`evacuation-center-translations`, `emergency-contact-translations`,
`alert-translations`, and `calamity-translations`. Each supports draft,
needs-review, publish, archive, and copy-English workflows. Guideline offline
packages are available at
`/api/citizen/guidelines/{slug}/offline-manifest/?language=ceb` and include
versions, file sizes, SHA-256 hashes, captions, subtitles, and media URLs.

Responder login:

```http
POST /api/responder/auth/login/
Content-Type: application/json

{"email":"responder@example.com","password":"your-password"}
```

Use the returned access token on protected requests:

```http
Authorization: Bearer <access-token>
```

Authentication endpoints include login, refresh, logout/blacklist, profile,
change password, forgot password, and reset password. Content routes support
CRUD, `/deleted/`, `/{id}/restore/`, and `/{id}/permanent-delete/`. Specialized
actions include guideline publish/archive, contact verify, center
capacity/status, and alert publish/resolve/cancel/archive.

List endpoints support `search`, `ordering`, module-specific filters, `page`,
and `page_size` (maximum 100). Nearby endpoints accept `latitude`, `longitude`,
and `radius` in kilometers.

## Standard responses

Rendered JSON is wrapped as:

```json
{"success":true,"message":"Request completed successfully.","data":{},"errors":null}
```

Errors use the same envelope with `success: false`, `data: null`, and field
errors under `errors`.

## Validation and security

- JWT access/refresh tokens with rotation and blacklist support
- Active, verified, fixed-role checks on every responder endpoint
- Soft deletion and protected restore/permanent-delete actions
- Audit logs for authentication and management operations
- JPEG, PNG, WebP, PDF, DOC, and DOCX uploads up to 10 MB
- Image integrity and dimension validation
- MySQL constraints for capacity and alert date ranges
- Haversine nearby calculations
- CORS and all credentials configured through `.env`

## Tests

```powershell
$env:USE_SQLITE='true'
python manage.py test
```

The suite covers public access/exclusions, method rejection, JWT lifecycle,
account state enforcement, CRUD, soft deletion, workflow actions, nearby
search, capacity rules, upload validation, filtering, and audit logging.
