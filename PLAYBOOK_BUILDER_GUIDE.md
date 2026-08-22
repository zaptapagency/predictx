# Playbook Builder Guide

## Overview

The Playbook Builder enables non-technical users to create sophisticated, multi-step workflows without code. Playbooks are reusable, templated workflows that execute actions based on triggers.

## Key Concepts

### Playbook
A complete workflow that:
- Triggers on specific events (prediction, segment, time, manual)
- Executes a sequence of actions
- Can be reused across customers
- Has performance metrics tracking

### Action
Individual step in a playbook. Types:
- **Email**: Send templated emails
- **Slack**: Post messages to Slack
- **Salesforce**: Create/update records
- **Webhook**: Call external APIs
- **Task**: Create follow-up tasks

### Trigger
When does the playbook run?
- **Prediction Threshold**: When model score exceeds threshold
- **Segment Match**: When customer enters segment
- **Time Based**: On a schedule (daily, weekly, etc)
- **Manual**: User triggers explicitly

### Template
Pre-built playbooks for common scenarios. Easily customizable.

---

## Getting Started

### Step 1: Navigate to Playbook Builder

Click "🎨 Playbooks" in main navigation or go to `/playbooks`.

### Step 2: Choose Your Approach

You have 3 options:

**Option A: Use a Template** (Recommended for beginners)
```
1. Click "📚 Templates" tab
2. Browse pre-built playbooks
3. Click "Use Template"
4. Customize as needed
5. Save
```

**Option B: Create from Scratch**
```
1. Click "+ New Playbook"
2. Select "Blank Playbook"
3. Add actions one by one
4. Configure each action
5. Save
```

**Option C: Duplicate Existing Playbook**
```
1. Find playbook in gallery
2. Click "Duplicate"
3. Customize
4. Save as new version
```

---

## Template Gallery

### Pre-Built Templates

