import os
import sys

# Add project root to Python path for src imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# test_data/user_profiles.py

TEST_USER = {
    "id": "e4c932b7-1190-4463-818b-a804a644f01f",
    "slack_id": "U0873G42G7Q",
    "slack_email": "sarah.han@fridaysatfour.co",
    "first_name": "Sarah",
    "last_name": "Han",
    "timezone": "America/Los_Angeles",  # From the sarah_conversation test
    "created_at": "2024-12-18 04:28:49.182847+00"
}