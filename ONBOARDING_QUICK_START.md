# Onboarding Quick Start Guide

## What Was Built

✅ **Complete onboarding flow** taking users from signup to first playbook in 5 minutes
✅ **Backend API** with 9 endpoints for progress tracking and analytics
✅ **Frontend service** (`onboardingService.ts`) handling all backend communication
✅ **Updated components** with real API integration
✅ **Database models** for progress and event tracking

---

## Integration Checklist (Fastest Path)

### Step 1: Register API Routes
In `backend/app/main.py`, add:

```python
from app.api import onboarding

app.include_router(onboarding.router)
```

### Step 2: Create Database Migration
```bash
cd backend
alembic revision --autogenerate -m "Add onboarding tables"
alembic upgrade head
```

### Step 3: Configure Salesforce OAuth
In `.env`:
```
SALESFORCE_CLIENT_ID=your_client_id
SALESFORCE_CLIENT_SECRET=your_client_secret
SALESFORCE_REDIRECT_URI=https://your-domain.com/auth/salesforce/callback
```

### Step 4: Add Salesforce Callback Handler
In `backend/app/api/auth.py`, add:

```python
from fastapi import APIRouter
from app.services.salesforce_service import exchange_salesforce_token
from app.api.onboarding import mark_salesforce_connected

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/salesforce/callback")
async def salesforce_callback(
    code: str,
    state: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Handle Salesforce OAuth callback"""
    
    # Exchange code for token
    token_data = exchange_salesforce_token(code)
    
    # Save connection
    connection = DataConnection(
        organization_id=current_user.organization_id,
        name="Salesforce",
        connector_type="salesforce",
        config={"instance_url": token_data['instance_url']},
        credentials={"access_token": token_data['access_token']},
        created_by_id=current_user.id
    )
    db.add(connection)
    db.commit()
    
    # Mark onboarding milestone
    await mark_salesforce_connected(current_user, db)
    
    # Redirect back to onboarding
    return RedirectResponse(url="/onboarding?step=template")
```

### Step 5: Wire Frontend Component
In `frontend/src/App.tsx`:

```typescript
import { OnboardingFlow } from './components/OnboardingFlow';

function App() {
  const [user, setUser] = useState(null);
  const [onboardingComplete, setOnboardingComplete] = useState(false);

  useEffect(() => {
    // Check onboarding status
    onboardingService.shouldShowOnboarding().then(show => {
      setOnboardingComplete(!show);
    });
  }, []);

  if (!onboardingComplete) {
    return <OnboardingFlow />;
  }

  return <MainDashboard />;
}
```

### Step 6: Test End-to-End
1. Create test user
2. Start onboarding flow
3. Complete each step
4. Verify data in database:
   ```sql
   SELECT * FROM onboarding_progress WHERE user_id = ?;
   SELECT * FROM onboarding_events WHERE user_id = ?;
   ```

---

## File Structure

```
frontend/
  src/
    components/
      OnboardingFlow.tsx           (550+ lines, now with API calls)
      onboarding-flow.css          (800+ lines, styling)
    services/
      onboardingService.ts         (200+ lines, API client)

backend/
  app/
    api/
      onboarding.py               (380+ lines, endpoints)
    db/
      onboarding_models.py         (95+ lines, database schemas)
```

---

## API Endpoints Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/onboarding/progress` | Get user's progress |
| POST | `/api/onboarding/steps/{id}/complete` | Mark step complete |
| POST | `/api/onboarding/goal` | Save goal selection |
| POST | `/api/onboarding/template` | Save template selection |
| POST | `/api/onboarding/salesforce/connected` | Track Salesforce connection |
| POST | `/api/onboarding/first-playbook-created` | Track playbook creation |
| POST | `/api/onboarding/first-prediction-seen` | Track prediction view |
| GET | `/api/onboarding/events` | Get analytics events |
| GET | `/api/onboarding/stats` | Get org-wide stats |

---

## Testing

