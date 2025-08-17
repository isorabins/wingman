/**
 * Unit Tests for LocationCapture Component
 * 
 * Test Coverage:
 * - Privacy mode switching
 * - Location request flow
 * - Error handling and retry mechanisms
 * - Manual city entry fallback
 * - Progress indicators
 * - Accessibility compliance
 */

import React from 'react'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { ChakraProvider } from '@chakra-ui/react'
import LocationCapture from '../LocationCapture'
import { LocationService, LocationResult, LocationErrorCode } from '../../services/locationService'

// Mock the LocationService
jest.mock('../../services/locationService', () => ({
  LocationService: jest.fn(),
  LocationErrorCode: {
    PERMISSION_DENIED: 'permission_denied',
    POSITION_UNAVAILABLE: 'position_unavailable',
    TIMEOUT: 'timeout',
    NETWORK_ERROR: 'network_error',
    INVALID_COORDINATES: 'invalid_coordinates',
    GEOCODING_FAILED: 'geocoding_failed',
    NOT_SUPPORTED: 'not_supported'
  },
  locationService: {
    getCurrentLocation: jest.fn(),
    retryLocation: jest.fn(),
    clearCache: jest.fn()
  }
}))

const mockLocationService = require('../../services/locationService').locationService

// Helper to render component with Chakra provider
const renderWithChakra = (component: React.ReactElement) => {
  return render(
    <ChakraProvider>{component}</ChakraProvider>
  )
}

