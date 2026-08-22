# Data Foundation & Workflow Automation Guide

## Overview

The Data Foundation consists of two critical systems that work together:

1. **Data Connectors** - Ingest customer data from multiple sources (Salesforce, CSV, Snowflake, etc.)
2. **Workflow Automation** - Execute actions based on predictions (Email, Slack, Salesforce, Webhooks, Tasks)

Together, they create the complete prediction → action → outcome feedback loop.

```
Data Sources → Data Connectors → ForecastX DB → ML Models → Predictions → Workflows → Actions → Outcomes
                                                               ↑___________________________________↓
                                              (Continuous learning & feedback loop)
```

---

## Part 1: Data Connectors

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Connector Manager (Factory)              │
│                                                             │
│  - create_connector()  - Instantiate right connector      │
│  - get_supported_types() - List available connectors      │
└────────────┬──────────────────────────────────────────────┘
             │
    ┌────────┴────────────────────────────────────────┐
    │                                                  │
┌─────────────────┐  ┌──────────────┐  ┌─────────────────┐
│ Salesforce      │  │ CSV Connector│  │ Snowflake       │
│ Connector       │  │              │  │ Connector       │
│                 │  │              │  │                 │
│ - OAuth2        │  │ - Local      │  │ - SQL Queries   │
│ - SOQL queries  │  │ - S3         │  │ - Pooling       │
│ - CRM objects   │  │ - GCS        │  │ - Schema sync   │
└─────────────────┘  └──────────────┘  └─────────────────┘
    │                      │                    │
    └──────────────────────┴────────────────────┘
                           │
                ┌──────────▼──────────┐
                │  Base Connector     │
                │  (Abstract class)   │
                │                     │
                │ - test_connection() │
                │ - get_schema()      │
                │ - fetch_data()      │
                │ - Type conversion   │
                └─────────────────────┘
```

### How to Use Data Connectors

#### 1. Create a Connection

```bash
POST /api/connectors/connections

{
  "name": "Production Salesforce",
  "connector_type": "salesforce",
  "description": "Main CRM",
  "config": {
    "instance_url": "https://mycompany.salesforce.com",
    "api_version": "v60.0"
  },
  "credentials": {
    "access_token": "00D...",
    "refresh_token": "5Aep...",
    "client_id": "3MV...",
    "client_secret": "9876543210"
  }
}
```

**Supported Connector Types:**
- **Salesforce**: CRM with OAuth authentication
- **CSV**: Local or cloud files (S3/GCS)
- **Snowflake**: Data warehouse with SQL
- **Segment** (TODO): Customer data platform
- **BigQuery** (TODO): Google's analytics warehouse
- **Redshift** (TODO): AWS data warehouse

#### 2. Test the Connection

```bash
POST /api/connectors/connections/{connection_id}/test

# Returns:
{
  "connection_id": 1,
  "is_valid": true,
  "error": null
}
```

#### 3. Create Data Sources

A data source maps to a specific table or dataset within a connection.

```bash
POST /api/connectors/sources

{
  "connection_id": 1,
  "name": "Salesforce Accounts",
  "source_path": "Account",
  "primary_key": "Id",
  "sync_type": "incremental",
  "incremental_field": "LastModifiedDate"
}
```

The system automatically fetches the schema:
```json
{
  "Id": {"type": "string", "nullable": false},
  "Name": {"type": "string", "nullable": false},
  "Revenue": {"type": "number", "nullable": true},
  "CreatedDate": {"type": "date", "nullable": false},
  "LastModifiedDate": {"type": "date", "nullable": true}
}
```

#### 4. Trigger Syncs

```bash
POST /api/connectors/sources/{source_id}/sync

{
  "sync_type": "manual",
  "force_full": false
}
```

Response:
```json
{
  "sync_id": 42,
  "status": "running",
  "message": "Sync started in background"
}
```

#### 5. Monitor Sync History

```bash
GET /api/connectors/sources/{source_id}/syncs

