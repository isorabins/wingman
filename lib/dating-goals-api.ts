// Dating Goals API Service
// Handles communication with dating goals backend endpoints

export interface DatingGoalsRequest {
  user_id: string;
  message: string;
  thread_id?: string;
}

export interface DatingGoalsResponse {
  success: boolean;
  message: string;
  thread_id: string;
  is_complete: boolean;
  topic_number?: number;
  completion_percentage: number;
}

export interface DatingGoalsData {
  success: boolean;
  user_id: string;
  goals?: string;
  preferred_venues: string[];
  comfort_level: 'low' | 'moderate' | 'high';
  goals_data: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface ConversationMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  topic_number?: number;
}

export class DatingGoalsApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string
  ) {
    super(message);
    this.name = 'DatingGoalsApiError';
  }
}

class DatingGoalsApi {
  private baseUrl: string;

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }

  /**
   * Send a message in the dating goals conversation
   */
  async sendMessage(request: DatingGoalsRequest): Promise<DatingGoalsResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/dating-goals`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new DatingGoalsApiError(
          error.detail || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          error.code
        );
      }

      const data = await response.json();
      return data;
    } catch (error) {
      if (error instanceof DatingGoalsApiError) {
        throw error;
      }
      
      // Network or other errors
      throw new DatingGoalsApiError(
        `Failed to send message: ${error instanceof Error ? error.message : 'Unknown error'}`,
        0,
        'NETWORK_ERROR'
      );
    }
  }

  /**
   * Retrieve completed dating goals data for a user
   */
  async getGoalsData(userId: string): Promise<DatingGoalsData> {
    try {
      const response = await fetch(`${this.baseUrl}/api/dating-goals/${userId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new DatingGoalsApiError(
          error.detail || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          error.code
        );
      }

      const data = await response.json();
      return data;
    } catch (error) {
      if (error instanceof DatingGoalsApiError) {
        throw error;
      }
      
      throw new DatingGoalsApiError(
        `Failed to retrieve goals data: ${error instanceof Error ? error.message : 'Unknown error'}`,
        0,
        'NETWORK_ERROR'
      );
    }
  }

  /**
   * Reset dating goals conversation for a user
   */
  async resetGoals(userId: string): Promise<{ success: boolean; message: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/dating-goals/${userId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new DatingGoalsApiError(
          error.detail || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          error.code
        );
      }

      const data = await response.json();
      return data;
    } catch (error) {
      if (error instanceof DatingGoalsApiError) {
        throw error;
      }
      
      throw new DatingGoalsApiError(
        `Failed to reset goals: ${error instanceof Error ? error.message : 'Unknown error'}`,
        0,
        'NETWORK_ERROR'
      );
    }
  }

  /**
   * Start a new dating goals conversation
   */
  async startConversation(userId: string): Promise<DatingGoalsResponse> {
    return this.sendMessage({
      user_id: userId,
      message: "I'd like to explore my dating goals and get some guidance from my coach.",
    });
  }

  /**
   * Continue an existing conversation with a user message
   */
  async continueConversation(
    userId: string,
    message: string,
    threadId: string
  ): Promise<DatingGoalsResponse> {
    return this.sendMessage({
      user_id: userId,
      message,
      thread_id: threadId,
    });
  }
}

// Export singleton instance
export const datingGoalsApi = new DatingGoalsApi();

// Utility functions for managing conversation state
export const createConversationMessage = (
  role: 'user' | 'assistant',
  content: string,
  topicNumber?: number
): ConversationMessage => ({
  id: crypto.randomUUID(),
  role,
  content,
  timestamp: new Date(),
  topic_number: topicNumber,
});

export const getTopicTitle = (topicNumber?: number): string => {
  const topics = {
    1: "Dating Goals & Objectives",
    2: "Preferred Venues & Settings", 
    3: "Comfort Level & Boundaries",
    4: "Wingman Integration Strategy"
  };
  
  return topics[topicNumber as keyof typeof topics] || "Getting Started";
};

export const formatCompletionPercentage = (percentage: number): string => {
  return `${Math.round(percentage)}%`;
};

export const isValidUserId = (userId: string): boolean => {
  // UUID v4 pattern validation
  const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  return uuidPattern.test(userId);
};