#### 🚨 Churn Prevention
**Trigger**: When customer churn risk score > 75%
**Actions**:
1. Send email to customer (personalized retention offer)
2. Notify team in Slack (#churn-alerts)
3. Create escalation task for CSM

**Best for**: Retention-focused orgs

#### 📈 Upsell Opportunity
**Trigger**: When customer shows expansion signals
**Actions**:
1. Email account owner with opportunity brief
2. Create Salesforce Opportunity record
3. Schedule call with sales rep

**Best for**: Growth-focused orgs

#### 🎯 Onboarding Success
**Trigger**: New customer activation
**Actions**:
1. Send welcome email with resources
2. Create onboarding task for CSM
3. Add to Slack onboarding channel

**Best for**: New customer experience

#### 📅 Renewal Preparation
**Trigger**: 60 days before renewal date
**Actions**:
1. Send renewal reminder email
2. Update Salesforce with renewal status
3. Create renewal task for renewal manager

**Best for**: Subscription businesses

---

## Building Playbooks

### Creating a New Playbook

#### Step 1: Define Basic Info
```
Name: "High-Value Churn Alert"
Description: "Alert team immediately when high-value 
              customers show churn risk"
Trigger Type: Prediction Threshold
Category: Retention
```

#### Step 2: Configure Trigger
```
Trigger Type: Prediction Threshold
Model: Churn Risk
Threshold: 0.75 (75%)
Comparison: Greater than
Additional Filter: Customer MRR > $10,000
```

#### Step 3: Add Actions

**Action 1: Email Alert**
```
Type: Email
To: {customer_success_email}
Subject: "URGENT: {customer_name} at high churn risk"
Body: "Customer churn risk: {churn_score}%
       MRR at risk: ${customer_mrr}
       Recommended action: {recommended_action}"
Condition: None (always send)
```

**Action 2: Slack Notification**
```
Type: Slack
Channel: #churn-alerts
Message: "🚨 {customer_name} (MRR: ${customer_mrr}) 
          showing {churn_score}% churn risk"
Condition: None
```

**Action 3: Create Task**
```
Type: Task
Title: "URGENT: Review {customer_name} account"
Description: "Customer at {churn_score}% churn risk.
              Last login: {days_since_last_login} days ago.
              Recent activity: {recent_activity}"
Owner: Account Manager
Priority: High
Condition: churn_score > 0.85
```

**Action 4: Update Salesforce** (Conditional)
```
Type: Salesforce
Object: Account
Action: Update
Fields:
  - Churn_Risk__c = "High"
  - Risk_Score__c = {churn_score}
  - Last_Risk_Assessment__c = TODAY()
Condition: churn_score > 0.75
```

#### Step 4: Review & Test

- Review all actions
- Click "Test Playbook"
- Select sample customer
- Verify all actions would trigger
- Check output

#### Step 5: Deploy

- Change status from "Draft" to "Active"
- Playbook now runs automatically
- Monitor performance in Performance tab

---

## Action Types

### Email Action

**Use for**: Reaching customers directly

**Configuration**:
```
To Field: {customer_email}
CC Field: {account_owner_email} (optional)
Subject Template: Dynamic subject with variables
Body Template: HTML or plain text
Attachments: List of files to attach
```

**Available Variables**:
- `{customer_name}` - Customer company name
- `{customer_email}` - Customer primary email
- `{prediction_score}` - Model score (0-1)
- `{risk_level}` - Risk categorization
- `{recommended_action}` - Action from model
- Custom fields from your data

**Example Subject**:
```
"⏰ Your renewal is coming: {customer_name}"
"🎉 Exclusive offer for {customer_name}"
"⚠️ Action needed: {customer_name}"
```

**Best Practices**:
- Keep subject line under 50 characters
- Use emoji for quick scanning
- Personalize with customer name
- Include clear CTA in body

### Slack Action

**Use for**: Team notifications and alerts

**Configuration**:
```
Channel: #channel-name
Message Template: Plain text or Slack markdown
Thread Root: Optional (replies to specific message)
Blocks: Advanced formatting (optional)
```

**Slack Markdown Supported**:
```
*bold text*
_italic text_
~strikethrough~
`code`
[Link](https://example.com)
:emoji: names
```

**Example Message**:
```
🚨 *Churn Alert*
Customer: {customer_name}
Churn Risk: {churn_score}%
MRR at Risk: ${customer_mrr}
Action: {recommended_action}
```

**Best Practices**:
- Use channel names instead of @mentions
- Use emoji for quick visual scanning
- Include link to dashboard/record
- Keep message concise

### Salesforce Action

**Use for**: Updating CRM records automatically

**Configuration**:
```
Object: Account|Contact|Opportunity|Task|Custom
Action: Create|Update
Field Mapping: Map template variables to fields
```

**Examples**:

Create Opportunity:
```
Object: Opportunity
Action: Create
Fields:
  AccountId: {customer_id}
  Name: "Expansion - {customer_name}"
  Amount: {expansion_value}
  StageName: "Prospecting"
  CloseDate: 30 days from today
```

Update Account:
```
Object: Account
Action: Update
Fields:
  Churn_Risk__c: "High"
  Risk_Score__c: {churn_score}
  Last_Assessment__c: TODAY()
  Risk_Owner__c: {assigned_csm_id}
```

**Best Practices**:
- Map only required fields
- Use picklist values exactly
- Include IDs for lookups
- Test on staging first

### Webhook Action

**Use for**: Integrating with external systems

**Configuration**:
```
URL: https://api.example.com/webhook
Method: POST|PUT|PATCH
Headers: Authorization, Content-Type, etc
Payload Template: JSON with variables
```

**Example - Hubspot**:
```
URL: https://api.hubapi.com/crm/v3/objects/companies/{customer_id}
Method: PATCH
Headers:
  Authorization: Bearer {hubspot_token}
  Content-Type: application/json
Payload:
{
  "properties": {
    "churn_risk": "{churn_score}",
    "last_scored": "$(TODAY())",
    "recommended_action": "{recommended_action}"
  }
}
```

**Best Practices**:
- Test webhook first
- Include proper authentication
- Handle errors gracefully
- Log requests for debugging

### Task Action

**Use for**: Creating follow-up items

**Configuration**:
```
Title Template: Task title with variables
Description Template: Detailed notes
Owner ID: Who should do the task
Priority: Low|Medium|High
Due Date: Relative (e.g., +3 days) or absolute
```

**Example**:
```
Title: "[URGENT] Review {customer_name} - Churn Risk"
Description: "Customer {customer_name} showing high churn indicators:
- Churn score: {churn_score}%
- Last login: {days_since_last_login} days ago
- MRR: ${customer_mrr}
Recommended action: {recommended_action}

Please review and follow up immediately."
Owner: {account_manager_id}
Priority: High
Due Date: Today
```

**Best Practices**:
- Include relevant context in description
- Assign to right person
- Set realistic due dates
- Use clear, actionable titles

---

## Conditional Actions

Execute actions only when conditions are met.

### Condition Syntax

```
condition: "score > 0.8 AND customer_mrr > 50000"
```

**Operators**:
- `>` Greater than
- `<` Less than
- `>=` Greater or equal
- `<=` Less or equal
- `==` Equal
- `!=` Not equal
- `AND` Logical AND
- `OR` Logical OR
- `NOT` Logical NOT

### Examples

Only email if high value:
```
condition: "customer_mrr > 100000"
```

Only create Salesforce task if really high risk:
```
condition: "churn_score > 0.85 AND model_confidence > 0.9"
```

Skip if already contacted recently:
```
condition: "days_since_last_contact > 14"
```

---

## Variables & Templating

### Available Variables

**Customer Data**:
- `{customer_id}` - Unique identifier
- `{customer_name}` - Company name
- `{customer_email}` - Primary email
- `{customer_phone}` - Phone number
- `{customer_mrr}` - Monthly revenue
- `{customer_industry}` - Industry

**Prediction Data**:
- `{prediction_score}` - Model score (0-1)
- `{prediction_score_pct}` - Score as percent (0-100)
- `{risk_level}` - low/medium/high/critical
- `{confidence}` - Model confidence (0-1)
- `{recommended_action}` - Suggested next step
- `{contributing_factors}` - Top 3 factors (JSON)

**Metrics**:
- `{days_since_last_login}` - Activity recency
- `{monthly_active_users}` - Usage metric
- `{mrr_change_pct}` - Revenue trend
- `{usage_change_pct}` - Usage trend

**System**:
- `{today}` - Today's date
- `{tomorrow}` - Tomorrow's date
- `{next_week}` - Date one week from now

### Using Variables

In Email Subject:
```
"Alert: {customer_name} at {prediction_score_pct}% risk"
```

In Slack Message:
```
"{customer_name} (${customer_mrr}) at {risk_level} risk"
```

In Salesforce Field:
```
Amount: {expansion_value}
```

In Conditions:
```
condition: "{prediction_score} > 0.75 AND {customer_mrr} > 50000"
```

---

## Performance Monitoring

### Key Metrics

**Execution Count**
- Total times playbook has run
- Tracks adoption

**Success Rate**
- % of executions that completed successfully
- Target: 95%+

**Action Breakdown**
- Success/failure by action type
- Identifies problematic steps

### Troubleshooting Failed Executions

**Email Failed**
- Check email address validity
- Verify email service is working
- Review email logs

**Slack Failed**
- Check channel exists and bot has access
- Verify Slack token is valid
- Check channel name formatting

**Salesforce Failed**
- Verify field names and values match picklists
- Check user has permissions
- Confirm required fields are populated

**Webhook Failed**
- Check endpoint is reachable
- Verify authentication token
- Check payload format
- Review webhook logs

---

## Best Practices

### Design
1. **Start simple** - Begin with 2-3 actions
2. **Use templates** - Save time with pre-built workflows
3. **Name clearly** - Use descriptive names
4. **Document** - Add clear descriptions
5. **Test first** - Always test before activating

### Implementation
1. **Monitor early** - Watch first runs closely
2. **Adjust timing** - Stagger actions if needed
3. **Use conditions** - Don't spam customers
4. **Track metrics** - Monitor success rates
5. **Iterate** - Refine based on performance

### Maintenance
1. **Archive old** - Don't delete, archive unused
2. **Update templates** - Refresh messaging periodically
3. **Review performance** - Check metrics monthly
4. **Collect feedback** - Ask teams for input
5. **Version control** - Document changes

### Avoiding Common Mistakes

❌ **Don't**:
- Use too many actions (5+)
- Send too frequently
- Forget to test
- Ignore success metrics
- Send to unverified emails

✅ **Do**:
- Keep playbooks focused
- Space out actions
- Test with sample data
- Monitor performance
- Verify email addresses

---

## Examples

### Example 1: Immediate Churn Alert

```
Name: "Emergency Churn Intervention"
Trigger: Churn score > 0.85
Actions:
1. Email CEO/COO (immediate)
2. Slack #executive-alerts (immediate)
3. SMS to account owner (immediate, conditional)
4. Create escalation task (immediate)
5. Update Salesforce (immediate)

Total actions: 5
Expected time: 2-3 minutes
Best for: High-value customers only
```

### Example 2: Gentle Upsell

```
Name: "Smart Expansion Opportunity"
Trigger: Expansion score > 0.7 AND account age > 6 months
Actions:
1. Email account owner with opportunity details
2. Create Salesforce opportunity
3. Add to Slack #growth channel
4. Assign to sales rep task

Conditions:
- Only for customers with clean payment history
- Only if they've been customer 6+ months
- Only if expansion value > $5000
```

### Example 3: Renewal Workflow

```
Name: "Proactive Renewal Campaign"

Three playbooks triggered at different times:

1. 90 days before renewal:
   - Email CFO with renewal summary
   - Create task: Start renewal discussions

2. 60 days before renewal:
   - Email CSM with renewal strategy
   - Update SF with renewal status
   - Create renewal opportunity

3. 30 days before renewal:
   - Send contract to customer
   - Slack reminder to renewal manager
   - Create task: Follow up if not signed
```

---

## API Reference

### Get All Playbooks
```bash
GET /api/playbooks
```

### Create Playbook
```bash
POST /api/playbooks

{
  "name": "My Playbook",
  "description": "Description",
  "category": "retention",
  "trigger_type": "prediction_threshold",
  "trigger_config": {
    "model_type": "churn",
    "threshold": 0.75
  },
  "actions": [
    {
      "type": "email",
      "sequence": 0,
      "config": {...}
    }
  ]
}
```

### Get Playbook Details
```bash
GET /api/playbooks/{id}
```

### Update Playbook
```bash
PUT /api/playbooks/{id}

{
  "name": "Updated name",
  "actions": [...]
}
```

### Activate/Deactivate
```bash
PUT /api/playbooks/{id}/status

{
  "status": "active" | "draft" | "archived"
}
```

### Get Performance
```bash
GET /api/playbooks/{id}/performance
```

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `1` | Playbooks tab |
| `2` | Templates tab |
| `3` | Builder tab |
| `4` | Performance tab |
| `N` | New playbook |
| `Esc` | Close modal |

---

## FAQ

**Q: Can I edit active playbooks?**
A: Yes, but changes apply to new executions only.

**Q: How many actions per playbook?**
A: Up to 10 recommended. More = harder to manage.

**Q: Can actions run in parallel?**
A: No, they run sequentially. Use conditions for branching.

**Q: How often can playbooks run?**
A: As often as triggers fire. Minimum 5 minute gap.

**Q: Can I undo a playbook execution?**
A: No, but you can manually fix records.

**Q: Do templates auto-update?**
A: No, templates are starting points only.

**Q: Can other teams use my playbooks?**
A: Yes, mark as public in sharing settings.

**Q: How do I track playbook impact?**
A: Use Performance tab and Salesforce reports.

**Q: What if action fails?**
A: Playbook pauses. Check logs and retry.

**Q: Can I pause a playbook?**
A: Yes, change status to "draft" or "paused".

---

## Support

For help:
1. Check this guide's examples
2. Try a template first
3. Test thoroughly before activating
4. Monitor performance metrics
5. Iterate based on results

Success metrics to track:
- % of executions that complete
- Customer response rates
- Revenue impact
- Team adoption
