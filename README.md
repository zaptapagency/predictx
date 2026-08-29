# ForecastX

ForecastX is a multi-tenant web app for predicting which customers are at risk
and then actually doing something about it. You upload a CSV of your customers,
train a model on a column that records a known outcome, score your customer
base with it, and the resulting predictions drive a risk heatmap and a
prioritized list of actions that can be delivered over email, Slack, or a
webhook.

It is a working product, not a finished one. This README and
[ARCHITECTURE.md](ARCHITECTURE.md) describe what the code actually does today.
Where something is implemented but unproven, it says so.

## The core loop

```
CSV upload  ->  train  ->  score  ->  fan-out  ->  act
```

1. **Upload** (`POST /api/connectors/csv/upload`) — a CSV of customer records is
   parsed, an id column is picked (or supplied), and each row is stored as a
   `CustomerData` record under a `DataSource` belonging to your organization.
2. **Train** (`POST /api/training/train`) — you pick a data source and a
   **labelled outcome column**. The backend builds a numeric feature matrix,
   splits off a test set, fits a scikit-learn classifier (gradient boosting by
   default; logistic regression and random forest are also selectable), and
   stores accuracy / precision / recall / AUC measured on the held-out split.
   The fitted estimator and scaler are pickled into a `ModelArtifact` row.
   If there is no usable label column, training is **refused** — the platform
   does not invent labels to produce a model with a meaningless score.
3. **Score** (`POST /api/training/score`) — the stored artifact is loaded and
   applied to the organization's customer rows, writing real `Prediction` rows
   with a probability, a risk band, and the model's feature importances.
4. **Fan-out** (`app/services/prediction_sync.py`) — those predictions are
   turned into `CustomerHealthScore` rows (the Heatmap) and `Action` rows (the
   Action Center), with an estimated revenue impact where the customer's annual
   revenue is known.
5. **Act** (`app/services/channels.py`) — an action is executed by delivering it
   over a real channel. An action is only marked complete when delivery is
   confirmed; a failure marks it FAILED with the reason.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the detail, including which delivery
channels are real, which are unverified, and which explicitly refuse to run.

## Running it locally

Requirements: Python 3.11+ and a PostgreSQL database (SQLite works for the test
suite). Redis is referenced in config but is not required to boot.

```bash
cd backend
pip install -r requirements.txt

export DATABASE_URL="postgresql://user:pass@localhost:5432/forecastx"
export JWT_SECRET_KEY="something-random"

uvicorn app.main:app --reload --port 8000
```

On startup the app runs Alembic migrations when available and then calls
`Base.metadata.create_all()` as a fallback, so an empty database will be
populated with the schema on first boot.

- API: <http://localhost:8000>
- Interactive API docs: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health>

### The UI

The shipped front end is a single vanilla-JS page:
**`frontend/public/dashboard.html`**. It talks to the API directly and renders
one tab per feature. Serve `frontend/public/` as static files (that is what the
Vercel config does — `outputDirectory: frontend/public`) or open the file and
point it at your API host.

A React application also lived under `frontend/src/`. It was never what got
deployed; if you still find remnants of it, do not treat them as the product UI.

### Docker

`docker-compose.yml` brings up Postgres, Redis and the backend. Note that the
root `Dockerfile` clones an external LightGBM repository that the current
training path does not use. Both files are convenient for a local
Postgres/Redis, but read them before trusting them for anything else.

## Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

The suite in `backend/tests/` deliberately concentrates on the places where
being wrong would be expensive rather than on coverage percentage: that
predictions are never fabricated (`test_no_fabricated_predictions.py`), that
prediction fan-out produces the health scores and actions it claims to
(`test_prediction_fanout.py`), that action execution only reports success on
confirmed delivery (`test_action_execution.py`), workflow execution
(`test_workflow_engine.py`), credential encryption
(`test_credential_encryption.py`), and basic API wiring (`test_api.py`). Run
`pytest` for the current list and count — this directory is actively growing.

## Documentation

| Document | What it covers |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | How the system is put together and how data moves through it |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Deploying the backend and static front end, environment variables, operations |
| [docs/gtm/](docs/gtm/README.md) | Go-to-market material: discovery, interviews, pricing. Plans, not descriptions of the product |

Anything not listed above has been removed. The repository previously carried
around fifty status and session-summary documents that contradicted each other
and the code; they were deleted rather than maintained. Read the code, or the
three documents above.
