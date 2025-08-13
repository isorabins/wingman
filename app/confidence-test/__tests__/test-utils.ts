import { vi } from 'vitest'

// Mock questions data for testing
export const mockQuestionsData = {
  questions: [
    {
      id: 1,
      question: "You see someone attractive at a coffee shop. What actually happens?",
      options: [
        { letter: "A", text: "I imagine 47 scenarios but never move", archetype: "analyzer" },
        { letter: "B", text: "I immediately go say hi before I lose nerve", archetype: "sprinter" },
        { letter: "C", text: "I wait for the 'perfect moment' that never comes", archetype: "ghost" },
        { letter: "D", text: "I try to make eye contact first", archetype: "naturalist" },
        { letter: "E", text: "I research their social media first", archetype: "scholar" },
        { letter: "F", text: "I worry about bothering them", archetype: "protector" }
      ]
    },
    {
      id: 2,
      question: "Your friend wants to set you up on a blind date. Your first reaction?",
      options: [
        { letter: "A", text: "I need to know everything about them first", archetype: "analyzer" },
        { letter: "B", text: "Yes! When and where?", archetype: "sprinter" },
        { letter: "C", text: "Maybe... but I'll probably cancel last minute", archetype: "ghost" },
        { letter: "D", text: "Let's see if we have natural chemistry", archetype: "naturalist" },
        { letter: "E", text: "What are their interests and values?", archetype: "scholar" },
        { letter: "F", text: "I hope they're not expecting too much", archetype: "protector" }
      ]
    }
    // Note: In real tests, we'd include all 12 questions, but abbreviated for space
  ],
  archetypes: {
    analyzer: {
      id: "analyzer",
      title: "🎯 THE ANALYZER",
      description: "You're thoughtful and strategic, but sometimes get stuck in your head.",
      experienceLevel: "Beginner",
      recommendedChallenges: ["Make eye contact with 5 people", "Say good morning to strangers"]
    },
    sprinter: {
      id: "sprinter",
      title: "⚡ THE SPRINTER",
      description: "You're action-oriented and brave, but sometimes move too fast.",
      experienceLevel: "Intermediate",
      recommendedChallenges: ["Practice active listening skills", "Ask follow-up questions"]
    },
    ghost: {
      id: "ghost",
      title: "👻 THE GHOST",
      description: "You're introverted and thoughtful, but fear vulnerability.",
      experienceLevel: "Beginner",
      recommendedChallenges: ["Make small talk with cashiers", "Attend one social event per week"]
    },
    naturalist: {
      id: "naturalist",
      title: "🌿 THE NATURALIST",
      description: "You're authentic and intuitive, but sometimes too passive.",
      experienceLevel: "Intermediate",
      recommendedChallenges: ["Initiate plans with someone", "Express your feelings clearly"]
    },
    scholar: {
      id: "scholar",
      title: "📚 THE SCHOLAR",
      description: "You're knowledge-focused, but sometimes over-intellectualize emotions.",
      experienceLevel: "Intermediate",
      recommendedChallenges: ["Share your feelings instead of thoughts", "Practice being present"]
    },
    protector: {
      id: "protector",
      title: "🛡️ THE PROTECTOR",
      description: "You're caring and relationship-focused, but sometimes neglect your own needs.",
      experienceLevel: "Beginner",
      recommendedChallenges: ["Express your own preferences", "Practice saying 'no'"]
    }
  }
}

// Create full 12-question mock for complete testing
export const fullMockQuestionsData = {
  questions: Array.from({ length: 12 }, (_, i) => ({
    id: i + 1,
    question: `Test question ${i + 1}?`,
    options: [
      { letter: "A", text: `Option A for question ${i + 1}`, archetype: "analyzer" },
      { letter: "B", text: `Option B for question ${i + 1}`, archetype: "sprinter" },
      { letter: "C", text: `Option C for question ${i + 1}`, archetype: "ghost" },
      { letter: "D", text: `Option D for question ${i + 1}`, archetype: "naturalist" },
      { letter: "E", text: `Option E for question ${i + 1}`, archetype: "scholar" },
      { letter: "F", text: `Option F for question ${i + 1}`, archetype: "protector" }
    ]
  })),
  archetypes: mockQuestionsData.archetypes
}

// Mock fetch responses
export const createMockFetch = (questionsData = mockQuestionsData) => {
  return vi.fn().mockImplementation((url: string) => {
    if (url.includes('questions.v1.json')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(questionsData),
      })
    }
    
    if (url.includes('/api/assessment/confidence')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ success: true }),
      })
    }
    
    return Promise.reject(new Error(`Unhandled URL: ${url}`))
  })
}

// Helper to answer all questions with specific archetype
export const answerAllQuestionsForArchetype = (archetype: string) => {
  return Array.from({ length: 12 }, () => {
    switch (archetype) {
      case 'analyzer': return 'A'
      case 'sprinter': return 'B' 
      case 'ghost': return 'C'
      case 'naturalist': return 'D'
      case 'scholar': return 'E'
      case 'protector': return 'F'
      default: return 'A'
    }
  })
}

// Helper to create test-specific analytics mock
export const createAnalyticsMock = () => {
  const mockGtag = vi.fn()
  Object.defineProperty(window, 'gtag', {
    value: mockGtag,
    writable: true,
  })
  return mockGtag
}

// Helper to wait for async operations
export const waitForNextTick = () => new Promise(resolve => setTimeout(resolve, 0))

// Custom render function with providers (if needed in future)
export const renderWithProviders = (ui: React.ReactElement) => {
  // For now, just use regular render, but this could be extended
  // to include theme providers, etc.
  return ui
}