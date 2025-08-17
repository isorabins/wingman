/**
 * ReputationBadge Component
 * Displays user reputation as a colored badge with optional score and tooltip
 */

"use client";

import React from 'react';
import {
  Badge,
  Tooltip,
  Skeleton,
  Alert,
  AlertIcon,
  Box,
  Text,
  VStack,
} from '@chakra-ui/react';
import { ReputationBadgeProps } from '@/lib/reputation/types';
import { useReputation } from '@/lib/reputation/useReputation';
import { reputationService } from '@/services/reputationService';

export function ReputationBadge({
  userId,
  size = 'md',
  variant = 'solid',
  showScore = false,
  showTooltip = true,
  className = '',
}: ReputationBadgeProps) {
  const { reputation, isLoading, error, isStale } = useReputation(userId, {
    useCache: true,
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  });

  // Loading state
  if (isLoading && !reputation) {
    return (
      <Skeleton
        height={size === 'sm' ? '20px' : size === 'md' ? '24px' : '28px'}
        width={showScore ? '60px' : '40px'}
        borderRadius="full"
        className={className}
      />
    );
  }

  // Error state
  if (error && !reputation) {
    return (
      <Tooltip 
        label={`Failed to load reputation: ${error.message}`}
        isDisabled={!showTooltip}
      >
        <Badge
          colorScheme="gray"
          variant="outline"
          size={size}
          className={className}
          aria-label="Reputation unavailable"
        >
          ?
        </Badge>
      </Tooltip>
    );
  }

  // No data state
  if (!reputation) {
    return (
      <Tooltip label="Reputation data not available" isDisabled={!showTooltip}>
        <Badge
          colorScheme="gray"
          variant="outline"
          size={size}
          className={className}
          aria-label="No reputation data"
        >
          --
        </Badge>
      </Tooltip>
    );
  }

  // Get Chakra UI colorScheme from badge color
  const getColorScheme = (badgeColor: string) => {
    switch (badgeColor) {
      case 'gold':
        return 'yellow';
      case 'green':
        return 'green';
      case 'red':
        return 'red';
      default:
        return 'gray';
    }
  };

  // Get display text
  const getDisplayText = () => {
    if (showScore) {
      return `${reputation.score}`;
    }
    
    // Display text based on reputation level
    switch (reputation.badge_color) {
      case 'gold':
        return 'Excellent';
      case 'green':
        return 'Good';
      case 'red':
        return 'Needs Work';
      default:
        return 'Unknown';
    }
  };

  // Accessibility label
  const ariaLabel = reputationService.getBadgeLabel(
    reputation.score,
    reputation.completed_sessions,
    reputation.no_shows
  );

  // Tooltip content
  const tooltipContent = (
    <VStack spacing={1} align="start" fontSize="sm">
      <Text fontWeight="bold">
        Reputation Score: {reputation.score}
      </Text>
      <Text>
        Completed Sessions: {reputation.completed_sessions}
      </Text>
      <Text>
        No-shows: {reputation.no_shows}
      </Text>
      {isStale && (
        <Text fontSize="xs" color="gray.300">
          (Data may be outdated)
        </Text>
      )}
    </VStack>
  );

  const badgeElement = (
    <Badge
      colorScheme={getColorScheme(reputation.badge_color)}
      variant={variant}
      size={size}
      className={className}
      aria-label={ariaLabel}
      opacity={isStale ? 0.7 : 1}
      position="relative"
    >
      {getDisplayText()}
      {isStale && (
        <Box
          position="absolute"
          top="-2px"
          right="-2px"
          width="6px"
          height="6px"
          bg="orange.400"
          borderRadius="full"
          title="Data may be outdated"
        />
      )}
    </Badge>
  );

  // Wrap with tooltip if enabled
  if (showTooltip) {
    return (
      <Tooltip
        label={tooltipContent}
        aria-label="Reputation details"
        placement="top"
        hasArrow
      >
        {badgeElement}
      </Tooltip>
    );
  }

  return badgeElement;
}

/**
 * Compact version for tight spaces
 */
export function ReputationBadgeCompact({ userId, ...props }: Omit<ReputationBadgeProps, 'size' | 'showScore'>) {
  return (
    <ReputationBadge
      userId={userId}
      size="sm"
      showScore={true}
      showTooltip={true}
      {...props}
    />
  );
}

/**
 * Large version with full reputation info
 */
export function ReputationBadgeLarge({ userId, ...props }: Omit<ReputationBadgeProps, 'size'>) {
  return (
    <ReputationBadge
      userId={userId}
      size="lg"
      showScore={false}
      showTooltip={true}
      {...props}
    />
  );
}

export default ReputationBadge;