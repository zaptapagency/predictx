from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.db.models_saas import (
    User,
    Subscription,
    Invoice,
    UsageLog,
    SubscriptionTier,
)
from app.utils import setup_logger
from app.database import get_db
from app.services.auth_service import get_current_user as current_user_dep

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])


class UserStatsResponse:
    total_users: int
    active_users: int
    verified_users: int
    admin_users: int


class UserListResponse:
    id: int
    email: str
    username: str
    full_name: str
    is_verified: bool
    is_active: bool
    is_admin: bool
    created_at: str

    class Config:
        orm_mode = True


class SubscriptionStatsResponse:
    total_subscriptions: int
    free_tier: int
    pro_tier: int
    enterprise_tier: int
    active_subscriptions: int
    canceled_subscriptions: int
    monthly_recurring_revenue: float


class PlatformAnalyticsResponse:
    total_predictions: int
    total_api_calls: int
    total_revenue: float
    predictions_this_month: int
    api_calls_this_month: int
    revenue_this_month: float
    average_predictions_per_user: float
    average_revenue_per_user: float


async def get_admin_user(current_user: User = Depends(current_user_dep), db: Session = Depends(get_db)):
    """Verify user is admin"""
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/users")
async def list_all_users(
    skip: int = Query(0),
    limit: int = Query(10),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """List all users (admin only)"""
    try:
        users = db.query(User).offset(skip).limit(limit).all()
        total = db.query(User).count()

        return {
            "items": users,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list users")


@router.get("/users/{user_id}")
async def get_user_details(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Get user details (admin only)"""
    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get subscription
        subscription = (
            db.query(Subscription)
            .filter(Subscription.user_id == user_id)
            .order_by(Subscription.created_at.desc())
            .first()
        )

        # Get usage stats (current month)
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)

        usage = (
            db.query(UsageLog)
            .filter(UsageLog.user_id == user_id, UsageLog.created_at >= month_start)
            .all()
        )

        total_cost = sum(log.cost for log in usage)

        return {
            "user": user,
            "subscription": subscription,
            "usage_this_month": {
                "actions": len(usage),
                "total_cost": float(total_cost),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user details: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user details")


@router.post("/users/{user_id}/toggle-admin")
async def toggle_admin_status(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Toggle user admin status (admin only)"""
    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.is_admin = not user.is_admin
        db.commit()

        logger.info(f"Admin status toggled for user: {user.email}")

        return {"message": "Admin status updated", "is_admin": user.is_admin}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling admin status: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to toggle admin status")


@router.get("/subscriptions")
async def get_subscription_stats(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Get subscription statistics (admin only)"""
    try:
        total = db.query(Subscription).count()
        free_tier = db.query(Subscription).filter(Subscription.tier == SubscriptionTier.FREE).count()
        pro_tier = db.query(Subscription).filter(Subscription.tier == SubscriptionTier.PRO).count()
        enterprise_tier = (
            db.query(Subscription).filter(Subscription.tier == SubscriptionTier.ENTERPRISE).count()
        )
        active = db.query(Subscription).filter(Subscription.status == "active").count()
        canceled = db.query(Subscription).filter(Subscription.status == "canceled").count()

        # Calculate MRR (Monthly Recurring Revenue)
        mrr = (
            db.query(Subscription)
            .filter(Subscription.status == "active", Subscription.tier != SubscriptionTier.FREE)
            .count()
        ) * 29  # Assuming Pro tier is $29/month

        return {
            "total_subscriptions": total,
            "free_tier": free_tier,
            "pro_tier": pro_tier,
            "enterprise_tier": enterprise_tier,
            "active_subscriptions": active,
            "canceled_subscriptions": canceled,
            "monthly_recurring_revenue": float(mrr),
        }

    except Exception as e:
        logger.error(f"Error getting subscription stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get subscription stats")


@router.get("/analytics")
async def get_platform_analytics(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Get platform analytics (admin only)"""
    try:
        # All time stats
        total_predictions = (
            db.query(UsageLog).filter(UsageLog.action == "prediction").count()
        )
        total_api_calls = db.query(UsageLog).filter(UsageLog.action == "api_call").count()
        total_revenue = (
            db.query(UsageLog)
            .with_entities(db.func.sum(UsageLog.cost))
            .scalar()
        ) or 0.0

        # This month stats
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)

        predictions_this_month = (
            db.query(UsageLog)
            .filter(UsageLog.action == "prediction", UsageLog.created_at >= month_start)
            .count()
        )
        api_calls_this_month = (
            db.query(UsageLog)
            .filter(UsageLog.action == "api_call", UsageLog.created_at >= month_start)
            .count()
        )
        revenue_this_month = (
            db.query(UsageLog)
            .filter(UsageLog.created_at >= month_start)
            .with_entities(db.func.sum(UsageLog.cost))
            .scalar()
        ) or 0.0

        # User stats
        total_users = db.query(User).count()
        avg_predictions = total_predictions / total_users if total_users > 0 else 0
        avg_revenue = float(total_revenue) / total_users if total_users > 0 else 0.0

        return {
            "total_predictions": total_predictions,
            "total_api_calls": total_api_calls,
            "total_revenue": float(total_revenue),
            "predictions_this_month": predictions_this_month,
            "api_calls_this_month": api_calls_this_month,
            "revenue_this_month": float(revenue_this_month),
            "average_predictions_per_user": float(avg_predictions),
            "average_revenue_per_user": float(avg_revenue),
        }

    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")


@router.get("/invoices")
async def get_all_invoices(
    skip: int = Query(0),
    limit: int = Query(10),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Get all invoices (admin only)"""
    try:
        invoices = (
            db.query(Invoice)
            .order_by(Invoice.invoice_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        total = db.query(Invoice).count()

        return {
            "items": invoices,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    except Exception as e:
        logger.error(f"Error getting invoices: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get invoices")
