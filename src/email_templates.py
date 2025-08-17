"""
Email service for WingmanMatch using Resend
Provides templated transactional emails for match notifications
"""

import logging
from typing import Dict, Any, Optional
import resend
from src.config import Config

logger = logging.getLogger(__name__)

class EmailService:
    """Resend email service for WingmanMatch match notifications"""
    
    def __init__(self):
        if Config.RESEND_API_KEY:
            resend.api_key = Config.RESEND_API_KEY
            self.enabled = True
            logger.info("Resend email service initialized")
        else:
            self.enabled = False
            logger.warning("RESEND_API_KEY not configured - email features disabled")
    
    async def send_match_invitation(self, to_email: str, inviter_name: str, venue_suggestion: str) -> bool:
        """Send match invitation email"""
        if not self.enabled:
            logger.warning("Email service disabled - match invitation not sent")
            return False
        
        try:
            email_data = {
                "from": "WingmanMatch <matches@wingmanmatch.com>",
                "to": [to_email],
                "subject": f"🎯 New Wingman Match with {inviter_name}",
                "html": self._get_match_invitation_template(inviter_name, venue_suggestion)
            }
            
            response = resend.Emails.send(email_data)
            logger.info(f"Match invitation sent to {to_email}: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send match invitation to {to_email}: {e}")
            return False
    
    async def send_match_acceptance(self, to_email: str, accepter_name: str, venue_name: str, scheduled_time: str) -> bool:
        """Send match acceptance notification"""
        if not self.enabled:
            logger.warning("Email service disabled - match acceptance not sent")
            return False
        
        try:
            email_data = {
                "from": "WingmanMatch <matches@wingmanmatch.com>",
                "to": [to_email],
                "subject": f"🎉 {accepter_name} accepted your wingman match!",
                "html": self._get_match_acceptance_template(accepter_name, venue_name, scheduled_time)
            }
            
            response = resend.Emails.send(email_data)
            logger.info(f"Match acceptance sent to {to_email}: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send match acceptance to {to_email}: {e}")
            return False
    
    async def send_match_decline(self, to_email: str, decliner_name: str) -> bool:
        """Send match decline notification"""
        if not self.enabled:
            logger.warning("Email service disabled - match decline not sent")
            return False
        
        try:
            email_data = {
                "from": "WingmanMatch <matches@wingmanmatch.com>",
                "to": [to_email],
                "subject": "Match update from WingmanMatch",
                "html": self._get_match_decline_template(decliner_name)
            }
            
            response = resend.Emails.send(email_data)
            logger.info(f"Match decline sent to {to_email}: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send match decline to {to_email}: {e}")
            return False
    
    async def send_session_reminder(self, to_email: str, partner_name: str, venue_name: str, scheduled_time: str) -> bool:
        """Send session reminder email"""
        if not self.enabled:
            logger.warning("Email service disabled - session reminder not sent")
            return False
        
        try:
            email_data = {
                "from": "WingmanMatch <matches@wingmanmatch.com>",
                "to": [to_email],
                "subject": f"⏰ Wingman session with {partner_name} tomorrow",
                "html": self._get_session_reminder_template(partner_name, venue_name, scheduled_time)
            }
            
            response = resend.Emails.send(email_data)
            logger.info(f"Session reminder sent to {to_email}: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send session reminder to {to_email}: {e}")
            return False
    
    def _get_match_invitation_template(self, inviter_name: str, venue_suggestion: str) -> str:
        """HTML template for match invitation"""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; color: white; text-align: center;">
                <h1 style="margin: 0; font-size: 28px;">🎯 New Wingman Match!</h1>
                <p style="margin: 10px 0 0 0; font-size: 18px;">You've been matched with {inviter_name}</p>
            </div>
            
            <div style="padding: 30px 20px;">
                <p style="font-size: 16px; line-height: 1.6;">
                    Hey there! Great news - <strong>{inviter_name}</strong> wants to be your wingman for some confidence building practice.
                </p>
                
                <p style="font-size: 16px; line-height: 1.6;">
                    They suggested meeting at: <strong>{venue_suggestion}</strong>
                </p>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #333; margin-top: 0;">How it works:</h3>
                    <ul style="color: #666; line-height: 1.6;">
                        <li>Meet up at a public venue</li>
                        <li>Each choose your own challenge level</li>
                        <li>Support each other through practice approaches</li>
                        <li>Confirm each other's completion</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://wingmanmatch.com/respond-to-match" 
                       style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block;">
                        Respond to Match
                    </a>
                </div>
            </div>
            
            <div style="text-align: center; color: #666; font-size: 14px; border-top: 1px solid #eee; padding-top: 20px;">
                <p>WingmanMatch - Building confidence through buddy accountability</p>
            </div>
        </body>
        </html>
        """
    
    def _get_match_acceptance_template(self, accepter_name: str, venue_name: str, scheduled_time: str) -> str:
        """HTML template for match acceptance"""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 30px; border-radius: 10px; color: white; text-align: center;">
                <h1 style="margin: 0; font-size: 28px;">🎉 Match Accepted!</h1>
                <p style="margin: 10px 0 0 0; font-size: 18px;">{accepter_name} is ready to be your wingman</p>
            </div>
            
            <div style="padding: 30px 20px;">
                <p style="font-size: 16px; line-height: 1.6;">
                    Awesome! <strong>{accepter_name}</strong> has accepted your wingman match request.
                </p>
                
                <div style="background: #e8f5e8; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4caf50;">
                    <h3 style="color: #2e7d32; margin-top: 0;">Session Details:</h3>
                    <p style="margin: 5px 0;"><strong>Venue:</strong> {venue_name}</p>
                    <p style="margin: 5px 0;"><strong>Time:</strong> {scheduled_time}</p>
                </div>
                
                <p style="font-size: 16px; line-height: 1.6;">
                    Remember to choose your challenge level when you meet up. You can each pick different difficulty levels - that's totally fine!
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://wingmanmatch.com/session-details" 
                       style="background: #4facfe; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block;">
                        View Session Details
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_match_decline_template(self, decliner_name: str) -> str:
        """HTML template for match decline"""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #f5f5f5; padding: 30px; border-radius: 10px; text-align: center;">
                <h1 style="margin: 0; font-size: 24px; color: #666;">Match Update</h1>
            </div>
            
            <div style="padding: 30px 20px;">
                <p style="font-size: 16px; line-height: 1.6;">
                    {decliner_name} isn't available for a wingman session right now, but don't worry - we'll find you another great match soon!
                </p>
                
                <div style="background: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107;">
                    <p style="margin: 0; color: #856404;">
                        <strong>Next steps:</strong> We're already looking for your next wingman match. You'll hear from us within 24 hours with a new potential buddy.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_session_reminder_template(self, partner_name: str, venue_name: str, scheduled_time: str) -> str:
        """HTML template for session reminder"""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #ff9a56 0%, #ff6a00 100%); padding: 30px; border-radius: 10px; color: white; text-align: center;">
                <h1 style="margin: 0; font-size: 28px;">⏰ Session Reminder</h1>
                <p style="margin: 10px 0 0 0; font-size: 18px;">Your wingman session is tomorrow!</p>
            </div>
            
            <div style="padding: 30px 20px;">
                <p style="font-size: 16px; line-height: 1.6;">
                    Just a friendly reminder about your upcoming wingman session with <strong>{partner_name}</strong>.
                </p>
                
                <div style="background: #fff8e1; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ff9800;">
                    <h3 style="color: #e65100; margin-top: 0;">Session Details:</h3>
                    <p style="margin: 5px 0;"><strong>Partner:</strong> {partner_name}</p>
                    <p style="margin: 5px 0;"><strong>Venue:</strong> {venue_name}</p>
                    <p style="margin: 5px 0;"><strong>Time:</strong> {scheduled_time}</p>
                </div>
                
                <p style="font-size: 16px; line-height: 1.6;">
                    Have your challenge ready to go, and remember - every approach is a win, regardless of outcome!
                </p>
            </div>
        </body>
        </html>
        """
    
    async def send_session_scheduled(self, to_email: str, user_name: str, venue_name: str, scheduled_time: str) -> bool:
        """Send session scheduled confirmation email"""
        if not self.enabled:
            logger.warning("Email service disabled - session scheduled notification not sent")
            return False
        
        try:
            email_data = {
                "from": "WingmanMatch <sessions@wingmanmatch.com>",
                "to": [to_email],
                "subject": f"🎯 Wingman Session Scheduled at {venue_name}",
                "html": self._get_session_scheduled_template(user_name, venue_name, scheduled_time)
            }
            
            response = resend.Emails.send(email_data)
            logger.info(f"Session scheduled notification sent to {to_email}: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send session scheduled notification to {to_email}: {e}")
            return False
    
    def _get_session_scheduled_template(self, user_name: str, venue_name: str, scheduled_time: str) -> str:
        """HTML template for session scheduled notification"""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; color: white; text-align: center;">
                <h1 style="margin: 0; font-size: 28px;">🎯 Session Scheduled!</h1>
                <p style="margin: 10px 0 0 0; font-size: 18px;">Your wingman session is confirmed</p>
            </div>
            
            <div style="padding: 30px 20px;">
                <p style="font-size: 16px; line-height: 1.6;">
                    Hi {user_name}! Great news - your wingman session has been scheduled and confirmed.
                </p>
                
                <div style="background: #e8f5e8; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4caf50;">
                    <h3 style="color: #2e7d32; margin-top: 0;">Session Details:</h3>
                    <p style="margin: 5px 0;"><strong>Venue:</strong> {venue_name}</p>
                    <p style="margin: 5px 0;"><strong>Time:</strong> {scheduled_time}</p>
                    <p style="margin: 5px 0;"><strong>Status:</strong> Confirmed ✅</p>
                </div>
                
                <div style="background: #f0f7ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #1976d2; margin-top: 0;">What to bring:</h3>
                    <ul style="color: #424242; line-height: 1.6; margin: 0; padding-left: 20px;">
                        <li>Your chosen challenge and confidence</li>
                        <li>Positive energy and supportive attitude</li>
                        <li>Willingness to step out of your comfort zone</li>
                        <li>Remember: every approach is practice, regardless of outcome!</li>
                    </ul>
                </div>
                
                <p style="font-size: 16px; line-height: 1.6; text-align: center; color: #666;">
                    Good luck with your session! You've got this. 💪
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://wingmanmatch.com/chat" 
                       style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block;">
                        Chat with your Wingman
                    </a>
                </div>
            </div>
        </body>
        </html>
        """

# Global email service instance
email_service = EmailService()