import { createContext, useContext, useState, useEffect } from 'react'
import axios from 'axios'

const AuthContext = createContext(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(true)

  // On mount, restore session from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('mathviz_session')
    if (stored) {
      try {
        const parsed = JSON.parse(stored)
        setSession(parsed.session)
        setUser(parsed.user)
        // Set default auth header
        axios.defaults.headers.common['Authorization'] = `Bearer ${parsed.session.access_token}`
      } catch (e) {
        localStorage.removeItem('mathviz_session')
      }
    }
    setLoading(false)
  }, [])

  const signup = async (email, password, displayName) => {
    const res = await axios.post('/api/auth/signup', {
      email,
      password,
      display_name: displayName || undefined
    })
    const data = res.data
    if (data.success && data.session) {
      setUser(data.user)
      setSession(data.session)
      localStorage.setItem('mathviz_session', JSON.stringify(data))
      axios.defaults.headers.common['Authorization'] = `Bearer ${data.session.access_token}`
    }
    return data
  }

  const signin = async (email, password) => {
    const res = await axios.post('/api/auth/signin', { email, password })
    const data = res.data
    if (data.success && data.session) {
      setUser(data.user)
      setSession(data.session)
      localStorage.setItem('mathviz_session', JSON.stringify(data))
      axios.defaults.headers.common['Authorization'] = `Bearer ${data.session.access_token}`
    }
    return data
  }

  const signout = () => {
    setUser(null)
    setSession(null)
    localStorage.removeItem('mathviz_session')
    delete axios.defaults.headers.common['Authorization']
  }

  return (
    <AuthContext.Provider value={{ user, session, loading, signup, signin, signout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  )
}

export default AuthContext
