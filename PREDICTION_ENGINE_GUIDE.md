# Prediction Engine Guide

## Overview

The Prediction Engine transforms customer data into actionable insights by training ML models and generating scores that trigger workflows.

```
Raw Customer Data (Salesforce, CSV, Snowflake)
         ↓
Feature Engineering (compute customer metrics)
         ↓
Model Training (learn patterns from history)
         ↓
Predictions (score each customer)
         ↓
Workflows (alert teams, update CRM, send emails)
         ↓
Outcomes (track actual results)
         ↓
Model Learning (improve predictions based on outcomes)
```

---

## Architecture

### 1. Feature Engineering

Transforms raw customer data into features suitable for ML models:

**Account Features**
- `company_size_log` - Employee count (log scale)
- `is_enterprise` - 1 if > 1000 employees
- `account_age_days` - Days since customer created
- `industry` - Industry category (one-hot encoded)
- `country` - Country code

**Billing Features**
- `mrr` - Monthly recurring revenue
- `mrr_log` - MRR on log scale
- `acv` - Annual contract value
- `days_since_last_payment` - Days overdue
- `renewal_soon` - 1 if renewal in 0-90 days

**Engagement Features**
- `features_enabled` - Count of features being used
- `monthly_active_users` - MAU
- `api_calls_last_30d` - API usage
- `days_since_last_login` - Activity recency
- `dormant_30d` / `dormant_90d` - No activity flags

**Trend Features** (computed over 30/90 day windows)
- `mrr_change_30d_pct` - Revenue growth rate
- `usage_change_30d_pct` - Usage trend
- `mrr_growing` / `mrr_declining` - Binary flags
- `usage_growing` / `usage_declining` - Binary flags

### 2. Model Training

Trains ML models on historical data:

```python
POST /api/predictions/models/train

{
  "name": "Churn Risk Model Q3 2026",
  "model_type": "churn",
  "algorithm": "xgboost",
  "training_start": "2024-01-01T00:00:00Z",
  "training_end": "2026-08-01T00:00:00Z",
  "hyperparameters": {
    "n_estimators": 100,
    "max_depth": 6,
    "learning_rate": 0.1
  }
}
```

**Supported Model Types**
- **churn** - Predict probability customer will churn (0-1)
- **opportunity** - Predict upsell/cross-sell opportunity score
- **expansion** - Predict customer will expand purchases
- **health** - Composite customer health score

**Supported Algorithms**
- `logistic_regression` - Fast, interpretable, baseline
- `random_forest` - Medium complexity, good balance
- `xgboost` / `gradient_boosting` - High accuracy, slower training

### 3. Predictions

Generates scores for customers:

```python
POST /api/predictions/predict

{
  "model_id": 1,
  "customer_id": "ACME-001"
}

# Response:
{
  "id": 42,
  "customer_id": "ACME-001",
  "score": 0.82,
  "confidence": 0.91,
  "risk_level": "high",
  "recommended_action": "immediate_outreach",
  "top_factors": [
    {
      "feature": "days_since_last_login",
      "value": 45,
      "importance": 0.23
    },
    {
      "feature": "mrr_declining",
      "value": 1,
      "importance": 0.19
    },
    {
      "feature": "renewal_overdue",
      "value": 1,
      "importance": 0.15
    }
  ],
  "predicted_at": "2026-08-22T10:30:00Z"
}
```

---

## Quick Start

### Step 1: Ensure Data is Connected

First, make sure you have data flowing in via connectors:

```bash
# Check that you have data sources
GET /api/connectors/sources

# If no data sources yet, create them:
POST /api/connectors/connections  # Create connection
POST /api/connectors/sources      # Create data source
POST /api/connectors/sources/{id}/sync  # Trigger sync
```

### Step 2: Train Your First Model

Start with churn (most common first use case):

```bash
POST /api/predictions/models/train

{
  "name": "Churn Risk - Initial",
  "model_type": "churn",
  "algorithm": "xgboost",
  "training_start": "2024-01-01T00:00:00Z",
  "training_end": "2026-08-15T00:00:00Z"
}
```

Monitor training:

```bash
# List models
GET /api/predictions/models

# Get model details
GET /api/predictions/models/1

# View training runs
GET /api/predictions/models/1/training-runs
```

### Step 3: Make Predictions

Once model reaches `ACTIVE` status:

