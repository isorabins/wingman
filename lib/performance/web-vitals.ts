/**
 * Web Vitals Performance Monitoring
 * Tracks Core Web Vitals and custom performance metrics
 */

import { getCLS, getFID, getFCP, getLCP, getTTFB, Metric } from 'web-vitals';

interface PerformanceMetric {
  name: string;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  timestamp: number;
  id: string;
  navigationType?: string;
  url: string;
}

interface PerformanceThresholds {
  good: number;
  needsImprovement: number;
}

// Core Web Vitals thresholds (based on Google's recommendations)
const THRESHOLDS: Record<string, PerformanceThresholds> = {
  CLS: { good: 0.1, needsImprovement: 0.25 },
  FID: { good: 100, needsImprovement: 300 },
  FCP: { good: 1800, needsImprovement: 3000 },
  LCP: { good: 2500, needsImprovement: 4000 },
  TTFB: { good: 800, needsImprovement: 1800 },
};

class WebVitalsMonitor {
  private metrics: PerformanceMetric[] = [];
  private isInitialized = false;

  /**
   * Initialize Web Vitals monitoring
   */
  init(): void {
    if (this.isInitialized || typeof window === 'undefined') return;

    try {
      // Monitor Core Web Vitals
      getCLS(this.handleMetric.bind(this));
      getFID(this.handleMetric.bind(this));
      getFCP(this.handleMetric.bind(this));
      getLCP(this.handleMetric.bind(this));
      getTTFB(this.handleMetric.bind(this));

      // Custom performance metrics
      this.trackCustomMetrics();

      this.isInitialized = true;
      
      if (process.env.NODE_ENV === 'development') {
        console.log('📊 Web Vitals monitoring initialized');
      }
    } catch (error) {
      console.warn('Failed to initialize Web Vitals monitoring:', error);
    }
  }

  /**
   * Handle incoming Web Vitals metrics
   */
  private handleMetric(metric: Metric): void {
    const performanceMetric: PerformanceMetric = {
      name: metric.name,
      value: metric.value,
      rating: this.getRating(metric.name, metric.value),
      timestamp: Date.now(),
      id: metric.id,
      navigationType: this.getNavigationType(),
      url: window.location.href,
    };

    this.metrics.push(performanceMetric);
    this.sendMetricToBackend(performanceMetric);

    // Development logging
    if (process.env.NODE_ENV === 'development') {
      console.log(`📈 ${metric.name}: ${metric.value} (${performanceMetric.rating})`);
    }
  }

  /**
   * Get performance rating based on thresholds
   */
  private getRating(metricName: string, value: number): 'good' | 'needs-improvement' | 'poor' {
    const threshold = THRESHOLDS[metricName];
    if (!threshold) return 'good';

    if (value <= threshold.good) return 'good';
    if (value <= threshold.needsImprovement) return 'needs-improvement';
    return 'poor';
  }

  /**
   * Get navigation type for context
   */
  private getNavigationType(): string {
    if (typeof window === 'undefined') return 'unknown';

    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    return navigation?.type || 'unknown';
  }

  /**
   * Track custom performance metrics
   */
  private trackCustomMetrics(): void {
    // Time to Interactive (TTI) approximation
    this.trackTimeToInteractive();
    
    // Bundle loading times
    this.trackBundleLoadTimes();
    
    // Component render times
    this.trackComponentRenderTimes();
  }

  /**
   * Track Time to Interactive approximation
   */
  private trackTimeToInteractive(): void {
    // Use requestIdleCallback to approximate TTI
    if ('requestIdleCallback' in window) {
      requestIdleCallback(() => {
        const navigationStart = performance.timeOrigin;
        const now = performance.now();
        
        const customMetric: PerformanceMetric = {
          name: 'TTI',
          value: now,
          rating: this.getRating('LCP', now), // Use LCP thresholds as approximation
          timestamp: Date.now(),
          id: `tti-${Date.now()}`,
          url: window.location.href,
        };

        this.metrics.push(customMetric);
        this.sendMetricToBackend(customMetric);
      });
    }
  }

