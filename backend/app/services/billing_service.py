import stripe
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.config import settings
from app.db.models_saas import (
    Subscription,
    Organization,
    Invoice,
    SubscriptionTier,
)
from app.utils import setup_logger
from datetime import datetime

logger = setup_logger(__name__)

stripe.api_key = settings.STRIPE_API_KEY

# Stripe product IDs (set these in Stripe dashboard)
STRIPE_PRICES = {
    "free": None,
    "pro": getattr(settings, "STRIPE_PRO_PRICE_ID", "price_pro"),
    "enterprise": getattr(settings, "STRIPE_ENTERPRISE_PRICE_ID", "price_enterprise"),
}


class BillingService:
    """Billing and subscription management"""

    @staticmethod
    def create_customer(organization: Organization, email: str) -> str:
        """Create Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=organization.name,
                metadata={"organization_id": organization.id},
            )

            organization.stripe_customer_id = customer.id
            logger.info(f"Created Stripe customer: {customer.id}")

            return customer.id
        except stripe.error.StripeError as e:
            logger.error(f"Error creating Stripe customer: {str(e)}")
            raise

    @staticmethod
    def create_subscription(
        db: Session, organization: Organization, tier: SubscriptionTier
    ) -> Optional[Subscription]:
        """Create subscription"""
        try:
            if tier == SubscriptionTier.FREE:
                # No Stripe subscription for free tier
                subscription = Subscription(
                    organization_id=organization.id,
                    tier=SubscriptionTier.FREE,
                    status="active",
                    monthly_predictions_limit=100,
                    api_calls_limit=1000,
                )

                db.add(subscription)
                db.commit()
                db.refresh(subscription)

                logger.info(
                    f"Created free subscription for organization: {organization.id}"
                )

                return subscription

            # Create Stripe subscription
            if not organization.stripe_customer_id:
                BillingService.create_customer(organization, organization.billing_email or "")

            price_id = STRIPE_PRICES.get(tier.value)

            if not price_id:
                raise ValueError(f"Price ID not configured for tier: {tier.value}")

            stripe_subscription = stripe.Subscription.create(
                customer=organization.stripe_customer_id,
                items=[{"price": price_id}],
                metadata={"organization_id": organization.id, "tier": tier.value},
            )

            # Determine limits based on tier
            if tier == SubscriptionTier.PRO:
                monthly_predictions_limit = 10000
                api_calls_limit = 100000
            else:  # ENTERPRISE
                monthly_predictions_limit = 0  # Unlimited
                api_calls_limit = 0

            subscription = Subscription(
                organization_id=organization.id,
                tier=tier,
                stripe_subscription_id=stripe_subscription.id,
                stripe_price_id=price_id,
                status="active",
                current_period_start=datetime.fromtimestamp(
                    stripe_subscription.current_period_start
                ),
                current_period_end=datetime.fromtimestamp(
                    stripe_subscription.current_period_end
                ),
                monthly_predictions_limit=monthly_predictions_limit,
                api_calls_limit=api_calls_limit,
            )

            db.add(subscription)
            db.commit()
            db.refresh(subscription)

            logger.info(f"Created subscription for organization: {organization.id}, tier: {tier}")

            return subscription

        except stripe.error.StripeError as e:
            logger.error(f"Error creating subscription: {str(e)}")
            db.rollback()
            raise

    @staticmethod
    def cancel_subscription(db: Session, subscription: Subscription) -> bool:
        """Cancel subscription"""
        try:
            if subscription.stripe_subscription_id:
                stripe.Subscription.delete(subscription.stripe_subscription_id)

            subscription.status = "canceled"
            subscription.canceled_at = datetime.utcnow()
            subscription.cancel_at_period_end = False

            db.commit()

            logger.info(f"Canceled subscription: {subscription.id}")

            return True

        except stripe.error.StripeError as e:
            logger.error(f"Error canceling subscription: {str(e)}")
            db.rollback()
            return False

    @staticmethod
    def upgrade_subscription(
        db: Session, subscription: Subscription, new_tier: SubscriptionTier
    ) -> bool:
        """Upgrade subscription"""
        try:
            if not subscription.stripe_subscription_id:
                # Create new subscription for free tier upgrades
                organization = subscription.organization
                BillingService.create_subscription(db, organization, new_tier)
                db.delete(subscription)
                db.commit()
                return True

            # Update existing Stripe subscription
            new_price_id = STRIPE_PRICES.get(new_tier.value)

            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                items=[
                    {
                        "id": subscription.stripe_subscription_id,
                        "price": new_price_id,
                    }
                ],
            )

            subscription.tier = new_tier
            subscription.stripe_price_id = new_price_id

            # Update limits
            if new_tier == SubscriptionTier.PRO:
                subscription.monthly_predictions_limit = 10000
                subscription.api_calls_limit = 100000
            else:  # ENTERPRISE
                subscription.monthly_predictions_limit = 0
                subscription.api_calls_limit = 0

            db.commit()

            logger.info(f"Upgraded subscription: {subscription.id} to {new_tier}")

            return True

        except stripe.error.StripeError as e:
            logger.error(f"Error upgrading subscription: {str(e)}")
            db.rollback()
            return False

    @staticmethod
    def handle_webhook(event: Dict[str, Any], db: Session) -> bool:
        """Handle Stripe webhooks"""
        try:
            if event["type"] == "invoice.paid":
                invoice_data = event["data"]["object"]
                subscription_id = invoice_data.get("subscription")

                # Create invoice record
                subscription = (
                    db.query(Subscription)
                    .filter(Subscription.stripe_subscription_id == subscription_id)
                    .first()
                )

                if subscription:
                    invoice = Invoice(
                        user_id=subscription.user_id,
                        stripe_invoice_id=invoice_data["id"],
                        amount=invoice_data["amount_paid"] / 100,
                        currency=invoice_data["currency"],
                        status=invoice_data["status"],
                        invoice_date=datetime.fromtimestamp(invoice_data["date"]),
                        paid_at=datetime.fromtimestamp(invoice_data["paid_at"]),
                        invoice_pdf_url=invoice_data.get("invoice_pdf"),
                    )

                    db.add(invoice)
                    db.commit()

                    logger.info(f"Recorded invoice: {invoice_data['id']}")

            elif event["type"] == "customer.subscription.deleted":
                sub_data = event["data"]["object"]
                subscription = (
                    db.query(Subscription)
                    .filter(Subscription.stripe_subscription_id == sub_data["id"])
                    .first()
                )

                if subscription:
                    subscription.status = "canceled"
                    subscription.canceled_at = datetime.fromtimestamp(sub_data["canceled_at"])
                    db.commit()

                    logger.info(f"Subscription canceled: {sub_data['id']}")

            return True

        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            return False
