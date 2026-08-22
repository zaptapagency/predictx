# Model Management Dashboard Integration Guide

## Quick Start

The Model Management Dashboard is now ready to integrate into your ForecastX application.

## File Locations

### Frontend Component
```
frontend/src/components/ModelManagementDashboard.tsx
frontend/src/components/model-management-dashboard.css
```

### Documentation
```
MODEL_MANAGEMENT_GUIDE.md
```

## Integration Steps

### 1. Add Route

In your main app router (e.g., `app.tsx` or `routes.tsx`):

```typescript
import { ModelManagementDashboard } from './components/ModelManagementDashboard';

// Add to routes
<Route path="/models" element={<ModelManagementDashboard />} />
<Route path="/models/:id" element={<ModelManagementDashboard />} />
```

### 2. Add Navigation Link

In your main navigation menu:

```typescript
<nav>
  <Link to="/">Home</Link>
  <Link to="/dashboard">Dashboard</Link>
  <Link to="/connectors">Data Sources</Link>
  <Link to="/workflows">Workflows</Link>
  <Link to="/models">🤖 Models</Link>  {/* Add this */}
</nav>
```

### 3. Verify API Endpoints

The dashboard expects these backend API endpoints to be available:

```
GET    /api/predictions/models
GET    /api/predictions/models/{id}
GET    /api/predictions/models/{id}/training-runs
POST   /api/predictions/models/train
GET    /api/predictions/predictions
GET    /api/predictions/predictions/{id}
POST   /api/predictions/predict
POST   /api/predictions/batch-predict
POST   /api/predictions/predictions/{id}/outcome
POST   /api/predictions/predictions/{id}/feedback
GET    /api/predictions/features
GET    /api/predictions/customer/{id}/features
```

All these are already implemented in `app/api/predictions_api.py`.

### 4. Test Integration

1. Start your backend server
2. Start your frontend dev server
3. Navigate to `/models` route
4. You should see:
   - Empty state (no models yet) or
   - List of existing models (if any exist)
   - "+ Train New Model" button

### 5. Train Your First Model

```bash
POST /api/predictions/models/train

{
  "name": "Churn Risk Model v1",
  "model_type": "churn",
  "algorithm": "xgboost",
  "training_start": "2024-01-01T00:00:00Z",
  "training_end": "2026-08-15T00:00:00Z"
}
```

The dashboard will:
1. Show model with "training" status
2. Poll for updates every 2 seconds
3. Show "active" status when complete
4. Display performance metrics

---

## Dashboard Flow

```
User visits /models
         ↓
Fetch models from API
         ↓
Display models list
         ↓
User clicks model
         ↓
Fetch model details + predictions + training runs
         ↓
Display tabs:
  • Details (performance metrics)
  • Predictions (recent scores)
  • Training (history)
  • Features (inputs used)
         ↓
User trains new model
         ↓
Show training in progress
         ↓
Update when complete
```

---

## Component Structure

```
ModelManagementDashboard (Main component)
├── ModelsSection (Tab 1)
│   ├── Model cards grid
│   ├── Filter by type
│   └── Train button
├── DetailsSection (Tab 2)
│   ├── Performance metrics card
│   ├── Training data card
│   ├── Model health card
│   └── Feature importance chart
├── PredictionsSection (Tab 3)
│   └── Predictions table
├── TrainingSection (Tab 4)
│   └── Training runs cards
├── FeaturesSection (Tab 5)
│   └── Features table
└── TrainModelModal
    └── Form to train new model
```

---

## Customization

### Change Colors

Edit `model-management-dashboard.css`:

```css
/* Current primary color */
background: linear-gradient(135deg, #3b82f6, #2563eb);

/* Change to your brand color */
background: linear-gradient(135deg, #8b5cf6, #7c3aed);  /* Purple */
```

### Add More Metrics

In `DetailsSection`, add new metric rows:

```typescript
<div className="mmd-metric-row">
  <span className="mmd-metric-name">Custom Metric</span>
  <span className="mmd-metric-val">{customValue}%</span>
</div>
```

### Extend Feature Engineering

In backend `feature_engineer.py`:

```python
def _compute_custom_features(self, raw_data: Dict) -> Dict:
    features = {}
    
    # Add your custom features
    if "custom_field" in raw_data:
        features["custom_metric"] = raw_data["custom_field"] * 100
    
    return features
```

### Add New Model Types

