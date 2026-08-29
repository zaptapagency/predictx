"""
Retention Email Tasks
Send automated emails to keep users engaged and coming back

Emails:
- Day 1: Welcome + first prediction
- Day 3: "You have at-risk customers"
- Day 7: Weekly summary
- Day 14: "See your saved customers"
- Every 7 days: Risk update + leaderboard position
"""

from celery import shared_task
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.models_saas import User, PredictionLog as Prediction, Organization
from app.services.email_service import EmailService
from app.db.database import SessionLocal
from app.utils.time import utcnow

email_service = EmailService()

# ============================================================================
# DAY 1: WELCOME EMAIL
# ============================================================================

@shared_task
def send_welcome_email(user_id: int):
    """Send welcome email after signup"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return

        email_service.send_email(
            to=user.email,
            subject="Welcome to ForecastX! 🎉",
            template="welcome",
            data={
                "user_name": user.name,
                "company_name": user.organization.name if user.organization else "Your Company",
                "dashboard_link": f"https://forecastx.io/dashboard",
            }
        )
    finally:
        db.close()

# ============================================================================
# DAY 3: ACTIVATION CHECK
# ============================================================================

@shared_task
def send_activation_reminder():
    """Send to users who haven't generated first prediction"""
    db = SessionLocal()
    try:
        # Find users who signed up 3 days ago but haven't generated predictions
        three_days_ago = utcnow() - timedelta(days=3)

        inactive_users = db.query(User).filter(
            User.created_at >= three_days_ago - timedelta(hours=1),
            User.created_at <= three_days_ago + timedelta(hours=1),
        ).all()

        for user in inactive_users:
            prediction_count = db.query(Prediction).filter(
                Prediction.user_id == user.id
            ).count()

            if prediction_count == 0:  # No predictions yet
                email_service.send_email(
                    to=user.email,
                    subject="⚠️ You have customers at risk",
                    template="activation_reminder",
                    data={
                        "user_name": user.name,
                        "dashboard_link": "https://forecastx.io/dashboard",
                        "sample_risk_count": 147,  # From sample prediction
                        "sample_revenue_risk": 145000,
                    }
                )
    finally:
        db.close()

# ============================================================================
# DAILY: CHURN RISK ALERT
# ============================================================================

@shared_task
def send_daily_risk_alerts():
    """Send daily email: "X customers at high risk this week"""
    db = SessionLocal()
    try:
        # Get all active users with connected data
        users = db.query(User).filter(
            User.is_active == True,
            User.organization.has(Organization.data_sources_count > 0)
        ).all()

        for user in users:
            # Get latest predictions (last 24 hours)
            yesterday = utcnow() - timedelta(days=1)
            recent_predictions = db.query(Prediction).filter(
                Prediction.user_id == user.id,
                Prediction.created_at >= yesterday,
                Prediction.churn_risk > 0.5
            ).all()

            if recent_predictions:
                # Get top 5 risky customers
                top_risky = sorted(recent_predictions, key=lambda p: p.churn_risk, reverse=True)[:5]
                revenue_at_risk = sum(p.mrr for p in recent_predictions)

                email_service.send_email(
                    to=user.email,
                    subject=f"⚠️ {len(recent_predictions)} customers at high churn risk",
                    template="daily_risk_alert",
                    data={
                        "user_name": user.name,
                        "high_risk_count": len(recent_predictions),
                        "revenue_at_risk": revenue_at_risk,
                        "top_customers": [
                            {
                                "name": p.customer_name,
                                "risk_score": f"{p.churn_risk*100:.0f}%",
                                "mrr": f"${p.mrr:,.0f}",
                                "reason": p.churn_reason,
                            }
                            for p in top_risky
                        ],
                        "dashboard_link": "https://forecastx.io/dashboard",
                    }
                )
    finally:
        db.close()

# ============================================================================
# WEEKLY: SUCCESS STORY
# ============================================================================

