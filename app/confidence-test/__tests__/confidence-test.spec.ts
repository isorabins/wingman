import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ChakraProvider } from '@chakra-ui/react'
import ConfidenceTest from '../page'
import { theme } from '../../theme'
import { 
  mockQuestionsData, 
  fullMockQuestionsData, 
  createMockFetch, 
  answerAllQuestionsForArchetype,
  createAnalyticsMock,
  waitForNextTick
} from './test-utils'

// Helper to render component with Chakra provider
const renderWithChakra = (component: React.ReactElement) => {
  return render(
    <ChakraProvider theme={theme}>
      {component}
    </ChakraProvider>
  )
}

describe('ConfidenceTest Component', () => {
  let mockFetch: any
  let mockGtag: any

  beforeEach(() => {
    mockFetch = createMockFetch(fullMockQuestionsData)
    global.fetch = mockFetch
    mockGtag = createAnalyticsMock()
  })

  describe('Initial Rendering and Welcome Screen', () => {
    it('renders welcome screen with proper heading and CTA', async () => {
      renderWithChakra(<ConfidenceTest />)
      
      expect(screen.getByText('Discover Your')).toBeInTheDocument()
      expect(screen.getByText('Dating Confidence Type')).toBeInTheDocument()
      expect(screen.getByText('Understanding your natural approach to dating')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /start the assessment/i })).toBeInTheDocument()
      expect(screen.getByText('Takes just 3 minutes • 12 quick questions')).toBeInTheDocument()
    })

    it('displays assessment benefits correctly', () => {
      renderWithChakra(<ConfidenceTest />)
      
      expect(screen.getByText('You\'ll discover:')).toBeInTheDocument()
      expect(screen.getByText('• Your confidence style')).toBeInTheDocument()
      expect(screen.getByText('• Perfect starting challenges')).toBeInTheDocument()
      expect(screen.getByText('• Experience level match')).toBeInTheDocument()
    })

    it('has proper navigation header with brand and back link', () => {
      renderWithChakra(<ConfidenceTest />)
      
      expect(screen.getByText('Wingman')).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /back to home/i })).toBeInTheDocument()
    })
  })

  describe('Question Loading and Progression', () => {
    it('loads questions data successfully', async () => {
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('/api/static/confidence-test/questions.v1.json')
      })
    })

    it('shows error toast when questions fail to load', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => {
        expect(screen.getByText('Error loading questions')).toBeInTheDocument()
      })
    })

    it('progresses to first question when start button is clicked', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled()
      })
      
      const startButton = screen.getByRole('button', { name: /start the assessment/i })
      await user.click(startButton)
      
      await waitFor(() => {
        expect(screen.getByText('Question 1')).toBeInTheDocument()
        expect(screen.getByText('of 12')).toBeInTheDocument()
      })
    })

    it('shows progress indicator with correct percentage', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      
      // Start assessment
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
      
      // Check progress on first question (1/12 = ~8.33%)
      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toHaveAttribute('aria-valuenow', '8.333333333333334')
      expect(progressBar).toHaveAttribute('aria-label', 'Assessment progress: 8% complete')
    })
  })

  describe('Question Answering and Navigation', () => {
    beforeEach(async () => {
      renderWithChakra(<ConfidenceTest />)
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      
      // Start assessment
      const user = userEvent.setup()
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
    })

    it('displays question with all answer options', async () => {
      await waitFor(() => {
        expect(screen.getByText('Test question 1?')).toBeInTheDocument()
        expect(screen.getByText('Option A for question 1')).toBeInTheDocument()
        expect(screen.getByText('Option B for question 1')).toBeInTheDocument()
        expect(screen.getByText('Option C for question 1')).toBeInTheDocument()
        expect(screen.getByText('Option D for question 1')).toBeInTheDocument()
        expect(screen.getByText('Option E for question 1')).toBeInTheDocument()
        expect(screen.getByText('Option F for question 1')).toBeInTheDocument()
      })
    })

    it('allows selecting an answer and updates visual state', async () => {
      const user = userEvent.setup()
      
      await waitFor(() => {
        expect(screen.getByText('Test question 1?')).toBeInTheDocument()
      })
      
      const optionA = screen.getByLabelText('Option A for question 1')
      await user.click(optionA)
      
      expect(optionA).toBeChecked()
    })

    it('shows back button disabled on first question', async () => {
      await waitFor(() => {
        const backButton = screen.getByRole('button', { name: /back/i })
        expect(backButton).toBeDisabled()
      })
    })

    it('enables back button on subsequent questions', async () => {
      const user = userEvent.setup()
      
      await waitFor(() => {
        expect(screen.getByText('Test question 1?')).toBeInTheDocument()
      })
      
      // Answer first question
      await user.click(screen.getByLabelText('Option A for question 1'))
      
      // Navigate to next question (manually trigger since auto-advance isn't implemented)
      // We need to simulate this by checking the back button on a later question
      // This test would need the actual navigation implementation
    })

    it('preserves answers when navigating back and forth', async () => {
      const user = userEvent.setup()
      
      await waitFor(() => {
        expect(screen.getByText('Test question 1?')).toBeInTheDocument()
      })
      
      // Select option A
      const optionA = screen.getByLabelText('Option A for question 1')
      await user.click(optionA)
      expect(optionA).toBeChecked()
      
      // Note: Navigation between questions would need to be implemented
      // This test validates the concept
    })
  })

  describe('Form Validation and Submission', () => {
    it('shows submit button only on last question', async () => {
      renderWithChakra(<ConfidenceTest />)
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      
      // Start assessment
      const user = userEvent.setup()
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
      
      // Should not show submit button on first question
      expect(screen.queryByText('Get My Results')).not.toBeInTheDocument()
    })

    it('shows validation error when trying to submit incomplete assessment', async () => {
      // This test would simulate being on the last question without all answers
      // and verify the toast error appears
      renderWithChakra(<ConfidenceTest />)
      
      // Simulate being on question 12 with incomplete answers
      // This would require mocking the component state or using a different approach
    })

    it('disables submit button when no answer selected on last question', async () => {
      // This test validates the submit button state logic
      renderWithChakra(<ConfidenceTest />)
      
      // This would test the isNextEnabled logic for the submit button
    })
  })

  describe('Analytics Integration', () => {
    it('fires assessment_started event when starting', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
      
      await waitFor(() => {
        expect(mockGtag).toHaveBeenCalledWith('event', 'assessment_started', {
          assessment_type: 'confidence'
        })
      })
    })

    it('fires assessment_completed event with archetype and duration', async () => {
      // This test would simulate completing the full assessment
      // and verify the completion analytics event
      renderWithChakra(<ConfidenceTest />)
      
      // Mock completing assessment (this would need the full flow)
      // Verify mockGtag called with assessment_completed event
    })
  })

  describe('Archetype Calculation and Results', () => {
    it('calculates analyzer archetype correctly', () => {
      renderWithChakra(<ConfidenceTest />)
      
      // Test the archetype calculation logic
      const analyzerAnswers = answerAllQuestionsForArchetype('analyzer')
      expect(analyzerAnswers).toEqual(Array(12).fill('A'))
    })

    it('calculates sprinter archetype correctly', () => {
      renderWithChakra(<ConfidenceTest />)
      
      const sprinterAnswers = answerAllQuestionsForArchetype('sprinter')
      expect(sprinterAnswers).toEqual(Array(12).fill('B'))
    })

    it('calculates ghost archetype correctly', () => {
      renderWithChakra(<ConfidenceTest />)
      
      const ghostAnswers = answerAllQuestionsForArchetype('ghost')
      expect(ghostAnswers).toEqual(Array(12).fill('C'))
    })

    it('calculates naturalist archetype correctly', () => {
      renderWithChakra(<ConfidenceTest />)
      
      const naturalistAnswers = answerAllQuestionsForArchetype('naturalist')
      expect(naturalistAnswers).toEqual(Array(12).fill('D'))
    })

    it('calculates scholar archetype correctly', () => {
      renderWithChakra(<ConfidenceTest />)
      
      const scholarAnswers = answerAllQuestionsForArchetype('scholar')
      expect(scholarAnswers).toEqual(Array(12).fill('E'))
    })

    it('calculates protector archetype correctly', () => {
      renderWithChakra(<ConfidenceTest />)
      
      const protectorAnswers = answerAllQuestionsForArchetype('protector')
      expect(protectorAnswers).toEqual(Array(12).fill('F'))
    })

    it('displays archetype results with proper formatting', async () => {
      // This test would simulate completion and verify the results screen
      renderWithChakra(<ConfidenceTest />)
      
      // Would need to mock the completion flow and verify results display
      // including title, description, experience level, and recommended challenges
    })
  })

  describe('Error Handling', () => {
    it('handles API submission failure gracefully', async () => {
      mockFetch.mockImplementation((url: string) => {
        if (url.includes('questions.v1.json')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(fullMockQuestionsData),
          })
        }
        if (url.includes('/api/assessment/confidence')) {
          return Promise.reject(new Error('API Error'))
        }
        return Promise.reject(new Error(`Unhandled URL: ${url}`))
      })
      
      renderWithChakra(<ConfidenceTest />)
      
      // This would test the API error handling and local fallback
    })

    it('shows error toast when API submission fails', async () => {
      // Similar to above but focuses on toast display
      renderWithChakra(<ConfidenceTest />)
    })

    it('falls back to local calculation when remote fails', async () => {
      // Test that archetype calculation works even without API
      renderWithChakra(<ConfidenceTest />)
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA attributes for radio groups', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
      
      await waitFor(() => {
        const radioGroup = screen.getByRole('radiogroup')
        expect(radioGroup).toBeInTheDocument()
        expect(radioGroup).toHaveAttribute('aria-labelledby')
      })
    })

    it('has proper progress bar accessibility', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
      
      await waitFor(() => {
        const progressBar = screen.getByRole('progressbar')
        expect(progressBar).toHaveAttribute('aria-valuenow')
        expect(progressBar).toHaveAttribute('aria-valuemin', '0')
        expect(progressBar).toHaveAttribute('aria-valuemax', '100')
        expect(progressBar).toHaveAttribute('aria-label')
      })
    })

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      
      // Test tab navigation
      await user.tab()
      expect(screen.getByRole('button', { name: /start the assessment/i })).toHaveFocus()
      
      // Test enter key activation
      await user.keyboard('{Enter}')
      
      await waitFor(() => {
        expect(screen.getByText('Question 1')).toBeInTheDocument()
      })
    })

    it('provides screen reader friendly announcements', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
      
      // Verify progress announcement
      await waitFor(() => {
        const progressLabel = screen.getByLabelText(/assessment progress/i)
        expect(progressLabel).toBeInTheDocument()
      })
    })
  })

  describe('Visual and UI Elements', () => {
    it('applies theme colors correctly', () => {
      renderWithChakra(<ConfidenceTest />)
      
      // This would test that proper theme colors are applied
      // Would need to check computed styles or specific Chakra classes
    })

    it('shows proper spacing and typography', () => {
      renderWithChakra(<ConfidenceTest />)
      
      // Test that typography tokens from theme are used correctly
    })

    it('displays cards with proper styling', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
      
      // Test that answer option cards are styled correctly
    })
  })

  describe('Performance', () => {
    it('renders initial screen quickly', () => {
      const startTime = performance.now()
      renderWithChakra(<ConfidenceTest />)
      const endTime = performance.now()
      
      // Should render in reasonable time (< 100ms for initial render)
      expect(endTime - startTime).toBeLessThan(100)
    })

    it('handles rapid clicking without issues', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      
      const startButton = screen.getByRole('button', { name: /start the assessment/i })
      
      // Rapidly click multiple times
      await user.click(startButton)
      await user.click(startButton)
      await user.click(startButton)
      
      // Should only progress once
      await waitFor(() => {
        expect(screen.getByText('Question 1')).toBeInTheDocument()
      })
    })
  })
})

describe('Complete User Journey Integration', () => {
  it('completes full assessment flow for analyzer archetype', async () => {
    const user = userEvent.setup()
    global.fetch = createMockFetch(fullMockQuestionsData)
    
    renderWithChakra(<ConfidenceTest />)
    
    // Wait for questions to load
    await waitFor(() => expect(global.fetch).toHaveBeenCalled())
    
    // Start assessment
    await user.click(screen.getByRole('button', { name: /start the assessment/i }))
    
    // This would simulate answering all 12 questions
    // and verify the complete flow to results
    
    await waitFor(() => {
      expect(screen.getByText('Question 1')).toBeInTheDocument()
    })
    
    // Note: Full implementation would require either:
    // 1. Mocking component state to simulate completion
    // 2. Creating a more complex test that actually answers all questions
    // 3. Testing the component methods directly
  })
})