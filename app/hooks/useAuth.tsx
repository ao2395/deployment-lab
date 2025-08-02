'use client'

import { useState, useEffect, createContext, useContext, ReactNode } from 'react'
import { authAPI, User } from '@/app/lib/api'
import Cookies from 'js-cookie'

interface AuthContextType {
  user: User | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  loading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const token = Cookies.get('access_token')
      if (!token) {
        setLoading(false)
        return
      }

      const response = await authAPI.verify()
      setUser(response.data)
    } catch {
      Cookies.remove('access_token')
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  const login = async (username: string, password: string) => {
    try {
      const response = await authAPI.login({ username, password })
      const { access_token } = response.data
      
      Cookies.set('access_token', access_token, { expires: 1 }) // 1 day
      
      const userResponse = await authAPI.verify()
      setUser(userResponse.data)
    } catch (error) {
      throw error
    }
  }

  const logout = () => {
    Cookies.remove('access_token')
    setUser(null)
    window.location.href = '/login'
  }

  const value = {
    user,
    login,
    logout,
    loading
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}