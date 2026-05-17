'use client'

import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react'
import { api, type JWTPayload } from './api'

interface AuthState {
  user: JWTPayload | null
  token: string | null
  isLoading: boolean
  isAuthenticated: boolean
}

interface AuthContextValue extends AuthState {
  setToken: (token: string) => void
  clearAuth: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

interface OpenClawAuth {
  token: string | null
  user: JWTPayload | null
  isAuthenticated: boolean
  setToken: (token: string) => void
  clearAuth: () => void
  refreshUser: () => Promise<void>
}

declare global {
  interface Window {
    openclawAuth?: OpenClawAuth
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    isLoading: true,
    isAuthenticated: false,
  })
  const mounted = useRef(false)

  const clearAuth = useCallback(() => {
    for (const key of ['openclaw_auth_token', 'auth_token', 'jwt_token', 'token']) {
      try {
        localStorage.removeItem(key)
      } catch {
        // ignore
      }
    }
    setState({
      user: null,
      token: null,
      isLoading: false,
      isAuthenticated: false,
    })
  }, [])

  const refreshUser = useCallback(async () => {
    const user = await api.auth.getVerifiedUser()
    const token = api.auth.getToken()
    setState({
      user,
      token,
      isLoading: false,
      isAuthenticated: !!user,
    })
  }, [])

  useEffect(() => {
    if (mounted.current) return
    mounted.current = true
    refreshUser()
  }, [refreshUser])

  const setToken = useCallback((token: string) => {
    try {
      localStorage.setItem('openclaw_auth_token', token)
    } catch {
      // localStorage not available
    }
    refreshUser()
  }, [refreshUser])

  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.openclawAuth = {
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        setToken,
        clearAuth,
        refreshUser,
      }
    }
  }, [state.token, state.user, state.isAuthenticated, setToken, clearAuth, refreshUser])

  return (
    <AuthContext.Provider value={{ ...state, setToken, clearAuth, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}