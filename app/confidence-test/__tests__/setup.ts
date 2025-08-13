import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock environment variables
process.env.NODE_ENV = 'test'

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
  }),
  useSearchParams: () => ({
    get: vi.fn(() => null),
  }),
  usePathname: () => '/confidence-test',
}))

// Mock Next.js Link component
vi.mock('next/link', () => ({
  default: ({ children, href, ...props }: any) => {
    return <a href={href} {...props}>{children}</a>
  },
}))

// Mock window.gtag for analytics
Object.defineProperty(window, 'gtag', {
  value: vi.fn(),
  writable: true,
})

// Mock fetch globally
global.fetch = vi.fn()

// Setup fetch mock reset before each test
beforeEach(() => {
  vi.resetAllMocks()
  // Reset fetch mock
  ;(global.fetch as any).mockClear()
})