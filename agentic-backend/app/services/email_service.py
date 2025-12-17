"""
Email service using Resend API for sending transactional emails.
"""

import resend
from typing import Optional
import logging
import os

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via Resend API."""

    def __init__(self):
        # Try multiple ways to get the API key
        api_key = settings.resend_api_key or os.environ.get("RESEND_API_KEY")

        if api_key:
            resend.api_key = api_key
            print(f"✅ Resend API key configured (starts with: {api_key[:10]}...)")
        else:
            print("⚠️ RESEND_API_KEY not configured. Email sending will fail.")

    async def send_waitlist_approval_email(
        self,
        to_email: str,
        user_name: Optional[str] = None,
    ) -> bool:
        """
        Send waitlist approval notification email.

        Args:
            to_email: Recipient email address
            user_name: Optional name of the user

        Returns:
            True if email sent successfully, False otherwise
        """
        if not settings.resend_api_key:
            logger.error("Cannot send email: RESEND_API_KEY not configured")
            return False

        name = user_name or "there"
        frontend_url = settings.frontend_url

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to Sahulat AI!</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f8fafc;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" style="max-width: 600px; width: 100%; border-collapse: collapse; background-color: #ffffff; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px 40px; text-align: center;">
                            <div style="display: inline-block; background: linear-gradient(135deg, #6366f1 0%, #14b8a6 100%); padding: 16px; border-radius: 16px; margin-bottom: 20px;">
                                <span style="font-size: 32px;">🤖</span>
                            </div>
                            <h1 style="margin: 0; font-size: 28px; font-weight: 700; color: #0f172a;">
                                You're In! 🎉
                            </h1>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 20px 40px 30px 40px;">
                            <p style="margin: 0 0 20px 0; font-size: 16px; line-height: 1.6; color: #475569;">
                                Hey {name},
                            </p>
                            <p style="margin: 0 0 20px 0; font-size: 16px; line-height: 1.6; color: #475569;">
                                Great news! Your waitlist request has been <strong style="color: #10b981;">approved</strong>. You now have full access to Sahulat AI and all its powerful features.
                            </p>
                            <p style="margin: 0 0 30px 0; font-size: 16px; line-height: 1.6; color: #475569;">
                                Here's what you can do now:
                            </p>
                            
                            <!-- Features List -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
                                <tr>
                                    <td style="padding: 12px 16px; background-color: #f1f5f9; border-radius: 8px; margin-bottom: 8px;">
                                        <span style="font-size: 20px; margin-right: 12px;">💬</span>
                                        <span style="color: #334155; font-size: 14px;">Chat with AI agents for sales, inventory & marketing</span>
                                    </td>
                                </tr>
                                <tr><td style="height: 8px;"></td></tr>
                                <tr>
                                    <td style="padding: 12px 16px; background-color: #f1f5f9; border-radius: 8px;">
                                        <span style="font-size: 20px; margin-right: 12px;">📊</span>
                                        <span style="color: #334155; font-size: 14px;">Connect QuickBooks, Google Sheets & WhatsApp</span>
                                    </td>
                                </tr>
                                <tr><td style="height: 8px;"></td></tr>
                                <tr>
                                    <td style="padding: 12px 16px; background-color: #f1f5f9; border-radius: 8px;">
                                        <span style="font-size: 20px; margin-right: 12px;">🚀</span>
                                        <span style="color: #334155; font-size: 14px;">Automate your business operations</span>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- CTA Button -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td align="center">
                                        <a href="{frontend_url}/chat" 
                                           style="display: inline-block; padding: 16px 32px; background: linear-gradient(135deg, #6366f1 0%, #14b8a6 100%); color: #ffffff; text-decoration: none; font-weight: 600; font-size: 16px; border-radius: 12px; box-shadow: 0 4px 14px 0 rgba(99, 102, 241, 0.4);">
                                            Start Using Sahulat AI →
                                        </a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; background-color: #f8fafc; border-radius: 0 0 16px 16px;">
                            <p style="margin: 0 0 10px 0; font-size: 14px; color: #64748b; text-align: center;">
                                Thank you for being an early adopter! ❤️
                            </p>
                            <p style="margin: 0; font-size: 12px; color: #94a3b8; text-align: center;">
                                Made with love in Pakistan 🇵🇰 | 
                                <a href="{frontend_url}" style="color: #6366f1; text-decoration: none;">sahulatai.app</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

        text_content = f"""
Hey {name},

Great news! Your waitlist request has been APPROVED. You now have full access to Sahulat AI and all its powerful features.

Here's what you can do now:
- Chat with AI agents for sales, inventory & marketing
- Connect QuickBooks, Google Sheets & WhatsApp
- Automate your business operations

Start using Sahulat AI: {frontend_url}/chat

Thank you for being an early adopter!