  /**
   * Track bundle loading performance
   */
  private trackBundleLoadTimes(): void {
    // Monitor resource timing for JavaScript bundles
    const observer = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        if (entry.name.includes('/_next/static/chunks/') && entry.name.endsWith('.js')) {
          const loadTime = entry.responseEnd - entry.fetchStart;
          
          const customMetric: PerformanceMetric = {
            name: 'Bundle-Load',
            value: loadTime,
            rating: loadTime < 1000 ? 'good' : loadTime < 3000 ? 'needs-improvement' : 'poor',
            timestamp: Date.now(),
            id: `bundle-${Date.now()}`,
            url: entry.name,
          };

          this.sendMetricToBackend(customMetric);
        }
      });
    });

    observer.observe({ entryTypes: ['resource'] });
  }

  /**
   * Track component render performance
   */
  private trackComponentRenderTimes(): void {
    // Track React component render times using Performance API
    if ('performance' in window && 'measure' in performance) {
      const observer = new PerformanceObserver((list) => {
        list.getEntries().forEach((entry) => {
          if (entry.name.startsWith('⚛️')) { // React DevTools markers
            const customMetric: PerformanceMetric = {
              name: 'Component-Render',
              value: entry.duration,
              rating: entry.duration < 16 ? 'good' : entry.duration < 50 ? 'needs-improvement' : 'poor',
              timestamp: Date.now(),
              id: `render-${Date.now()}`,
              url: window.location.href,
            };

            this.sendMetricToBackend(customMetric);
          }
        });
      });

      try {
        observer.observe({ entryTypes: ['measure'] });
      } catch (error) {
        // Some browsers might not support all entry types
        console.warn('Component render tracking not supported:', error);
      }
    }
  }

  /**
   * Send metric to backend for aggregation
   */
  private async sendMetricToBackend(metric: PerformanceMetric): Promise<void> {
    // Batch metrics to avoid overwhelming the backend
    if (this.metrics.length % 5 === 0) {
      try {
        await fetch('/api/performance/metrics', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            metrics: this.metrics.slice(-5), // Send last 5 metrics
            userAgent: navigator.userAgent,
            timestamp: Date.now(),
          }),
        });
      } catch (error) {
        // Fail silently for performance tracking
        if (process.env.NODE_ENV === 'development') {
          console.warn('Failed to send performance metrics:', error);
        }
      }
    }
  }

  /**
   * Get current performance summary
   */
  getPerformanceSummary(): {
    scores: Record<string, number>;
    ratings: Record<string, string>;
    totalMetrics: number;
  } {
    const latestMetrics = this.getLatestMetrics();
    
    const scores: Record<string, number> = {};
    const ratings: Record<string, string> = {};

    Object.entries(latestMetrics).forEach(([name, metric]) => {
      scores[name] = metric.value;
      ratings[name] = metric.rating;
    });

    return {
      scores,
      ratings,
      totalMetrics: this.metrics.length,
    };
  }

  /**
   * Get latest metric for each type
   */
  private getLatestMetrics(): Record<string, PerformanceMetric> {
    const latest: Record<string, PerformanceMetric> = {};

    this.metrics.forEach((metric) => {
      if (!latest[metric.name] || metric.timestamp > latest[metric.name].timestamp) {
        latest[metric.name] = metric;
      }
    });

    return latest;
  }

  /**
   * Calculate overall performance score (0-100)
   */
  calculatePerformanceScore(): number {
    const latestMetrics = this.getLatestMetrics();
    const coreMetrics = ['CLS', 'FID', 'FCP', 'LCP', 'TTFB'];
    
    let totalScore = 0;
    let validMetrics = 0;

    coreMetrics.forEach((metricName) => {
      const metric = latestMetrics[metricName];
      if (metric) {
        let score = 0;
        if (metric.rating === 'good') score = 100;
        else if (metric.rating === 'needs-improvement') score = 75;
        else score = 50;

        totalScore += score;
        validMetrics++;
      }
    });

    return validMetrics > 0 ? Math.round(totalScore / validMetrics) : 0;
  }
}

// Singleton instance
export const webVitalsMonitor = new WebVitalsMonitor();

/**
 * Initialize Web Vitals monitoring (call this in _app.tsx)
 */
export const initWebVitals = (): void => {
  webVitalsMonitor.init();
};

/**
 * Get performance data for display
 */
export const getPerformanceData = () => {
  return {
    summary: webVitalsMonitor.getPerformanceSummary(),
    score: webVitalsMonitor.calculatePerformanceScore(),
  };
};