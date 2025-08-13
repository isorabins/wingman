import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ChakraProvider } from '@chakra-ui/react'
import { theme } from '../../theme'
import ProfileSetupPage from '../page'

// Mock Next.js router
const mockPush = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}))

// Mock Supabase client
vi.mock('../../../lib/supabase-client', () => ({
  supabase: {
    storage: {
      from: () => ({
        upload: vi.fn().mockResolvedValue({
          data: { path: 'test-path' },
          error: null
        }),
        getPublicUrl: vi.fn().mockReturnValue({
          data: { publicUrl: 'https://example.com/photo.jpg' }
        })
      })
    }
  }
}))

// Mock photo upload service
vi.mock('../../../storage/photo_upload', () => ({
  photoUploadService: {
    validatePhotoFile: vi.fn().mockReturnValue({ valid: true }),
    uploadPhoto: vi.fn().mockResolvedValue({
      success: true,
      photoUrl: 'https://example.com/photo.jpg'
    })
  }
}))

// Mock geolocation
const mockGeolocation = {
  getCurrentPosition: vi.fn(),
  watchPosition: vi.fn(),
  clearWatch: vi.fn(),
}

Object.defineProperty(global.navigator, 'geolocation', {
  value: mockGeolocation,
  writable: true,
})

// Mock fetch for API calls
global.fetch = vi.fn()

// Test wrapper component
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <ChakraProvider theme={theme}>
    {children}
  </ChakraProvider>
)

