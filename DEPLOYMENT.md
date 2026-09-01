# Hazard Hero deployment

The API ships as a production Docker image and supports a managed MySQL database
or the included MySQL 8.4 Compose service. The container runs as a non-root user,
waits for the database, applies migrations, and starts Gunicorn. Static files are
served by WhiteNoise.

> **Security:** this repository previously tracked `.env`. Rotate the existing
> Django secret, database passwords, and any email credentials before deploying.
> Removing `.env` from the current Git index does not erase it from older commits;
> purge shared Git history separately if real credentials were committed.

## Required production services

- A Docker host or container platform
- MySQL 8.0 or newer
- An HTTPS reverse proxy or the platform's managed HTTPS ingress
- Persistent storage mounted at `/app/media`, unless media is moved to object
  storage
- SMTP credentials if password-reset email must be delivered

## Deploy with Docker Compose

Install Docker Engine with the Compose plugin on the server, then clone the
repository and create the production environment file:

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Put the generated value in `SECRET_KEY`. Replace every example hostname and
password in `.env`; `DB_PASSWORD` and `MYSQL_ROOT_PASSWORD` must be different
strong values. Keep `DEBUG=false`.

Start the services:

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f web
```

Place the API behind HTTPS and forward the original protocol in
`X-Forwarded-Proto`. The container listens on `HOST_PORT` (8000 by default).
Verify the deployment:

```bash
curl https://api.example.com/health/
```

The successful response is:

```json
{"status": "ok", "database": "ok"}
```

Create the first administrator/responder after the first deployment:

```bash
docker compose exec web python manage.py createsuperuser
```

Sample data is optional:

```bash
docker compose exec web python manage.py loaddata fixtures/sample_data.json
docker compose exec web python manage.py seed_sample_translations
```

## Deploy to a container platform

Build from `Dockerfile`, configure the variables from `.env.example`, and set
the health-check path to `/health/`. The platform supplies `PORT`; the
entrypoint binds Gunicorn to it automatically.

Connect `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` to a
managed MySQL instance. If the provider requires a CA certificate, mount it in
the container and set `DB_SSL_CA` to its path.

For a single application replica, leave `RUN_MIGRATIONS=true`. For multiple
replicas, run `python manage.py migrate --noinput` once as the platform's
release/pre-deploy command and set `RUN_MIGRATIONS=false` on the web replicas.

The default filesystem storage requires a persistent `/app/media` volume.
`SERVE_MEDIA=true` lets this container serve those uploads. At larger scale,
use shared object storage and keep `SERVE_MEDIA=false`.

## Coolify and Nixpacks

For Coolify, select the **Dockerfile** build pack and use `/Dockerfile` from the
repository root. Expose port `8000` and configure `/health/` as the health-check
path.

If the application is configured to use **Nixpacks**, the included
`nixpacks.toml` keeps Python, the compiler, `pkg-config`, and the MariaDB client
in one Nix toolchain. It also exposes the client metadata and runtime library
paths required by `mysqlclient`, collects static assets, and starts the same
migration-aware production entrypoint. No custom install or start command is
needed in the hosting panel. If the panel ignores this file, switch the build
pack to Dockerfile instead of mixing Ubuntu MySQL headers into the Nix
toolchain.

The settings append Coolify's `COOLIFY_FQDN` and `COOLIFY_URL` values to
`ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`. The Nixpacks configuration uses
`https://hazardheroapi.site` as the production domain and enables HTTPS
redirects.

The build log must show the current dependency versions from
`requirements.txt`. If it still shows `Django==5.0.14`, the platform is
deploying an older Git commit or the wrong branch. Push the current `main`
branch and redeploy without the build cache.

## Operations

Back up both MySQL and the media volume. For Compose:

```bash
docker compose exec -T db sh -c \
  'exec mysqldump -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"' \
  > hazard_hero.sql
```

To deploy an update:

```bash
git pull --ff-only
docker compose up -d --build
```

Review application logs and `/health/` after every rollout. Do not commit
`.env`, database files, generated static files, or user-uploaded media.
