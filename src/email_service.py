"""
Email Service for WingmanMatch

Provides comprehensive email functionality using Resend API for match notifications,
user communications, and system alerts. Features template-based emails, retry logic,
and graceful error handling.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from enum import Enum

import resend
from resend.exceptions import ResendError

from src.config import Config
from src.retry_policies import with_email_retry, execute_with_retry

logger = logging.getLogger(__name__)

class EmailTemplate(Enum):
    """Enumeration of available email templates"""
    MATCH_INVITATION = "match_invitation"
    MATCH_ACCEPTED = "match_accepted"
    MATCH_DECLINED = "match_declined"
    SESSION_REMINDER = "session_reminder"
    CHALLENGE_REMINDER = "challenge_reminder"
    WELCOME_ONBOARDING = "welcome_onboarding"
    MATCH_COMPLETION = "match_completion"
    SYSTEM_NOTIFICATION = "system_notification"

class EmailPriority(Enum):
    """Email priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class EmailServiceError(Exception):
    """Custom exception for email service errors"""
    pass

class EmailService:
    """
    Email service for WingmanMatch using Resend API.
    
    Provides template-based email sending with retry logic, fallback mechanisms,
    and comprehensive error handling.
    """
    
    def __init__(self):
        self._is_available = False
        self._fallback_mode = False
        self._pending_emails: List[Dict[str, Any]] = []
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Resend email service"""
        if not Config.RESEND_API_KEY:
            logger.warning("Resend API key not configured, email service in fallback mode")
            self._fallback_mode = True
            return
        
        try:
            resend.api_key = Config.RESEND_API_KEY
            self._is_available = True
            logger.info("Email service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize email service: {str(e)}")
            self._fallback_mode = True
    
    def _get_email_templates(self) -> Dict[str, Dict[str, str]]:
        """Get email template definitions"""
        return {
            EmailTemplate.MATCH_INVITATION.value: {
                "subject": "🎯 You have a new WingmanMatch invitation!",
                "template": """
Hello {recipient_name},

Great news! We've found you a potential wingman match for your challenge: "{challenge_title}".

**Your potential wingman:** {wingman_name}
**Challenge:** {challenge_title}
**Challenge Type:** {challenge_type}
**Duration:** {duration_days} days

{wingman_name} has a similar goal and complementary skills that could make this a powerful partnership.

**Next Steps:**
1. Review their profile and challenge details
2. Accept or decline the match invitation
3. If you accept, you'll be connected to start your journey together!

View Match Details: {match_url}

Ready to tackle your challenge with a wingman? Let's make it happen!

Best regards,
The WingmanMatch Team

---
If you no longer wish to receive match invitations, you can update your preferences here: {preferences_url}
                """.strip()
            },
            
            EmailTemplate.MATCH_ACCEPTED.value: {
                "subject": "🎉 Your WingmanMatch has been accepted!",
                "template": """
Hello {recipient_name},

Fantastic news! {partner_name} has accepted your wingman match invitation.

**Challenge:** {challenge_title}
**Partner:** {partner_name}
**Start Date:** {start_date}
**Duration:** {duration_days} days

You're now matched and ready to begin your journey together!

**What happens next:**
1. Access your shared challenge dashboard
2. Set up your first check-in session
3. Begin working together towards your goals

Start Your Challenge: {challenge_dashboard_url}

We're excited to see what you'll achieve together!

Best regards,
The WingmanMatch Team
                """.strip()
            },
            
            EmailTemplate.MATCH_DECLINED.value: {
                "subject": "WingmanMatch update - Let's find you another match",
                "template": """
Hello {recipient_name},

Thanks for considering the recent wingman match opportunity. While {partner_name} wasn't the right fit this time, we're committed to finding you the perfect wingman partner.

**Your challenge:** {challenge_title}

We're actively searching for other potential matches based on your preferences and goals. We'll notify you as soon as we find someone who could be a great fit.

**In the meantime:**
- Keep working on your challenge solo
- Update your preferences if needed
- Invite friends who might be interested in similar challenges

Update Preferences: {preferences_url}
Invite Friends: {invite_url}

Don't give up - the right wingman match is out there!