describe('Profile Setup Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  it('renders profile setup form with all required fields', () => {
    render(
      <TestWrapper>
        <ProfileSetupPage />
      </TestWrapper>
    )

    // Check main heading
    expect(screen.getByText('Complete Your Profile')).toBeInTheDocument()

    // Check form sections
    expect(screen.getByText('Profile Photo')).toBeInTheDocument()
    expect(screen.getByText('About You')).toBeInTheDocument()
    expect(screen.getByText('Location & Preferences')).toBeInTheDocument()

    // Check required form fields
    expect(screen.getByLabelText(/Tell us about yourself/i)).toBeInTheDocument()
    expect(screen.getByText('Location Privacy')).toBeInTheDocument()
    expect(screen.getByText(/Travel Radius/i)).toBeInTheDocument()

    // Check submit button
    expect(screen.getByRole('button', { name: /Complete Profile/i })).toBeInTheDocument()
  })

  it('validates bio field with character limits and PII detection', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <ProfileSetupPage />
      </TestWrapper>
    )

    const bioField = screen.getByLabelText(/Tell us about yourself/i)
    
    // Test minimum character validation
    await user.type(bioField, 'Short')
    
    // Should show character count
    expect(screen.getByText('5/400')).toBeInTheDocument()

    // Clear and test PII detection
    await user.clear(bioField)
    await user.type(bioField, 'Call me at 555-123-4567 or email test@example.com')
    
    // Should prevent PII in bio
    const submitButton = screen.getByRole('button', { name: /Complete Profile/i })
    expect(submitButton).toBeDisabled()
  })

  it('handles location permissions and geolocation', async () => {
    const user = userEvent.setup()
    
    // Mock successful geolocation
    mockGeolocation.getCurrentPosition.mockImplementation((success) => {
      success({
        coords: {
          latitude: 37.7749,
          longitude: -122.4194
        }
      })
    })

    // Mock reverse geocoding
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        city: 'San Francisco',
        locality: 'San Francisco'
      })
    })

    render(
      <TestWrapper>
        <ProfileSetupPage />
      </TestWrapper>
    )

    const locationButton = screen.getByRole('button', { name: /Use My Current Location/i })
    await user.click(locationButton)

    await waitFor(() => {
      expect(mockGeolocation.getCurrentPosition).toHaveBeenCalled()
    })

    // Should show success message
    await waitFor(() => {
      expect(screen.getByText(/Location captured successfully/i)).toBeInTheDocument()
    })
  })

  it('handles photo upload with drag and drop', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <ProfileSetupPage />
      </TestWrapper>
    )

    // Find upload area
    const uploadArea = screen.getByText(/Upload a profile photo/i).closest('div')
    expect(uploadArea).toBeInTheDocument()

    // Create a mock file
    const mockFile = new File(['fake image content'], 'test-photo.jpg', {
      type: 'image/jpeg'
    })

    // Mock file input
    const fileInput = uploadArea?.querySelector('input[type="file"]')
    if (fileInput) {
      Object.defineProperty(fileInput, 'files', {
        value: [mockFile],
        writable: false,
      })

      fireEvent.change(fileInput)
    }

    // Should show upload progress
    await waitFor(() => {
      expect(screen.getByText(/Uploading/i)).toBeInTheDocument()
    })
  })

  it('handles privacy mode toggle between precise and city-only', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <ProfileSetupPage />
      </TestWrapper>
    )

    // Should start with precise location mode
    expect(screen.getByText('Share exact location')).toBeInTheDocument()

    // Find privacy toggle switch
    const privacySwitch = screen.getByRole('checkbox')
    await user.click(privacySwitch)

    // Should switch to city-only mode
    expect(screen.getByText('City only')).toBeInTheDocument()

    // Should show city input field
    expect(screen.getByLabelText(/City/i)).toBeInTheDocument()
  })

  it('submits form with valid data and redirects to find-buddy', async () => {
    const user = userEvent.setup()
    
    // Mock successful API response
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        success: true,
        message: 'Profile completed successfully',
        ready_for_matching: true,
        user_id: 'demo-user-id'
      })
    })

    render(
      <TestWrapper>
        <ProfileSetupPage />
      </TestWrapper>
    )

    // Fill out bio
    const bioField = screen.getByLabelText(/Tell us about yourself/i)
    await user.type(bioField, 'I love meeting new people and exploring the city. Looking for a confident wingman buddy!')

    // Switch to city-only mode and enter city
    const privacySwitch = screen.getByRole('checkbox')
    await user.click(privacySwitch)
    
    const cityField = screen.getByLabelText(/City/i)
    await user.type(cityField, 'San Francisco, CA')

    // Submit form
    const submitButton = screen.getByRole('button', { name: /Complete Profile/i })
    await user.click(submitButton)

    // Should call API and redirect
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/profile/complete', expect.objectContaining({
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: expect.stringContaining('San Francisco, CA')
      }))
    })

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/find-buddy')
    })
  })

  it('handles API errors gracefully', async () => {
    const user = userEvent.setup()
    
    // Mock API error
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: () => Promise.resolve({
        detail: 'Invalid bio content'
      })
    })

    render(
      <TestWrapper>
        <ProfileSetupPage />
      </TestWrapper>
    )

    // Fill out form with valid data
    const bioField = screen.getByLabelText(/Tell us about yourself/i)
    await user.type(bioField, 'Valid bio content for testing error handling scenarios.')

    const privacySwitch = screen.getByRole('checkbox')
    await user.click(privacySwitch)
    
    const cityField = screen.getByLabelText(/City/i)
    await user.type(cityField, 'San Francisco, CA')

    // Submit form
    const submitButton = screen.getByRole('button', { name: /Complete Profile/i })
    await user.click(submitButton)

    // Should show error message (would normally show as toast)
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled()
      // Error handling is done via toast notifications
      // In a real test, we'd mock useToast and verify error display
    })

    // Should not redirect on error
    expect(mockPush).not.toHaveBeenCalled()
  })

  it('meets accessibility requirements', () => {
    render(
      <TestWrapper>
        <ProfileSetupPage />
      </TestWrapper>
    )

    // Check for proper form labels
    expect(screen.getByLabelText(/Tell us about yourself/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/City/i)).toBeInTheDocument()

    // Check for ARIA attributes
    const progressBar = screen.getByRole('progressbar')
    expect(progressBar).toHaveAttribute('aria-valuenow')
    expect(progressBar).toHaveAttribute('aria-valuemin')
    expect(progressBar).toHaveAttribute('aria-valuemax')

    // Check for proper button roles
    const submitButton = screen.getByRole('button', { name: /Complete Profile/i })
    expect(submitButton).toBeInTheDocument()

    // Check for proper heading hierarchy
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Complete Your Profile')
    expect(screen.getAllByRole('heading', { level: 2 })).toHaveLength(3) // Photo, Bio, Location sections
  })
})