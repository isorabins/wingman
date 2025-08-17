// Server-side session data fetching utility
// Uses fetch with cache tags for Next.js revalidation

export interface Challenge {
  id: string
  title: string
  description: string
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  points: number
}

export interface SessionParticipant {
  id: string
  name: string
  email: string
  challenge: Challenge
  confirmed: boolean
}

export interface SessionData {
  id: string
  match_id: string
  venue_name: string
  scheduled_time: string
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled'
  notes?: string
  participants: {
    user1: SessionParticipant
    user2: SessionParticipant
  }
  reputation_preview: {
    user1_delta: number
    user2_delta: number
  }
  created_at: string
}

/**
 * Fetch session data by ID with cache tags for revalidation
 * This is a server-side utility for Server Components
 */
export async function getSession(sessionId: string): Promise<SessionData | null> {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    
    // Fetch session data with cache tags for Next.js revalidation
    const response = await fetch(`${apiUrl}/api/session/${sessionId}`, {
      next: { 
        tags: ['session', `session:${sessionId}`],
        revalidate: 300 // 5 minutes
      },
      cache: 'force-cache',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (response.status === 404) {
      return null
    }

    if (!response.ok) {
      throw new Error(`Failed to fetch session: ${response.status} ${response.statusText}`)
    }

    const sessionData: SessionData = await response.json()
    return sessionData
    
  } catch (error) {
    console.error('Error fetching session:', error)
    // Return null for not found, throw for other errors
    if (error instanceof Error && error.message.includes('404')) {
      return null
    }
    throw error
  }
}

/**
 * Mock session data for development when backend isn't available
 */
export function getMockSessionData(sessionId: string): SessionData {
  return {
    id: sessionId,
    match_id: 'mock-match-123',
    venue_name: 'Starbucks Downtown',
    scheduled_time: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // Tomorrow
    status: 'scheduled',
    notes: 'Looking forward to practicing approach challenges together!',
    participants: {
      user1: {
        id: 'user-1',
        name: 'Alex',
        email: 'alex@example.com',
        challenge: {
          id: 'challenge-1',
          title: 'Start a Conversation',
          description: 'Approach someone new and start a genuine conversation',
          difficulty: 'beginner',
          points: 10
        },
        confirmed: false
      },
      user2: {
        id: 'user-2', 
        name: 'Jordan',
        email: 'jordan@example.com',
        challenge: {
          id: 'challenge-2',
          title: 'Ask Open Questions',
          description: 'Practice asking open-ended questions that lead to deeper conversation',
          difficulty: 'intermediate',
          points: 15
        },
        confirmed: false
      }
    },
    reputation_preview: {
      user1_delta: 10,
      user2_delta: 15
    },
    created_at: new Date().toISOString()
  }
}