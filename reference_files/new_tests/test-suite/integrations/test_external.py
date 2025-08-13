import sys
import os
# Add project root to Python path for src imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# Add test-suite directory to path for test_config
test_suite_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if test_suite_dir not in sys.path:
    sys.path.insert(0, test_suite_dir)

from openai import OpenAI
import pytest
from supabase import create_client, Client
from test_config import TestConfig as Config
from anthropic import Anthropic


@pytest.fixture(scope="module")
def supabase_client():
    client: Client = create_client(
        Config.TEST_DB_URL, Config.TEST_DB_KEY)
    return client

@pytest.fixture(scope="module")
def anthropic_client():
    """Fixture to initialize Anthropic API client."""
    return Anthropic(api_key=Config.ANTHROPIC_API_KEY)


@pytest.fixture(scope="module")
def openai_client():
    """Fixture to initialize OpenAI API client."""
    openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
    return openai_client


def test_supabase_connection(supabase_client):
    """Test if the Supabase connection is valid by performing a simple request."""
    try:
        response = supabase_client.table("teams").select("*").limit(1).execute()
        assert response.data is not None
    except Exception as e:
        pytest.fail(f"Connection to Supabase failed: {e}")


def test_anthropic_connection(anthropic_client):
    """Test if the Anthropic connection is valid by sending a simple request."""
    try:
        response = anthropic_client.messages.create(
            model=Config.ANTHROPIC_MODEL,
            max_tokens=1000,
            temperature=0,
            messages=[{
                "role": "user",
                "content": "Hello!"
            }]
        )
        assert isinstance(response.content[0].text, str)
        assert len(response.content[0].text) > 0
        print(f"\nResponse: {response.content[0].text}")
    except Exception as e:
        pytest.fail(f"Connection to Anthropic failed: {e}")

def test_openai_connection(openai_client):
    """Test if the OpenAI connection is valid by sending a simple request."""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello!"}]
        )
        assert response and response.choices
    except Exception as e:
        pytest.fail(f"Connection to OpenAI failed: {e}")