# Returns:
{
  "syncs": [
    {
      "id": 42,
      "status": "success",
      "started_at": "2026-08-22T10:30:00Z",
      "completed_at": "2026-08-22T10:35:15Z",
      "records_fetched": 15000,
      "records_inserted": 5000,
      "records_updated": 10000,
      "error_message": null
    }
  ]
}
```

### Sync Strategies

#### Full Sync
Fetches all records every time. Good for:
- Initial import
- Correcting corrupted data
- Small datasets (< 100K records)

#### Incremental Sync
Only fetches changed records since last sync. Good for:
- Large datasets (> 100K records)
- Frequent syncs (hourly, daily)
- Reducing API quota usage

**How it works:**
```
Last sync value: 2026-08-20T15:30:00Z
Query: SELECT * FROM Accounts WHERE LastModifiedDate > '2026-08-20T15:30:00Z'
New last sync value: 2026-08-22T10:35:15Z
```

### Supported Sync Fields

Each connector has common fields for incremental sync:
- **Salesforce**: `LastModifiedDate`, `CreatedDate`, `SystemModstamp`
- **CSV**: Any sortable field (date, id, timestamp)
- **Snowflake**: Any date or numeric field

---

## Part 2: Workflow Automation

### Architecture

```
┌──────────────────────────────────────┐
│     Workflow Definition               │
│                                       │
│  Trigger: When to run this workflow  │
│  - Prediction created                │
│  - Prediction score > threshold      │
│  - Customer in segment               │
│  - Scheduled (cron)                  │
│                                       │
│  Actions: What to do                 │
│  - Email                             │
│  - Slack                             │
│  - Salesforce update                 │
│  - Webhook                           │
│  - Create task                       │
│                                       │
│  Conditions: When to skip action     │
│  - IF prediction_score > 0.8         │
│  - IF customer_value > 10000         │
└────────────────┬─────────────────────┘
                 │
        ┌────────▼────────┐
        │ Workflow Engine │
        │                 │
        │ - Execute flow  │
        │ - Template rend │
        │ - Error handle  │
        │ - Track results │
        └────────┬────────┘
                 │
    ┌────────────┴──────────────┐
    │                           │
┌───▼─────┐  ┌────────┐  ┌─────▼──┐
│  Email  │  │ Slack  │  │SF/Task │
│ Service │  │ API    │  │API     │
└─────────┘  └────────┘  └────────┘
```

### How to Use Workflows

#### 1. Create a Workflow

```bash
POST /api/workflows

{
  "name": "Churn Risk Alert",
  "description": "Alert teams when churn risk detected",
  "trigger_type": "prediction_threshold",
  "trigger_config": {
    "model_type": "churn",
    "field": "churn_probability",
    "threshold": 0.75,
    "comparison": "greater_than"
  },
  "model_type": "churn",
  "segment_filter": {
    "annual_revenue": {"$gt": 50000}
  },
  "actions": [
    {
      "type": "email",
      "sequence": 0,
      "config": {
        "to_field": "{customer_email}",
        "subject_template": "Alert: {customer_name} is at {churn_probability}% churn risk",
        "body_template": "Customer {customer_name} has churn probability of {churn_probability}%. Recommended action: immediate outreach."
      }
    },
    {
      "type": "slack",
      "sequence": 1,
      "config": {
        "channel": "#churn-alerts",
        "message_template": "🚨 {customer_name} churn risk: {churn_probability}%"
      }
    },
    {
      "type": "salesforce",
      "sequence": 2,
      "condition": "churn_probability > 0.8",
      "config": {
        "object": "Account",
        "action": "update",
        "field_mapping": {
          "Churn_Risk__c": "{churn_probability}",
          "Risk_Level__c": "High"
        }
      }
    }
  ]
}
```

#### 2. Manage Workflow Status

```bash
# Draft (test mode)
PUT /api/workflows/{workflow_id}
{
  "status": "draft"
}

# Active (runs on predictions)
PUT /api/workflows/{workflow_id}
{
  "status": "active"
}

# Paused
PUT /api/workflows/{workflow_id}
{
  "status": "paused"
}
```

#### 3. Test Before Going Live

```bash
POST /api/workflows/{workflow_id}/test

{
  "customer_id": "ACME-001",
  "trigger_data": {
    "customer_name": "ACME Corp",
    "customer_email": "contact@acme.com",
    "churn_probability": 0.82,
    "customer_value": 125000
  }
}

# Returns:
{
  "execution_id": 123,
  "status": "success",
  "results": [
    {
      "action_id": 1,
      "status": "success",
      "external_id": "email_1692726600.5"
    },
    {
      "action_id": 2,
      "status": "success",
      "external_id": "slack_1692726602.3"
    },
    {
      "action_id": 3,
      "status": "success",
      "external_id": "sf_ACME-001"
    }
  ]
}
```

#### 4. Monitor Executions

```bash
GET /api/workflows/{workflow_id}/executions

# Returns execution history with status, duration, and result counts
```

```bash
GET /api/workflows/executions/{execution_id}

