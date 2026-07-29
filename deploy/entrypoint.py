import os
import sys
import time


def enabled(name, default=True):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def prepare_database():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    import django

    django.setup()

    from django.core.management import call_command
    from django.db import connections

    attempts = int(os.getenv("DATABASE_STARTUP_ATTEMPTS", "12"))
    delay = float(os.getenv("DATABASE_STARTUP_DELAY_SECONDS", "5"))

    for attempt in range(1, attempts + 1):
        try:
            connections["default"].ensure_connection()
            break
        except Exception as error:
            if attempt == attempts:
                raise
            print(
                f"Database unavailable ({error}); retrying "
                f"{attempt}/{attempts} in {delay:g}s.",
                flush=True,
            )
            time.sleep(delay)

    if enabled("RUN_MIGRATIONS"):
        call_command("migrate", interactive=False)

    connections.close_all()


def start_server():
    port = os.getenv("PORT", "8000")
    workers = os.getenv("GUNICORN_WORKERS", "3")
    threads = os.getenv("GUNICORN_THREADS", "2")
    timeout = os.getenv("GUNICORN_TIMEOUT", "120")

    command = [
        "gunicorn",
        "config.wsgi:application",
        "--bind",
        f"0.0.0.0:{port}",
        "--workers",
        workers,
        "--threads",
        threads,
        "--timeout",
        timeout,
        "--access-logfile",
        "-",
        "--error-logfile",
        "-",
    ]
    os.execvp(command[0], command)


if __name__ == "__main__":
    try:
        prepare_database()
        start_server()
    except Exception as error:
        print(f"Application startup failed: {error}", file=sys.stderr, flush=True)
        raise
