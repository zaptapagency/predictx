from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import stripe
import hmac
import hashlib
from app.db.models_saas import Subscription, Invoice, User, Organization, SubscriptionTier
from app.database import get_db
from app.services.billing_service import BillingService
from app.api.marketplace import confirm_marketplace_checkout, fail_marketplace_checkout
from app.services.email_service import EmailService
from app.config import settings
from app.utils import setup_logger
from app.database import get_db
from app.utils.time import utcnow

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

stripe.api_key = settings.STRIPE_API_KEY


def verify_stripe_webhook(request_body: bytes, signature: str) -> bool:
    """Verify Stripe webhook signature"""
    try:
        event = stripe.Webhook.construct_event(
            request_body, signature, settings.STRIPE_WEBHOOK_SECRET
        )
        return event
    except ValueError:
        return None
    except stripe.error.SignatureVerificationError:
        return None


@router.post("/stripe")
async def handle_stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events"""
    try:
        request_body = await request.body()
        signature = request.headers.get("stripe-signature")

        if not signature:
            raise HTTPException(status_code=400, detail="Missing signature")

        event = verify_stripe_webhook(request_body, signature)

        if not event:
            raise HTTPException(status_code=400, detail="Invalid signature")

        # Handle different event types
        event_type = event["type"]
        data = event["data"]["object"]

        logger.info(f"Received Stripe event: {event_type}")

        if event_type == "customer.subscription.created":
            handle_subscription_created(db, data)

        elif event_type == "customer.subscription.updated":
            handle_subscription_updated(db, data)

        elif event_type == "customer.subscription.deleted":
            handle_subscription_deleted(db, data)

        elif event_type == "invoice.payment_succeeded":
            handle_invoice_payment_succeeded(db, data)

        elif event_type == "invoice.payment_failed":
            handle_invoice_payment_failed(db, data)

        elif event_type == "charge.refunded":
            handle_charge_refunded(db, data)

        elif event_type == "checkout.session.completed":
            confirm_marketplace_checkout(db, data)

        elif event_type in ("checkout.session.expired", "checkout.session.async_payment_failed"):
            fail_marketplace_checkout(db, data)

        return {"status": "success"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


def handle_subscription_created(db: Session, data: dict):
    """Handle subscription created event"""
    try:
        stripe_customer_id = data.get("customer")
        stripe_subscription_id = data["id"]

        # Find organization by stripe customer id
        organization = (
            db.query(Organization)
            .filter(Organization.stripe_customer_id == stripe_customer_id)
            .first()
        )

        if not organization:
            logger.warning(f"Organization not found for customer: {stripe_customer_id}")
            return

        # Get subscription tier from price id
        price_id = data["items"]["data"][0]["price"]["id"]
        tier = get_tier_from_price_id(price_id)

        # Update subscription
        subscription = (
            db.query(Subscription)
            .filter(Subscription.organization_id == organization.id)
            .first()
        )

        if subscription:
            subscription.tier = tier
            subscription.stripe_subscription_id = stripe_subscription_id
            subscription.status = "active"
            subscription.current_period_start = datetime.fromtimestamp(
                data["current_period_start"]
            )
            subscription.current_period_end = datetime.fromtimestamp(
                data["current_period_end"]
            )
        else:
            subscription = Subscription(
                organization_id=organization.id,
                user_id=organization.owner_id,
                tier=tier,
                stripe_subscription_id=stripe_subscription_id,
                status="active",
                current_period_start=datetime.fromtimestamp(
                    data["current_period_start"]
                ),
                current_period_end=datetime.fromtimestamp(data["current_period_end"]),
            )
            db.add(subscription)

        db.commit()
        logger.info(f"Subscription created: {stripe_subscription_id}")

    except Exception as e:
        logger.error(f"Error handling subscription created: {str(e)}")
        db.rollback()


def handle_subscription_updated(db: Session, data: dict):
    """Handle subscription updated event"""
    try:
        stripe_subscription_id = data["id"]

        subscription = (
            db.query(Subscription)
            .filter(Subscription.stripe_subscription_id == stripe_subscription_id)
            .first()
        )

        if not subscription:
            logger.warning(f"Subscription not found: {stripe_subscription_id}")
            return

        # Update tier
        price_id = data["items"]["data"][0]["price"]["id"]
        tier = get_tier_from_price_id(price_id)
        subscription.tier = tier

        # Update period
        subscription.current_period_start = datetime.fromtimestamp(
            data["current_period_start"]
        )
        subscription.current_period_end = datetime.fromtimestamp(
            data["current_period_end"]
        )

        db.commit()
        logger.info(f"Subscription updated: {stripe_subscription_id}")

    except Exception as e:
        logger.error(f"Error handling subscription updated: {str(e)}")
        db.rollback()


def handle_subscription_deleted(db: Session, data: dict):
    """Handle subscription deleted event"""
    try:
        stripe_subscription_id = data["id"]

        subscription = (
            db.query(Subscription)
            .filter(Subscription.stripe_subscription_id == stripe_subscription_id)
            .first()
        )

        if not subscription:
            logger.warning(f"Subscription not found: {stripe_subscription_id}")
            return

        subscription.status = "canceled"
        db.commit()

        # Send email to user
        user = db.query(User).filter(User.id == subscription.user_id).first()
        if user:
            EmailService.send_subscription_canceled_email(user.email)

        logger.info(f"Subscription canceled: {stripe_subscription_id}")

    except Exception as e:
        logger.error(f"Error handling subscription deleted: {str(e)}")
        db.rollback()


def handle_invoice_payment_succeeded(db: Session, data: dict):
    """Handle invoice payment succeeded event"""
    try:
        stripe_invoice_id = data["id"]
        stripe_customer_id = data.get("customer")
        amount = data["amount_paid"]
        currency = data["currency"]

        # Find organization
        organization = (
            db.query(Organization)
            .filter(Organization.stripe_customer_id == stripe_customer_id)
            .first()
        )

        if not organization:
            logger.warning(f"Organization not found for customer: {stripe_customer_id}")
            return

        # Create invoice record
        invoice = (
            db.query(Invoice)
            .filter(Invoice.stripe_invoice_id == stripe_invoice_id)
            .first()
        )

        if not invoice:
            invoice = Invoice(
                user_id=organization.owner_id,
                stripe_invoice_id=stripe_invoice_id,
                amount=amount / 100,  # Convert cents to dollars
                currency=currency,
                status="paid",
                invoice_date=utcnow(),
                paid_at=utcnow(),
            )
            db.add(invoice)
        else:
            invoice.status = "paid"
            invoice.paid_at = utcnow()

        db.commit()

        # Send email to user
        user = db.query(User).filter(User.id==organization.owner_id).first()
        if user:
            EmailService.send_invoice_email(user.email, stripe_invoice_id, amount / 100)

        logger.info(f"Invoice paid: {stripe_invoice_id}")

    except Exception as e:
        logger.error(f"Error handling invoice payment succeeded: {str(e)}")
        db.rollback()


def handle_invoice_payment_failed(db: Session, data: dict):
    """Handle invoice payment failed event"""
    try:
        stripe_invoice_id = data["id"]
        stripe_customer_id = data.get("customer")

        # Find organization
        organization = (
            db.query(Organization)
            .filter(Organization.stripe_customer_id == stripe_customer_id)
            .first()
        )

        if not organization:
            logger.warning(f"Organization not found for customer: {stripe_customer_id}")
            return

        # Update invoice status
        invoice = (
            db.query(Invoice)
            .filter(Invoice.stripe_invoice_id == stripe_invoice_id)
            .first()
        )

        if invoice:
            invoice.status = "failed"
            db.commit()

        # Send email to user
        user = db.query(User).filter(User.id == organization.owner_id).first()
        if user:
            EmailService.send_payment_failed_email(user.email)

        logger.info(f"Invoice payment failed: {stripe_invoice_id}")

    except Exception as e:
        logger.error(f"Error handling invoice payment failed: {str(e)}")
        db.rollback()


def handle_charge_refunded(db: Session, data: dict):
    """Handle charge refunded event"""
    try:
        stripe_invoice_id = data.get("invoice")

        if not stripe_invoice_id:
            return

        invoice = (
            db.query(Invoice)
            .filter(Invoice.stripe_invoice_id == stripe_invoice_id)
            .first()
        )

        if invoice:
            invoice.status = "refunded"
            db.commit()

            # Send email to user
            user = db.query(User).filter(User.id == invoice.user_id).first()
            if user:
                EmailService.send_refund_email(user.email)

        logger.info(f"Charge refunded: {stripe_invoice_id}")

    except Exception as e:
        logger.error(f"Error handling charge refunded: {str(e)}")
        db.rollback()


def get_tier_from_price_id(price_id: str):
    """Get tier from Stripe price ID"""
    if price_id == settings.STRIPE_PRO_PRICE_ID:
        return SubscriptionTier.PRO
    elif price_id == settings.STRIPE_ENTERPRISE_PRICE_ID:
        return SubscriptionTier.ENTERPRISE
    else:
        return SubscriptionTier.FREE