# Returns detailed action-by-action breakdown
```

### Action Types

#### Email

```json
{
  "type": "email",
  "config": {
    "to_field": "{customer_email}",
    "cc_field": "{manager_email}",
    "subject_template": "Subject with {variables}",
    "body_template": "HTML body with {variables}",
    "attachments": ["invoice.pdf"]
  }
}
```

#### Slack

```json
{
  "type": "slack",
  "config": {
    "channel": "#channel-name",
    "message_template": "Message with {variables}",
    "thread_root": "{message_id}",
    "blocks": []
  }
}
```

#### Salesforce

```json
{
  "type": "salesforce",
  "config": {
    "object": "Account|Contact|Opportunity|Task",
    "action": "create|update",
    "field_mapping": {
      "Field_Name__c": "{variable_name}",
      "Status": "At Risk"
    }
  }
}
```

#### Webhook

```json
{
  "type": "webhook",
  "config": {
    "url": "https://api.example.com/hook",
    "method": "POST",
    "headers": {
      "Authorization": "Bearer token123"
    },
    "payload_template": {
      "customer_id": "{customer_id}",
      "prediction": "{churn_probability}",
      "action": "review_account"
    }
  }
}
```

#### Task Creation

```json
{
  "type": "task",
  "config": {
    "title_template": "[ACTION] Review {customer_name} account",
    "description_template": "Churn risk: {churn_probability}%. Value: ${customer_value}",
    "owner_id": 42,
    "priority": "high",
    "due_date": "+2_days"
  }
}
```

### Template Variables

All templates support variable interpolation using `{variable_name}` syntax:

```
{customer_name}
{customer_email}
{prediction_score}
{prediction_score_percentage}    (0-100 format)
{churn_probability}
{opportunity_amount}
{prediction_reason}
{model_confidence}
```

Access nested fields with dot notation:
```
{account.name}
{account.industry}
{contact.title}
```

### Conditions

Skip actions conditionally:

```json
{
  "type": "email",
  "condition": "churn_probability > 0.8 AND customer_value > 50000",
  "config": {...}
}
```

Supported operators:
- Comparison: `>`, `<`, `>=`, `<=`, `==`, `!=`
- Logical: `AND`, `OR`, `NOT`
- Membership: `IN`, `NOT IN`

### Scheduled Workflows

Run workflows on a schedule (not triggered by predictions):

```bash
POST /api/workflows

{
  "name": "Weekly Team Report",
  "trigger_type": "time_based",
  "trigger_config": {
    "cron": "0 9 * * 1",  # Every Monday at 9am
    "timezone": "America/New_York"
  },
  "actions": [...]
}
```

Cron expression format: `minute hour day month weekday`
- `0 9 * * 1` = Monday 9:00am
- `0 17 * * *` = Daily 5:00pm
- `*/15 * * * *` = Every 15 minutes

---

## Integration: Data → Predictions → Workflows

### Complete Example: Churn Prevention

**1. Setup Data Connectors**

```bash
# Connect Salesforce
POST /api/connectors/connections
{
  "name": "Salesforce Prod",
  "connector_type": "salesforce",
  "config": {...},
  "credentials": {...}
}

# Connect CSV billing data
POST /api/connectors/connections
{
  "name": "Billing Data",
  "connector_type": "csv",
  "config": {"file_path": "s3://bucket/billing.csv"},
  "credentials": {...}
}

# Create data sources
POST /api/connectors/sources
{
  "connection_id": 1,
  "name": "Accounts",
  "source_path": "Account"
}

POST /api/connectors/sources
{
  "connection_id": 2,
  "name": "Monthly Billing",
  "source_path": "billing.csv"
}
```

**2. Schedule Syncs**

```bash
# Daily Salesforce sync
POST /api/connectors/sources/1/sync
{
  "sync_type": "manual"
}