Best regards,
The WingmanMatch Team
                """.strip()
            },
            
            EmailTemplate.SESSION_REMINDER.value: {
                "subject": "⏰ WingmanMatch session reminder - {session_time}",
                "template": """
Hello {recipient_name},

This is a friendly reminder about your upcoming wingman session.

**Session Details:**
- **Partner:** {partner_name}
- **Time:** {session_time}
- **Challenge:** {challenge_title}
- **Session Focus:** {session_focus}

**Preparation checklist:**
□ Review your progress since last session
□ Prepare any questions or challenges you're facing
□ Have your action items from last time ready to discuss
□ Join the session 5 minutes early

Join Session: {session_url}

Looking forward to another productive session!

Best regards,
The WingmanMatch Team
                """.strip()
            },
            
            EmailTemplate.CHALLENGE_REMINDER.value: {
                "subject": "🚀 Challenge progress check-in - How are you doing?",
                "template": """
Hello {recipient_name},

Hope your challenge is going well! It's been {days_since_start} days since you started "{challenge_title}" with {partner_name}.

**Challenge Progress:**
- **Days completed:** {days_completed} of {total_days}
- **Progress:** {progress_percentage}%
- **Next milestone:** {next_milestone}

**Stay on track:**
- Schedule your next wingman session
- Update your progress in the dashboard
- Celebrate small wins along the way

Update Progress: {progress_url}
Schedule Session: {scheduling_url}

You've got this! Keep pushing forward.

Best regards,
The WingmanMatch Team
                """.strip()
            },
            
            EmailTemplate.WELCOME_ONBOARDING.value: {
                "subject": "🎯 Welcome to WingmanMatch - Let's find your perfect wingman!",
                "template": """
Hello {recipient_name},

Welcome to WingmanMatch! We're excited to help you achieve your goals with the perfect wingman partner.

**Your journey starts here:**
1. **Complete your profile** - Help us understand your goals and preferences
2. **Define your challenge** - What do you want to accomplish?
3. **Get matched** - We'll find you a compatible wingman partner
4. **Start achieving** - Work together towards your goals!

**Next steps:**
Complete Your Profile: {profile_url}
Browse Challenge Ideas: {challenges_url}
Learn How It Works: {how_it_works_url}

**Pro tip:** The more detailed your profile and challenge description, the better we can match you with the right wingman!

Questions? Reply to this email or check out our FAQ: {faq_url}

Let's make your goals a reality!

Best regards,
The WingmanMatch Team
                """.strip()
            },
            
            EmailTemplate.MATCH_COMPLETION.value: {
                "subject": "🏆 Congratulations! You've completed your WingmanMatch challenge",
                "template": """
Hello {recipient_name},

Congratulations! You and {partner_name} have successfully completed your "{challenge_title}" challenge!

**Challenge Summary:**
- **Duration:** {duration_days} days
- **Goal achieved:** {goal_achieved}
- **Sessions completed:** {sessions_completed}
- **Final progress:** {final_progress}%

**Celebrate your success:**
□ Share your achievement on social media
□ Write a review of your wingman experience
□ Consider starting a new challenge

**What's next?**
- Start a new challenge with a different wingman
- Continue working with {partner_name} on a new goal
- Become a wingman for someone else's challenge

Share Your Success: {share_url}
Start New Challenge: {new_challenge_url}
Leave Feedback: {feedback_url}

We're proud of what you've accomplished together!

Best regards,
The WingmanMatch Team
                """.strip()
            },
            
            EmailTemplate.SYSTEM_NOTIFICATION.value: {
                "subject": "WingmanMatch System Notification",
                "template": """
Hello {recipient_name},

{notification_message}

{action_required}

