/**
 * Test Data for WingmanMatch E2E Tests
 * 
 * Contains all test data, mock users, and validation scenarios
 * for the complete user journey testing
 */

export interface TestUserProfile {
  email: string
  bio: string
  city: string
  travelRadius: number
  coordinates?: {
    latitude: number
    longitude: number
  }
}

export interface TestMatch {
  matchId: string
  user1Id: string
  user2Id: string
  status: 'pending' | 'accepted' | 'declined'
}

// Test user profiles for different scenarios
export const TEST_USERS: Record<string, TestUserProfile> = {
  alex: {
    email: 'alex.wingman.test@example.com',
    bio: "Software engineer looking to build dating confidence. Love hiking, coffee shops, and meaningful conversations. Seeking a wingman buddy for practice and accountability.",
    city: 'San Francisco, CA',
    travelRadius: 25,
    coordinates: {
      latitude: 37.7749,
      longitude: -122.4194
    }
  },
  
  jordan: {
    email: 'jordan.wingman.test@example.com', 
    bio: "Graphic designer who wants to overcome approach anxiety. Interested in art galleries, bookstores, and authentic connections. Ready to support and be supported.",
    city: 'Oakland, CA',
    travelRadius: 30,
    coordinates: {
      latitude: 37.8044,
      longitude: -122.2711
    }
  },
  
  taylor: {
    email: 'taylor.wingman.test@example.com',
    bio: "Marketing professional seeking to build social confidence. Enjoy outdoor activities, music venues, and genuine conversations. Looking for mutual growth.",
    city: 'Berkeley, CA', 
    travelRadius: 20,
    coordinates: {
      latitude: 37.8715,
      longitude: -122.2730
    }
  },
  
  casey: {
    email: 'casey.wingman.test@example.com',
    bio: "Teacher working on dating confidence and social skills. Love museums, cafes, and thoughtful discussions. Seeking a supportive accountability partner.",
    city: 'San Jose, CA',
    travelRadius: 35,
    coordinates: {
      latitude: 37.3382,
      longitude: -121.8863
    }
  }
}

// Chat messages for testing
export const TEST_MESSAGES = {
  initial: "Hey! Ready for our wingman session?",
  response: "Absolutely! Where should we meet?",
  planning: "How about that coffee shop we discussed?",
  confirmation: "Perfect! See you there at 2pm",
  encouragement: "You've got this! Let's practice some conversation starters",
  followup: "That went great! Ready for the next challenge?"
}

// Venue suggestions for chat testing
export const VENUE_SUGGESTIONS = {
  coffeeShops: [
    "Blue Bottle Coffee",
    "Philz Coffee", 
    "Local coffee shop"
  ],
  bookstores: [
    "City Lights Bookstore",
    "Green Apple Books",
    "Independent bookstore"
  ],
  malls: [
    "Westfield San Francisco Centre",
    "Union Square",
    "Food court"
  ],
  parks: [
    "Golden Gate Park",
    "Dolores Park", 
    "Local park"
  ]
}

// Error scenarios for testing
export const ERROR_SCENARIOS = {
  invalidEmail: 'invalid-email-format',
  shortBio: 'Too short',
  longBio: 'a'.repeat(401), // Over 400 char limit
  bioWithPII: 'Call me at 555-123-4567 or email personal@test.com',
  invalidCity: '',
  longMessage: 'a'.repeat(2001), // Over 2000 char limit
  shortMessage: 'a', // Under 2 char minimum
  sqlInjection: "'; DROP TABLE users; --",
  xssAttempt: '<script>alert("xss")</script>'
}

// Validation patterns
export const VALIDATION_PATTERNS = {
  email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  bioMinLength: 10,
  bioMaxLength: 400,
  messageMinLength: 2,
  messageMaxLength: 2000,
  travelRadiusMin: 5,
  travelRadiusMax: 50
}

// API endpoints for testing
export const API_ENDPOINTS = {
  testAuth: '/auth/test-login',
  profileComplete: '/api/profile/complete',
  matchCandidates: '/api/matches/candidates',
  matchDistance: '/api/matches/distance',
  autoMatch: '/api/matches/auto',
  buddyRespond: '/api/buddy/respond',
  chatMessages: '/api/chat/messages',
  chatSend: '/api/chat/send'
}

// Frontend routes for testing
export const FRONTEND_ROUTES = {
  signin: '/auth/signin',
  profileSetup: '/profile-setup',
  findBuddy: '/find-buddy',
  matches: '/matches',
  buddyChat: '/buddy-chat'
}

// Test timeouts (in milliseconds)
export const TEST_TIMEOUTS = {
  pageLoad: 10000,
  apiResponse: 5000,
  userInteraction: 3000,
  networkRequest: 8000,
  messageDelivery: 10000, // For polling chat messages
  authFlow: 15000
}