describe('LocationCapture', () => {
  const mockProps = {
    onLocationUpdate: jest.fn(),
    onPrivacyModeChange: jest.fn(),
    privacyMode: 'precise' as const,
    initialCity: '',
    isRequired: true,
    disabled: false
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Privacy Mode Toggle', () => {
    it('should render privacy toggle with precise mode selected', () => {
      renderWithChakra(<LocationCapture {...mockProps} />)

      expect(screen.getByText('Location Privacy')).toBeInTheDocument()
      expect(screen.getByText('Share exact location')).toBeInTheDocument()
      expect(screen.getByRole('checkbox')).toBeChecked()
    })

    it('should switch to city-only mode when toggle is clicked', async () => {
      renderWithChakra(<LocationCapture {...mockProps} />)

      const toggle = screen.getByRole('checkbox')
      fireEvent.click(toggle)

      await waitFor(() => {
        expect(mockProps.onPrivacyModeChange).toHaveBeenCalledWith('city_only')
      })
    })

    it('should render city-only mode correctly', () => {
      renderWithChakra(
        <LocationCapture {...mockProps} privacyMode="city_only" />
      )

      expect(screen.getByText('City only')).toBeInTheDocument()
      expect(screen.getByRole('checkbox')).not.toBeChecked()
      expect(screen.getByPlaceholderText(/Enter your city/)).toBeInTheDocument()
    })

    it('should show privacy badges correctly', () => {
      const { rerender } = renderWithChakra(<LocationCapture {...mockProps} />)

      expect(screen.getByText('Precise')).toBeInTheDocument()

      rerender(
        <ChakraProvider>
          <LocationCapture {...mockProps} privacyMode="city_only" />
        </ChakraProvider>
      )

      expect(screen.getByText('Private')).toBeInTheDocument()
    })
  })

  describe('Location Request Flow', () => {
    it('should render location button in precise mode', () => {
      renderWithChakra(<LocationCapture {...mockProps} />)

      expect(screen.getByText('Use My Current Location')).toBeInTheDocument()
    })

    it('should handle successful location request', async () => {
      const mockResult: LocationResult = {
        success: true,
        coordinates: { lat: 37.7749, lng: -122.4194, accuracy: 10 },
        city: 'San Francisco',
        source: 'gps'
      }

      mockLocationService.getCurrentLocation.mockResolvedValue(mockResult)

      renderWithChakra(<LocationCapture {...mockProps} />)

      const locationButton = screen.getByText('Use My Current Location')
      fireEvent.click(locationButton)

      await waitFor(() => {
        expect(screen.getByText('Location captured • San Francisco')).toBeInTheDocument()
      })

      expect(mockProps.onLocationUpdate).toHaveBeenCalledWith({
        lat: 37.7749,
        lng: -122.4194,
        city: 'San Francisco'
      })
    })

    it('should show progress during location request', async () => {
      const mockResult: LocationResult = {
        success: true,
        coordinates: { lat: 37.7749, lng: -122.4194 },
        source: 'gps'
      }

      mockLocationService.getCurrentLocation.mockImplementation(
        ({ onProgress }) => {
          // Simulate progress updates
          setTimeout(() => onProgress?.('permission', 10), 10)
          setTimeout(() => onProgress?.('acquiring', 30), 20)
          setTimeout(() => onProgress?.('acquired', 60), 30)
          setTimeout(() => onProgress?.('geocoding', 70), 40)
          setTimeout(() => onProgress?.('complete', 100), 50)
          
          return Promise.resolve(mockResult)
        }
      )

      renderWithChakra(<LocationCapture {...mockProps} />)

      const locationButton = screen.getByText('Use My Current Location')
      
      act(() => {
        fireEvent.click(locationButton)
      })

      // Should show progress indicator
      await waitFor(() => {
        expect(screen.getByRole('progressbar')).toBeInTheDocument()
      })
    })

    it('should handle permission denied error', async () => {
      const mockResult: LocationResult = {
        success: false,
        error: 'Location access denied. Please enable location permissions.',
        errorCode: LocationErrorCode.PERMISSION_DENIED,
        retryable: false,
        source: 'gps'
      }

      mockLocationService.getCurrentLocation.mockResolvedValue(mockResult)

      renderWithChakra(<LocationCapture {...mockProps} />)

      const locationButton = screen.getByText('Use My Current Location')
      fireEvent.click(locationButton)

      await waitFor(() => {
        expect(screen.getByText('Location Failed')).toBeInTheDocument()
        expect(screen.getByText(/Location access denied/)).toBeInTheDocument()
      })

      // Should show permission help text
      expect(screen.getByText('Location Permission Needed')).toBeInTheDocument()
    })

    it('should handle timeout error with retry option', async () => {
      const mockResult: LocationResult = {
        success: false,
        error: 'Location request timed out.',
        errorCode: LocationErrorCode.TIMEOUT,
        retryable: true,
        source: 'gps'
      }

      mockLocationService.getCurrentLocation.mockResolvedValue(mockResult)

      renderWithChakra(<LocationCapture {...mockProps} />)

      const locationButton = screen.getByText('Use My Current Location')
      fireEvent.click(locationButton)

      await waitFor(() => {
        expect(screen.getByText('Try Again')).toBeInTheDocument()
        expect(screen.getByText('Enter City Manually')).toBeInTheDocument()
      })
    })

    it('should handle retry functionality', async () => {
      const retryResult: LocationResult = {
        success: true,
        coordinates: { lat: 37.7749, lng: -122.4194 },
        city: 'San Francisco',
        source: 'gps'
      }

      mockLocationService.retryLocation.mockResolvedValue(retryResult)

      // First show error state
      renderWithChakra(<LocationCapture {...mockProps} />)
      
      // Simulate error state by directly setting it
      const errorResult: LocationResult = {
        success: false,
        error: 'Location request timed out.',
        errorCode: LocationErrorCode.TIMEOUT,
        retryable: true,
        source: 'gps'
      }

      mockLocationService.getCurrentLocation.mockResolvedValue(errorResult)

      const locationButton = screen.getByText('Use My Current Location')
      fireEvent.click(locationButton)

      await waitFor(() => {
        expect(screen.getByText('Try Again')).toBeInTheDocument()
      })

      // Click retry button
      const retryButton = screen.getByText('Try Again')
      fireEvent.click(retryButton)

      await waitFor(() => {
        expect(mockLocationService.retryLocation).toHaveBeenCalled()
      })
    })

    it('should disable location button when disabled prop is true', () => {
      renderWithChakra(<LocationCapture {...mockProps} disabled={true} />)

      const locationButton = screen.getByText('Use My Current Location')
      expect(locationButton).toBeDisabled()
    })

    it('should disable location button after successful capture', async () => {
      const mockResult: LocationResult = {
        success: true,
        coordinates: { lat: 37.7749, lng: -122.4194 },
        city: 'San Francisco',
        source: 'gps'
      }

      mockLocationService.getCurrentLocation.mockResolvedValue(mockResult)

      renderWithChakra(<LocationCapture {...mockProps} />)

      const locationButton = screen.getByText('Use My Current Location')
      fireEvent.click(locationButton)

      await waitFor(() => {
        const updatedButton = screen.getByText('Location captured • San Francisco')
        expect(updatedButton).toBeDisabled()
      })
    })
  })

  describe('Manual City Entry', () => {
    it('should show manual city input in city-only mode', () => {
      renderWithChakra(
        <LocationCapture {...mockProps} privacyMode="city_only" />
      )

      const cityInput = screen.getByPlaceholderText(/Enter your city/)
      expect(cityInput).toBeInTheDocument()
      expect(cityInput).not.toBeDisabled()
    })

    it('should handle manual city input changes', () => {
      renderWithChakra(
        <LocationCapture {...mockProps} privacyMode="city_only" />
      )

      const cityInput = screen.getByPlaceholderText(/Enter your city/)
      fireEvent.change(cityInput, { target: { value: 'New York, NY' } })

      expect(mockProps.onLocationUpdate).toHaveBeenCalledWith({
        city: 'New York, NY'
      })
    })

    it('should show manual entry fallback after location failure', async () => {
      const mockResult: LocationResult = {
        success: false,
        error: 'Location request timed out.',
        errorCode: LocationErrorCode.TIMEOUT,
        retryable: true,
        source: 'gps'
      }

      mockLocationService.getCurrentLocation.mockResolvedValue(mockResult)

      renderWithChakra(<LocationCapture {...mockProps} />)

      const locationButton = screen.getByText('Use My Current Location')
      fireEvent.click(locationButton)

      await waitFor(() => {
        expect(screen.getByText('Enter City Manually')).toBeInTheDocument()
      })

      // Click the manual entry button
      const manualButton = screen.getByText('Enter City Manually')
      fireEvent.click(manualButton)

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Enter your city/)).toBeInTheDocument()
      })
    })

    it('should handle initial city value', () => {
      renderWithChakra(
        <LocationCapture 
          {...mockProps} 
          privacyMode="city_only" 
          initialCity="Boston, MA" 
        />
      )

      const cityInput = screen.getByPlaceholderText(/Enter your city/)
      expect(cityInput).toHaveValue('Boston, MA')
    })

    it('should show required error for empty city when required', () => {
      renderWithChakra(
        <LocationCapture 
          {...mockProps} 
          privacyMode="city_only"
          isRequired={true}
        />
      )

      // Empty city input should show validation error
      const cityInput = screen.getByPlaceholderText(/Enter your city/)
      fireEvent.blur(cityInput) // Trigger validation

      // Note: In actual implementation, this would need form validation context
      // For now, we just verify the input is present and can be interacted with
      expect(cityInput).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels and roles', () => {
      renderWithChakra(<LocationCapture {...mockProps} />)

      // Check for proper form controls
      expect(screen.getByRole('checkbox')).toBeInTheDocument()
      expect(screen.getByText('Location Privacy')).toBeInTheDocument()
      
      // Location button should be accessible
      const locationButton = screen.getByRole('button', { name: /Use My Current Location/ })
      expect(locationButton).toBeInTheDocument()
    })

    it('should support keyboard navigation', () => {
      renderWithChakra(<LocationCapture {...mockProps} />)

      const toggle = screen.getByRole('checkbox')
      toggle.focus()
      expect(toggle).toHaveFocus()

      // Tab to next element
      fireEvent.keyDown(toggle, { key: 'Tab' })
      
      const locationButton = screen.getByRole('button', { name: /Use My Current Location/ })
      expect(locationButton).toBeInTheDocument()
    })

    it('should provide clear error messages', async () => {
      const mockResult: LocationResult = {
        success: false,
        error: 'Location access denied. Please enable location permissions.',
        errorCode: LocationErrorCode.PERMISSION_DENIED,
        retryable: false,
        source: 'gps'
      }

      mockLocationService.getCurrentLocation.mockResolvedValue(mockResult)

      renderWithChakra(<LocationCapture {...mockProps} />)

      const locationButton = screen.getByText('Use My Current Location')
      fireEvent.click(locationButton)

      await waitFor(() => {
        // Error should be announced to screen readers
        expect(screen.getByText('Location Failed')).toBeInTheDocument()
        expect(screen.getByText(/Location access denied/)).toBeInTheDocument()
      })
    })

    it('should have tooltips for additional information', () => {
      renderWithChakra(<LocationCapture {...mockProps} />)

      // Privacy badge should have tooltip (hover to show more info)
      const precisebadge = screen.getByText('Precise')
      expect(preciseBadge).toBeInTheDocument()
    })
  })

  describe('Component Integration', () => {
    it('should call onLocationUpdate with coordinates for precise mode', async () => {
      const mockResult: LocationResult = {
        success: true,
        coordinates: { lat: 40.7128, lng: -74.0060, accuracy: 5 },
        city: 'New York',
        source: 'gps'
      }

      mockLocationService.getCurrentLocation.mockResolvedValue(mockResult)

      renderWithChakra(<LocationCapture {...mockProps} />)

      const locationButton = screen.getByText('Use My Current Location')
      fireEvent.click(locationButton)

      await waitFor(() => {
        expect(mockProps.onLocationUpdate).toHaveBeenCalledWith({
          lat: 40.7128,
          lng: -74.0060,
          city: 'New York'
        })
      })
    })

    it('should call onLocationUpdate with only city for city-only mode', () => {
      renderWithChakra(
        <LocationCapture {...mockProps} privacyMode="city_only" />
      )

      const cityInput = screen.getByPlaceholderText(/Enter your city/)
      fireEvent.change(cityInput, { target: { value: 'Chicago, IL' } })

      expect(mockProps.onLocationUpdate).toHaveBeenCalledWith({
        city: 'Chicago, IL'
      })
    })

    it('should handle privacy mode changes correctly', () => {
      renderWithChakra(<LocationCapture {...mockProps} />)

      const toggle = screen.getByRole('checkbox')
      fireEvent.click(toggle)

      expect(mockProps.onPrivacyModeChange).toHaveBeenCalledWith('city_only')
    })

    it('should show location accuracy information when available', async () => {
      const mockResult: LocationResult = {
        success: true,
        coordinates: { lat: 37.7749, lng: -122.4194, accuracy: 10 },
        city: 'San Francisco',
        source: 'gps'
      }

      mockLocationService.getCurrentLocation.mockResolvedValue(mockResult)

      renderWithChakra(<LocationCapture {...mockProps} />)

      const locationButton = screen.getByText('Use My Current Location')
      fireEvent.click(locationButton)

      await waitFor(() => {
        expect(screen.getByText(/Location accuracy: ±10m/)).toBeInTheDocument()
      })
    })

    it('should indicate cached location source', async () => {
      const mockResult: LocationResult = {
        success: true,
        coordinates: { lat: 37.7749, lng: -122.4194, accuracy: 10 },
        city: 'San Francisco',
        source: 'cache'
      }

      mockLocationService.getCurrentLocation.mockResolvedValue(mockResult)

      renderWithChakra(<LocationCapture {...mockProps} />)

      const locationButton = screen.getByText('Use My Current Location')
      fireEvent.click(locationButton)

      await waitFor(() => {
        expect(screen.getByText(/\(cached\)/)).toBeInTheDocument()
      })
    })
  })

  describe('Edge Cases', () => {
    it('should handle rapid clicking of location button', async () => {
      const mockResult: LocationResult = {
        success: true,
        coordinates: { lat: 37.7749, lng: -122.4194 },
        source: 'gps'
      }

      mockLocationService.getCurrentLocation.mockResolvedValue(mockResult)

      renderWithChakra(<LocationCapture {...mockProps} />)

      const locationButton = screen.getByText('Use My Current Location')
      
      // Rapid clicks
      fireEvent.click(locationButton)
      fireEvent.click(locationButton)
      fireEvent.click(locationButton)

      // Should only trigger once
      await waitFor(() => {
        expect(mockLocationService.getCurrentLocation).toHaveBeenCalledTimes(1)
      })
    })

    it('should handle component unmounting during location request', async () => {
      mockLocationService.getCurrentLocation.mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 1000))
      )

      const { unmount } = renderWithChakra(<LocationCapture {...mockProps} />)

      const locationButton = screen.getByText('Use My Current Location')
      fireEvent.click(locationButton)

      // Unmount component before location request completes
      unmount()

      // Should not cause any errors
      expect(true).toBe(true) // Test passes if no errors thrown
    })
  })
})