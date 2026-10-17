# Backend

## News ingestion

The FastAPI server only reads cached articles. `GET /news` returns the newest
cached rows and `GET /feed` ranks cached rows. Neither endpoint calls NewsAPI.

News ingestion runs as a standalone transaction:

1. Acquire a PostgreSQL transaction advisory lock.
2. Fetch each configured NewsAPI query.
3. Bulk insert with `ON CONFLICT (url) DO NOTHING`.
4. Delete rows older than the retention period.
5. Delete the oldest excess rows above the hard cap.
6. Commit and log JSON metrics.

Run it from the `backend` directory:

```bash
python -m app.jobs.ingest_news
```

Optional overrides:

```bash
python -m app.jobs.ingest_news --query technology --query science --page-size 20 --retention-days 30 --max-rows 10000
```

## Database migration

Apply the retention and feed indexes before enabling the cron job:

```bash
alembic upgrade head
```

The initial migration baselines the complete schema with `IF NOT EXISTS`, so it
works for both the existing populated database and a fresh database.

## Render cron

The repository `render.yaml` defines an hourly cron job. Configure its secret
environment values in Render, then use this schedule and command. The command
applies pending migrations before ingestion:

```text
Schedule: 0 * * * *
Command:  python -m alembic upgrade head && python -m app.jobs.ingest_news
```

The cron only needs `DATABASE_URL` and `NEWSAPI_KEY`. Use the same database URL
as the web service. A failed fetch rolls back the whole run, and an overlapping
run exits successfully with `skipped_locked`.

## Configuration

Copy the variable names from `.env.example`. Defaults retain 30 days and at
most 10,000 rows. `INGESTION_QUERIES` is a comma-separated list.
