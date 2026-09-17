import axios from 'axios'
import {
  type ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from '../lib/authStorage'
import { api } from '../lib/api'
import type {
  AdminUser,
  LoginCredentials,
  TokenResponse,
} from '../types/auth'
import {
  AuthContext,
  type AuthContextValue,
} from './authContext'

function getLoginError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail

    if (typeof detail === 'string') {
      return detail
    }

    if (!error.response) {
      return 'Unable to reach the server. Please try again.'
    }
  }

  return 'Unable to sign in. Please try again.'
}

export function AuthProvider({
  children,
}: {
  children: ReactNode
}) {
  const [user, setUser] = useState<AdminUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const token = getAccessToken()

    if (!token) {
      queueMicrotask(() => {
        setIsLoading(false)
      })

      return
    }

    let isCancelled = false

    async function restoreSession() {
      try {
        const response = await api.get<AdminUser>('/auth/me')

        if (!isCancelled) {
          setUser(response.data)
        }
      } catch {
        clearAccessToken()

        if (!isCancelled) {
          setUser(null)
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false)
        }
      }
    }

    void restoreSession()

    return () => {
      isCancelled = true
    }
  }, [])

  const login = useCallback(
    async (credentials: LoginCredentials) => {
      try {
        const response = await api.post<TokenResponse>(
          '/auth/login',
          credentials,
        )

        setAccessToken(response.data.access_token)

        try {
          const meResponse = await api.get<AdminUser>('/auth/me')
          setUser(meResponse.data)
        } catch (error) {
          clearAccessToken()
          throw error
        }
      } catch (error) {
        throw new Error(
          getLoginError(error),
          { cause: error },
        )
      }
    },
    [],
  )

  const logout = useCallback(() => {
    clearAccessToken()
    setUser(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: user !== null,
      isLoading,
      login,
      logout,
    }),
    [isLoading, login, logout, user],
  )

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