Made with love in Pakistan 🇵🇰
sahulatai.app
"""

        try:
            params: resend.Emails.SendParams = {
                "from": settings.email_from_address,
                "to": [to_email],
                "subject": "🎉 You're approved! Welcome to Sahulat AI",
                "html": html_content,
                "text": text_content,
                "reply_to": "contact@sahulatai.app",
                "tags": [
                    {"name": "type", "value": "waitlist_approval"},
                ],
            }

            email_response = resend.Emails.send(params)
            logger.info(
                f"Approval email sent successfully to {to_email}: {email_response.get('id')}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to send approval email to {to_email}: {str(e)}")
            return False

    async def send_welcome_email(
        self,
        to_email: str,
        user_name: Optional[str] = None,
    ) -> bool:
        """
        Send welcome email to new users (when they sign up).

        Args:
            to_email: Recipient email address
            user_name: Optional name of the user

        Returns:
            True if email sent successfully, False otherwise
        """
        if not settings.resend_api_key:
            logger.error("Cannot send email: RESEND_API_KEY not configured")
            return False

        name = user_name or "there"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f8fafc;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" style="max-width: 600px; width: 100%; background-color: #ffffff; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                    <tr>
                        <td style="padding: 40px; text-align: center;">
                            <div style="background: linear-gradient(135deg, #6366f1 0%, #14b8a6 100%); padding: 16px; border-radius: 16px; display: inline-block; margin-bottom: 20px;">
                                <span style="font-size: 32px;">🤖</span>
                            </div>
                            <h1 style="margin: 0 0 20px 0; font-size: 24px; color: #0f172a;">Welcome to Sahulat AI!</h1>
                            <p style="margin: 0 0 20px 0; font-size: 16px; color: #475569; line-height: 1.6;">
                                Hey {name}, thanks for signing up! You've been added to our waitlist.
                            </p>
                            <p style="margin: 0; font-size: 14px; color: #64748b; line-height: 1.6;">
                                We're a bootstrapped startup managing high demand carefully. We'll notify you as soon as your access is approved!
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 20px 40px 40px; background-color: #f8fafc; border-radius: 0 0 16px 16px; text-align: center;">
                            <p style="margin: 0; font-size: 12px; color: #94a3b8;">
                                Made with ❤️ in Pakistan | <a href="{settings.frontend_url}" style="color: #6366f1;">sahulatai.app</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

        try:
            params: resend.Emails.SendParams = {
                "from": settings.email_from_address,
                "to": [to_email],
                "subject": "Welcome to Sahulat AI - You're on the waitlist!",
                "html": html_content,
                "reply_to": "contact@sahulatai.app",
                "tags": [
                    {"name": "type", "value": "welcome"},
                ],
            }

            email_response = resend.Emails.send(params)
            logger.info(f"Welcome email sent to {to_email}: {email_response.get('id')}")
            return True

        except Exception as e:
            logger.error(f"Failed to send welcome email to {to_email}: {str(e)}")
            return False

    async def send_custom_email(
        self,
        to_emails: list[str],
        subject: str,
        message: str,
        sender_name: str = "Sahulat AI Team",
    ) -> dict:
        """
        Send a custom email to one or more recipients.

        Args:
            to_emails: List of recipient email addresses
            subject: Email subject line
            message: Email body (plain text, will be formatted in HTML)
            sender_name: Name to show as sender

        Returns:
            Dict with success count and failed emails
        """
        if not settings.resend_api_key:
            logger.error("Cannot send email: RESEND_API_KEY not configured")
            return {"success_count": 0, "failed": to_emails, "error": "Email not configured"}

        results = {"success_count": 0, "failed": [], "sent_to": []}

        # Convert plain text message to HTML with line breaks
        html_message = message.replace("\n", "<br>")

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f8fafc;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" style="max-width: 600px; width: 100%; background-color: #ffffff; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                    <tr>
                        <td style="padding: 40px 40px 20px 40px; text-align: center;">
                            <div style="background: linear-gradient(135deg, #6366f1 0%, #14b8a6 100%); padding: 16px; border-radius: 16px; display: inline-block; margin-bottom: 20px;">
                                <span style="font-size: 32px;">🤖</span>
                            </div>
                            <h1 style="margin: 0 0 10px 0; font-size: 24px; color: #0f172a;">{subject}</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 0 40px 40px 40px;">
                            <div style="font-size: 16px; color: #475569; line-height: 1.8;">
                                {html_message}
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 20px 40px 30px; border-top: 1px solid #e2e8f0;">
                            <p style="margin: 0 0 5px 0; font-size: 14px; color: #64748b;">
                                Best regards,<br>
                                <strong style="color: #334155;">{"SahulatAI"}</strong>
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 20px 40px; background-color: #f8fafc; border-radius: 0 0 16px 16px; text-align: center;">
                            <p style="margin: 0; font-size: 12px; color: #94a3b8;">
                                Made with ❤️ in Pakistan | <a href="{settings.frontend_url}" style="color: #6366f1;">sahulatai.app</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

        for email in to_emails:
            try:
                params: resend.Emails.SendParams = {
                    "from": settings.email_from_address,
                    "to": [email],
                    "subject": subject,
                    "html": html_content,
                    "reply_to": "contact@sahulatai.app",
                    "tags": [
                        {"name": "type", "value": "admin-custom"},
                    ],
                }

                email_response = resend.Emails.send(params)
                logger.info(f"Custom email sent to {email}: {email_response.get('id')}")
                results["success_count"] += 1
                results["sent_to"].append(email)

            except Exception as e:
                logger.error(f"Failed to send custom email to {email}: {str(e)}")
                results["failed"].append(email)

        return results


# Singleton instance
email_service = EmailService()
