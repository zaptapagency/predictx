"""
Sample prediction endpoint - shows instant value to new users
Generates realistic but synthetic churn predictions on sample data
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import random
from app.db.database import get_db
from app.db.models_saas import User

router = APIRouter(prefix="/api", tags=["predictions"])

# ============================================================================
# SYNTHETIC DATA GENERATION
# ============================================================================

SAMPLE_COMPANIES = [
    "Acme Corp", "TechCorp", "StartupXYZ", "CloudBase", "DataWorks",
    "NextGen", "Innovate Inc", "Future Systems", "Digital Ventures", "ProActive"
]

SAMPLE_REASONS = [
    "Declining API usage (down 60%)",
    "Support tickets increased 3x",
    "Feature adoption below 20%",
    "Payment method expired",
    "No login in 30 days",
    "Competitor activity detected",
    "Contract near end (no renewal signals)",
    "Usage below average for tier",
    "Free trial ending (no engagement)",
]

def generate_sample_customers(count: int = 1000) -> list:
    """Generate synthetic customer data for sample prediction"""

    customers = []
    for i in range(count):
        # Generate realistic metrics
        mrr = random.choice([499, 999, 1999, 4999, 9999, 19999])
        api_usage_trend = random.uniform(-0.7, 1.5)  # -70% to +150%
        days_since_login = random.randint(0, 90)
        support_tickets = random.randint(0, 15)
        feature_adoption = random.uniform(0.1, 1.0)

        # Calculate churn risk based on signals
        risk_score = 0
        risk_score += max(0, -api_usage_trend * 0.3)  # Declining usage
        risk_score += (support_tickets / 10) * 0.2    # Support tickets
        risk_score += (1 - feature_adoption) * 0.2    # Low feature adoption
        risk_score += (days_since_login / 90) * 0.15  # Inactive
        risk_score = min(1.0, max(0, risk_score))     # Clamp to 0-1

        customers.append({
            'id': f'cust_{i:04d}',
            'name': f'{random.choice(SAMPLE_COMPANIES)} Customer {i}',
            'email': f'contact-{i}@samplecustomer.com',
            'mrr': mrr,
            'churn_risk': risk_score,
            'reason': random.choice(SAMPLE_REASONS),
            'api_usage_trend': api_usage_trend,
            'days_since_login': days_since_login,
            'support_tickets': support_tickets,
            'feature_adoption': feature_adoption,
        })

    return customers

# ============================================================================
# SAMPLE PREDICTION ENDPOINT
# ============================================================================

@router.post("/predictions/sample")
def generate_sample_prediction(
    user: User = Depends(lambda db=Depends(get_db): None),
    db: Session = Depends(get_db)
):
    """
    Generate sample churn prediction on synthetic data

    This endpoint:
    1. Generates 1000 synthetic customer records
    2. Runs churn prediction model on them
    3. Returns business impact summary
    4. Shows top 10 at-risk customers

    Timeline: <2 seconds
    Result: User sees immediate value without uploading data
    """

    # Generate sample data
    customers = generate_sample_customers(count=1000)

    # Calculate statistics
    high_risk_customers = [c for c in customers if c['churn_risk'] > 0.5]
    revenue_at_risk = sum(c['mrr'] for c in high_risk_customers)
    avg_risk_score = sum(c['churn_risk'] for c in customers) / len(customers)

    # Sort by risk and get top 10
    top_10 = sorted(customers, key=lambda x: x['churn_risk'], reverse=True)[:10]

    return {
        'high_risk_count': len(high_risk_customers),
        'revenue_at_risk': revenue_at_risk,
        'avg_risk_score': avg_risk_score,
        'total_customers': len(customers),
        'percent_at_risk': round((len(high_risk_customers) / len(customers)) * 100, 1),
        'top_10_customers': top_10,
        'summary': {
            'high_risk': len(high_risk_customers),
            'medium_risk': len([c for c in customers if 0.3 <= c['churn_risk'] <= 0.5]),
            'low_risk': len([c for c in customers if c['churn_risk'] < 0.3]),
        },
        'message': f'Found {len(high_risk_customers)} customers at high churn risk. Revenue at risk: ${revenue_at_risk:,.0f}',
        'action': 'Connect your real data to get accurate predictions for your customers'
    }
