from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from typing import List
from app.db.models_saas import User, Subscription, Invoice, SubscriptionTier
from app.database import get_db
from app.services.auth_service import get_current_user as current_user_dep
from app.services.billing_service import BillingService
from app.services.email_service import EmailService
from app.utils import setup_logger
from app.utils.time import utcnow

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


class UpgradeSubscriptionRequest(BaseModel):
    tier: SubscriptionTier


class SubscriptionResponse(BaseModel):
    id: int
    tier: SubscriptionTier
    status: str
    monthly_predictions_limit: int
    api_calls_limit: int
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None

    class Config:
        orm_mode = True


class InvoiceResponse(BaseModel):
    id: int
    amount: float
    currency: str
    status: str
    invoice_date: datetime
    paid_at: Optional[datetime] = None
    invoice_pdf_url: Optional[str] = None

    class Config:
        orm_mode = True


@router.get("/current", response_model=SubscriptionResponse)
async def get_current_subscription(current_user: User = Depends(current_user_dep), db: Session = Depends(get_db)):
    """Get current subscription"""
    try:
        subscription = (
            db.query(Subscription)
            .filter(Subscription.user_id == current_user.id)
            .order_by(Subscription.created_at.desc())
            .first()
        )

        if not subscription:
            # Create free subscription if doesn't exist
            subscription = Subscription(
                user_id=current_user.id,
                organization_id=current_user.organization_id,
                tier=SubscriptionTier.FREE,
                status="active",
                monthly_predictions_limit=100,
                api_calls_limit=1000,
            )
            db.add(subscription)
            db.commit()
            db.refresh(subscription)

        return subscription

    except Exception as e:
        logger.error(f"Error getting subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get subscription")


@router.post("/upgrade", response_model=SubscriptionResponse)
async def upgrade_subscription(
    request: UpgradeSubscriptionRequest,
    current_user: User = Depends(current_user_dep),
    db: Session = Depends(get_db),
):
    """Upgrade subscription tier"""
    try:
        if request.tier == SubscriptionTier.FREE:
            raise HTTPException(status_code=400, detail="Cannot downgrade to free tier")

        subscription = (
            db.query(Subscription)
            .filter(Subscription.user_id == current_user.id)
            .order_by(Subscription.created_at.desc())
            .first()
        )

        if not subscription:
            # Create new subscription
            subscription = BillingService.create_subscription(
                db, current_user.organization, request.tier
            )
        else:
            # Upgrade existing subscription
            if not BillingService.upgrade_subscription(db, subscription, request.tier):
                raise HTTPException(status_code=400, detail="Failed to upgrade subscription")
            db.refresh(subscription)

        # Send confirmation email
        EmailService.send_subscription_confirmation(
            current_user.email, request.tier.value, "$29/month"
        )

        logger.info(f"User upgraded to {request.tier}: {current_user.email}")

        return subscription

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error upgrading subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upgrade subscription")


@router.post("/cancel")
async def cancel_subscription(current_user: User = Depends(current_user_dep), db: Session = Depends(get_db)):
    """Cancel subscription"""
    try:
        subscription = (
            db.query(Subscription)
            .filter(Subscription.user_id == current_user.id)
            .order_by(Subscription.created_at.desc())
            .first()
        )

        if not subscription:
            raise HTTPException(status_code=404, detail="No active subscription")

        if subscription.tier == SubscriptionTier.FREE:
            raise HTTPException(status_code=400, detail="Cannot cancel free subscription")

        if not BillingService.cancel_subscription(db, subscription):
            raise HTTPException(status_code=400, detail="Failed to cancel subscription")

        logger.info(f"Subscription canceled: {current_user.email}")

        return {"message": "Subscription canceled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error canceling subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")


@router.get("/invoices", response_model=List[InvoiceResponse])
async def get_invoices(current_user: User = Depends(current_user_dep), db: Session = Depends(get_db)):
    """Get user's invoices"""
    try:
        invoices = (
            db.query(Invoice)
            .filter(Invoice.user_id == current_user.id)
            .order_by(Invoice.invoice_date.desc())
            .all()
        )

        return invoices

    except Exception as e:
        logger.error(f"Error getting invoices: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get invoices")


@router.get("/usage")
async def get_usage(current_user: User = Depends(current_user_dep), db: Session = Depends(get_db)):
    """Get current usage statistics"""
    try:
        from datetime import datetime, timedelta
        from app.db.models_saas import UsageLog

        subscription = (
            db.query(Subscription)
            .filter(Subscription.user_id == current_user.id)
            .order_by(Subscription.created_at.desc())
            .first()
        )

        # Get current month usage
        now = utcnow()
        month_start = datetime(now.year, now.month, 1)
        month_end = (
            datetime(now.year, now.month + 1, 1)
            if now.month < 12
            else datetime(now.year + 1, 1, 1)
        )

        predictions = (
            db.query(UsageLog)
            .filter(
                UsageLog.user_id == current_user.id,
                UsageLog.action == "prediction",
                UsageLog.created_at >= month_start,
                UsageLog.created_at < month_end,
            )
            .count()
        )

        api_calls = (
            db.query(UsageLog)
            .filter(
                UsageLog.user_id == current_user.id,
                UsageLog.action == "api_call",
                UsageLog.created_at >= month_start,
                UsageLog.created_at < month_end,
            )
            .count()
        )

        total_cost = (
            db.query(UsageLog)
            .filter(
                UsageLog.user_id == current_user.id,
                UsageLog.created_at >= month_start,
                UsageLog.created_at < month_end,
            )
            .with_entities(func.sum(UsageLog.cost))
            .scalar()
        ) or 0.0

        return {
            "tier": subscription.tier.value if subscription else "free",
            "predictions": {
                "used": predictions,
                "limit": subscription.monthly_predictions_limit if subscription else 100,
            },
            "api_calls": {
                "used": api_calls,
                "limit": subscription.api_calls_limit if subscription else 1000,
            },
            "cost": float(total_cost),
            "period_start": month_start.isoformat(),
            "period_end": month_end.isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting usage: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get usage")
