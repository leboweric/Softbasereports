import { createContext, useContext, useState, useEffect } from 'react'
import { post, get, setToken, clearToken, getToken } from '../lib/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [dealer, setDealer] = useState(null)
  const [loading, setLoading] = useState(true)

  // Check for existing session on mount
  useEffect(() => {
    const token = getToken()
    if (token) {
      fetchCurrentUser()
    } else {
      setLoading(false)
    }
  }, [])

  const fetchCurrentUser = async () => {
    try {
      const data = await get('/api/auth/me')
      setUser(data.user)
      setDealer(data.dealer)
    } catch (error) {
      console.error('Failed to fetch current user:', error)
      clearToken()
    } finally {
      setLoading(false)
    }
  }

  const login = async (email, password) => {
    const data = await post('/api/auth/login', { email, password })
    setToken(data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    setUser(data.user)
    setDealer(data.dealer)
    return data
  }

  const logout = () => {
    clearToken()
    setUser(null)
    setDealer(null)
  }

  const register = async (userData) => {
    const data = await post('/api/auth/register', userData)
    return data
  }

  const value = {
    user,
    dealer,
    loading,
    login,
    logout,
    register,
    isCurrieAdmin: user?.user_type === 'currie_admin',
    isCurrieAnalyst: user?.user_type === 'currie_analyst',
    isDealerUser: user?.user_type === 'dealer',
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