Best regards,
The WingmanMatch Team
                """.strip()
            }
        }
    
    def _format_email_content(self, template: EmailTemplate, variables: Dict[str, Any]) -> Dict[str, str]:
        """Format email content with provided variables"""
        templates = self._get_email_templates()
        template_data = templates.get(template.value)
        
        if not template_data:
            raise EmailServiceError(f"Template not found: {template.value}")
        
        try:
            subject = template_data["subject"].format(**variables)
            content = template_data["template"].format(**variables)
            
            return {
                "subject": subject,
                "content": content
            }
        except KeyError as e:
            raise EmailServiceError(f"Missing template variable: {e}")
    
    @with_email_retry()
    async def send_email(
        self,
        to_email: str,
        template: EmailTemplate,
        variables: Dict[str, Any],
        priority: EmailPriority = EmailPriority.NORMAL,
        from_email: str = "noreply@wingmanmatch.com",
        from_name: str = "WingmanMatch",
        reply_to: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        Send an email using the specified template.
        
        Args:
            to_email: Recipient email address
            template: Email template to use
            variables: Variables to substitute in template
            priority: Email priority level
            from_email: Sender email address
            from_name: Sender name
            reply_to: Reply-to email address
            tags: Email tags for tracking
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if self._fallback_mode:
            return await self._handle_fallback_email(
                to_email, template, variables, priority
            )
        
        try:
            # Format email content
            formatted_content = self._format_email_content(template, variables)
            
            # Prepare email data
            email_data = {
                "from": f"{from_name} <{from_email}>",
                "to": [to_email],
                "subject": formatted_content["subject"],
                "text": formatted_content["content"],
                "reply_to": reply_to or "support@wingmanmatch.com",
                "tags": tags or [template.value, priority.value]
            }
            
            # Send email via Resend
            response = resend.Emails.send(email_data)
            
            if response and hasattr(response, 'id'):
                logger.info(f"Email sent successfully: {response.id} to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email to {to_email}: No response ID")
                return False
                
        except ResendError as e:
            logger.error(f"Resend API error sending email to {to_email}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending email to {to_email}: {str(e)}")
            raise
    
    async def _handle_fallback_email(
        self,
        to_email: str,
        template: EmailTemplate,
        variables: Dict[str, Any],
        priority: EmailPriority
    ) -> bool:
        """Handle email sending in fallback mode (when Resend is unavailable)"""
        try:
            formatted_content = self._format_email_content(template, variables)
            
            # Store email for later sending or logging
            email_record = {
                "to_email": to_email,
                "template": template.value,
                "subject": formatted_content["subject"],
                "content": formatted_content["content"],
                "priority": priority.value,
                "timestamp": datetime.now().isoformat(),
                "sent": False
            }
            
            self._pending_emails.append(email_record)
            
            # Log email content for debugging (in development only)
            if Config.DEVELOPMENT_MODE:
                logger.info(f"FALLBACK EMAIL to {to_email}:")
                logger.info(f"Subject: {formatted_content['subject']}")
                logger.info(f"Content:\n{formatted_content['content']}")
            
            logger.warning(f"Email queued in fallback mode: {template.value} to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error in fallback email handling: {str(e)}")
            return False
    
    async def send_match_invitation(
        self,
        to_email: str,
        recipient_name: str,
        wingman_name: str,
        challenge_title: str,
        challenge_type: str,
        duration_days: int,
        match_url: str,
        preferences_url: str
    ) -> bool:
        """Send match invitation email"""
        variables = {
            "recipient_name": recipient_name,
            "wingman_name": wingman_name,
            "challenge_title": challenge_title,
            "challenge_type": challenge_type,
            "duration_days": duration_days,
            "match_url": match_url,
            "preferences_url": preferences_url
        }
        
        return await self.send_email(
            to_email,
            EmailTemplate.MATCH_INVITATION,
            variables,
            EmailPriority.HIGH,
            tags=["match", "invitation"]
        )
    
    async def send_match_accepted(
        self,
        to_email: str,
        recipient_name: str,
        partner_name: str,
        challenge_title: str,
        start_date: str,
        duration_days: int,
        challenge_dashboard_url: str
    ) -> bool:
        """Send match accepted notification email"""
        variables = {
            "recipient_name": recipient_name,
            "partner_name": partner_name,
            "challenge_title": challenge_title,
            "start_date": start_date,
            "duration_days": duration_days,
            "challenge_dashboard_url": challenge_dashboard_url
        }
        
        return await self.send_email(
            to_email,
            EmailTemplate.MATCH_ACCEPTED,
            variables,
            EmailPriority.HIGH,
            tags=["match", "accepted"]
        )
    
    async def send_match_declined(
        self,
        to_email: str,
        recipient_name: str,
        partner_name: str,
        challenge_title: str,
        preferences_url: str,
        invite_url: str
    ) -> bool:
        """Send match declined notification email"""
        variables = {
            "recipient_name": recipient_name,
            "partner_name": partner_name,
            "challenge_title": challenge_title,
            "preferences_url": preferences_url,
            "invite_url": invite_url
        }
        
        return await self.send_email(
            to_email,
            EmailTemplate.MATCH_DECLINED,
            variables,
            EmailPriority.NORMAL,
            tags=["match", "declined"]
        )
    
    async def send_session_reminder(
        self,
        to_email: str,
        recipient_name: str,
        partner_name: str,
        session_time: str,
        challenge_title: str,
        session_focus: str,
        session_url: str
    ) -> bool:
        """Send session reminder email"""
        variables = {
            "recipient_name": recipient_name,
            "partner_name": partner_name,
            "session_time": session_time,
            "challenge_title": challenge_title,
            "session_focus": session_focus,
            "session_url": session_url
        }
        
        return await self.send_email(
            to_email,
            EmailTemplate.SESSION_REMINDER,
            variables,
            EmailPriority.HIGH,
            tags=["session", "reminder"]
        )
    
    async def send_welcome_email(
        self,
        to_email: str,
        recipient_name: str,
        profile_url: str,
        challenges_url: str,
        how_it_works_url: str,
        faq_url: str
    ) -> bool:
        """Send welcome onboarding email"""
        variables = {
            "recipient_name": recipient_name,
            "profile_url": profile_url,
            "challenges_url": challenges_url,
            "how_it_works_url": how_it_works_url,
            "faq_url": faq_url
        }
        
        return await self.send_email(
            to_email,
            EmailTemplate.WELCOME_ONBOARDING,
            variables,
            EmailPriority.NORMAL,
            tags=["welcome", "onboarding"]
        )
    
    async def send_bulk_emails(
        self,
        email_list: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """
        Send multiple emails concurrently.
        
        Args:
            email_list: List of email dictionaries with required fields
            max_concurrent: Maximum concurrent email sends
            
        Returns:
            Dict with success/failure statistics
        """
        results = {
            "total": len(email_list),
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def send_single_email(email_data):
            async with semaphore:
                try:
                    success = await self.send_email(**email_data)
                    if success:
                        results["successful"] += 1
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"Failed to send to {email_data.get('to_email', 'unknown')}")
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(f"Error sending to {email_data.get('to_email', 'unknown')}: {str(e)}")
        
        # Execute all email sends concurrently
        tasks = [send_single_email(email_data) for email_data in email_list]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info(f"Bulk email send completed: {results['successful']}/{results['total']} successful")
        return results
    
    def get_pending_emails(self) -> List[Dict[str, Any]]:
        """Get list of pending emails (fallback mode only)"""
        return self._pending_emails.copy()
    
    def clear_pending_emails(self) -> int:
        """Clear pending emails and return count of cleared emails"""
        count = len(self._pending_emails)
        self._pending_emails.clear()
        return count
    
    def is_available(self) -> bool:
        """Check if email service is available"""
        return self._is_available and not self._fallback_mode
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get email service status information"""
        return {
            "available": self._is_available,
            "fallback_mode": self._fallback_mode,
            "pending_emails_count": len(self._pending_emails),
            "resend_api_key_configured": bool(Config.RESEND_API_KEY),
            "templates_available": len(self._get_email_templates())
        }

# Global email service instance
email_service = EmailService()

# Convenience functions for common email operations

async def send_match_invitation_email(
    to_email: str,
    recipient_name: str,
    wingman_name: str,
    challenge_title: str,
    challenge_type: str,
    duration_days: int,
    match_url: str,
    preferences_url: str
) -> bool:
    """Convenience function to send match invitation email"""
    return await email_service.send_match_invitation(
        to_email, recipient_name, wingman_name, challenge_title,
        challenge_type, duration_days, match_url, preferences_url
    )

async def send_welcome_email(
    to_email: str,
    recipient_name: str,
    profile_url: str,
    challenges_url: str,
    how_it_works_url: str,
    faq_url: str
) -> bool:
    """Convenience function to send welcome email"""
    return await email_service.send_welcome_email(
        to_email, recipient_name, profile_url, challenges_url,
        how_it_works_url, faq_url
    )

async def get_email_service_health() -> Dict[str, Any]:
    """Get email service health status"""
    return email_service.get_service_status()