In `prediction_models.py`:

```python
class ModelType(str, enum.Enum):
    CHURN = "churn"
    OPPORTUNITY = "opportunity"
    EXPANSION = "expansion"
    HEALTH = "health"
    NPS = "nps"  # Add new type
    CUSTOM = "custom"  # Add custom type
```

---

## Dashboard Features Checklist

### Models Tab
- [x] Display all models
- [x] Show status badges
- [x] Display accuracy, F1, AUC metrics
- [x] Show feature count
- [x] Display last training date
- [x] Highlight drifted models
- [x] Filter by model type
- [x] Select model to view details
- [x] Train new model button

### Details Tab
- [x] Performance metrics (accuracy, precision, recall, F1, AUC)
- [x] Training data info (period, records, date)
- [x] Model health (status, drift flag, features, algorithm)
- [x] Top features by importance

### Predictions Tab
- [x] List recent predictions
- [x] Show customer ID
- [x] Display prediction score
- [x] Color-coded risk level
- [x] Show confidence
- [x] Display recommended action
- [x] Track outcome status
- [x] Show prediction timestamp

### Training Tab
- [x] List training runs
- [x] Show status (success/failed)
- [x] Display duration
- [x] Show records used
- [x] Display metrics (accuracy, precision, recall, F1)
- [x] Show error messages if failed

### Features Tab
- [x] List all features
- [x] Show feature type
- [x] Display source
- [x] Show statistics (mean, median, std)
- [x] Sortable/filterable

### Train Modal
- [x] Model name input
- [x] Model type selector
- [x] Algorithm selector
- [x] Training start date
- [x] Training end date
- [x] Submit button
- [x] Validation

---

## API Response Formats

### Models List
```json
{
  "models": [
    {
      "id": 1,
      "name": "Churn Model v1",
      "model_type": "churn",
      "status": "active",
      "algorithm": "xgboost",
      "accuracy": 0.78,
      "f1_score": 0.76,
      "auc_roc": 0.85,
      "features_count": 20,
      "training_date": "2026-08-20T10:30:00Z",
      "is_drifted": false,
      "created_at": "2026-08-15T00:00:00Z"
    }
  ]
}
```

### Model Details
```json
{
  "id": 1,
  "name": "Churn Model v1",
  "model_type": "churn",
  "status": "active",
  "algorithm": "xgboost",
  "features": ["mrr", "account_age_days", ...],
  "feature_importance": {
    "mrr": 0.15,
    "days_since_last_login": 0.12,
    ...
  },
  "performance": {
    "accuracy": 0.78,
    "precision": 0.75,
    "recall": 0.81,
    "f1_score": 0.78,
    "auc_roc": 0.85
  },
  "training": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2026-06-30T00:00:00Z",
    "records": 2543,
    "date": "2026-08-20T10:30:00Z"
  },
  "health": {
    "is_drifted": false,
    "last_checked": "2026-08-22T10:00:00Z"
  }
}
```

### Predictions List
```json
{
  "predictions": [
    {
      "id": 42,
      "customer_id": "ACME-001",
      "score": 0.82,
      "confidence": 0.91,
      "risk_level": "high",
      "recommended_action": "immediate_outreach",
      "predicted_at": "2026-08-22T10:30:00Z",
      "has_outcome": true
    }
  ]
}
```

### Training Runs
```json
{
  "runs": [
    {
      "id": 42,
      "status": "success",
      "started": "2026-08-20T10:00:00Z",
      "completed": "2026-08-20T10:02:25Z",
      "duration_seconds": 145,
      "records": 2543,
      "metrics": {
        "accuracy": 0.7843,
        "precision": 0.7689,
        "recall": 0.8023,
        "f1": 0.7852
      },
      "error": null
    }
  ]
}
```

---

## Performance Optimization

### Lazy Loading
The dashboard only fetches model details when selected:

```typescript
useEffect(() => {
  if (selectedModel) {
    fetchPredictions(selectedModel.id);
    fetchTrainingRuns(selectedModel.id);
  }
}, [selectedModel]);
```

### Pagination
Predictions are limited to 50 most recent:

```typescript
GET /api/predictions/predictions?model_id=1&limit=50
```

### Caching
Consider adding SWR or React Query:

```typescript
import useSWR from 'swr';

const { data: models } = useSWR('/api/predictions/models', fetcher);
```

---

## Error Handling

