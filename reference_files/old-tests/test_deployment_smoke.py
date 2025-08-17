import logging
import os
import unittest
from unittest.mock import patch
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeploymentSmokeTest(unittest.TestCase):
    """
    Smoke test to verify the application is functioning correctly after deployment.
    This is specifically designed to be run after deployment to ensure the src/ restructuring
    hasn't broken core functionality.
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up the test client"""
        # We'll use environment variables that should be set in the workflow
        cls.slack_token = os.environ.get("SLACK_BOT_TOKEN")
        cls.test_channel = os.environ.get("SMOKE_TEST_CHANNEL")
        
        # Skip tests if credentials aren't available
        if not cls.slack_token or not cls.test_channel:
            raise unittest.SkipTest("Slack credentials not available for smoke test")
        
        cls.client = WebClient(token=cls.slack_token)
        cls.timestamp = None
    
    def test_01_slack_connection(self):
        """Test basic connectivity to Slack API"""
        try:
            response = self.client.api_test()
            self.assertTrue(response["ok"])
            logger.info("✅ Successfully connected to Slack API")
        except SlackApiError as e:
            self.fail(f"Failed to connect to Slack API: {e}")
    
    def test_02_send_message(self):
        """Test sending a message to the test channel"""
        try:
            test_message = "SMOKE_TEST: Verify deployment of src/ restructuring"
            result = self.client.chat_postMessage(
                channel=self.__class__.test_channel,
                text=test_message
            )
            self.__class__.timestamp = result["ts"]
            self.assertTrue(result["ok"])
            logger.info(f"✅ Successfully sent test message at {self.__class__.timestamp}")
        except SlackApiError as e:
            self.fail(f"Failed to send message: {e}")
    

    # Updated function (fixed):
    def test_03_bot_response(self):
        """Test that the bot responds to our message"""
        # Skip if we don't have a timestamp from the previous test
        if not self.__class__.timestamp:
            self.skipTest("No message timestamp available")
        
        try:
            # First verify bot is in the channel
            channel_info = self.client.conversations_info(channel=self.__class__.test_channel)
            channel_id = channel_info.get("channel", {}).get("id")
            
            # Get bot's user ID
            bot_info = self.client.auth_test()
            bot_id = bot_info.get("bot_id")
            bot_user_id = bot_info.get("user_id")
            
            if not bot_id or not bot_user_id:
                self.fail("Could not retrieve bot ID information")
                
            # Check if bot is in channel
            members = self.client.conversations_members(channel=channel_id)
            is_member = bot_user_id in members.get("members", [])
            
            if not is_member:
                self.fail(f"Bot is not a member of the test channel {self.__class__.test_channel}. Please add the bot to this channel.")
                
            # Wait for bot response (real wait, not mocked)
            import time
            retries = 3
            bot_responses = []
            
            # Retry a few times with short waits to give the bot time to respond
            for _ in range(retries):
                time.sleep(2)  # Wait 2 seconds
                
                # Get conversation history with real API call
                result = self.client.conversations_history(
                    channel=self.__class__.test_channel,
                    oldest=self.__class__.timestamp,
                    limit=5
                )
                
                # Check for bot responses
                bot_responses = [msg for msg in result.get("messages", []) 
                                if msg.get("bot_id") and float(msg["ts"]) > float(self.__class__.timestamp)]
                                
                if bot_responses:
                    break
                    
            # Log detailed information for debugging
            logger.info(f"Found {len(bot_responses)} bot responses after message timestamp {self.__class__.timestamp}")
            if bot_responses:
                logger.info(f"Bot response: {bot_responses[0].get('text', '')[:50]}...")
            
            self.assertTrue(len(bot_responses) > 0, "Bot did not respond to test message after multiple retries")
            logger.info("✅ Bot responded to test message")
        except SlackApiError as e:
            self.fail(f"Failed to check for bot response: {e.response['error']}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up by deleting the test message"""
        if cls.timestamp and cls.slack_token and cls.test_channel:
            try:
                cls.client.chat_delete(channel=cls.test_channel, ts=cls.timestamp)
                logger.info("Test message deleted")
            except SlackApiError:
                logger.warning("Could not delete test message")

if __name__ == "__main__":
    unittest.main() 