# Frontend Integration

## API Configuration

### Environment Variables
```bash
# .env.local
NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000  # Local
NEXT_PUBLIC_BACKEND_API_URL=https://fridays-at-four-c9c6b7a513be.herokuapp.com  # Prod
NEXT_PUBLIC_SUPABASE_URL=https://mxlmadjuauugvlukgrla.supabase.co  # Dev
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### API Client Setup
```typescript
// lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL;

export const apiClient = {
  async post<T>(endpoint: string, data: any): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return response.json();
  },
  
  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    return response.json();
  }
};
```

## Chat Integration

### Non-Streaming Chat
```typescript
// hooks/useChat.ts
import { useState } from 'react';
import { apiClient } from '@/lib/api';

interface ChatMessage {
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
}

interface ChatRequest {
  user_input: string;
  user_id: string;
  thread_id?: string;
}

interface ChatResponse {
  response: string;
  thread_id: string;
  user_id: string;
  processing_time?: number;
}

export const useChat = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [threadId, setThreadId] = useState<string>();

  const sendMessage = async (message: string, userId: string) => {
    setIsLoading(true);
    
    // Add user message immediately
    const userMessage: ChatMessage = {
      content: message,
      role: 'user',
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await apiClient.post<ChatResponse>('/query', {
        user_input: message,
        user_id: userId,
        thread_id: threadId
      });

      // Add assistant response
      const assistantMessage: ChatMessage = {
        content: response.response,
        role: 'assistant',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, assistantMessage]);
      setThreadId(response.thread_id);
      
    } catch (error) {
      console.error('Chat error:', error);
      // Add error message
      const errorMessage: ChatMessage = {
        content: 'Sorry, I encountered an error. Please try again.',
        role: 'assistant',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return { messages, sendMessage, isLoading };
};
```

### Streaming Chat
```typescript
// hooks/useStreamingChat.ts
import { useState, useCallback } from 'react';

export const useStreamingChat = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const sendStreamingMessage = useCallback(async (message: string, userId: string) => {
    setIsStreaming(true);
    
    // Add user message
    const userMessage: ChatMessage = {
      content: message,
      role: 'user',
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_API_URL}/query_stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_input: message,
          user_id: userId,
          thread_id: threadId
        })
      });

      if (!response.body) {
        throw new Error('ReadableStream not supported');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      // Create placeholder for assistant message
      const assistantMessageIndex = messages.length + 1;
      setMessages(prev => [...prev, {
        content: '',
        role: 'assistant',
        timestamp: new Date().toISOString()
      }]);

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          
          // Update assistant message with streaming content
          setMessages(prev => prev.map((msg, index) => 
            index === assistantMessageIndex 
              ? { ...msg, content: msg.content + chunk }
              : msg
          ));
        }
      } finally {
        reader.releaseLock();
      }
      
    } catch (error) {
      console.error('Streaming error:', error);
    } finally {
      setIsStreaming(false);
    }
  }, [threadId, messages.length]);

  return { messages, sendStreamingMessage, isStreaming };
};
```

## Project Overview Integration

### Fetch Project Data
```typescript
// hooks/useProject.ts
import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';

interface ProjectOverview {
  project_name: string;
  project_type: string;
  goals: string[];
  challenges: string[];
  success_metrics: Record<string, any>;
}

