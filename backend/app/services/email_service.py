import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
from app.config import settings
from app.utils import setup_logger

logger = setup_logger(__name__)


class EmailService:
    """Email sending service"""

    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str = "",
    ) -> bool:
        """Send email"""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = settings.SMTP_USER
            message["To"] = to_email

            # Add text and HTML versions
            if text_content:
                message.attach(MIMEText(text_content, "plain"))
            message.attach(MIMEText(html_content, "html"))

            # Send email
            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(message)

            logger.info(f"Email sent to: {to_email}")
            return True

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False

    @staticmethod
    def send_welcome_email(user_email: str, user_name: str) -> bool:
        """Send welcome email"""
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>Welcome to PredictX!</h2>
                    <p>Hi {user_name},</p>
                    <p>Thanks for signing up! You're now part of our growing community of ML enthusiasts.</p>
                    <p><strong>Your free tier includes:</strong></p>
                    <ul>
                        <li>100 predictions per month</li>
                        <li>1,000 API calls per month</li>
                        <li>Access to all prediction models</li>
                    </ul>
                    <p>Ready to make your first prediction? <a href="https://predictx.com/dashboard">Get started →</a></p>
                    <hr>
                    <p style="font-size: 12px; color: #666;">
                        If you have any questions, feel free to reach out to support@predictx.com
                    </p>
                </div>
            </body>
        </html>
        """

        return EmailService.send_email(
            to_email=user_email,
            subject="Welcome to PredictX!",
            html_content=html_content,
        )

    @staticmethod
    def send_verification_email(user_email: str, verification_link: str) -> bool:
        """Send email verification"""
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>Verify Your Email</h2>
                    <p>Please click the link below to verify your email address:</p>
                    <p><a href="{verification_link}" style="background-color: #667eea; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Verify Email</a></p>
                    <p>Or copy this link: <code>{verification_link}</code></p>
                    <p style="color: #666; font-size: 12px;">This link expires in 24 hours.</p>
                </div>
            </body>
        </html>
        """

        return EmailService.send_email(
            to_email=user_email,
            subject="Verify Your Email - PredictX",
            html_content=html_content,
        )

    @staticmethod
    def send_password_reset_email(user_email: str, reset_link: str) -> bool:
        """Send password reset email"""
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>Reset Your Password</h2>
                    <p>Click the link below to reset your password:</p>
                    <p><a href="{reset_link}" style="background-color: #667eea; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a></p>
                    <p>Or copy this link: <code>{reset_link}</code></p>
                    <p style="color: #666; font-size: 12px;">This link expires in 24 hours.</p>
                    <p style="color: #666; font-size: 12px;">If you didn't request a password reset, you can ignore this email.</p>
                </div>
            </body>
        </html>
        """

        return EmailService.send_email(
            to_email=user_email,
            subject="Password Reset - PredictX",
            html_content=html_content,
        )

    @staticmethod
    def send_subscription_confirmation(
        user_email: str, tier: str, amount: str
    ) -> bool:
        """Send subscription confirmation"""
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>Subscription Confirmed!</h2>
                    <p>Your {tier.upper()} subscription is now active.</p>
                    <p><strong>Plan Details:</strong></p>
                    <ul>
                        <li>Tier: {tier.upper()}</li>
                        <li>Amount: {amount}</li>
                        <li>Billing: Monthly</li>
                    </ul>
                    <p>You can manage your subscription anytime in your <a href="https://predictx.com/settings/billing">billing settings</a>.</p>
                    <p>Thank you for your business!</p>
                </div>
            </body>
        </html>
        """

        return EmailService.send_email(
            to_email=user_email,
            subject="Subscription Confirmed - PredictX",
            html_content=html_content,
        )

    @staticmethod
    def send_usage_limit_warning(user_email: str, tier: str, usage_type: str) -> bool:
        """Send usage limit warning"""
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>Usage Limit Warning</h2>
                    <p>You've reached 80% of your monthly {usage_type} limit for your {tier.upper()} plan.</p>
                    <p>Consider upgrading to a higher tier to get more allowance. <a href="https://predictx.com/settings/billing">Upgrade now →</a></p>
                </div>
            </body>
        </html>
        """

        return EmailService.send_email(
            to_email=user_email,
            subject=f"{usage_type.capitalize()} Limit Warning - PredictX",
            html_content=html_content,
        )

    @staticmethod
    def send_subscription_canceled_email(user_email: str) -> bool:
        """Send subscription canceled email"""
        html_content = """
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>Subscription Canceled</h2>
                    <p>Your subscription has been canceled. You'll remain on the free tier.</p>
                    <p>If you'd like to reactivate, just visit your <a href="https://predictx.com/settings/billing">billing settings</a>.</p>
                    <p>We'd love to hear your feedback! Feel free to reply to this email or contact support@predictx.com</p>
                </div>
            </body>
        </html>
        """

        return EmailService.send_email(
            to_email=user_email,
            subject="Subscription Canceled - PredictX",
            html_content=html_content,
        )

    @staticmethod
    def send_invoice_email(user_email: str, invoice_id: str, amount: float) -> bool:
        """Send invoice email"""
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>Invoice Received</h2>
                    <p>Your payment of ${amount:.2f} has been processed successfully.</p>
                    <p><strong>Invoice ID:</strong> {invoice_id}</p>
                    <p>You can view your invoice and billing history in your <a href="https://predictx.com/settings/billing">billing settings</a>.</p>
                    <p>Thank you for your business!</p>
                </div>
            </body>
        </html>
        """

        return EmailService.send_email(
            to_email=user_email,
            subject="Invoice Received - PredictX",
            html_content=html_content,
        )

    @staticmethod
    def send_payment_failed_email(user_email: str) -> bool:
        """Send payment failed email"""
        html_content = """
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>Payment Failed</h2>
                    <p>We were unable to process your payment. Your subscription may be at risk.</p>
                    <p>Please update your payment method in your <a href="https://predictx.com/settings/billing">billing settings</a> as soon as possible.</p>
                    <p>If you need help, contact support@predictx.com</p>
                </div>
            </body>
        </html>
        """

        return EmailService.send_email(
            to_email=user_email,
            subject="Payment Failed - PredictX",
            html_content=html_content,
        )

    @staticmethod
    def send_refund_email(user_email: str) -> bool:
        """Send refund confirmation email"""
        html_content = """
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>Refund Processed</h2>
                    <p>A refund has been processed for your account.</p>
                    <p>The refund should appear in your account within 3-5 business days.</p>
                    <p>If you have any questions, please contact support@predictx.com</p>
                </div>
            </body>
        </html>
        """

        return EmailService.send_email(
            to_email=user_email,
            subject="Refund Processed - PredictX",
            html_content=html_content,
        )