@shared_task
def send_weekly_success_email():
    """Send weekly email: "Here's who you saved this week"""
    db = SessionLocal()
    try:
        # Get all users
        users = db.query(User).all()

        for user in users:
            # Get predictions from last 7 days
            week_ago = utcnow() - timedelta(days=7)
            week_predictions = db.query(Prediction).filter(
                Prediction.user_id == user.id,
                Prediction.created_at >= week_ago
            ).all()

            if week_predictions:
                # Calculate metrics
                avg_risk = sum(p.churn_risk for p in week_predictions) / len(week_predictions)
                high_risk_customers = [p for p in week_predictions if p.churn_risk > 0.5]

                email_service.send_email(
                    to=user.email,
                    subject="📊 Your Weekly Churn Report",
                    template="weekly_summary",
                    data={
                        "user_name": user.name,
                        "predictions_this_week": len(week_predictions),
                        "high_risk_identified": len(high_risk_customers),
                        "avg_risk_score": f"{avg_risk*100:.0f}%",
                        "dashboard_link": "https://forecastx.io/dashboard",
                    }
                )
    finally:
        db.close()

# ============================================================================
# REACTIVATION: USER HASN'T LOGGED IN 7 DAYS
# ============================================================================

@shared_task
def send_reactivation_email():
    """Send to users who haven't logged in for 7 days"""
    db = SessionLocal()
    try:
        seven_days_ago = utcnow() - timedelta(days=7)

        inactive_users = db.query(User).filter(
            User.is_active == True,
            User.last_login < seven_days_ago
        ).all()

        for user in inactive_users:
            # Get their latest predictions
            latest_prediction = db.query(Prediction).filter(
                Prediction.user_id == user.id
            ).order_by(Prediction.created_at.desc()).first()

            if latest_prediction:
                email_service.send_email(
                    to=user.email,
                    subject="🔔 Your churn predictions are waiting",
                    template="reactivation",
                    data={
                        "user_name": user.name,
                        "last_check_days": 7,
                        "latest_risk_count": "147",  # Example
                        "dashboard_link": "https://forecastx.io/dashboard",
                    }
                )
    finally:
        db.close()

# ============================================================================
# CHURN PREVENTION: USER ABOUT TO CANCEL
# ============================================================================

@shared_task
def send_churn_prevention_email():
    """Send to users showing signs of leaving"""
    db = SessionLocal()
    try:
        users = db.query(User).all()

        for user in users:
            # Calculate churn risk signals
            days_since_login = (utcnow() - (user.last_login or user.created_at)).days
            prediction_count = db.query(Prediction).filter(
                Prediction.user_id == user.id
            ).count()

            # If 14+ days inactive OR no predictions made, they're at risk
            if days_since_login > 14 or prediction_count == 0:
                email_service.send_email(
                    to=user.email,
                    subject="We miss you! Here's what you're missing...",
                    template="churn_prevention",
                    data={
                        "user_name": user.name,
                        "dashboard_link": "https://forecastx.io/dashboard",
                        "support_email": "support@forecastx.io",
                    }
                )
    finally:
        db.close()

# ============================================================================
# SCHEDULE THESE TASKS
# ============================================================================

"""
In celery beat config (celery_schedule):

from celery.schedules import crontab

# Send welcome email immediately after signup
app.conf.beat_schedule = {
    'send-daily-risk-alerts': {
        'task': 'app.tasks.retention_emails.send_daily_risk_alerts',
        'schedule': crontab(hour=9, minute=0),  # 9am every day
    },
    'send-weekly-success-email': {
        'task': 'app.tasks.retention_emails.send_weekly_success_email',
        'schedule': crontab(day_of_week=1, hour=9, minute=0),  # Monday 9am
    },
    'send-reactivation-email': {
        'task': 'app.tasks.retention_emails.send_reactivation_email',
        'schedule': crontab(hour=17, minute=0),  # 5pm daily
    },
    'send-churn-prevention-email': {
        'task': 'app.tasks.retention_emails.send_churn_prevention_email',
        'schedule': crontab(hour=19, minute=0),  # 7pm daily
    },
}
"""