The dashboard handles:
- API failures gracefully
- Network timeouts
- Missing data
- Invalid responses

Add error states:

```typescript
if (error) {
  return <div className="mmd-error">Failed to load: {error.message}</div>;
}
```

---

## Responsive Design

The dashboard is fully responsive:

**Desktop (1200px+)**
- 3-column grid for model cards
- Full tables with all columns
- Side-by-side details

**Tablet (768px - 1199px)**
- 2-column grid
- Stacked sections
- Scrollable tables

**Mobile (< 768px)**
- 1-column grid
- Single column layout
- Vertical stacking
- Touch-friendly buttons

---

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

No IE11 support (uses CSS Grid, modern JavaScript).

---

## Accessibility

Features:
- Semantic HTML
- ARIA labels on interactive elements
- Keyboard navigation (Tab through elements)
- Color contrast meets WCAG AA
- Screen reader friendly

---

## Testing

### Unit Tests
Test individual sections:

```typescript
describe('ModelsSection', () => {
  it('renders model cards', () => {
    const models = [...];
    render(<ModelsSection models={models} />);
    expect(screen.getAllByRole('button')).toHaveLength(models.length);
  });
});
```

### Integration Tests
Test full dashboard flow:

```typescript
describe('ModelManagementDashboard', () => {
  it('trains and monitors model', async () => {
    render(<ModelManagementDashboard />);
    
    // Click train button
    fireEvent.click(screen.getByText('Train New Model'));
    
    // Fill form
    fireEvent.change(screen.getByLabelText('Model Name'), {
      target: { value: 'Test Model' }
    });
    
    // Submit
    fireEvent.click(screen.getByText('Start Training'));
    
    // Wait for model to appear
    await screen.findByText('Test Model');
  });
});
```

### E2E Tests
With Cypress/Playwright:

```typescript
describe('Model Management E2E', () => {
  it('complete workflow', () => {
    cy.visit('/models');
    cy.contains('Train New Model').click();
    cy.get('input[type="text"]').type('My Model');
    cy.get('select').select('churn');
    cy.contains('Start Training').click();
    cy.contains('My Model').should('be.visible');
  });
});
```

---

## Monitoring

### Key Metrics
- Model training success rate
- Prediction latency
- Dashboard load time
- API error rate
- Feature drift frequency

### Alerts to Set
- Model training failed
- Model accuracy dropped > 5%
- Prediction latency > 500ms
- API errors > 1% per minute
- Drift detected on active model

---

## Common Issues & Solutions

### Models Tab Shows "No Models"
**Cause**: Database is empty or API error

**Solution**:
1. Check backend is running: `GET /api/predictions/models`
2. Train a new model
3. Check browser console for errors

### Details Tab Shows Partial Data
**Cause**: API response incomplete

**Solution**:
1. Verify model has completed training
2. Check API is returning all fields
3. Reload page

### Predictions Table is Empty
**Cause**: No predictions generated yet

**Solution**:
1. Make predictions: `POST /api/predictions/batch-predict`
2. Wait for predictions to complete
3. Refresh predictions tab

### Training Not Starting
**Cause**: Form validation or API error

**Solution**:
1. Fill all required fields
2. Check dates are valid (start < end)
3. Check backend logs for errors
4. Verify API endpoint exists

---

## Future Enhancements

Potential additions:
- [ ] Export predictions to CSV
- [ ] A/B testing framework
- [ ] Model versioning/comparison
- [ ] Automated retraining scheduler
- [ ] Performance benchmarks
- [ ] Custom alerts & notifications
- [ ] Prediction explanations (LIME/SHAP)
- [ ] Model audit trail
- [ ] Team collaboration features
- [ ] Prediction API rate limiting

---

## Support

For issues or questions:
1. Check `MODEL_MANAGEMENT_GUIDE.md` for usage details
2. Review `PREDICTION_ENGINE_GUIDE.md` for API reference
3. Check browser console for errors
4. Review backend logs: `tail -f logs/prediction_engine.log`
5. Verify all API endpoints are working

---

## Summary

The Model Management Dashboard provides complete visibility and control over your ML models. It enables:

✅ Training and managing multiple models
✅ Monitoring performance and detecting drift
✅ Reviewing predictions and outcomes
✅ Understanding feature importance
✅ Tracking training history

Integrated with the prediction engine, data connectors, and workflows, it completes the ForecastX platform for end-to-end predictive analytics.
