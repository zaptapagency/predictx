"""
Demo Data Seeder
Populates the calling user's organization with realistic demo data so every
dashboard tab has content. Idempotent per organization: calling it twice
clears and re-creates the demo rows.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random

from app.db.models_saas import User
from app.db.database import get_db
from app.services.auth_service import get_current_user
from app.db.action_models import Action, QuickAction
from app.db.activity_models import TeamActivity
from app.db.copilot_models import CopilotRecommendation
from app.db.heatmap_models import CustomerHealthScore
from app.db.insights_models import Insight
from app.db.leaderboard_models import LeaderboardEntry, UserStats, UserActivity, Achievement
from app.db.marketplace_models import Playbook
from app.db.prediction_models import Model, Prediction, ModelType, ModelStatus
from app.db.quickwin_models import QuickWin
from app.db.roi_models import ImpactRecord
from app.utils.time import utcnow

router = APIRouter(prefix="/api/demo", tags=["demo"])

CUSTOMERS = [
    ("acme-corp", "Acme Corp", 12500),
    ("globex", "Globex Inc", 8900),
    ("initech", "Initech", 5400),
    ("umbrella", "Umbrella Labs", 21000),
    ("stark-ind", "Stark Industries", 45000),
    ("wayne-ent", "Wayne Enterprises", 38000),
    ("hooli", "Hooli", 7600),
    ("pied-piper", "Pied Piper", 3200),
]


@router.post("/seed")
def seed_demo_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fill the caller's organization with demo data across every feature."""
    org_id = current_user.organization_id
    uid = current_user.id
    now = utcnow()
    rnd = random.Random(org_id)  # deterministic per org

    # Clear previous demo rows for this org so re-seeding doesn't duplicate
    for model in (Action, QuickAction, TeamActivity, CopilotRecommendation,
                  CustomerHealthScore, Insight, LeaderboardEntry, QuickWin,
                  ImpactRecord, Prediction, Model, Playbook):
        db.query(model).filter(model.organization_id == org_id).delete()
    db.query(UserStats).filter(UserStats.user_id == uid).delete()
    db.query(UserActivity).filter(UserActivity.user_id == uid).delete()
    db.query(Achievement).filter(Achievement.user_id == uid).delete()
    db.commit()

    # --- Prediction model + predictions ---
    model = Model(
        organization_id=org_id, name="Churn Predictor v2", model_type=ModelType.CHURN,
        description="Demo churn model trained on 12 months of usage data",
        status=ModelStatus.ACTIVE, algorithm="xgboost",
        features=["login_frequency", "support_tickets", "mrr", "seats_used", "nps"],
        feature_importance={"login_frequency": 0.34, "support_tickets": 0.27,
                            "mrr": 0.18, "seats_used": 0.12, "nps": 0.09},
        training_record_count=4820, training_date=now - timedelta(days=12),
        accuracy=0.87, precision=0.83, recall=0.79, auc_roc=0.91,
        created_by_id=uid,
    )
    db.add(model)
    db.flush()

    risk_levels = ["critical", "high", "medium", "low"]
    for i, (cid, cname, mrr) in enumerate(CUSTOMERS):
        score = round(0.92 - i * 0.11, 2)
        db.add(Prediction(
            organization_id=org_id, model_id=model.id, customer_id=cid,
            score=max(score, 0.08), confidence=round(rnd.uniform(0.7, 0.95), 2),
            percentile=round(95 - i * 11, 1),
            risk_level=risk_levels[min(i // 2, 3)],
            recommended_action=["reach_out", "offer_discount", "schedule_qbr", "monitor"][min(i // 2, 3)],
            top_factors=[
                {"feature": "login_frequency", "impact": "-42% in 30 days"},
                {"feature": "support_tickets", "impact": "+3 this month"},
            ],
            predicted_at=now - timedelta(days=rnd.randint(0, 14)),
        ))

    # --- Actions ---
    priorities = ["critical", "critical", "high", "high", "medium", "medium", "low", "low"]
    for i, (cid, cname, mrr) in enumerate(CUSTOMERS):
        db.add(Action(
            organization_id=org_id,
            title=f"Reach out to {cname}",
            description=f"{cname} shows churn risk — usage down, tickets up. Recommended: personal check-in call.",
            action_type=["email", "task", "email", "task"][i % 4],
            priority=priorities[i], status="pending",
            entity_type="customer", entity_id=cid, entity_name=cname,
            entity_email=f"contact@{cid}.example.com",
            estimated_impact=float(mrr), impact_type="revenue_saved", impact_unit="usd",
            recommended_message=f"Hi {cname} team — noticed a dip in usage. Can we help?",
            assigned_to_id=uid, due_at=now + timedelta(days=2 + i),
        ))

    # --- Quick wins (both models: QuickAction feeds the Action Center, QuickWin feeds Quick Wins tab) ---
    quick_defs = [
        ("Email all critical-risk customers", "📧", "bulk_email", 4, 47400.0, 0.72),
        ("Schedule QBRs with top accounts", "📅", "bulk_task", 3, 104000.0, 0.65),
        ("Send NPS survey to healthy accounts", "📊", "bulk_email", 5, 12000.0, 0.81),
    ]
    for i, (title, icon, atype, count, impact, prob) in enumerate(quick_defs):
        db.add(QuickWin(
            organization_id=org_id, title=title, icon=icon,
            description=f"One click targets {count} accounts.",
            action_type=atype,
            action_config={"template": "demo"}, target_criteria={"risk": "critical"},
            estimated_target_count=count, estimated_impact=impact,
            success_probability=prob, order=i,
        ))
        db.add(QuickAction(
            organization_id=org_id, created_by_id=uid, name=title, icon=icon,
            description=f"One click targets {count} accounts.",
            action_config={"template": "demo", "type": atype},
            filter_config={"priority": ["critical", "high"]},
            impact_estimate=impact,
            times_used=rnd.randint(2, 9), success_rate=prob * 100,
        ))

    # --- Insights ---
    insights = [
        ("recommendation", "Umbrella Labs is your biggest save opportunity", "⚠️",
         "Churn risk 81% with $21K MRR at stake. A retention call this week has a 68% success rate.", 21000.0, True),
        ("milestone", "Your churn model accuracy hit 87%", "🎯",
         "Up 4 points since last training run. Predictions are getting sharper.", None, False),
        ("recommendation", "3 accounts are ripe for expansion", "📈",
         "Stark Industries, Wayne Enterprises and Globex are using 90%+ of their seats.", 34000.0, False),
        ("reminder", "2 critical actions are due tomorrow", "⏰",
         "Acme Corp and Globex outreach actions are approaching their due dates.", None, True),
    ]
    for itype, title, icon, desc, impact, urgent in insights:
        db.add(Insight(
            user_id=uid, organization_id=org_id, insight_type=itype,
            title=title, description=desc, icon=icon,
            recommended_action="Open Action Center", action_type="task",
            estimated_impact=impact, confidence=0.8, is_urgent=urgent,
        ))

    # --- Copilot recommendations ---
    recs = [
        ("Call Umbrella Labs today", "Usage fell 40% and their renewal is in 45 days.",
         "Schedule retention call", "call", 21000.0, 0.68),
        ("Offer Stark Industries the enterprise tier", "They're at 96% seat utilization for 3 months.",
         "Send expansion proposal", "email", 15000.0, 0.74),
        ("Re-run churn model with fresh data", "14 days since last training; drift check recommends refresh.",
         "Start training run", "workflow", None, 0.9),
    ]
    for title, reasoning, action, atype, impact, prob in recs:
        db.add(CopilotRecommendation(
            user_id=uid, organization_id=org_id, title=title,
            description=reasoning, reasoning=reasoning,
            suggested_action=action, action_type=atype,
            entity_type="customer", estimated_impact=impact,
            success_probability=prob, confidence=prob, model_version="demo-1",
        ))

    # --- Heatmap health scores ---
    for i, (cid, cname, mrr) in enumerate(CUSTOMERS):
        churn = max(0.92 - i * 0.11, 0.05)
        db.add(CustomerHealthScore(
            organization_id=org_id, customer_id=cid,
            overall_health=round(100 - churn * 90, 1), churn_risk=round(churn, 2),
            expansion_potential=round(rnd.uniform(0.1, 0.9), 2),
            support_urgency=round(churn * 0.8, 2),
            health_trend=["declining", "declining", "stable", "improving"][min(i // 2, 3)],
            red_flags=max(3 - i // 2, 0), yellow_flags=rnd.randint(0, 3),
            green_flags=min(i, 5),
        ))

    # --- ROI impact records ---
    for i in range(6):
        cid, cname, mrr = CUSTOMERS[i]
        db.add(ImpactRecord(
            organization_id=org_id,
            impact_type=["revenue_saved", "revenue_created"][i % 2],
            impact_category=["churn_prevention", "expansion"][i % 2],
            entity_type="customer", entity_id=cid, entity_name=cname,
            value_amount=float(mrr) * rnd.uniform(0.5, 1.2),
            confidence_level=round(rnd.uniform(0.6, 0.95), 2), is_confirmed=i < 3,
            predicted_at=now - timedelta(days=rnd.randint(1, 25)),
            value_realized_at=now - timedelta(days=rnd.randint(0, 10)) if i < 3 else None,
        ))

    # --- Leaderboard, stats, activity ---
    week_start = now - timedelta(days=now.weekday())
    db.add(LeaderboardEntry(
        organization_id=org_id, user_id=uid, period="week",
        period_start=week_start, period_end=week_start + timedelta(days=7),
        rank=1, rank_previous=2, rank_change=1, score=1240.0,
        customers_saved=3, expansions_closed=1, actions_taken=14,
        revenue_generated=47800.0, predictions_made=22, accuracy_score=0.87,
        action_streak=5, is_top_performer=True,
    ))
    db.add(UserStats(
        user_id=uid, organization_id=org_id,
        total_predictions=22, total_actions=14, total_customers_saved=3,
        total_expansions_closed=1, total_revenue_generated=47800.0,
        this_month_actions=14, this_week_actions=6, today_actions=2,
        prediction_accuracy=0.87, action_success_rate=0.71,
        avg_revenue_per_action=3414.0, days_active=9,
    ))
    db.add(Achievement(
        user_id=uid, organization_id=org_id, achievement_type="churn_saver",
        name="Churn Saver", description="Saved 3 customers from churning",
    ))
    activities = [
        ("customer_saved", "Saved Acme Corp", "Retention call converted a critical churn risk into a renewal.", "Acme Corp", 12500.0, True),
        ("expansion_closed", "Closed Stark Industries expansion", "Upgraded to enterprise tier after seat-limit alert.", "Stark Industries", 15000.0, True),
        ("achievement_unlocked", "Earned the Churn Saver badge", "3 customers saved this month.", None, None, True),
        ("action_completed", "Completed QBR with Globex", "Quarterly review surfaced 2 new use cases.", "Globex Inc", None, False),
    ]
    for atype, title, desc, ename, revenue, celebrate in activities:
        db.add(TeamActivity(
            organization_id=org_id, user_id=uid, activity_type=atype,
            title=title, description=desc, entity_type="customer",
            entity_name=ename, revenue_impact=revenue,
            is_celebratory=celebrate,
            created_at=now - timedelta(hours=rnd.randint(1, 96)),
        ))
        db.add(UserActivity(
            organization_id=org_id, user_id=uid, activity_type=atype,
            activity_title=title, activity_description=desc,
            revenue_impact=revenue, entity_name=ename, is_celebratory=celebrate,
            created_at=now - timedelta(hours=rnd.randint(1, 96)),
        ))

    # --- Marketplace playbooks ---
    playbooks = [
        ("High-Value Churn Prevention", "churn", "churn-prediction", "🛡️", 79.0, False, 0.78, 6.5, 15, 342, 4.7),
        ("Lead Scoring Accelerator", "leads", "lead-scoring", "🎯", 49.0, False, 0.71, 4.2, 10, 208, 4.5),
        ("Expansion Detector", "expansion", "expansion-prediction", "📈", 59.0, False, 0.66, 3.8, 20, 154, 4.4),
        ("CSV Quick-Start Starter", "starter", "churn-prediction", "🚀", 0.0, True, 0.6, 2.5, 5, 861, 4.8),
    ]
    for name, cat, use, icon, price, free, sr, roi, setup, downloads, rating in playbooks:
        db.add(Playbook(
            organization_id=org_id, creator_id=uid, name=name,
            slug=f"{use}-{org_id}-{name.lower().replace(' ', '-')[:24]}",
            description=f"{name}: proven {cat} playbook with {roi}x typical ROI.",
            category=cat, use_case=use, industry="SaaS",
            price_monthly=price, free=free,
            configuration={"trigger": "score > 0.7", "actions": ["email", "task"]},
            icon=icon, tags=["proven", "demo"], downloads=downloads,
            active_users=downloads // 3, avg_rating=rating, review_count=downloads // 8,
            status="published", published_at=now - timedelta(days=60),
            success_rate=sr, typical_roi=roi, setup_time_minutes=setup,
        ))

    db.commit()
    return {
        "success": True,
        "message": "Demo data loaded",
        "seeded": {
            "customers": len(CUSTOMERS), "predictions": len(CUSTOMERS),
            "actions": len(CUSTOMERS), "quick_wins": len(quick_defs),
            "insights": len(insights), "copilot_recommendations": len(recs),
            "health_scores": len(CUSTOMERS), "impact_records": 6,
            "activities": len(activities), "marketplace_playbooks": len(playbooks),
        },
    }
