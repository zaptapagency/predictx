# Deploying ForecastX

The deployed shape is: **FastAPI backend on Railway**, **static front end on
Vercel**, **PostgreSQL** as the database. Redis is configured for but not
required to boot. This merges the previous Railway, Vercel, credentials,
checklist and monitoring documents into one.

## What gets deployed where

| Piece | Where | Config in repo |
|---|---|---|
| Backend (FastAPI) | Railway, Docker build | `railway.json`, root `Dockerfile` |
| Front end (`frontend/public/`, static) | Vercel | `vercel.json` (`outputDirectory: frontend/public`) |
| Database | Managed PostgreSQL (Railway plugin or elsewhere) | `DATABASE_URL` |

`railway.json` starts the app with
`uvicorn app.main:app --host 0.0.0.0 --port $PORT` and health-checks `/health`.

`vercel.json` has `buildCommand: exit 0` — there is no front-end build step; it
publishes `frontend/public/` (which contains `index.html` and
`dashboard.html`) as static files.

CI lives in `.github/workflows/`: `test.yml`, `deploy-railway.yml`,
`deploy-frontend.yml`, `deploy-digitalocean.yml`.

## Environment variables

Declared in `backend/app/config.py`. Anything not listed there is ignored.

### Required

| Variable | Notes |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET_KEY` | Signs auth tokens. The default is a placeholder — always override it |

### Strongly recommended in production

| Variable | Notes |
|---|---|
| `ENCRYPTION_KEY` | Fernet key for connector credentials and integration configs. When unset, the key is **derived from `JWT_SECRET_KEY`** (see `app/services/crypto.py`) — encryption still happens, but rotating the JWT secret then invalidates stored credentials, and the two secrets share a blast radius. Set this explicitly |
| `ENVIRONMENT` | `production` |
| `DEBUG` | `false` |
| `FRONTEND_URL` | Used in links generated in outbound email |

### Feature-gated (the corresponding feature is unavailable without them)

| Variable | Enables |
|---|---|
| `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` | Email delivery of actions and workflow steps. Without `SMTP_USER`/`SMTP_PASSWORD` the email channel reports itself as not configured rather than silently dropping mail |
| `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRO_PRICE_ID`, `STRIPE_ENTERPRISE_PRICE_ID` | Subscriptions and billing |
| `REDIS_URL` | Configured; the app boots without it |
| `SENTRY_DSN` | Error reporting |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET_NAME`, `AWS_REGION` | S3, optional |
| `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET` | Google sign-in. Caveat: `app/api/oauth.py` reads `GOOGLE_CLIENT_ID` / `MICROSOFT_CLIENT_ID`, which `config.py` does not declare — verify this path works before depending on it |
| `LIGHTGBM_REPO_*` | Legacy external-model loading; not used by the current training path |

Slack and outbound webhook destinations are **not** environment variables —
they are configured per organization at runtime in the Integrations tab and
stored encrypted in the database.

Never commit real credentials. Set them in the Railway/Vercel dashboards or
via CLI.

## Backend to Railway

```bash
npm install -g @railway/cli
railway login
railway init
railway add            # add the PostgreSQL plugin

railway variables set JWT_SECRET_KEY="$(python -c 'import secrets;print(secrets.token_urlsafe(48))')"
railway variables set ENCRYPTION_KEY="$(python -c 'from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())')"
railway variables set ENVIRONMENT=production DEBUG=false
# ...plus SMTP / Stripe / FRONTEND_URL as needed

railway up
railway domain          # note the resulting backend URL
```

`DATABASE_URL` is injected by the PostgreSQL plugin.

### Schema

There is no separate migration step required for a first deploy. On startup
`run_migrations()` in `app/main.py` runs `alembic upgrade head` when
`alembic.ini` is present, then calls `Base.metadata.create_all()` as a fallback
so any missing tables are created. To run migrations explicitly:

```bash
railway run python -m alembic upgrade head
```

## Front end to Vercel

```bash
npm install -g vercel
vercel --prod
```

Vercel publishes `frontend/public/`. The dashboard calls the backend directly,
so the API base URL in `frontend/public/dashboard.html` must point at the
deployed backend. The backend's CORS middleware currently returns
`Access-Control-Allow-Origin: *` for all responses, so a new front-end origin
does not require a backend change — but `CORS_ORIGINS` in `config.py` still
carries a hardcoded list, so keep it in mind if that middleware is tightened.

## Stripe webhooks

If billing is enabled, point a Stripe webhook endpoint at
`https://<backend-url>/api/webhooks/stripe` and set `STRIPE_WEBHOOK_SECRET` to
the signing secret Stripe gives you for that endpoint.

## Verifying a deploy

```bash
curl https://<backend-url>/health          # {"status":"healthy", ...}
curl https://<backend-url>/docs            # OpenAPI UI
```

Then walk the actual product loop, which is the only check that matters:

1. Sign up, confirm an organization exists for the new user.
2. Upload a CSV with a binary outcome column on the Connectors tab.
3. Train a model on that column from the Predictions tab; confirm the reported
   metrics are non-trivial and that training on a source *without* a label
   column is refused.
4. Score the model; confirm predictions appear.
5. Confirm the Heatmap and Action Center populate from those predictions.
6. Configure Slack in Integrations and use the test-message button — it sends a
   real message.
7. Execute one action and confirm it was actually delivered. A green tick with
   nothing received is a bug, not a success.

## Operating it

```bash
railway logs -f                       # follow logs
railway logs | grep -i error
railway variables                     # confirm what is actually set
railway run python -c "from app.database import engine; print(engine.connect())"
```

Common failures:

| Symptom | First thing to check |
|---|---|
| Backend won't boot | `DATABASE_URL` reachable; `run_migrations()` re-raises on schema failure, so the traceback is in the logs |
| A new table is missing | Its model module must be imported inside `run_migrations()` in `app/main.py`, and registered on the `Base` in `app/db/database.py` |
| Email actions fail as "not configured" | `SMTP_USER` / `SMTP_PASSWORD` unset. For Gmail this must be an app password |
| Slack actions fail | The org has no Slack webhook saved in Integrations, or the webhook was revoked. Use the test endpoint to isolate |
| Salesforce action fails | Expected until it has been proven against a live org — this path has never been tested end to end |
| Stored connector credentials suddenly unreadable | `ENCRYPTION_KEY` or (when it is unset) `JWT_SECRET_KEY` changed |
| Payments not recording | Check the Stripe dashboard's webhook delivery log, then `railway logs \| grep webhook` |

Take database backups from the Railway PostgreSQL plugin, and treat the
prediction and action tables as the data you cannot regenerate.
