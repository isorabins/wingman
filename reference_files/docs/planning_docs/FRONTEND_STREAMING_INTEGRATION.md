# Frontend Streaming Integration Guide

## 🎯 Overview

Fridays at Four backend now uses **real Claude API streaming** instead of the previous LangChain implementation. This guide explains how to integrate the frontend with the new streaming endpoint.

## 🔄 Current vs New Implementation

### Current Frontend (Fake Streaming)
The frontend currently uses simulated streaming that takes a complete response and displays it character by character:

```javascript
// Current implementation in chat page
const simulateStreaming = (fullText: string) => {
  let currentIndex = 0;
  const interval = setInterval(() => {
    if (currentIndex < fullText.length) {
      setStreamingMessage(fullText.substring(0, currentIndex + 1));
      currentIndex++;
    } else {
      clearInterval(interval);
      setIsStreaming(false);
    }
  }, 50);
};
```

### New Backend (Real Streaming)
The backend now provides **true streaming responses** from Claude API, sending data as it's generated.

## 🚀 Backend Streaming Endpoint

### Endpoint Details
- **URL**: `/query_stream` (existing endpoint)
- **Method**: `POST`
- **Response Type**: `text/event-stream` with Server-Sent Events (SSE)
- **Content-Type**: `text/event-stream`

### Request Format
```javascript
POST /query_stream
Content-Type: application/json

{
  "question": "User's message",
  "user_id": "uuid-string",
  "user_timezone": "America/Los_Angeles",
  "thread_id": "optional-thread-id"
}
```

### Response Format
The endpoint streams data in real-time using Server-Sent Events format:

```
data: {"chunk": "Hello"}

data: {"chunk": " there"}

data: {"chunk": "!"}

data: {"done": true}

```

Each line contains:
- `data: ` prefix (SSE format)
- JSON object with `chunk` or `done` property
- `chunk` - Contains text chunks
- `done: true` - Indicates streaming complete

## 💻 Frontend Integration

### 1. Fetch API with ReadableStream

Replace the current fake streaming with real streaming using the Fetch API:

```javascript
async function sendMessageWithStreaming(message: string, userId: string, threadId: string) {
  const response = await fetch(`${API_BASE}/stream-chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
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
          processStreamChunk(line.trim());
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