```bash
# Single prediction
POST /api/predictions/predict

{
  "model_id": 1,
  "customer_id": "ACME-001"
}

# Batch predictions (all customers)
POST /api/predictions/batch-predict

{
  "model_id": 1
}

# Or specific customers
POST /api/predictions/batch-predict

{
  "model_id": 1,
  "customer_ids": ["ACME-001", "ACME-002", "ACME-003"]
}
```

### Step 4: Create Workflows Triggered by Predictions

Link predictions to actions:

```bash
POST /api/workflows

{
  "name": "Churn Alert Workflow",
  "trigger_type": "prediction_threshold",
  "trigger_config": {
    "model_type": "churn",
    "threshold": 0.75,
    "comparison": "greater_than"
  },
  "actions": [
    {
      "type": "email",
      "config": {
        "to_field": "csm@company.com",
        "subject_template": "Alert: {customer_name} at risk",
        "body_template": "Churn probability: {score}%..."
      }
    },
    {
      "type": "salesforce",
      "config": {
        "object": "Account",
        "action": "update",
        "field_mapping": {"Risk_Level__c": "High"}
      }
    }
  ]
}
```

### Step 5: Track Outcomes and Refine

Record what actually happened:

```bash
# Record outcome
POST /api/predictions/predictions/{prediction_id}/outcome

{
  "outcome_type": "churn",
  "occurred_at": "2026-09-15T00:00:00Z",
  "notes": "Customer churned on renewal"
}

# Submit feedback
POST /api/predictions/predictions/{prediction_id}/feedback

{
  "helpful": true,
  "accurate": true,
  "comments": "Prediction matched actual behavior perfectly"
}
```

Outcomes feed back into model training for continuous improvement.

---

## Feature Engineering Details

### How Features Are Computed

**Numeric Features** (used directly in models):
- Extracted from raw data
- Missing values filled with median
- Standardized (zero mean, unit variance)

**Categorical Features** (one-hot encoded):
- Industry: finance → [is_finance=1, is_saas=0, is_retail=0]
- Country: US → [is_us=1, is_eu=0, is_apac=0]

**Trend Features** (computed from historical data):
- Compare current snapshot to 30/90 days ago
- Calculate percentage change
- Create binary flags for growth/decline

### Feature List

| Feature | Type | Source | Description |
|---------|------|--------|-------------|
| `company_size_log` | numeric | account | Log of employee count |
| `is_enterprise` | binary | account | 1 if > 1000 employees |
| `account_age_days` | numeric | account | Days since account created |
| `industry` | categorical | account | Industry category |
| `mrr` | numeric | billing | Monthly recurring revenue |
| `mrr_log` | numeric | billing | MRR on log scale |
| `days_since_last_payment` | numeric | billing | Payment recency |
| `payment_overdue` | binary | billing | 1 if > 30 days overdue |
| `renewal_soon` | binary | billing | 1 if renewal in 0-90 days |
| `features_enabled` | numeric | engagement | Count of features used |
| `monthly_active_users` | numeric | engagement | MAU |
| `api_calls_last_30d` | numeric | engagement | API usage count |
| `days_since_last_login` | numeric | engagement | Login recency |
| `dormant_30d` | binary | engagement | 1 if inactive 30+ days |
| `dormant_90d` | binary | engagement | 1 if inactive 90+ days |
| `mrr_change_30d_pct` | numeric | trend | 30-day revenue growth % |
| `usage_change_30d_pct` | numeric | trend | 30-day usage growth % |
| `mrr_growing` | binary | trend | 1 if revenue growing > 5% |
| `mrr_declining` | binary | trend | 1 if revenue declining > 5% |
| `usage_growing` | binary | trend | 1 if usage growing > 10% |
| `usage_declining` | binary | trend | 1 if usage declining > 10% |

### Custom Features

Add your own features by computing them in the feature engineer:

```python
# In FeatureEngineer._compute_custom_features()

features["custom_metric"] = raw_data.get("metric") * scaling_factor
features["custom_ratio"] = raw_data.get("a") / raw_data.get("b")
features["custom_flag"] = 1 if raw_data.get("condition") else 0
```

---

## Model Training Guide

### Data Requirements

**Minimum Training Data**: 50+ customers with outcomes

**Ideal Training Data**: 
- 2+ years of history
- 500+ customers with outcomes
- Balanced classes (if churn model: 10-30% actual churn)

### Preparing Training Data

