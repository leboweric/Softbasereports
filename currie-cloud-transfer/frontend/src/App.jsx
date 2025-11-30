import { Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'

// Pages
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Dealers from './pages/Dealers'
import Reports from './pages/Reports'
import AdminSetup from './pages/AdminSetup'
import Layout from './components/Layout'

// Auth context
import { AuthProvider, useAuth } from './hooks/useAuth'

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-currie-600"></div>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return children
}

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="dealers" element={<Dealers />} />
          <Route path="reports" element={<Reports />} />
          <Route path="admin/setup" element={<AdminSetup />} />
        </Route>
      </Routes>
    </AuthProvider>
  )
}

export default App