export const useProject = (userId: string) => {
  const [project, setProject] = useState<ProjectOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProject = async () => {
      try {
        const data = await apiClient.get<ProjectOverview>(`/project-overview/${userId}`);
        setProject(data);
      } catch (err) {
        if (err instanceof Error && err.message.includes('404')) {
          setProject(null); // No project yet
        } else {
          setError('Failed to fetch project data');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchProject();
  }, [userId]);

  return { project, loading, error };
};
```

### Create/Update Project
```typescript
// hooks/useProjectMutation.ts
import { useState } from 'react';
import { apiClient } from '@/lib/api';

export const useProjectMutation = () => {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const createProject = async (userId: string, projectData: Partial<ProjectOverview>) => {
    setIsSubmitting(true);
    try {
      const response = await apiClient.post<ProjectOverview>(
        `/project-overview/${userId}`,
        projectData
      );
      return response;
    } catch (error) {
      console.error('Project creation error:', error);
      throw error;
    } finally {
      setIsSubmitting(false);
    }
  };

  return { createProject, isSubmitting };
};
```

## Chat Components

### Chat Interface
```typescript
// components/ChatInterface.tsx
import React, { useState } from 'react';
import { useChat } from '@/hooks/useChat';

interface ChatInterfaceProps {
  userId: string;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ userId }) => {
  const [input, setInput] = useState('');
  const { messages, sendMessage, isLoading } = useChat();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    
    await sendMessage(input, userId);
    setInput('');
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-md p-3 rounded-lg ${
                message.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              {message.content}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 p-3 rounded-lg">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t">
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
          >
            {isLoading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </form>
    </div>
  );
};
```

### Project Dashboard
```typescript
// components/ProjectDashboard.tsx
import React from 'react';
import { useProject } from '@/hooks/useProject';

interface ProjectDashboardProps {
  userId: string;
}

export const ProjectDashboard: React.FC<ProjectDashboardProps> = ({ userId }) => {
  const { project, loading, error } = useProject(userId);

  if (loading) return <div>Loading project...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!project) return <div>No project found</div>;

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{project.project_name}</h1>
        <p className="text-gray-600">{project.project_type}</p>
      </div>

      <div>
        <h2 className="text-lg font-semibold mb-2">Goals</h2>
        <ul className="list-disc list-inside space-y-1">
          {project.goals.map((goal, index) => (
            <li key={index}>{goal}</li>
          ))}
        </ul>
      </div>

      <div>
        <h2 className="text-lg font-semibold mb-2">Challenges</h2>
        <ul className="list-disc list-inside space-y-1">
          {project.challenges.map((challenge, index) => (
            <li key={index}>{challenge}</li>
          ))}
        </ul>
      </div>

      <div>
        <h2 className="text-lg font-semibold mb-2">Success Metrics</h2>
        <pre className="bg-gray-100 p-3 rounded text-sm">
          {JSON.stringify(project.success_metrics, null, 2)}
        </pre>
      </div>
    </div>
  );
};
```

## Error Handling

### Global Error Boundary
```typescript
// components/ErrorBoundary.tsx
import React, { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 text-center">
          <h2 className="text-xl font-bold text-red-600">Something went wrong</h2>
          <p className="text-gray-600 mt-2">Please refresh the page and try again.</p>
          <button
            onClick={() => this.setState({ hasError: false })}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### API Error Handling
```typescript
// utils/errorHandling.ts
export const handleApiError = (error: any): string => {
  if (error.response?.status === 422) {
    return 'Invalid input. Please check your data and try again.';
  }
  if (error.response?.status === 500) {
    return 'Server error. Please try again later.';
  }
  if (error.message?.includes('Failed to fetch')) {
    return 'Network error. Please check your connection.';
  }
  return 'An unexpected error occurred. Please try again.';
};
```

## Authentication (Future)

### Supabase Auth Setup
```typescript
// lib/supabase.ts
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Auth hook
export const useAuth = () => {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        setUser(session?.user ?? null);
      }
    );

    return () => subscription.unsubscribe();
  }, []);

  return { user, signIn: supabase.auth.signIn, signOut: supabase.auth.signOut };
};
```

## Testing

### API Mocking
```typescript
// __tests__/mocks/api.ts
export const mockApiClient = {
  post: jest.fn(),
  get: jest.fn()
};

// Mock successful chat response
mockApiClient.post.mockResolvedValue({
  response: 'Hello! How can I help you today?',
  thread_id: 'mock-thread-id',
  user_id: 'mock-user-id'
});
```

### Component Testing
```typescript
// __tests__/components/ChatInterface.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChatInterface } from '@/components/ChatInterface';

jest.mock('@/hooks/useChat', () => ({
  useChat: () => ({
    messages: [],
    sendMessage: jest.fn(),
    isLoading: false
  })
}));

test('sends message on form submit', async () => {
  const mockSendMessage = jest.fn();
  
  render(<ChatInterface userId="test-user" />);
  
  const input = screen.getByPlaceholderText('Type your message...');
  const button = screen.getByText('Send');
  
  fireEvent.change(input, { target: { value: 'Hello' } });
  fireEvent.click(button);
  
  await waitFor(() => {
    expect(mockSendMessage).toHaveBeenCalledWith('Hello', 'test-user');
  });
});
```

## Repositories
- **Backend**: Current repo (FastAPI)
- **Frontend**: Separate Next.js repository
- **Integration**: REST API calls, no shared code

## API Integration

### Environment Setup (Frontend)
```bash
# Frontend .env.local
NEXT_PUBLIC_API_URL=https://fridays-at-four-c9c6b7a513be.herokuapp.com
NEXT_PUBLIC_SUPABASE_URL=https://wqfwsrpjzjqoqejlxhbx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here
```

### Chat Integration
```typescript
// Frontend chat implementation
const sendMessage = async (message: string, userId: string, threadId?: string) => {
  const response = await fetch(`${API_URL}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_input: message,
      user_id: userId,
      thread_id: threadId
    })
  });
  
  return response.json();
};
```

### Streaming Implementation
```typescript
// Server-sent events for streaming responses
const streamChat = async (message: string, userId: string) => {
  const response = await fetch(`${API_URL}/query_stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_input: message,
      user_id: userId
    })
  });

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    // Process streaming chunk
  }
};
```

## Authentication Flow

### Supabase Auth (Frontend)
```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
);

// Get user session
const { data: { session } } = await supabase.auth.getSession();
const userId = session?.user?.id;
```

### Backend Integration
Backend auto-creates profiles for new user IDs, no additional auth needed.

## CORS Configuration

Backend configured to allow:
- `app.fridaysatfour.co` (production frontend)
- `localhost:3000` (local development)

## Data Flow

```
Frontend State → API Request → Backend Processing → Database → API Response → Frontend Update
```

### Key Patterns
1. **User ID**: Extract from Supabase session, pass to all API calls
2. **Thread Management**: Frontend generates thread IDs for conversation grouping
3. **Error Handling**: Backend returns structured errors, frontend displays user-friendly messages
4. **Loading States**: Show loading during API calls, streaming for real-time responses

## Local Development

```bash
# Backend
source activate-env.sh && faf-dev

# Frontend (in separate repo)
npm run dev

# Integration test
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Hello", "user_id": "test-id"}'
```

## Production Deployment

- **Backend**: Manual Heroku deployment (`git push heroku main`)
- **Frontend**: Auto-deploy from main branch to Vercel
- **CORS**: Production frontend domain whitelisted in backend 