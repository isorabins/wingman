#!/usr/bin/env python3
"""
Tests for content summarization functionality
These tests verify the summarization components work correctly with mocked dependencies.
"""

import os
import sys

# Add project root to Python path for src imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta, date
from src.content_summarizer import ContentSummarizer, SummaryResult


@pytest.mark.asyncio
async def test_content_summarizer_ainvoke():
    """Test ContentSummarizer.ainvoke() method"""
    # Mock Claude client
    mock_claude_client = AsyncMock()
    mock_claude_client.send_message = AsyncMock(return_value="Test summary response")
    
    # Create summarizer and mock the client
    summarizer = ContentSummarizer()
    
    with patch.object(summarizer, '_get_claude_client', return_value=mock_claude_client):
        # Test content that should be processed
        test_content = "This is a test conversation about a project."
        
        result = await summarizer.ainvoke(test_content)
        
        # Verify response structure
        assert isinstance(result, dict)
        assert "final_summary" in result
        assert "summaries" in result
        
        # Verify Claude client was called
        mock_claude_client.send_message.assert_called()


@pytest.mark.asyncio
async def test_content_summarizer_error_handling():
    """Test ContentSummarizer error handling"""
    # Mock Claude client that raises an error
    mock_claude_client = AsyncMock()
    mock_claude_client.send_message = AsyncMock(side_effect=Exception("API Error"))
    
    # Create summarizer and mock the client
    summarizer = ContentSummarizer()
    
    with patch.object(summarizer, '_get_claude_client', return_value=mock_claude_client):
        test_content = "Test content"
        
        result = await summarizer.ainvoke(test_content)
        
        # Should return error response, not raise exception
        assert isinstance(result, dict)
        # The actual error message includes "Error reducing summaries" or "Error processing chunk"
        assert any(error_text in result["final_summary"] for error_text in [
            "Error reducing summaries",
            "Error processing chunk", 
            "Error in summarization"
        ])


def test_text_splitter():
    """Test SimpleTextSplitter functionality"""
    from src.content_summarizer import SimpleTextSplitter
    
    splitter = SimpleTextSplitter(chunk_size=50, chunk_overlap=10)
    
    # Test with short text (shouldn't split)
    short_text = "This is a short text."
    chunks = splitter.split_text(short_text)
    assert len(chunks) == 1
    assert chunks[0] == short_text
    
    # Test with longer text (should split)
    long_text = "This is a much longer text that should be split into multiple chunks because it exceeds the chunk size limit."
    chunks = splitter.split_text(long_text)
    assert len(chunks) > 1
    assert all(len(chunk) <= 60 for chunk in chunks)  # Allow some buffer for word boundaries


@pytest.mark.asyncio 
async def test_summary_result_structure():
    """Test SummaryResult dataclass"""
    # Test basic structure
    summary = SummaryResult(
        summary="Test summary",
        metadata={"test": "data"}
    )
    
    assert summary.summary == "Test summary"
    assert summary.metadata == {"test": "data"}
    assert summary.error is None
    
    # Test with error
    error_summary = SummaryResult(
        summary="",
        metadata={},
        error="Test error"
    )
    
    assert error_summary.error == "Test error"


@pytest.mark.asyncio
async def test_summarizer_initialization():
    """Test ContentSummarizer initialization"""
    # Test default initialization
    summarizer = ContentSummarizer()
    assert summarizer.model_name == "claude-3-5-sonnet-20241022"
    assert summarizer.claude_client is None  # Lazy loading
    
    # Test custom model
    custom_summarizer = ContentSummarizer(model="claude-3-sonnet-20240229")
    assert custom_summarizer.model_name == "claude-3-sonnet-20240229"


@pytest.mark.asyncio
async def test_chunking_with_sentences():
    """Test that text splitter properly handles sentence boundaries"""
    from src.content_summarizer import SimpleTextSplitter
    
    splitter = SimpleTextSplitter(chunk_size=100, chunk_overlap=20)
    
    text_with_sentences = """This is the first sentence. This is a second sentence that continues the thought.
    This is a third sentence. This fourth sentence should be in a different chunk because we're approaching the limit."""
    
    chunks = splitter.split_text(text_with_sentences)
    
    # Should have multiple chunks
    assert len(chunks) > 1
    
    # First chunk should end at a sentence boundary if possible
    if len(chunks) > 1:
        first_chunk = chunks[0]
        # Should end with sentence punctuation if splitting worked correctly
        assert any(first_chunk.rstrip().endswith(punct) for punct in ['.', '!', '?'])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