### Unit Test Example
```typescript
test('complete onboarding flow', async () => {
  render(<OnboardingFlow />);
  
  // Step 1: Welcome
  fireEvent.click(screen.getByText("Let's Get Started"));
  await waitFor(() => expect(screen.getByText("What's your goal?")).toBeInTheDocument());
  
  // Step 2: Goal Selection
  fireEvent.click(screen.getByText("Churn Prevention"));
  fireEvent.click(screen.getByText("Continue →"));
  
  // Step 3: Salesforce Connection
  // (Mock OAuth flow)
  
  // Step 4: Template Selection
  fireEvent.click(screen.getByText("Churn Prevention"));
  fireEvent.click(screen.getByText("Use This Template →"));
  
  // Step 5: First Win
  fireEvent.click(screen.getByText("🚀 Activate Playbook"));
  
  // Celebration
  await waitFor(() => expect(screen.getByText("You Did It! 🎊")).toBeInTheDocument());
});
```

### Database Verification
```sql
-- Check completion rate
SELECT 
  COUNT(*) as total,
  SUM(CASE WHEN is_completed THEN 1 ELSE 0 END) as completed,
  ROUND(SUM(CASE WHEN is_completed THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 1) as completion_rate
FROM onboarding_progress;

-- Check step funnel
SELECT 
  JSON_ARRAY_LENGTH(completed_steps) as steps_completed,
  COUNT(*) as users
FROM onboarding_progress
GROUP BY JSON_ARRAY_LENGTH(completed_steps)
ORDER BY steps_completed;
```

---

## Success Metrics (First Week)

| Metric | Target | Check Daily |
|--------|--------|-------------|
| Signup → Onboarding Start | 100% | Yes |
| Step 1 → 2 | 70%+ | Yes |
| Step 2 → 3 | 65%+ | Yes |
| Step 3 → 4 | 80%+ | Yes |
| Step 4 → 5 | 75%+ | Yes |
| Completion | 80%+ | Yes |
| Avg Time | < 5 min | Yes |

---

## Troubleshooting

### Issue: Salesforce OAuth redirect fails
**Solution**: Verify `SALESFORCE_REDIRECT_URI` matches exactly in both Salesforce app config and `.env`

### Issue: Progress not saving
**Solution**: Check database migrations ran: `alembic current` should show latest

### Issue: Onboarding not showing
**Solution**: Check `shouldShowOnboarding()` returns `true` for new users

### Issue: API returns 404
**Solution**: Verify routes registered in `main.py` with `include_router(onboarding.router)`

---

## Environment Variables

```env
# Salesforce OAuth
SALESFORCE_CLIENT_ID=<your-oauth-client-id>
SALESFORCE_CLIENT_SECRET=<your-oauth-client-secret>
SALESFORCE_REDIRECT_URI=https://api.forecastx.com/auth/salesforce/callback

# Frontend
REACT_APP_API_BASE_URL=https://api.forecastx.com
REACT_APP_SALESFORCE_CLIENT_ID=<your-oauth-client-id>
```

---

## Next Steps After Launch

1. **Day 1**: Monitor completion rate and step-by-step dropoff
2. **Day 3**: Check Salesforce connection success rate
3. **Week 1**: Analyze email open rates and user retention
4. **Week 2**: Cohort analysis: onboarded vs non-onboarded users
5. **Week 3**: Iterate on low-conversion steps

---

## Support

### For deployment questions:
See [DEPLOYMENT_AND_INTEGRATION_GUIDE.md](DEPLOYMENT_AND_INTEGRATION_GUIDE.md)

### For implementation details:
See [ONBOARDING_IMPLEMENTATION_GUIDE.md](ONBOARDING_IMPLEMENTATION_GUIDE.md)

### For code reference:
- Backend API: `backend/app/api/onboarding.py`
- Frontend Service: `frontend/src/services/onboardingService.ts`
- Database Models: `backend/app/db/onboarding_models.py`
- UI Component: `frontend/src/components/OnboardingFlow.tsx`