1. **Set Training Period**
   ```
   Start: 2024-01-01 (oldest historical data)
   End: 2026-06-30 (leave 2 months for validation)
   ```

2. **Define Outcome Variable**
   - Churn: Customer did not renew
   - Expansion: Customer increased MRR
   - Renewal: Customer renewed contract

3. **Handle Missing Data**
   - Rows with missing outcomes: excluded
   - Rows with missing features: filled with median

### Model Performance Metrics

After training, model reports:

**Classification Metrics** (for churn/opportunity/expansion):
- **Accuracy** - % of predictions correct
- **Precision** - % of positive predictions correct
- **Recall** - % of actual positives found
- **F1 Score** - Harmonic mean of precision & recall
- **AUC-ROC** - Area under ROC curve (0.5 = random, 1.0 = perfect)

**How to Interpret**:
- Accuracy 75%, Precision 80%, Recall 70% = Good balance
- High precision, low recall = Misses true positives
- Low precision, high recall = Too many false alarms

### Training on Your Own Data

```bash
POST /api/predictions/models/train

{
  "name": "Custom Churn Model",
  "model_type": "churn",
  "algorithm": "xgboost",
  "training_start": "2024-01-01T00:00:00Z",
  "training_end": "2026-06-30T00:00:00Z",
  "hyperparameters": {
    "n_estimators": 200,
    "max_depth": 8,
    "learning_rate": 0.05,
    "min_child_weight": 5
  }
}

# Response includes training run ID
# Training happens in background
# Check status:

GET /api/predictions/models/{id}/training-runs
```

---

## Prediction Interpretation

### Understanding Prediction Output

```json
{
  "score": 0.82,
  "confidence": 0.91,
  "risk_level": "high",
  "recommended_action": "immediate_outreach",
  "top_factors": [
    {
      "feature": "days_since_last_login",
      "value": 45,
      "importance": 0.23
    }
  ]
}
```

**Score (0-1)**: Probability of outcome
- 0.0 = 0% chance
- 0.5 = 50% chance
- 1.0 = 100% chance

**Confidence (0-1)**: How certain is the model?
- 0.95+ = Very confident
- 0.7-0.9 = Reasonably confident
- < 0.7 = Low confidence (use with caution)

**Risk Level**: Categorical bucketing for human consumption
- For churn: low (< 0.4), medium (0.4-0.6), high (0.6-0.8), critical (> 0.8)
- For opportunity: low, medium, high

**Recommended Action**: Suggested next step
- For churn: "immediate_outreach", "outreach", "monitor", "maintain"
- For opportunity: "pursue", "explore", "track"

**Top Factors**: Why did the model predict this?
- Shows which features most influenced the score
- Helps explain prediction to stakeholders
- Guides action (e.g., "renew soon" → send renewal reminder)

### Risk Level to Action Mapping

```
Churn Model:
├─ Score 0.0-0.4: Low Risk
│  └─ Action: Maintain regular engagement
├─ Score 0.4-0.6: Medium Risk
│  └─ Action: Monitor, track usage trends
├─ Score 0.6-0.8: High Risk
│  └─ Action: Proactive outreach, identify concerns
└─ Score 0.8-1.0: Critical Risk
   └─ Action: Immediate escalation to leadership

Opportunity Model:
├─ Score 0.0-0.4: Low Opportunity
│  └─ Action: Track for future
├─ Score 0.4-0.6: Medium Opportunity
│  └─ Action: Qualify opportunity
└─ Score 0.6-1.0: High Opportunity
   └─ Action: Pursue deal
```

---

## Model Drift & Monitoring

### What is Model Drift?

**Prediction Drift**: Average score changes significantly
- Example: Churn model average score shifts from 0.3 to 0.6
- Indicates: Customer behavior changed or model became miscalibrated

**Feature Drift**: Input feature distributions change
- Example: MRR distribution shifted (customers getting bigger or smaller)
- Indicates: Business context changed, model needs retraining

### Detecting Drift

```bash
# Check model health
GET /api/predictions/models/1

# If is_drifted = true, time to retrain
```

System automatically:
1. Compares recent predictions to historical distribution
2. Monitors feature statistics over time
3. Flags models when drift detected (15% mean shift)

### Handling Drift

**If model is drifted:**

1. Retrain with recent data
   ```bash
   POST /api/predictions/models/train
   {
     "name": "Churn Model (Retrained Sept 2026)",
     "model_type": "churn",
     "training_start": "2024-01-01T00:00:00Z",
     "training_end": "2026-08-31T00:00:00Z"
   }
   ```