// Performance thresholds
export const PERFORMANCE_THRESHOLDS = {
  pageLoadMax: 3000, // 3 seconds
  apiResponseMax: 1000, // 1 second
  formInteractionMax: 100, // 100ms
  chatMessageMax: 2000 // 2 seconds for message delivery
}

// Geographic test data
export const GEO_TEST_DATA = {
  sanFrancisco: {
    latitude: 37.7749,
    longitude: -122.4194,
    city: 'San Francisco, CA'
  },
  oakland: {
    latitude: 37.8044,
    longitude: -122.2711,
    city: 'Oakland, CA'
  },
  berkeley: {
    latitude: 37.8715,
    longitude: -122.2730,
    city: 'Berkeley, CA'
  },
  sanJose: {
    latitude: 37.3382,
    longitude: -121.8863,
    city: 'San Jose, CA'
  },
  // Invalid coordinates for edge case testing
  invalid: {
    latitude: 91.0, // Invalid latitude
    longitude: -181.0, // Invalid longitude
    city: 'Invalid Location'
  }
}

// Mock responses for API testing
export const MOCK_RESPONSES = {
  authSuccess: {
    success: true,
    user_id: 'test-user-123',
    access_token: 'mock-access-token',
    refresh_token: 'mock-refresh-token',
    session_expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
    email: 'test@example.com'
  },
  
  profileSuccess: {
    success: true,
    message: 'Profile completed successfully',
    ready_for_matching: true,
    user_id: 'test-user-123'
  },
  
  matchCandidates: {
    candidates: [
      {
        user_id: 'candidate-1',
        profile: {
          bio: 'Great wingman buddy candidate',
          distance_miles: 8.5
        }
      },
      {
        user_id: 'candidate-2', 
        profile: {
          bio: 'Another excellent candidate',
          distance_miles: 12.3
        }
      }
    ],
    total: 2
  },
  
  chatMessagesEmpty: {
    messages: [],
    has_more: false,
    cursor: null
  },
  
  chatSendSuccess: {
    success: true,
    message_id: 'msg-123',
    created_at: new Date().toISOString()
  }
}

// Test configuration
export const TEST_CONFIG = {
  baseUrl: process.env.TEST_BASE_URL || 'http://localhost:3000',
  apiUrl: process.env.TEST_API_URL || 'http://localhost:8000',
  headless: process.env.CI === 'true',
  slowMo: process.env.CI === 'true' ? 0 : 100,
  trace: process.env.CI === 'true' ? 'retain-on-failure' : 'on-first-retry',
  retries: 2,
  workers: process.env.CI === 'true' ? 1 : 2
}

// Utility functions for test data
export class TestDataHelper {
  static generateRandomEmail(): string {
    const timestamp = Date.now()
    const random = Math.random().toString(36).substring(7)
    return `test.${timestamp}.${random}@wingman.test`
  }
  
  static generateRandomUserId(): string {
    return `test-user-${Date.now()}-${Math.random().toString(36).substring(7)}`
  }
  
  static generateRandomMatchId(): string {
    return `test-match-${Date.now()}-${Math.random().toString(36).substring(7)}`
  }
  
  static getRandomTestUser(): TestUserProfile {
    const users = Object.values(TEST_USERS)
    const randomIndex = Math.floor(Math.random() * users.length)
    const baseUser = users[randomIndex]
    
    return {
      ...baseUser,
      email: this.generateRandomEmail()
    }
  }
  
  static createTestMatch(user1Id: string, user2Id: string): TestMatch {
    return {
      matchId: this.generateRandomMatchId(),
      user1Id,
      user2Id,
      status: 'pending'
    }
  }
  
  static isValidEmail(email: string): boolean {
    return VALIDATION_PATTERNS.email.test(email)
  }
  
  static isValidBio(bio: string): boolean {
    return bio.length >= VALIDATION_PATTERNS.bioMinLength && 
           bio.length <= VALIDATION_PATTERNS.bioMaxLength &&
           !this.containsPII(bio)
  }
  
  static containsPII(text: string): boolean {
    // Simple PII detection for testing
    const emailPattern = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/
    const phonePattern = /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/
    
    return emailPattern.test(text) || phonePattern.test(text)
  }
  
  static calculateDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
    // Haversine formula for distance calculation (in miles)
    const R = 3959 // Earth's radius in miles
    const dLat = (lat2 - lat1) * Math.PI / 180
    const dLon = (lon2 - lon1) * Math.PI / 180
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon/2) * Math.sin(dLon/2)
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
    return R * c
  }
}

export default {
  TEST_USERS,
  TEST_MESSAGES,
  VENUE_SUGGESTIONS,
  ERROR_SCENARIOS,
  VALIDATION_PATTERNS,
  API_ENDPOINTS,
  FRONTEND_ROUTES,
  TEST_TIMEOUTS,
  PERFORMANCE_THRESHOLDS,
  GEO_TEST_DATA,
  MOCK_RESPONSES,
  TEST_CONFIG,
  TestDataHelper
}