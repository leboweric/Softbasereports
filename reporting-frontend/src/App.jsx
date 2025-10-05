import { useState, useEffect } from 'react'
import Layout from './components/Layout'
import Login from './components/Login'
import Dashboard from './components/Dashboard'
import ReportCreator from './components/ReportCreator'
import Reports from './components/Reports'
import RentalDiagnostic from './components/RentalDiagnostic'
import ServiceReport from './components/departments/ServiceReport'
import PartsReport from './components/departments/PartsReport'
import RentalReport from './components/departments/RentalReport'
import AccountingReport from './components/departments/AccountingReport'
import InvoiceExplorer from './components/departments/InvoiceExplorer'
import AIQueryTester from './components/AIQueryTester'
import TableDiscovery from './components/TableDiscovery'
import MinitracSearch from './components/MinitracSearch'
import UserManagementEnhanced from './components/UserManagementEnhanced'
import { UserManagement } from './components/admin/UserManagement'
import { apiUrl } from '@/lib/api'
import { PermissionsContext, getAccessibleNavigation } from './contexts/PermissionsContext'
import './App.css'

function App() {
  const [user, setUser] = useState(null)
  const [organization, setOrganization] = useState(null)
  const [permissions, setPermissions] = useState([])
  const [accessibleDepartments, setAccessibleDepartments] = useState([])
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
        // Add navigation data to user object for compatibility
        const userWithNavigation = {
          ...data.user,
          navigation: data.navigation,
          resources: data.resources,
          permissions_summary: data.permissions_summary
        }
        setUser(userWithNavigation)
        setOrganization(data.organization)
        // Set permissions and accessible departments from response data
        setPermissions(data.permissions || [])
        setAccessibleDepartments(data.accessible_departments || [])
        
        // Check if current page is accessible
        const navigation = getAccessibleNavigation(userWithNavigation)
        if (!navigation[currentPage]) {
          // Redirect to first available page using same order as Layout.jsx
          const desiredOrder = ['dashboard', 'parts', 'service', 'rental', 'accounting', 'minitrac', 'user-management']
          const firstAvailablePage = desiredOrder.find(id => navigation[id]) || Object.keys(navigation)[0] || 'parts'
          setCurrentPage(firstAvailablePage)
        }
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

  const handleLogin = (userData, organizationData, userPermissions = [], departments = []) => {
    // Process login data
    
    setUser(userData)
    setOrganization(organizationData)
    setPermissions(userPermissions)
    setAccessibleDepartments(departments)
    
    // User state updated
    
    // Use dynamic navigation to determine landing page
    const navigation = getAccessibleNavigation(userData)
    // Navigation data retrieved
    
    // Use same order as Layout.jsx to ensure Dashboard is first choice
    const desiredOrder = ['dashboard', 'parts', 'service', 'rental', 'accounting', 'minitrac', 'user-management']
    const firstAvailablePage = desiredOrder.find(id => navigation[id]) || Object.keys(navigation)[0] || 'parts'
    // Setting default page
    setCurrentPage(firstAvailablePage)
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    setUser(null)
    setOrganization(null)
    setPermissions([])
    setAccessibleDepartments([])
    setCurrentPage('dashboard')
  }

  const handleNavigate = (pageId) => {
    setCurrentPage(pageId)
  }

  // Check if user has permission to view a page
  const hasPermission = (permission) => {
    return permissions.includes(permission) || permissions.includes('*')
  }

  // Check if user can access a department
  const canAccessDepartment = (department) => {
    return accessibleDepartments.includes(department) || 
           accessibleDepartments.includes('Dashboard') ||
           permissions.includes('*')
  }

  const renderPage = () => {
    if (!user) return null
    
    // Get accessible navigation for this user
    const navigation = getAccessibleNavigation(user)
    
    // Check if user has access to current page
    if (!navigation[currentPage]) {
      // Redirect to first available page using same order as Layout.jsx
      const desiredOrder = ['dashboard', 'parts', 'service', 'rental', 'accounting', 'minitrac', 'user-management']
      const firstAvailablePage = desiredOrder.find(id => navigation[id]) || Object.keys(navigation)[0]
      if (firstAvailablePage && firstAvailablePage !== currentPage) {
        setCurrentPage(firstAvailablePage)
        // Return the default page immediately instead of null
        return <Dashboard user={user} organization={organization} />
      }
      // If no navigation available, show dashboard as fallback
      return <Dashboard user={user} organization={organization} />
    }
    
    // Render the appropriate page
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard user={user} organization={organization} />
      case 'report-creator':
        return <ReportCreator user={user} organization={organization} />
      case 'reports':
        return <Reports user={user} organization={organization} />
      case 'rental-diagnostic':
        return <RentalDiagnostic user={user} organization={organization} />
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
      case 'user-management':
        return <UserManagement user={user} />
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
    <PermissionsContext.Provider value={{ user, navigation: getAccessibleNavigation(user) }}>
      <Layout 
        user={user} 
        onLogout={handleLogout}
        currentPage={currentPage}
        onNavigate={handleNavigate}
        permissions={permissions}
        accessibleDepartments={accessibleDepartments}
      >
        {renderPage()}
      </Layout>
    </PermissionsContext.Provider>
  )
}

export default App

