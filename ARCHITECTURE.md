# ForecastX Architecture

How the system is actually put together, and how a row of customer data becomes
an email that someone received. This document describes structure and
mechanism, not project status — feature-level status changes too fast to write
down, and a stale status file is worse than none.

## Shape of the repository

```
backend/
  app/
    main.py             FastAPI app factory; registers every router, runs
                        migrations + create_all fallback on startup
    config.py           Pydantic Settings, read from environment / .env
    database.py         Engine + session; app/db/database.py holds the Base
    api/                One module per feature, each exposing an APIRouter
    db/                 SQLAlchemy models, split by feature area
    services/           Cross-cutting logic (see below)
    connectors/         External data sources (CSV, Salesforce, Snowflake)
    ml/                 Older model-loading helpers
    fixtures/           Seed playbook templates
  tests/                pytest suite
frontend/
  public/dashboard.html The shipped UI: one vanilla-JS page, tab per feature
  public/index.html     Marketing / landing page
```

Multi-tenancy is by `organization_id`. Every user belongs to an Organization
(one is auto-created at signup, and `run_migrations()` backfills any user who
predates that), and essentially every feature table carries an
`organization_id` that queries filter on.

## The data flow

### 1. Data in

`app/api/csv_upload.py` (mounted under `/api/connectors/csv`) accepts a CSV
upload. It decodes UTF-8 (falling back to latin-1), reads the header row,
chooses an id column (explicit `id_column`, otherwise inferred), coerces values
that are clearly numbers or booleans, and writes one `CustomerData` row per CSV
row under a new `DataSource`. There is a file size limit and the endpoint
rejects empty files, missing headers, and non-CSV filenames.

`app/connectors/` holds the alternative path: a `ConnectorManager` factory over
`BaseConnector` implementations. Registered types are **csv**, **salesforce**,
and **snowflake** (the last only when `snowflake-connector-python` is
installed). Segment, BigQuery and Redshift appear as commented-out TODOs — they
do not exist. `app/api/connectors.py` manages connections, data sources and
syncs on top of that factory. Stored connector credentials are encrypted at
rest via `app/services/crypto.py` (Fernet; key from `ENCRYPTION_KEY`, derived
from `JWT_SECRET_KEY` when unset).

### 2. Training

`app/api/training.py`:

- `GET /api/training/candidates/{data_source_id}` looks over the loaded rows and
  proposes which column could serve as a binary outcome label.
- `POST /api/training/train` requires `label_column`. Labels are coerced from
  true/false, yes/no, 1/0. Training is **rejected** when the column is not
  binary, when every row shares the same outcome, or when there are no numeric
  feature columns. Missing feature values are filled with the column mean.
- The rows are split with `train_test_split` (stratified where possible), scaled
  with `StandardScaler`, and fitted with one of `GradientBoostingClassifier`
  (default), `RandomForestClassifier`, or `LogisticRegression`.
- Accuracy, precision, recall and ROC-AUC are computed **on the held-out test
  split**, not on training data, and stored on the `Model` row alongside
  normalized feature importances. A warning is attached when a class has fewer
  than 5 examples.
- The fitted estimator, the scaler, the feature list and the column means are
  pickled and base64-encoded into a `ModelArtifact` row.

The deliberate design constraint here: **the platform will not train without a
genuine outcome column.** Inventing labels would yield an accuracy number that
means nothing, and the test `tests/test_no_fabricated_predictions.py` exists to
keep that property from regressing.

### 3. Scoring

`POST /api/training/score` loads the `ModelArtifact`, unpickles the bundle,
rebuilds the feature matrix for the organization's customer rows using the
stored feature list and means, and writes real `Prediction` rows — a
probability, a risk band, and the contributing factors. No prediction is
written without a model behind it.

### 4. Fan-out

`app/services/prediction_sync.py` — `sync_from_predictions(db, org_id, model,
predictions)` is called after scoring and is the single place where predictions
become the rest of the product:

- **`_sync_health_scores`** upserts one `CustomerHealthScore` per customer. A
  model score in 0..1 becomes a 0-100 health score (inverted for risk models),
  with contributing metrics attached. This is what the **Heatmap** tab reads.
- **`_sync_actions`** creates `Action` rows for the customers that warrant one.
  Each carries an `estimated_impact`: for a risk model, `annual_revenue x
  probability` (revenue at stake); for an upside model, 20% of the account
  weighted by confidence. When the customer's annual revenue is unknown the
  impact is `None` rather than a guess. This is what the **Action Center** reads
  and sorts by.

Customer names, emails and revenue are looked up case-insensitively from the
synced `CustomerData`, so they depend on what was in the uploaded CSV.

### 5. Acting

