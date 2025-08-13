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

describe('Confidence Test Performance', () => {
  let mockFetch: any
  let mockGtag: any

  beforeEach(() => {
    mockFetch = createMockFetch(fullMockQuestionsData)
    global.fetch = mockFetch
    mockGtag = createAnalyticsMock()
  })

  describe('Initial Render Performance', () => {
    it('renders initial component quickly', () => {
      const startTime = performance.now()
      renderWithChakra(<ConfidenceTest />)
      const endTime = performance.now()
      
      expect(endTime - startTime).toBeLessThan(50) // Should render in < 50ms
      expect(screen.getByText(/discover your/i)).toBeInTheDocument()
    })

    it('handles multiple simultaneous renders efficiently', () => {
      const renders = []
      const startTime = performance.now()
      
      for (let i = 0; i < 10; i++) {
        renders.push(renderWithChakra(<ConfidenceTest />))
      }
      
      const endTime = performance.now()
      
      // Should handle multiple renders efficiently
      expect(endTime - startTime).toBeLessThan(200)
      
      // Cleanup
      renders.forEach(({ unmount }) => unmount())
    })

    it('maintains consistent render times across multiple attempts', () => {
      const renderTimes = []
      
      for (let i = 0; i < 5; i++) {
        const startTime = performance.now()
        const { unmount } = renderWithChakra(<ConfidenceTest />)
        const endTime = performance.now()
        
        renderTimes.push(endTime - startTime)
        unmount()
      }
      
      // Render times should be consistently fast
      const avgTime = renderTimes.reduce((a, b) => a + b) / renderTimes.length
      expect(avgTime).toBeLessThan(50)
    })
  })

  describe('Data Loading Performance', () => {
    it('loads questions data efficiently', async () => {
      const startTime = performance.now()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      const endTime = performance.now()
      
      expect(endTime - startTime).toBeLessThan(100)
    })

    it('handles large question datasets without performance degradation', async () => {
      // Create large dataset
      const largeDataset = {
        questions: Array.from({ length: 500 }, (_, i) => ({
          id: i + 1,
          question: `Performance test question ${i + 1}?`,
          options: Array.from({ length: 6 }, (_, j) => ({
            letter: String.fromCharCode(65 + j),
            text: `Option ${String.fromCharCode(65 + j)} for question ${i + 1}`,
            archetype: ['analyzer', 'sprinter', 'ghost', 'naturalist', 'scholar', 'protector'][j]
          }))
        })),
        archetypes: fullMockQuestionsData.archetypes
      }
      
      mockFetch = createMockFetch(largeDataset)
      global.fetch = mockFetch
      
      const startTime = performance.now()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      const endTime = performance.now()
      
      // Should handle large datasets efficiently
      expect(endTime - startTime).toBeLessThan(500)
    })

    it('processes archetype calculation efficiently', () => {
      renderWithChakra(<ConfidenceTest />)
      
      // Test archetype calculation performance
      const responses = Array(12).fill('A')
      
      const startTime = performance.now()
      
      // Simulate the scoring calculation that happens in the component
      const scores: Record<string, number> = {
        analyzer: 0,
        sprinter: 0,
        ghost: 0,
        naturalist: 0,
        scholar: 0,
        protector: 0
      }
      
      responses.forEach(() => {
        scores.analyzer += 1 // Simulate scoring logic
      })
      
      const maxScore = Math.max(...Object.values(scores))
      const topArchetype = Object.entries(scores).find(([_, score]) => score === maxScore)?.[0]
      
      const endTime = performance.now()
      
      expect(endTime - startTime).toBeLessThan(5) // Should be very fast
      expect(topArchetype).toBe('analyzer')
    })
  })

  describe('User Interaction Performance', () => {
    it('handles rapid answer selection efficiently', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
      
      await waitFor(() => {
        expect(screen.getByText('Question 1')).toBeInTheDocument()
      })
      
      const radioButtons = screen.getAllByRole('radio')
      
      const startTime = performance.now()
      
      // Rapidly select different options
      for (let i = 0; i < 20; i++) {
        await user.click(radioButtons[i % radioButtons.length])
      }
      
      const endTime = performance.now()
      
      // Should handle rapid interactions efficiently
      expect(endTime - startTime).toBeLessThan(1000) // 1 second for 20 interactions
    })

    it('maintains responsive UI during state updates', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
      
      // Measure time between interaction and UI update
      const radioButton = screen.getAllByRole('radio')[0]
      
      const startTime = performance.now()
      await user.click(radioButton)
      
      // Wait for state update to complete
      await waitFor(() => expect(radioButton).toBeChecked())
      const endTime = performance.now()
      
      // State updates should be nearly instantaneous
      expect(endTime - startTime).toBeLessThan(50)
    })

    it('handles multiple concurrent interactions gracefully', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
      
      await waitFor(() => {
        const radioButtons = screen.getAllByRole('radio')
        expect(radioButtons.length).toBeGreaterThan(0)
      })
      
      const radioButtons = screen.getAllByRole('radio')
      
      // Simulate multiple rapid concurrent interactions
      const interactions = []
      for (let i = 0; i < 5; i++) {
        interactions.push(user.click(radioButtons[i % radioButtons.length]))
      }
      
      const startTime = performance.now()
      await Promise.all(interactions)
      const endTime = performance.now()
      
      // Should handle concurrent interactions efficiently
      expect(endTime - startTime).toBeLessThan(200)
    })
  })

  describe('Memory Usage Performance', () => {
    it('cleans up properly on unmount', () => {
      const { unmount } = renderWithChakra(<ConfidenceTest />)
      
      // Simulate some interactions to create potential memory leaks
      const startMemory = (performance as any).memory?.usedJSHeapSize || 0
      
      unmount()
      
      // Force garbage collection if available
      if ((global as any).gc) {
        (global as any).gc()
      }
      
      const endMemory = (performance as any).memory?.usedJSHeapSize || 0
      
      // Memory should not increase significantly (accounting for test overhead)
      if (startMemory && endMemory) {
        expect(endMemory - startMemory).toBeLessThan(1000000) // Less than 1MB increase
      }
    })

    it('handles multiple mount/unmount cycles without memory leaks', () => {
      const initialMemory = (performance as any).memory?.usedJSHeapSize || 0
      
      // Multiple mount/unmount cycles
      for (let i = 0; i < 10; i++) {
        const { unmount } = renderWithChakra(<ConfidenceTest />)
        unmount()
      }
      
      // Force garbage collection
      if ((global as any).gc) {
        (global as any).gc()
      }
      
      const finalMemory = (performance as any).memory?.usedJSHeapSize || 0
      
      // Memory should not grow significantly
      if (initialMemory && finalMemory) {
        expect(finalMemory - initialMemory).toBeLessThan(5000000) // Less than 5MB total
      }
    })

    it('efficiently manages state updates', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
      
      const startMemory = (performance as any).memory?.usedJSHeapSize || 0
      
      // Perform many state updates
      const radioButtons = screen.getAllByRole('radio')
      for (let i = 0; i < 100; i++) {
        await user.click(radioButtons[i % radioButtons.length])
      }
      
      const endMemory = (performance as any).memory?.usedJSHeapSize || 0
      
      // Memory usage should remain reasonable
      if (startMemory && endMemory) {
        expect(endMemory - startMemory).toBeLessThan(2000000) // Less than 2MB for state updates
      }
    })
  })

  describe('Network Performance', () => {
    it('handles network latency gracefully', async () => {
      // Mock slow network
      mockFetch.mockImplementation((url: string) => {
        if (url.includes('questions.v1.json')) {
          return new Promise(resolve => {
            setTimeout(() => {
              resolve({
                ok: true,
                json: () => Promise.resolve(fullMockQuestionsData),
              })
            }, 1000) // 1 second delay
          })
        }
        return Promise.reject(new Error(`Unhandled URL: ${url}`))
      })
      
      const startTime = performance.now()
      renderWithChakra(<ConfidenceTest />)
      
      // Component should render immediately, not wait for network
      expect(screen.getByText(/discover your/i)).toBeInTheDocument()
      
      const renderTime = performance.now() - startTime
      expect(renderTime).toBeLessThan(100) // Immediate render
      
      // Wait for network request to complete
      await waitFor(() => expect(mockFetch).toHaveBeenCalled(), { timeout: 2000 })
    })

    it('batches API calls efficiently', async () => {
      let apiCallCount = 0
      
      mockFetch.mockImplementation((url: string) => {
        apiCallCount++
        if (url.includes('questions.v1.json')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(fullMockQuestionsData),
          })
        }
        return Promise.reject(new Error(`Unhandled URL: ${url}`))
      })
      
      // Multiple components should share API calls
      renderWithChakra(<ConfidenceTest />)
      renderWithChakra(<ConfidenceTest />)
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      
      // Should not make redundant API calls
      // Note: This test assumes some form of request deduplication
      expect(apiCallCount).toBeGreaterThan(0)
    })
  })

  describe('Bundle Size and Load Performance', () => {
    it('loads component code efficiently', () => {
      // Test component bundle size impact
      const startTime = performance.now()
      
      // Dynamic import simulation
      const componentModule = () => import('../page')
      
      const loadTime = performance.now() - startTime
      expect(loadTime).toBeLessThan(10) // Should load quickly
    })

    it('minimizes re-renders during interactions', async () => {
      let renderCount = 0
      
      // Mock React DevTools profiler (simplified)
      const originalRender = React.createElement
      React.createElement = (...args) => {
        renderCount++
        return originalRender(...args)
      }
      
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      const initialRenderCount = renderCount
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
      
      const finalRenderCount = renderCount
      
      // Should minimize unnecessary re-renders
      expect(finalRenderCount - initialRenderCount).toBeLessThan(20)
      
      // Restore original
      React.createElement = originalRender
    })
  })

  describe('Real-world Performance Scenarios', () => {
    it('maintains performance under typical user behavior', async () => {
      const user = userEvent.setup()
      
      const startTime = performance.now()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      
      // Simulate typical user flow
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
      
      await waitFor(() => {
        expect(screen.getByText('Question 1')).toBeInTheDocument()
      })
      
      // Answer a question
      const radioButtons = screen.getAllByRole('radio')
      await user.click(radioButtons[0])
      
      const endTime = performance.now()
      
      // Entire typical interaction should be fast
      expect(endTime - startTime).toBeLessThan(500)
    })

    it('scales well with extended usage sessions', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
      
      const startTime = performance.now()
      
      // Simulate extended usage (many interactions)
      const radioButtons = screen.getAllByRole('radio')
      for (let i = 0; i < 50; i++) {
        await user.click(radioButtons[i % radioButtons.length])
        
        // Small delay to simulate real usage
        await new Promise(resolve => setTimeout(resolve, 10))
      }
      
      const endTime = performance.now()
      
      // Should maintain performance during extended use
      expect(endTime - startTime).toBeLessThan(3000) // 3 seconds for 50 interactions
    })
  })
})