# Weekly billing sync
POST /api/connectors/sources/2/sync
{
  "sync_type": "manual"
}
```

**3. Train Churn Model**

Model trains on:
- Customer data from Salesforce (industry, size, territory)
- Billing data (MRR, payment history)
- Engagement data (usage, support tickets)
- Historical churned customers

**4. Create Churn Workflows**

```bash
POST /api/workflows
{
  "name": "Churn Risk - Executive Alert",
  "trigger_type": "prediction_threshold",
  "trigger_config": {
    "model_type": "churn",
    "threshold": 0.75
  },
  "actions": [
    {
      "type": "email",
      "config": {
        "to_field": "vp-sales@company.com",
        "subject_template": "🚨 High churn risk: {customer_name}",
        "body_template": "..."
      }
    },
    {
      "type": "salesforce",
      "config": {
        "object": "Account",
        "action": "update",
        "field_mapping": {"Risk_Level__c": "Critical"}
      }
    },
    {
      "type": "task",
      "config": {
        "title_template": "Review account: {customer_name}",
        "owner_id": 42
      }
    }
  ]
}
```

**5. Monitor Results**

Track workflow executions and outcomes:
- How many workflows triggered?
- What % resulted in retention?
- What was ROI of outreach?

---

## Best Practices

### Data Connectors

1. **Use Incremental Sync** for production data (reduces API usage, faster syncs)
2. **Test Connections** before adding to production workflows
3. **Monitor Sync History** for failures and investigate quickly
4. **Keep Primary Keys Consistent** across syncs
5. **Use Appropriate Refresh Intervals**:
   - CRM data: Daily or more frequent
   - Billing data: Daily or weekly
   - Data warehouse: Nightly
   - CSV uploads: Manual as needed

### Workflows

1. **Start in Draft Mode** - Test thoroughly before going live
2. **Use Conditions** to avoid spamming customers
3. **Monitor First Execution** - Check logs for unexpected behavior
4. **Combine Actions Thoughtfully** - Email + Slack + Task = maximum visibility
5. **Track Outcomes** - Did the workflow achieve its goal?
6. **Version Control** - Document why workflows were changed
7. **Archive Old Workflows** - Don't delete, just archive for history

### Common Patterns

**Pattern 1: Alert + Create Task**
- Action 1: Send Slack alert
- Action 2: Create task for follow-up
- Condition: Only if score > 0.8 AND manual_review_required

**Pattern 2: Email + Salesforce Update**
- Action 1: Send customer retention email
- Action 2: Update Account record with engagement flag
- Condition: Only if customer has history of responding

**Pattern 3: Multi-stakeholder Alert**
- Action 1: Email CSM
- Action 2: Slack to exec channel
- Action 3: Create escalation task
- Condition: Only if customer value > $100K

**Pattern 4: Self-healing Workflow**
- Action 1: Automatically update Salesforce field
- Action 2: Send SMS if contact_method=sms
- Action 3: Create task only if no automatic contact method

---

## Troubleshooting

### Sync Failures

**Problem**: "Connection failed"
- Check credentials are valid
- Verify network access to source
- Check API rate limits
- Review connector logs

**Problem**: "Schema changed"
- Re-sync source schema
- Update field mappings
- Check if connector supports new fields

### Workflow Issues

**Problem**: "Action didn't execute"
- Check workflow status (must be ACTIVE)
- Verify conditions are not blocking execution
- Check action configuration is valid
- Review execution logs

**Problem**: "Template variables not replaced"
- Ensure variable names match exactly (case-sensitive)
- Use dot notation for nested fields: `{account.name}`
- Check that data contains the field

**Problem**: "Salesforce update failed"
- Verify API token is valid
- Check Field_Mapping field names are correct
- Ensure user has permission to update those fields
- Check field types match values (number, date, text)

---

## Next Steps

1. **Connect your data sources** - Start with Salesforce or CSV
2. **Set up first sync** - Test incremental sync strategy
3. **Monitor data quality** - Check sync logs for issues
4. **Create test workflow** - Build simple workflow in DRAFT mode
5. **Test with sample data** - Use /test endpoint before going live
6. **Activate workflow** - Move to ACTIVE status
7. **Track outcomes** - Monitor execution history and adjust

---

## API Reference

### Connectors
- `POST /api/connectors/connections` - Create connection
- `GET /api/connectors/connections` - List connections
- `POST /api/connectors/connections/{id}/test` - Test connection
- `POST /api/connectors/sources` - Create data source
- `GET /api/connectors/sources` - List data sources
- `POST /api/connectors/sources/{id}/sync` - Trigger sync
- `GET /api/connectors/sources/{id}/syncs` - Sync history

### Workflows
- `POST /api/workflows` - Create workflow
- `GET /api/workflows` - List workflows
- `PUT /api/workflows/{id}` - Update workflow
- `POST /api/workflows/{id}/test` - Test workflow
- `POST /api/workflows/{id}/execute` - Execute workflow
- `GET /api/workflows/{id}/executions` - Execution history
- `GET /api/workflows/executions/{id}` - Execution details