2. Test new model on recent predictions
   ```bash
   GET /api/predictions/models/{new_id}/training-runs
   # Compare accuracy to old model
   ```

3. Update workflows to use new model

4. Archive old model

---

## Batch Predictions

### Running Batch Predictions

Score all customers at once:

```bash
# All customers
POST /api/predictions/batch-predict
{
  "model_id": 1
}

# Specific customers
POST /api/predictions/batch-predict
{
  "model_id": 1,
  "customer_ids": ["ACME-001", "ACME-002", "ACME-003"]
}
```

Runs in background. Check status:

```bash
GET /api/predictions/predictions?model_id=1&limit=100
```

### Scheduling Batch Predictions

Run predictions on a schedule:

```python
# In your scheduling system (APScheduler, Celery, etc)

from app.services.model_service import ModelService

def batch_predict_daily():
    db = get_db()
    service = ModelService(db)
    
    # Predict for all models every night at 2 AM
    models = db.query(Model).filter(Model.status == ModelStatus.ACTIVE).all()
    
    for model in models:
        service.batch_predict(model.organization_id, model.id)
```

---

## Outcomes & Feedback

### Recording Outcomes

Track what actually happened:

```bash
POST /api/predictions/predictions/42/outcome

{
  "outcome_type": "churn",
  "outcome_value": 12500,  # MRR at time of churn
  "notes": "Customer churned after pricing increase"
}
```

**Outcome Types**:
- `churn` - Customer churned
- `expansion` - Customer expanded (increased MRR)
- `renewal` - Customer renewed contract
- `upgrade` - Customer upgraded plan

### Providing Feedback

Help the model learn:

```bash
POST /api/predictions/predictions/42/feedback

{
  "helpful": true,
  "accurate": true,
  "comments": "Prediction perfectly captured customer risk"
}
```

---

## API Reference

### Models

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/predictions/models/train` | POST | Train new model |
| `/api/predictions/models` | GET | List all models |
| `/api/predictions/models/{id}` | GET | Get model details |
| `/api/predictions/models/{id}/training-runs` | GET | Training history |

### Predictions

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/predictions/predict` | POST | Single prediction |
| `/api/predictions/batch-predict` | POST | Batch predictions |
| `/api/predictions/predictions` | GET | List predictions |
| `/api/predictions/predictions/{id}` | GET | Prediction details |

### Outcomes & Feedback

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/predictions/predictions/{id}/outcome` | POST | Record outcome |
| `/api/predictions/predictions/{id}/feedback` | POST | Submit feedback |

### Features

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/predictions/features` | GET | List all features |
| `/api/predictions/customer/{id}/features` | GET | Customer features |
| `/api/predictions/feature-statistics` | GET | Feature statistics |

---

## Common Questions

**Q: How much training data do I need?**
A: Minimum 50 customers with outcomes. Ideal: 500+ customers over 2+ years.

**Q: How long does training take?**
A: Usually 1-5 minutes for XGBoost. Larger datasets can take 10-30 minutes.

**Q: How often should I retrain?**
A: Monthly or when drift is detected. More frequent retraining (weekly) if business is changing rapidly.

**Q: Can I use custom features?**
A: Yes! Extend `FeatureEngineer` class to compute custom metrics from your data.

**Q: What if my model has low accuracy?**
A: Common causes: insufficient data, missing important features, incorrect outcome definition. Start with baseline model and gradually add features.

**Q: How do I know if predictions are working?**
A: Compare predictions to actual outcomes. Track: precision, recall, and customer action rate (% of predicted at-risk who did take predicted action).

**Q: Can I build models for other outcomes?**
A: Yes! Supported types: churn, opportunity, expansion, health, NPS. Extend for custom outcomes.

**Q: What happens to predictions if I update my data sources?**
A: New features will automatically flow in. Existing predictions stay as-is. Next batch prediction will use new features.

---

## Next Steps

1. **Connect your data** → Use data connectors
2. **Train first model** → Start with churn
3. **Generate predictions** → Score all customers
4. **Create workflows** → Connect predictions to actions
5. **Track outcomes** → Record what happens
6. **Refine & retrain** → Improve model performance
7. **Monitor metrics** → Watch for drift
8. **Expand models** → Add opportunity, expansion models