`app/services/channels.py` is the delivery layer, shared by both the Action
Center and the workflow engine. It distinguishes two failure kinds:

- `ChannelUnavailable` — the channel is not set up (no SMTP credentials, no
  Slack webhook, no Salesforce connection). The user is told what to configure.
- `ChannelError` — the channel was tried and refused or failed. HTTP-based
  channels retry a bounded number of times before giving up.

| Channel | Mechanism | Status |
|---|---|---|
| `email` | Real SMTP send using `SMTP_USER` / `SMTP_PASSWORD` | Works |
| `slack` | POST to a Slack incoming webhook stored in Integrations | Works |
| `webhook` | POST of a JSON payload to a configured URL | Works |
| `task` | Internal task assignment inside the app | Works |
| `salesforce` | Creates a Task record via the org's Salesforce connection | **Implemented but never tested against a live Salesforce org** — treat the first run as a test |
| `phone_call`, `meeting`, anything else | `deliver_unsupported` | Raises "not built yet" on purpose. The platform cannot place a call for you and will not pretend it did |

The governing rule, enforced in `app/api/actions.py` and covered by
`tests/test_action_execution.py`: **an action is only marked COMPLETED when
delivery is confirmed.** Anything else is FAILED, with the error surfaced to the
user. Bulk execution reports executed and failed counts separately.

`app/api/integrations.py` is where Slack and webhook destinations are
configured (`GET`/`PUT`/`DELETE /api/integrations`, plus
`POST /api/integrations/{channel}/test` which sends a real test message).

### 6. Workflows / playbooks

`app/services/workflow_engine.py` executes multi-step playbooks against the
same `channels.py` delivery layer — so a workflow step is subject to exactly the
same "confirmed delivery or it failed" rule. It supports templated field
substitution, conditional steps and segment filters. A run whose steps all
succeeded is COMPLETED; a run with some failures is **PARTIAL**; a run that
failed outright is **FAILED**. It does not report success for steps that did
not deliver.

## Dashboard tabs and the endpoints behind them

`frontend/public/dashboard.html` defines its tabs declaratively. Each is a name
plus the API path it fetches:

| Tab | Endpoint |
|---|---|
| Home | `/api/user/home` |
| Onboarding | `/api/onboarding/progress` |
| Predictions | `/api/predictions/predictions`, `/api/predictions/models` (+ training panel) |
| Action Center | `/api/actions/dashboard` |
| Quick Wins | `/api/quick-wins/available` |
| Playbooks | `/api/workflows/` |
| Insights | `/api/insights/feed` |
| Copilot | `/api/copilot/recommendations` |
| Heatmap | `/api/heatmap/overview` |
| ROI Tracker | `/api/roi/dashboard` |
| Leaderboard | `/api/leaderboard/rankings` |
| Activity Feed | `/api/activity-feed/team` |
| Adoption | `/api/adoption/team-summary` |
| Team | `/api/teams/members`, `/api/teams/pending-invitations` |
| Marketplace | `/api/marketplace/playbooks` |
| Integrations | `/api/integrations` |
| Connectors | `/api/connectors/csv/customers`, `/api/connectors/connections`, `/api/connectors/types` |

Tabs differ in how closely they are wired to real prediction output. Heatmap,
Action Center, Predictions, Integrations, Connectors and Playbooks sit directly
on the flow described above. The rest are at varying stages of being connected
to it — check the endpoint's module rather than assuming.

## SaaS layer

Separate from the prediction product, `app/api/saas_*.py` provides
authentication (JWT), subscriptions and billing (`services/billing_service.py`,
Stripe), API keys, user profile and admin endpoints. `app/api/webhooks.py`
handles inbound Stripe webhooks. `app/api/oauth.py` exposes Google and
Microsoft sign-in endpoints — note that it reads settings
(`GOOGLE_CLIENT_ID`, `MICROSOFT_CLIENT_ID`) that are **not declared in
`config.py`**, which declares `GOOGLE_OAUTH_CLIENT_ID` instead. Verify that path
before relying on it.

## Things to know before you change anything

- **Schema creation happens at startup**, in `run_migrations()` in `main.py`.
  Alembic runs when present; `Base.metadata.create_all()` always follows as a
  fallback. A new model file must be imported in that function's import block or
  its table will not be created.
- **`Base` lives in `app/db/database.py`.** Models registered on a different
  Base will be silently skipped by `create_all`.
- The root `Dockerfile` clones an external LightGBM repository into the image.
  The training path described above uses scikit-learn and does not need it.
- `app/ml/` and `LIGHTGBM_REPO_*` settings are from an earlier design in which
  pre-trained models were loaded from an external repository. Current training
  and scoring live in `app/api/training.py`.
