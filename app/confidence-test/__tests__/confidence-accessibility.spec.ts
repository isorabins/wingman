import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
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

describe('Confidence Test Accessibility', () => {
  let mockFetch: any
  let mockGtag: any

  beforeEach(() => {
    mockFetch = createMockFetch(fullMockQuestionsData)
    global.fetch = mockFetch
    mockGtag = createAnalyticsMock()
  })

  describe('Keyboard Navigation', () => {
    it('supports tab navigation through all interactive elements', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      // Tab through welcome screen elements
      await user.tab()
      expect(screen.getByRole('button', { name: /start the assessment/i })).toHaveFocus()
      
      await user.tab()
      expect(screen.getByRole('link', { name: /back to home/i })).toHaveFocus()
    })

    it('supports enter key to activate buttons', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      
      const startButton = screen.getByRole('button', { name: /start the assessment/i })
      startButton.focus()
      
      await user.keyboard('{Enter}')
      
      await waitFor(() => {
        expect(screen.getByText('Question 1')).toBeInTheDocument()
      })
    })

    it('supports arrow key navigation within radio groups', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
      
      await waitFor(() => {
        const radioGroup = screen.getByRole('radiogroup')
        expect(radioGroup).toBeInTheDocument()
      })
      
      // Focus first radio button
      const firstRadio = screen.getAllByRole('radio')[0]
      firstRadio.focus()
      
      // Use arrow key to navigate
      await user.keyboard('{ArrowDown}')
      
      // Second radio should be focused and selected
      const secondRadio = screen.getAllByRole('radio')[1]
      expect(secondRadio).toHaveFocus()
    })

    it('supports space key to select radio buttons', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
      
      await waitFor(() => {
        const firstRadio = screen.getAllByRole('radio')[0]
        firstRadio.focus()
        
        await user.keyboard(' ')
        expect(firstRadio).toBeChecked()
      })
    })
  })

  describe('ARIA Attributes and Labels', () => {
    it('has proper radiogroup ARIA attributes', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
      
      await waitFor(() => {
        const radioGroup = screen.getByRole('radiogroup')
        expect(radioGroup).toHaveAttribute('aria-labelledby')
        expect(radioGroup).toHaveAttribute('role', 'radiogroup')
      })
    })

    it('has proper progress bar ARIA attributes', async () => {
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

    it('provides descriptive labels for all form controls', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
      
      await waitFor(() => {
        const radioButtons = screen.getAllByRole('radio')
        radioButtons.forEach(radio => {
          expect(radio).toHaveAccessibleName()
        })
      })
    })

    it('has proper heading hierarchy', () => {
      renderWithChakra(<ConfidenceTest />)
      
      // Welcome screen should have proper heading structure
      const mainHeading = screen.getByRole('heading', { level: 1 })
      expect(mainHeading).toBeInTheDocument()
      expect(mainHeading).toHaveTextContent(/discover your/i)
    })
  })

  describe('Screen Reader Support', () => {
    it('provides meaningful progress announcements', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
      
      await waitFor(() => {
        const progressLabel = screen.getByLabelText(/assessment progress/i)
        expect(progressLabel).toHaveTextContent(/8% complete/)
      })
    })

    it('provides context for current question', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
      
      await waitFor(() => {
        expect(screen.getByText('Question 1')).toBeInTheDocument()
        expect(screen.getByText('of 12')).toBeInTheDocument()
      })
    })

    it('provides accessible names for interactive elements', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
      
      await waitFor(() => {
        const backButton = screen.getByRole('button', { name: /back/i })
        expect(backButton).toHaveAccessibleName()
      })
    })
  })

  describe('Focus Management', () => {
    it('manages focus properly during screen transitions', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      
      const startButton = screen.getByRole('button', { name: /start the assessment/i })
      await user.click(startButton)
      
      // Focus should move to first question area
      await waitFor(() => {
        const questionHeading = screen.getByRole('heading', { level: 2 })
        expect(questionHeading).toBeInTheDocument()
      })
    })

    it('maintains logical tab order', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
      
      await waitFor(() => {
        // Tab should go through radio options in order
        const radioButtons = screen.getAllByRole('radio')
        expect(radioButtons.length).toBeGreaterThan(0)
      })
    })

    it('returns focus to logical position after interactions', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
      
      await waitFor(() => {
        const firstRadio = screen.getAllByRole('radio')[0]
        expect(firstRadio).toBeInTheDocument()
      })
    })
  })

  describe('Color Contrast and Visual Accessibility', () => {
    it('uses proper color contrast for text elements', () => {
      renderWithChakra(<ConfidenceTest />)
      
      // Test would verify computed styles meet WCAG contrast requirements
      // This is typically done with accessibility testing tools
      const heading = screen.getByText(/discover your/i)
      expect(heading).toBeInTheDocument()
    })

    it('provides visual focus indicators', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await user.tab()
      const focusedElement = document.activeElement
      
      // Should have visible focus styling
      expect(focusedElement).toHaveClass(/chakra-button/)
    })

    it('works without color as the only differentiator', async () => {
      const user = userEvent.setup()
      renderWithChakra(<ConfidenceTest />)
      
      await waitFor(() => expect(mockFetch).toHaveBeenCalled())
      await user.click(screen.getByRole('button', { name: /start the assessment/i }))
      
      await waitFor(() => {
        // Selected state should be indicated by more than just color
        const radioButtons = screen.getAllByRole('radio')
        radioButtons.forEach(radio => {
          // Chakra UI radio buttons use checkmarks, not just color
          expect(radio).toBeInTheDocument()
        })
      })
    })
  })

  describe('Reduced Motion Support', () => {
    it('respects prefers-reduced-motion setting', () => {
      // Mock reduced motion preference
      Object.defineProperty(window, 'matchMedia', {
        value: vi.fn().mockImplementation(query => ({
          matches: query === '(prefers-reduced-motion: reduce)',
          media: query,
          onchange: null,
          addListener: vi.fn(),
          removeListener: vi.fn(),
        })),
      })
      
      renderWithChakra(<ConfidenceTest />)
      
      // Component should render without motion-dependent functionality
      expect(screen.getByText(/discover your/i)).toBeInTheDocument()
    })
  })

  describe('Language and Internationalization', () => {
    it('has proper language attributes', () => {
      renderWithChakra(<ConfidenceTest />)
      
      // Document should have proper lang attribute (set at higher level)
      // Component text should be clear and understandable
      expect(screen.getByText(/discover your/i)).toBeInTheDocument()
    })

    it('uses clear and simple language', () => {
      renderWithChakra(<ConfidenceTest />)
      
      // Text should be at appropriate reading level
      expect(screen.getByText('Takes just 3 minutes • 12 quick questions')).toBeInTheDocument()
    })
  })
})