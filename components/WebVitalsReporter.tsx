/**
 * Web Vitals Reporter Component
 * Initializes performance monitoring and provides dev tools
 */

'use client';

import { useEffect, useState } from 'react';
import { Box, Text, Badge, VStack, HStack, useColorModeValue } from '@chakra-ui/react';
import { initWebVitals, getPerformanceData } from '@/lib/performance/web-vitals';
import { usePrefetch } from '@/lib/performance/prefetch';
import { usePathname } from 'next/navigation';

interface PerformanceDisplayProps {
  showInDev?: boolean;
}

export const WebVitalsReporter: React.FC<PerformanceDisplayProps> = ({ 
  showInDev = true 
}) => {
  const [performanceData, setPerformanceData] = useState<any>(null);
  const [isDevMode, setIsDevMode] = useState(false);
  const pathname = usePathname();

  // Initialize prefetching for current route
  const { stats } = usePrefetch(pathname);

  useEffect(() => {
    // Check if we're in development mode
    setIsDevMode(process.env.NODE_ENV === 'development');

    // Initialize Web Vitals monitoring
    initWebVitals();

    // Update performance data periodically
    const interval = setInterval(() => {
      setPerformanceData(getPerformanceData());
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // Don't render in production unless explicitly enabled
  if (!isDevMode && !showInDev) {
    return null;
  }

  const bgColor = useColorModeValue('gray.50', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  return (
    <>
      {/* Hidden in production by default */}
      {isDevMode && performanceData && (
        <Box
          position="fixed"
          top={4}
          right={4}
          bg={bgColor}
          border="1px solid"
          borderColor={borderColor}
          borderRadius="md"
          p={3}
          fontSize="xs"
          maxW="300px"
          zIndex={9999}
          opacity={0.9}
          _hover={{ opacity: 1 }}
          transition="opacity 0.2s"
        >
          <VStack spacing={2} align="start">
            <Text fontWeight="bold" fontSize="sm">
              🚀 Performance Monitor
            </Text>
            
            <HStack spacing={2} wrap="wrap">
              <Badge colorScheme={performanceData.score >= 90 ? 'green' : performanceData.score >= 75 ? 'yellow' : 'red'}>
                Score: {performanceData.score}
              </Badge>
              
              {performanceData.summary.ratings.LCP && (
                <Badge 
                  colorScheme={
                    performanceData.summary.ratings.LCP === 'good' ? 'green' : 
                    performanceData.summary.ratings.LCP === 'needs-improvement' ? 'yellow' : 'red'
                  }
                >
                  LCP: {Math.round(performanceData.summary.scores.LCP || 0)}ms
                </Badge>
              )}
              
              {performanceData.summary.ratings.CLS && (
                <Badge 
                  colorScheme={
                    performanceData.summary.ratings.CLS === 'good' ? 'green' : 
                    performanceData.summary.ratings.CLS === 'needs-improvement' ? 'yellow' : 'red'
                  }
                >
                  CLS: {(performanceData.summary.scores.CLS || 0).toFixed(3)}
                </Badge>
              )}
            </HStack>

            <HStack spacing={2} fontSize="10px" color="gray.500">
              <Text>Prefetched: {stats.prefetchedRoutes}</Text>
              <Text>•</Text>
              <Text>Metrics: {performanceData.summary.totalMetrics}</Text>
            </HStack>
          </VStack>
        </Box>
      )}

      {/* Send metrics to backend for analysis */}
      <script
        dangerouslySetInnerHTML={{
          __html: `
            if (typeof window !== 'undefined') {
              // Report Web Vitals to analytics
              function sendToAnalytics(metric) {
                // Send to backend API for aggregation
                fetch('/api/performance/vitals', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({
                    name: metric.name,
                    value: metric.value,
                    id: metric.id,
                    url: window.location.href,
                    timestamp: Date.now()
                  })
                }).catch(() => {
                  // Fail silently for performance tracking
                });
              }

              // Track page visibility changes for accurate metrics
              let isPageVisible = !document.hidden;
              document.addEventListener('visibilitychange', () => {
                isPageVisible = !document.hidden;
              });

              // Only track metrics when page is visible
              window.webVitalsCallback = function(metric) {
                if (isPageVisible) {
                  sendToAnalytics(metric);
                }
              };
            }
          `,
        }}
      />
    </>
  );
};

export default WebVitalsReporter;