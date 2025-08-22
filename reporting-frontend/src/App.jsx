import { useState, useEffect } from 'react'
import Layout from './components/Layout'
import Login from './components/Login'
import Dashboard from './components/Dashboard'
import AIQuery from './components/AIQuery'
import ReportCreator from './components/ReportCreator'
import Reports from './components/Reports'
import DatabaseExplorer from './components/DatabaseExplorer'
import ServiceReport from './components/departments/ServiceReport'
import PartsReport from './components/departments/PartsReport'
import RentalReport from './components/departments/RentalReport'
import AccountingReport from './components/departments/AccountingReport'
import InvoiceExplorer from './components/departments/InvoiceExplorer'
import AIQueryTester from './components/AIQueryTester'
import TableDiscovery from './components/TableDiscovery'
import MinitracSearch from './components/MinitracSearch'
import { apiUrl } from '@/lib/api'
import './App.css'

function App() {
  const [user, setUser] = useState(null)
  const [organization, setOrganization] = useState(null)
  const [currentPage, setCurrentPage] = useState('dashboard')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('token')
    if (token) {
      validateToken(token)
    } else {
      setLoading(false)
    }
  }, [])

  const validateToken = async (token) => {
    try {
      const response = await fetch(apiUrl('/api/auth/me'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setUser(data.user)
        setOrganization(data.organization)
      } else {
        localStorage.removeItem('token')
      }
    } catch (error) {
      console.error('Token validation failed:', error)
      localStorage.removeItem('token')
    } finally {
      setLoading(false)
    }
  }

  const handleLogin = (userData, organizationData) => {
    setUser(userData)
    setOrganization(organizationData)
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    setUser(null)
    setOrganization(null)
    setCurrentPage('dashboard')
  }

  const handleNavigate = (pageId) => {
    setCurrentPage(pageId)
  }

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard user={user} organization={organization} />
      case 'ai-query':
        return <AIQuery user={user} organization={organization} />
      case 'report-creator':
        return <ReportCreator user={user} organization={organization} />
      case 'reports':
        return <Reports user={user} organization={organization} />
      case 'database-explorer':
        return <DatabaseExplorer user={user} organization={organization} />
      case 'service':
        return <ServiceReport user={user} organization={organization} onNavigate={handleNavigate} />
      case 'parts':
        return <PartsReport user={user} organization={organization} />
      case 'rental':
        return <RentalReport user={user} organization={organization} />
      case 'accounting':
        return <AccountingReport user={user} organization={organization} />
      case 'invoice-explorer':
        return <InvoiceExplorer user={user} organization={organization} />
      case 'ai-query-tester':
        return <AIQueryTester user={user} organization={organization} />
      case 'table-discovery':
        return <TableDiscovery user={user} organization={organization} />
      case 'minitrac':
        return <MinitracSearch user={user} organization={organization} />
      case 'users':
        return <div className="p-8 text-center text-gray-500">Users management coming soon...</div>
      case 'settings':
        return <div className="p-8 text-center text-gray-500">Settings coming soon...</div>
      default:
        return <Dashboard user={user} organization={organization} />
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return <Login onLogin={handleLogin} />
  }

  return (
    <Layout 
      user={user} 
      onLogout={handleLogout}
      currentPage={currentPage}
      onNavigate={handleNavigate}
    >
      {renderPage()}
    </Layout>
  )
}

export default App