function processStreamChunk(line: string) {
  // Remove 'data: ' prefix if present
  const jsonStr = line.startsWith('data: ') ? line.slice(6) : line;
  
  try {
    const data = JSON.parse(jsonStr);
    
    if (data.type === 'content') {
      // Append text to current message
      setStreamingMessage(prev => prev + data.text);
    } else if (data.type === 'done') {
      // Streaming complete
      setIsStreaming(false);
      // Save final message to conversation history
      saveFinalMessage();
    }
  } catch (error) {
    console.error('Error parsing stream chunk:', error, 'Line:', line);
  }
}
```

### 2. EventSource Alternative (Simpler but Less Control)

Alternatively, use EventSource for simpler implementation:

```javascript
async function sendMessageWithEventSource(message: string, userId: string, threadId: string) {
  // First, send the message to initiate streaming
  const initResponse = await fetch(`${API_BASE}/stream-chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      user_id: userId,
      user_timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      thread_id: threadId
    })
  });

  if (!initResponse.ok) {
    throw new Error(`HTTP error! status: ${initResponse.status}`);
  }

  // Create EventSource connection
  const eventSource = new EventSource(`${API_BASE}/stream-chat/${threadId}`);
  
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'content') {
      setStreamingMessage(prev => prev + data.text);
    } else if (data.type === 'done') {
      setIsStreaming(false);
      eventSource.close();
      saveFinalMessage();
    }
  };

  eventSource.onerror = (error) => {
    console.error('EventSource error:', error);
    eventSource.close();
    setIsStreaming(false);
  };
}
```

### 3. React Component Integration

Update your chat component to use real streaming:

```typescript
const ChatComponent: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentThreadId, setCurrentThreadId] = useState<string>();

  const handleSendMessage = async (content: string) => {
    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    };

    // Add user message immediately
    setMessages(prev => [...prev, userMessage]);
    
    // Start streaming AI response
    setIsStreaming(true);
    setStreamingMessage('');
    
    const threadId = currentThreadId || generateId();
    setCurrentThreadId(threadId);

    try {
      await sendMessageWithStreaming(content, userId, threadId);
    } catch (error) {
      console.error('Streaming error:', error);
      setIsStreaming(false);
      // Handle error - maybe show error message
    }
  };

  const saveFinalMessage = () => {
    if (streamingMessage.trim()) {
      const aiMessage: Message = {
        id: generateId(),
        role: 'assistant',
        content: streamingMessage,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, aiMessage]);
      setStreamingMessage('');
    }
  };

  return (
    <div>
      {/* Message history */}
      {messages.map(message => (
        <MessageBubble key={message.id} message={message} />
      ))}
      
      {/* Streaming message */}
      {isStreaming && (
        <MessageBubble 
          message={{
            id: 'streaming',
            role: 'assistant',
            content: streamingMessage,
            timestamp: new Date().toISOString()
          }}
          isStreaming={true}
        />
      )}
    </div>
  );
};
```

## ⚠️ Error Handling

### Common Scenarios

1. **Network Interruption**
```javascript
const handleStreamError = (error: Error) => {
  console.error('Streaming error:', error);
  setIsStreaming(false);
  
  // Show user-friendly error
  const errorMessage: Message = {
    id: generateId(),
    role: 'assistant',
    content: 'Sorry, there was a connection issue. Please try again.',
    timestamp: new Date().toISOString(),
    isError: true
  };
  setMessages(prev => [...prev, errorMessage]);
};
```

2. **Timeout Handling**
```javascript
const streamWithTimeout = async (message: string, timeoutMs = 60000) => {
  const timeoutPromise = new Promise((_, reject) => {
    setTimeout(() => reject(new Error('Streaming timeout')), timeoutMs);
  });

  try {
    await Promise.race([
      sendMessageWithStreaming(message, userId, threadId),
      timeoutPromise
    ]);
  } catch (error) {
    handleStreamError(error as Error);
  }
};
```

## 🔄 Migration Steps

### Step 1: Remove Fake Streaming
```javascript
// Remove this function
const simulateStreaming = (fullText: string) => { /* ... */ };
```

### Step 2: Add Real Streaming
```javascript
// Add the real streaming implementation from above
```

### Step 3: Update State Management
```javascript
// Ensure streaming message state is handled separately from regular messages
const [streamingMessage, setStreamingMessage] = useState('');
const [isStreaming, setIsStreaming] = useState(false);
```

### Step 4: Test Integration
1. Test with short messages
2. Test with long messages that stream for several seconds
3. Test network interruption scenarios
4. Test concurrent message sending

## 🧪 Testing Considerations

### Local Development
```javascript
// For local testing, ensure backend URL is correct
const API_BASE = process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://localhost:8000';
```

### Production Testing
1. Test on both dev and production environments
2. Monitor network tab for proper streaming format
3. Check for memory leaks with long conversations
4. Verify proper connection cleanup

## 📊 Performance Benefits

### Real Streaming Advantages:
1. **Immediate Response**: Text appears as soon as Claude generates it
2. **Better UX**: Users see progress instead of waiting for complete response
3. **Reduced Perceived Latency**: Streaming feels faster even with same total time
4. **Authentic Experience**: Matches modern AI chat interfaces

### Implementation Notes:
- **Memory Efficient**: No need to buffer complete response
- **Connection Management**: Proper cleanup prevents memory leaks
- **Error Recovery**: Better handling of network issues
- **Scalable**: Handles long responses without blocking

## 🔧 Debugging Tips

### Browser Network Tab
- Look for `/stream-chat` endpoint calls
- Response should show as "streaming" or "pending" while active
- Content-Type should be `text/plain; charset=utf-8`

### Console Logging
```javascript
// Add debug logging during development
console.log('Stream chunk received:', data);
console.log('Current streaming message length:', streamingMessage.length);
```

### Common Issues
1. **CORS**: Ensure streaming endpoint has proper CORS headers
2. **Buffering**: Some proxies may buffer responses - test direct connection
3. **Browser Compatibility**: Modern browsers required for ReadableStream
4. **Connection Limits**: Be aware of browser connection limits for concurrent streams

---

This integration will provide users with a much more responsive and modern chat experience, with text appearing in real-time as Claude generates it! 🚀 