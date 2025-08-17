"use client"
import { createContext, useContext, useEffect, useState } from 'react'
import { User, Session } from '@supabase/supabase-js'
import { supabase } from './supabase-client'

interface AuthContextType {
  user: User | null
  session: Session | null
  loading: boolean
  signOut: () => Promise<void>
  signIn: (email: string) => Promise<{ error: any }>
  isTestMode: boolean
}

// Mock user for development testing
const createMockUser = (): User => ({
  id: 'test-user-12345',
  app_metadata: {},
  user_metadata: {
    email: 'test@wingman.dev',
    name: 'Test User'
  },
  aud: 'authenticated',
  created_at: '2024-01-01T00:00:00Z',
  email: 'test@wingman.dev',
  email_confirmed_at: '2024-01-01T00:00:00Z',
  last_sign_in_at: '2024-01-01T00:00:00Z',
  phone: '',
  role: 'authenticated',
  updated_at: '2024-01-01T00:00:00Z'
})

// Check if we're in test mode (development only)
const isTestModeEnabled = (): boolean => {
  // Only allow test mode in development
  if (process.env.NODE_ENV !== 'development') {
    return false
  }
  
  // Check for ?test=true query parameter - only on client side
  if (typeof window !== 'undefined') {
    const urlParams = new URLSearchParams(window.location.search)
    return urlParams.get('test') === 'true'
  }
  
  return false
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  session: null,
  loading: true,
  signOut: async () => {},
  signIn: async () => ({ error: null }),
  isTestMode: false
})

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const [isTestMode, setIsTestMode] = useState(false)

  useEffect(() => {
    // Check test mode after mount to avoid hydration mismatch
    const testMode = isTestModeEnabled()
    setIsTestMode(testMode)
    
    // Handle test mode
    if (testMode) {
      console.log('🧪 Test Mode Enabled - Using Backend Test Authentication')
      
      // Authenticate with backend test endpoint
      const authenticateTestUser = async () => {
        try {
          const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
          const response = await fetch(`${apiUrl}/auth/test-login`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              email: 'test@wingman.dev',
              create_user: true
            }),
          })
          
          if (response.ok) {
            const authData = await response.json()
            const mockUser = createMockUser()
            // Use the real user ID from backend
            mockUser.id = authData.user_id
            setUser(mockUser)
            console.log('🧪 Test user authenticated with backend ID:', authData.user_id)
          } else {
            console.error('Test authentication failed, using fallback mock user')
            const mockUser = createMockUser()
            setUser(mockUser)
          }
        } catch (error) {
          console.error('Test authentication error:', error)
          const mockUser = createMockUser()
          setUser(mockUser)
        } finally {
          setSession(null) // We don't need a full session for testing
          setLoading(false)
        }
      }
      
      authenticateTestUser()
      return
    }

    // Get initial session (production auth)
    const getInitialSession = async () => {
      try {
        const { data: { session }, error } = await supabase.auth.getSession()
        if (error) {
          console.error('Error getting session:', error)
        } else {
          setSession(session)
          setUser(session?.user ?? null)
        }
      } catch (error) {
        console.error('Session initialization error:', error)
      } finally {
        setLoading(false)
      }
    }

    getInitialSession()

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        console.log('Auth state changed:', event, session?.user?.email)
        setSession(session)
        setUser(session?.user ?? null)
        setLoading(false)
      }
    )

    return () => subscription.unsubscribe()
  }, [])

  const signOut = async () => {
    if (isTestMode) {
      console.log('🧪 Test Mode - Mock Sign Out')
      setUser(null)
      setSession(null)
      return
    }

    try {
      const { error } = await supabase.auth.signOut()
      if (error) {
        console.error('Sign out error:', error)
      }
    } catch (error) {
      console.error('Sign out exception:', error)
    }
  }

  const signIn = async (email: string) => {
    if (isTestMode) {
      console.log('🧪 Test Mode - Mock Sign In for:', email)
      const mockUser = createMockUser()
      setUser(mockUser)
      return { error: null }
    }

    try {
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: {
          emailRedirectTo: `${window.location.origin}/auth/callback`
        }
      })
      return { error }
    } catch (error) {
      console.error('Sign in exception:', error)
      return { error }
    }
  }

  return (
    <AuthContext.Provider value={{ user, session, loading, signOut, signIn, isTestMode }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}