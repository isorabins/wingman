// Fixed streaming method for existing /query_stream endpoint
async sendMessageWithStreaming(
  userId: string, 
  threadId: string, 
  message: string,
  onChunk: (chunk: string) => void,
  onComplete: () => void,
  onError: (error: Error) => void
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE}/query_stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: message,        // Changed from 'message' to 'question'
        user_id: userId,
        user_timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        thread_id: threadId
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    if (!reader) {
      throw new Error('No response body reader available');
    }

    try {
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        // Decode the chunk and add to buffer
        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;
        
        // Process complete lines (ending with \n\n)
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer
        
        for (const line of lines) {
          if (line.trim()) {
            this.processStreamChunk(line.trim(), onChunk, onComplete, onError);
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  } catch (error) {
    onError(error as Error);
  }
}

private processStreamChunk(
  line: string, 
  onChunk: (chunk: string) => void,
  onComplete: () => void,
  onError: (error: Error) => void
): void {
  // Remove 'data: ' prefix if present
  const jsonStr = line.startsWith('data: ') ? line.slice(6) : line;
  
  try {
    const data = JSON.parse(jsonStr);
    
    if (data.chunk) {
      // Append text chunk to current message
      onChunk(data.chunk);
    } else if (data.done) {
      // Streaming complete
      onComplete();
    } else if (data.error) {
      // Error occurred
      onError(new Error(data.error));
    }
  } catch (error) {
    console.error('Error parsing stream chunk:', error, 'Line:', line);
    onError(new Error('Failed to parse stream response'));
  }
}

// Frontend React Component Streaming Fix
// This shows the proper pattern for accumulating streaming chunks

import React, { useState, useCallback } from 'react';

const ChatComponent = () => {
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState(''); // ← KEY: Accumulator state

  const sendMessageWithStreaming = useCallback(async (userMessage, userId, threadId) => {
    try {
      // Add user message immediately
      const userMsg = {
        id: Date.now(),
        role: 'user',
        content: userMessage,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, userMsg]);

      // Start streaming
      setIsStreaming(true);
      setStreamingMessage(''); // ← CRITICAL: Reset accumulator

      const response = await fetch(`${API_BASE}/query_stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: userMessage,
          user_id: userId,
          user_timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          thread_id: threadId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      if (!reader) {
        throw new Error('No response body reader available');
      }

      try {
        while (true) {
          const { done, value } = await reader.read();
          
          if (done) break;
          
          const chunk = decoder.decode(value, { stream: true });
          buffer += chunk;
          
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || '';
          
          for (const line of lines) {
            if (line.trim()) {
              processStreamChunk(line.trim());
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    } catch (error) {
      console.error('Streaming error:', error);
      setIsStreaming(false);
    }
  }, []);

  const processStreamChunk = useCallback((line) => {
    const jsonStr = line.startsWith('data: ') ? line.slice(6) : line;
    
    try {
      const data = JSON.parse(jsonStr);
      
      if (data.content) {
        // ← 🎯 KEY FIX: Accumulate chunks into streamingMessage state
        setStreamingMessage(prev => prev + data.content);
        console.log('Accumulated message:', streamingMessage + data.content);
      } 
      
      if (data.done) {
        // ← 🎯 KEY FIX: Move complete message to messages array
        setMessages(prev => [...prev, {
          id: Date.now(),
          role: 'assistant', 
          content: streamingMessage,
          timestamp: new Date().toISOString()
        }]);
        
        // Reset streaming state
        setIsStreaming(false);
        setStreamingMessage('');
      }
    } catch (error) {
      console.error('Error parsing stream chunk:', error, 'Line:', line);
    }
  }, [streamingMessage]); // ← IMPORTANT: Include streamingMessage in dependency

  return (
    <div className="chat-container">
      {/* Display message history */}
      {messages.map(message => (
        <div key={message.id} className={`message ${message.role}`}>
          {message.content}
        </div>
      ))}
      
      {/* ← 🎯 KEY FIX: Display streaming message while it builds */}
      {isStreaming && streamingMessage && (
        <div className="message assistant streaming">
          {streamingMessage}
          <span className="cursor">|</span>
        </div>
      )}
      
      {/* Chat input component */}
      <ChatInput onSendMessage={sendMessageWithStreaming} />
    </div>
  );
};

export default ChatComponent; 