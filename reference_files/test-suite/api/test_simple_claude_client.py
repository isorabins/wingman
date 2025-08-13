#!/usr/bin/env python3
"""
Tests for Simple Claude Client - SDK-based implementation
Tests our actual simplified interface, not a complex HTTP client.
"""

import pytest
import os
import sys
from unittest.mock import patch, AsyncMock, MagicMock

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.claude_client_simple import SimpleClaudeClient, ClaudeCredentials
from anthropic import AsyncAnthropic


class TestClaudeCredentials:
    """Test Claude credentials handling"""
    
    def test_credentials_with_api_key(self):
        """Test credentials when API key is available"""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-test-key'}):
            creds = ClaudeCredentials()
            assert creds.api_key == 'sk-ant-test-key'
    
    def test_credentials_missing_api_key(self):
        """Test credentials when API key is missing"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY environment variable is required"):
                ClaudeCredentials()


class TestSimpleClaudeClient:
    """Test Simple Claude Client implementation"""
    
    @pytest.fixture
    def mock_credentials(self):
        """Mock credentials for testing"""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-test-key'}):
            return ClaudeCredentials()
    
    @pytest.fixture
    def client(self, mock_credentials):
        """Create client instance for testing"""
        return SimpleClaudeClient(mock_credentials)
    
    def test_client_initialization(self, mock_credentials):
        """Test that client initializes correctly"""
        client = SimpleClaudeClient(mock_credentials)
        assert client.credentials == mock_credentials
        assert isinstance(client.client, AsyncAnthropic)
    
    @pytest.mark.asyncio
    async def test_send_message_non_streaming(self, client):
        """Test non-streaming message sending"""
        # Mock the Anthropic client response
        mock_message = MagicMock()
        mock_message.content = [MagicMock()]
        mock_message.content[0].text = "Hello! I'm Claude."
        
        with patch.object(client.client.messages, 'create', new_callable=AsyncMock, return_value=mock_message) as mock_create:
            response = await client.send_message([
                {"role": "user", "content": "Hello"}
            ])
            
            assert response == "Hello! I'm Claude."
            mock_create.assert_called_once()
            
            # Verify the call arguments
            call_args = mock_create.call_args
            assert call_args[1]['messages'] == [{"role": "user", "content": "Hello"}]
            assert call_args[1]['model'] == "claude-sonnet-4-20250514"  # default
            assert call_args[1]['max_tokens'] == 4000  # default
            assert call_args[1]['temperature'] == 0.7  # default
    
    @pytest.mark.asyncio
    async def test_send_message_with_custom_parameters(self, client):
        """Test message sending with custom parameters"""
        mock_message = MagicMock()
        mock_message.content = [MagicMock()]
        mock_message.content[0].text = "Custom response"
        
        with patch.object(client.client.messages, 'create', new_callable=AsyncMock, return_value=mock_message) as mock_create:
            response = await client.send_message(
                messages=[{"role": "user", "content": "Test"}],
                model="claude-3-opus-20240229",
                max_tokens=100,
                temperature=0.3
            )
            
            assert response == "Custom response"
            
            # Verify custom parameters were passed
            call_args = mock_create.call_args
            assert call_args[1]['model'] == "claude-3-opus-20240229"
            assert call_args[1]['max_tokens'] == 100
            assert call_args[1]['temperature'] == 0.3
    
    @pytest.mark.asyncio
    async def test_send_message_streaming(self, client):
        """Test streaming message sending"""
        # Mock the streaming response
        async def mock_text_stream():
            yield "Hello "
            yield "from "
            yield "Claude!"
        
        mock_stream = AsyncMock()
        mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
        mock_stream.__aexit__ = AsyncMock(return_value=None)
        mock_stream.text_stream = mock_text_stream()
        
        with patch.object(client.client.messages, 'stream', return_value=mock_stream):
            # Get the async generator
            response_gen = await client.send_message(
                messages=[{"role": "user", "content": "Hello"}],
                stream=True
            )
            
            # Collect all chunks
            chunks = []
            async for chunk in response_gen:
                chunks.append(chunk)
            
            assert chunks == ["Hello ", "from ", "Claude!"]
    
    @pytest.mark.asyncio
    async def test_send_message_anthropic_error(self, client):
        """Test error handling when Anthropic SDK raises an exception"""
        # Use a generic exception since APIError requires complex setup
        with patch.object(client.client.messages, 'create', new_callable=AsyncMock, side_effect=Exception("API Error")):
            with pytest.raises(Exception, match="API Error"):
                await client.send_message([{"role": "user", "content": "test"}])
    
    @pytest.mark.asyncio
    async def test_send_message_streaming_error(self, client):
        """Test error handling in streaming mode"""
        with patch.object(client.client.messages, 'stream', side_effect=Exception("Streaming error")):
            with pytest.raises(Exception, match="Streaming error"):
                # Need to actually get the generator and try to iterate it
                response_gen = await client.send_message([{"role": "user", "content": "test"}], stream=True)
                # This should raise the exception when we try to iterate
                async for chunk in response_gen:
                    pass


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    @pytest.mark.asyncio
    async def test_create_claude_client(self):
        """Test create_claude_client convenience function"""
        from src.claude_client_simple import create_claude_client
        
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-test-key'}):
            client = await create_claude_client()
            assert isinstance(client, SimpleClaudeClient)
    
    @pytest.mark.asyncio
    async def test_send_claude_message(self):
        """Test send_claude_message convenience function"""
        from src.claude_client_simple import send_claude_message
        
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-test-key'}):
            with patch('src.claude_client_simple.SimpleClaudeClient') as MockClient:
                mock_instance = AsyncMock()
                mock_instance.send_message.return_value = "Test response"
                MockClient.return_value = mock_instance
                
                response = await send_claude_message([
                    {"role": "user", "content": "Hello"}
                ])
                
                assert response == "Test response"
                mock_instance.send_message.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 