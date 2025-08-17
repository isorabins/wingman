import { getCLS, getFCP, getFID, getLCP, getTTFB, Metric } from 'web-vitals';

export interface PerformanceData {
  name: string;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  delta: number;
  id: string;
  timestamp: number;
}

export class PerformanceMonitor {
  private static metrics: PerformanceData[] = [];
  private static isInitialized = false;

  static initialize() {
    if (this.isInitialized) return;
    
    if (typeof window !== 'undefined') {
      getCLS(this.handleMetric);
      getFCP(this.handleMetric);
      getFID(this.handleMetric);
      getLCP(this.handleMetric);
      getTTFB(this.handleMetric);
      
      this.isInitialized = true;
    }
  }

  private static handleMetric = (metric: Metric) => {
    const performanceData: PerformanceData = {
      name: metric.name,
      value: metric.value,
      rating: metric.rating,
      delta: metric.delta,
      id: metric.id,
      timestamp: Date.now()
    };

    this.metrics.push(performanceData);
    this.reportMetric(performanceData);
  };

  private static reportMetric(metric: PerformanceData) {
    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`Performance Metric: ${metric.name}`, {
        value: `${metric.value.toFixed(2)}ms`,
        rating: metric.rating,
        target: this.getTarget(metric.name)
      });
    }

    // In production, this would send to analytics service
    // analytics.track('performance_metric', metric);
  }

  private static getTarget(metricName: string): string {
    const targets = {
      FCP: '< 1.5s',
      LCP: '< 2.5s',
      FID: '< 100ms',
      CLS: '< 0.1',
      TTFB: '< 600ms'
    };
    return targets[metricName as keyof typeof targets] || 'N/A';
  }

  static getMetrics(): PerformanceData[] {
    return [...this.metrics];
  }

  static getMetricByName(name: string): PerformanceData | undefined {
    return this.metrics.find(metric => metric.name === name);
  }

  static getBundleSize(): { totalSize: number; chunks: any[] } {
    if (typeof window === 'undefined') return { totalSize: 0, chunks: [] };
    
    const chunks: any[] = [];
    let totalSize = 0;

    // Get performance entries for script resources
    const scriptEntries = performance.getEntriesByType('resource')
      .filter(entry => entry.name.includes('.js'));

    scriptEntries.forEach(entry => {
      const size = (entry as any).transferSize || 0;
      totalSize += size;
      chunks.push({
        name: entry.name.split('/').pop(),
        size: size,
        loadTime: entry.duration
      });
    });

    return { totalSize, chunks };
  }

  static getNavigationTiming() {
    if (typeof window === 'undefined') return null;
    
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    const paintEntries = performance.getEntriesByType('paint');

    return {
      loadTime: navigation.loadEventEnd - navigation.fetchStart,
      domContentLoaded: navigation.domContentLoadedEventEnd - navigation.fetchStart,
      firstPaint: paintEntries.find(entry => entry.name === 'first-paint')?.startTime || 0,
      firstContentfulPaint: paintEntries.find(entry => entry.name === 'first-contentful-paint')?.startTime || 0,
      timeToInteractive: navigation.domInteractive - navigation.fetchStart
    };
  }

  static generateReport(): string {
    const metrics = this.getMetrics();
    const bundleInfo = this.getBundleSize();
    const navigation = this.getNavigationTiming();

    let report = '\n=== PERFORMANCE REPORT ===\n\n';
    
    report += 'Core Web Vitals:\n';
    metrics.forEach(metric => {
      const status = metric.rating === 'good' ? '✅' : 
                   metric.rating === 'needs-improvement' ? '⚠️' : '❌';
      report += `  ${status} ${metric.name}: ${metric.value.toFixed(2)}ms (${metric.rating})\n`;
    });

    if (navigation) {
      report += '\nLoad Performance:\n';
      report += `  Load Time: ${navigation.loadTime.toFixed(2)}ms\n`;
      report += `  DOM Content Loaded: ${navigation.domContentLoaded.toFixed(2)}ms\n`;
      report += `  Time to Interactive: ${navigation.timeToInteractive.toFixed(2)}ms\n`;
    }

    report += `\nBundle Size: ${(bundleInfo.totalSize / 1024).toFixed(2)} KB\n`;
    report += `Chunks: ${bundleInfo.chunks.length}\n`;

    return report;
  }
}

// Auto-initialize in browser environment
if (typeof window !== 'undefined') {
  PerformanceMonitor.initialize();
}