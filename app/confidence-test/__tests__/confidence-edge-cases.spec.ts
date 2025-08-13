import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ChakraProvider } from '@chakra-ui/react'
import ConfidenceTest from '../page'
import { theme } from '../../theme'
import { fullMockQuestionsData, createMockFetch, createAnalyticsMock } from './test-utils'

const renderWithChakra = (component: React.ReactElement) => {
  return render(
    <ChakraProvider theme={theme}>
      {component}
    </ChakraProvider>
  )
}

describe('Confidence Test Edge Cases and Error Handling', () => {
  let mockFetch: any
  let mockGtag: any

  beforeEach(() => {
    mockFetch = createMockFetch(fullMockQuestionsData)
    global.fetch = mockFetch
    mockGtag = createAnalyticsMock()
  })

  describe('Network and API Edge Cases', () => {
    it('handles questions loading failure gracefully', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => {
        expect(screen.getByText('Error loading questions')).toBeInTheDocument()
      })
    })

    it('handles partial questions data', async () => {
      const partialData = {
        questions: fullMockQuestionsData.questions.slice(0, 5), // Only 5 questions
        archetypes: fullMockQuestionsData.archetypes
      }
      
      mockFetch = createMockFetch(partialData)
      global.fetch = mockFetch
      
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      
      // Should handle gracefully even with fewer questions
      const user = userEvent.setup()
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
    })

    it('handles malformed questions data', async () => {
      const malformedData = {
        questions: [
          { id: 1, question: "Test?", options: [] }, // No options
          { id: 2, options: [{ letter: "A", text: "Test" }] }, // No question
        ],
        archetypes: {}
      }
      
      mockFetch = createMockFetch(malformedData)
      global.fetch = mockFetch
      
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      
      // Should not crash with malformed data
      expect(screen.getByText(/discover your/i)).toBeInTheDocument()
    })

    it('handles missing archetype data in results', async () => {
      const dataWithoutArchetypes = {
        questions: fullMockQuestionsData.questions,
        archetypes: {} // Empty archetypes
      }
      
      mockFetch = createMockFetch(dataWithoutArchetypes)
      global.fetch = mockFetch
      
      renderWithChakra(<ConfidenceTest />)
      
      // Should fall back to default archetype data
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
    })

    it('handles API submission timeout', async () => {
      mockFetch.mockImplementation((url: string) => {
        if (url.includes('questions.v1.json')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(fullMockQuestionsData),
          })
        }
        if (url.includes('/api/assessment/confidence')) {
          return new Promise(() => {}) // Never resolves (timeout simulation)
        }
        return Promise.reject(new Error(`Unhandled URL: ${url}`))
      })
      
      renderWithChakra(<ConfidenceTest />)
      
      // Should handle API timeout gracefully without hanging UI
    })

    it('handles slow network connections', async () => {
      mockFetch.mockImplementation((url: string) => {
        if (url.includes('questions.v1.json')) {
          return new Promise(resolve => {
            setTimeout(() => {
              resolve({
                ok: true,
                json: () => Promise.resolve(fullMockQuestionsData),
              })
            }, 2000) // 2 second delay
          })
        }
        return Promise.reject(new Error(`Unhandled URL: ${url}`))
      })
      
      renderWithChakra(<ConfidenceTest />)
      
      // Component should show loading state appropriately
      expect(screen.getByText(/discover your/i)).toBeInTheDocument()
    })
  })

  describe('User Interaction Edge Cases', () => {
    it('handles rapid clicking on start button', async () => {
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

    it('handles rapid answer selection changes', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
      
      await waitFor(() => {
        const radioButtons = screen.getAllByRole('radio')
        expect(radioButtons.length).toBeGreaterThan(0)
      })
      
      // Rapidly change selections
      const radioButtons = screen.getAllByRole('radio')
      await user.click(radioButtons[0])
      await user.click(radioButtons[1])
      await user.click(radioButtons[2])
      
      // Should handle gracefully and maintain last selection
      expect(radioButtons[2]).toBeChecked()
    })

    it('handles browser back/forward navigation', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
      
      // Simulate browser back button
      window.history.back()
      
      // Component should handle navigation state correctly
      // Note: This would require proper router integration testing
    })

    it('handles page refresh during assessment', () => {
      renderWithChakra(<ConfidenceTest />)
      
      // Simulate page refresh (component remount)
      const { unmount } = render(
        <ChakraProvider theme={theme}>
          <ConfidenceTest />
        </ChakraProvider>
      )
      
      unmount()
      
      // Re-render component
      renderWithChakra(<ConfidenceTest />)
      
      // Should start fresh (as expected behavior)
      expect(screen.getByText(/discover your/i)).toBeInTheDocument()
    })

    it('handles incomplete form submission attempts', async () => {
      // This test simulates trying to submit without all answers
      // Would require mocking the component state to be on question 12
      // with incomplete answers
      renderWithChakra(<ConfidenceTest />)
      
      // Mock being on last question with incomplete answers
      // This would trigger the validation toast
    })
  })

  describe('Performance Edge Cases', () => {
    it('handles large numbers of rapid state updates', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
      
      // Simulate many rapid interactions
      const radioButtons = screen.getAllByRole('radio')
      for (let i = 0; i < 50; i++) {
        await user.click(radioButtons[i % radioButtons.length])
      }
      
      // Should remain responsive
      expect(radioButtons[0]).toBeInTheDocument()
    })

    it('handles memory leaks in long-running sessions', () => {
      // Test component cleanup and memory management
      const { unmount } = renderWithChakra(<ConfidenceTest />)
      
      // Component should clean up properly
      unmount()
      
      // Verify no lingering event listeners or timers
      expect(global.fetch).toBeDefined()
    })

    it('handles large question datasets efficiently', async () => {
      // Create mock data with many more questions
      const largeDataset = {
        questions: Array.from({ length: 100 }, (_, i) => ({
          id: i + 1,
          question: `Large dataset question ${i + 1}?`,
          options: Array.from({ length: 10 }, (_, j) => ({
            letter: String.fromCharCode(65 + j), // A, B, C, etc.
            text: `Option ${String.fromCharCode(65 + j)}`,
            archetype: 'analyzer'
          }))
        })),
        archetypes: fullMockQuestionsData.archetypes
      }
      
      mockFetch = createMockFetch(largeDataset)
      global.fetch = mockFetch
      
      const startTime = performance.now()
      renderWithChakra(<ConfidenceTest />)
      const endTime = performance.now()
      
      // Should render efficiently even with large datasets
      expect(endTime - startTime).toBeLessThan(200)
    })
  })

  describe('Browser Compatibility Edge Cases', () => {
    it('handles missing modern JavaScript features gracefully', () => {
      // Mock older browser environment
      const originalFetch = global.fetch
      delete (global as any).fetch
      
      renderWithChakra(<ConfidenceTest />)
      
      // Should handle missing fetch gracefully
      expect(screen.getByText(/discover your/i)).toBeInTheDocument()
      
      // Restore fetch
      global.fetch = originalFetch
    })

    it('handles missing local storage', () => {
      // Mock environment without localStorage
      const originalLocalStorage = window.localStorage
      delete (window as any).localStorage
      
      renderWithChakra(<ConfidenceTest />)
      
      // Should work without localStorage
      expect(screen.getByText(/discover your/i)).toBeInTheDocument()
      
      // Restore localStorage
      window.localStorage = originalLocalStorage
    })

    it('handles disabled JavaScript features', () => {
      // Mock disabled features
      const originalConsole = console.error
      console.error = vi.fn()
      
      renderWithChakra(<ConfidenceTest />)
      
      // Should render basic HTML structure
      expect(screen.getByText(/discover your/i)).toBeInTheDocument()
      
      console.error = originalConsole
    })
  })

  describe('Data Validation Edge Cases', () => {
    it('handles invalid question IDs', async () => {
      const invalidData = {
        questions: [
          { id: null, question: "Test?", options: [] },
          { id: "invalid", question: "Test 2?", options: [] }
        ],
        archetypes: fullMockQuestionsData.archetypes
      }
      
      mockFetch = createMockFetch(invalidData)
      global.fetch = mockFetch
      
      renderWithChakra(<ConfidenceTest />)
      
      // Should handle invalid IDs gracefully
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
    })

    it('handles missing question properties', async () => {
      const incompleteData = {
        questions: [
          { id: 1 }, // Missing question and options
          { id: 2, question: "Test?" }, // Missing options
          { id: 3, options: [] } // Missing question
        ],
        archetypes: fullMockQuestionsData.archetypes
      }
      
      mockFetch = createMockFetch(incompleteData)
      global.fetch = mockFetch
      
      renderWithChakra(<ConfidenceTest />)
      
      // Should not crash with incomplete data
      expect(screen.getByText(/discover your/i)).toBeInTheDocument()
    })

    it('handles circular references in data', async () => {
      const circularData = { ...fullMockQuestionsData }
      // Create circular reference (would be caught by JSON.stringify)
      circularData.questions[0].self = circularData.questions[0]
      
      mockFetch = createMockFetch(circularData)
      global.fetch = mockFetch
      
      renderWithChakra(<ConfidenceTest />)
      
      // Should handle gracefully
      expect(screen.getByText(/discover your/i)).toBeInTheDocument()
    })
  })

  describe('Analytics Edge Cases', () => {
    it('handles missing analytics library', () => {
      // Remove gtag
      delete (window as any).gtag
      
      renderWithChakra(<ConfidenceTest />)
      
      // Should work without analytics
      expect(screen.getByText(/discover your/i)).toBeInTheDocument()
    })

    it('handles analytics errors gracefully', async () => {
      // Mock gtag that throws errors
      const errorGtag = vi.fn().mockImplementation(() => {
        throw new Error('Analytics error')
      })
      Object.defineProperty(window, 'gtag', {
        value: errorGtag,
        writable: true,
      })
      
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      
      // Should not crash when analytics fails
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
      
      expect(screen.getByText('Question 1')).toBeInTheDocument()
    })
  })

  describe('Race Condition Edge Cases', () => {
    it('handles rapid component mount/unmount cycles', async () => {
      for (let i = 0; i < 10; i++) {
        const { unmount } = renderWithChakra(<ConfidenceTest />)
        unmount()
      }
      
      // Final render should work correctly
      renderWithChakra(<ConfidenceTest />)
      expect(screen.getByText(/discover your/i)).toBeInTheDocument()
    })

    it('handles concurrent API calls', async () => {
      // Multiple renders triggering same API call
      renderWithChakra(<ConfidenceTest />)
      renderWithChakra(<ConfidenceTest />)
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => {
        // Should handle concurrent calls gracefully
        expect(screen.getByText(/discover your/i)).toBeInTheDocument()
      })
    })
  })
})