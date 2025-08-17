/**
 * ReputationBadge Component Tests
 * Tests for reputation badge component functionality
 */

import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import { theme } from '@/app/theme';
import ReputationBadge, { ReputationBadgeCompact, ReputationBadgeLarge } from '../ReputationBadge';
import { reputationService } from '@/services/reputationService';

// Mock the reputation service
jest.mock('@/services/reputationService', () => ({
  reputationService: {
    getUserReputation: jest.fn(),
    getCachedReputation: jest.fn(),
    getBadgeLabel: jest.fn(),
  },
}));

const mockedReputationService = reputationService as jest.Mocked<typeof reputationService>;

// Test wrapper with Chakra UI provider
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ChakraProvider theme={theme}>
    {children}
  </ChakraProvider>
);

// Mock reputation data
const mockReputationData = {
  score: 5,
  badge_color: 'green' as const,
  completed_sessions: 8,
  no_shows: 3,
  cache_timestamp: '2024-08-17T10:00:00Z',
};

const mockGoldReputationData = {
  score: 15,
  badge_color: 'gold' as const,
  completed_sessions: 20,
  no_shows: 5,
  cache_timestamp: '2024-08-17T10:00:00Z',
};

const mockRedReputationData = {
  score: -2,
  badge_color: 'red' as const,
  completed_sessions: 2,
  no_shows: 4,
  cache_timestamp: '2024-08-17T10:00:00Z',
};

describe('ReputationBadge', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedReputationService.getBadgeLabel.mockReturnValue('Good reputation: 5 points, 8 completed sessions, 3 no-shows');
  });

  describe('Loading State', () => {
    it('should show skeleton when loading', () => {
      mockedReputationService.getUserReputation.mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 1000))
      );

      render(
        <TestWrapper>
          <ReputationBadge userId="test-user-1" />
        </TestWrapper>
      );

      expect(screen.getByRole('presentation')).toBeInTheDocument(); // Skeleton has presentation role
    });
  });

  describe('Success States', () => {
    it('should display green badge for good reputation', async () => {
      mockedReputationService.getUserReputation.mockResolvedValue(mockReputationData);

      render(
        <TestWrapper>
          <ReputationBadge userId="test-user-1" />
        </TestWrapper>
      );

      await waitFor(() => {
        const badge = screen.getByText('Good');
        expect(badge).toBeInTheDocument();
        expect(badge.closest('[data-theme]')).toHaveAttribute('data-colorscheme', 'green');
      });
    });

    it('should display gold badge for excellent reputation', async () => {
      mockedReputationService.getUserReputation.mockResolvedValue(mockGoldReputationData);

      render(
        <TestWrapper>
          <ReputationBadge userId="test-user-1" />
        </TestWrapper>
      );

      await waitFor(() => {
        const badge = screen.getByText('Excellent');
        expect(badge).toBeInTheDocument();
        expect(badge.closest('[data-theme]')).toHaveAttribute('data-colorscheme', 'yellow');
      });
    });

    it('should display red badge for poor reputation', async () => {
      mockedReputationService.getUserReputation.mockResolvedValue(mockRedReputationData);

      render(
        <TestWrapper>
          <ReputationBadge userId="test-user-1" />
        </TestWrapper>
      );

      await waitFor(() => {
        const badge = screen.getByText('Needs Work');
        expect(badge).toBeInTheDocument();
        expect(badge.closest('[data-theme]')).toHaveAttribute('data-colorscheme', 'red');
      });
    });

    it('should display score when showScore is true', async () => {
      mockedReputationService.getUserReputation.mockResolvedValue(mockReputationData);

      render(
        <TestWrapper>
          <ReputationBadge userId="test-user-1" showScore={true} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('5')).toBeInTheDocument();
      });
    });
  });

  describe('Error State', () => {
    it('should show error badge when fetch fails', async () => {
      mockedReputationService.getUserReputation.mockRejectedValue(
        new Error('Network error')
      );

      render(
        <TestWrapper>
          <ReputationBadge userId="test-user-1" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('?')).toBeInTheDocument();
      });
    });
  });

  describe('Tooltip', () => {
    it('should show tooltip with reputation details on hover', async () => {
      mockedReputationService.getUserReputation.mockResolvedValue(mockReputationData);

      render(
        <TestWrapper>
          <ReputationBadge userId="test-user-1" showTooltip={true} />
        </TestWrapper>
      );

      await waitFor(() => {
        const badge = screen.getByText('Good');
        fireEvent.mouseOver(badge);
      });

      await waitFor(() => {
        expect(screen.getByText('Reputation Score: 5')).toBeInTheDocument();
        expect(screen.getByText('Completed Sessions: 8')).toBeInTheDocument();
        expect(screen.getByText('No-shows: 3')).toBeInTheDocument();
      });
    });

    it('should not show tooltip when showTooltip is false', async () => {
      mockedReputationService.getUserReputation.mockResolvedValue(mockReputationData);

      render(
        <TestWrapper>
          <ReputationBadge userId="test-user-1" showTooltip={false} />
        </TestWrapper>
      );

      await waitFor(() => {
        const badge = screen.getByText('Good');
        fireEvent.mouseOver(badge);
      });

      // Wait a bit to ensure tooltip doesn't appear
      await new Promise(resolve => setTimeout(resolve, 200));
      
      expect(screen.queryByText('Reputation Score: 5')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper aria-label', async () => {
      mockedReputationService.getUserReputation.mockResolvedValue(mockReputationData);

      render(
        <TestWrapper>
          <ReputationBadge userId="test-user-1" />
        </TestWrapper>
      );

      await waitFor(() => {
        const badge = screen.getByLabelText('Good reputation: 5 points, 8 completed sessions, 3 no-shows');
        expect(badge).toBeInTheDocument();
      });
    });
  });

  describe('Variants', () => {
    it('should render compact variant correctly', async () => {
      mockedReputationService.getUserReputation.mockResolvedValue(mockReputationData);

      render(
        <TestWrapper>
          <ReputationBadgeCompact userId="test-user-1" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('5')).toBeInTheDocument(); // Shows score in compact mode
      });
    });

    it('should render large variant correctly', async () => {
      mockedReputationService.getUserReputation.mockResolvedValue(mockReputationData);

      render(
        <TestWrapper>
          <ReputationBadgeLarge userId="test-user-1" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Good')).toBeInTheDocument(); // Shows text in large mode
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle null userId gracefully', () => {
      render(
        <TestWrapper>
          <ReputationBadge userId="" />
        </TestWrapper>
      );

      expect(screen.getByText('--')).toBeInTheDocument();
    });

    it('should handle cached data', async () => {
      mockedReputationService.getCachedReputation.mockReturnValue(mockReputationData);
      mockedReputationService.getUserReputation.mockResolvedValue(mockReputationData);

      render(
        <TestWrapper>
          <ReputationBadge userId="test-user-1" />
        </TestWrapper>
      );

      // Should show cached data immediately
      await waitFor(() => {
        expect(screen.getByText('Good')).toBeInTheDocument();
      });
    });
  });
});