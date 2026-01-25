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
import DatabaseExplorer from './components/DatabaseExplorer'
import UserManagementEnhanced from './components/UserManagementEnhanced'
import { UserManagement } from './components/admin/UserManagement'
import { TenantManagement } from './components/admin/TenantManagement'
import KnowledgeBase from './components/KnowledgeBase'
import Currie from './components/Currie'
import Financial from './components/Financial'
import QBRDashboard from './components/QBRDashboard'
import Billing from './components/Billing'
import RepCompAdmin from './components/RepCompAdmin'
import MyCommissions from './components/MyCommissions'
import SchemaExplorer from './components/SchemaExplorer'
import VitalCaseData from './components/vital/VitalCaseData'
import VitalFinancial from './components/vital/VitalFinancial'
import VitalMarketing from './components/vital/VitalMarketing'
import VitalDataSources from './components/vital/VitalDataSources'
import VitalHubSpotDashboard from './components/vital/VitalHubSpotDashboard'
import VitalQuickBooksDashboard from './components/vital/VitalQuickBooksDashboard'
import VitalAzureSQLDashboard from './components/vital/VitalAzureSQLDashboard'
import VitalZoomDashboard from './components/vital/VitalZoomDashboard'
import VitalFinanceBilling from './components/vital/VitalFinanceBilling'
import VitalMobileAppDashboard from './components/vital/VitalMobileAppDashboard'
import VitalCustomer360 from './components/vital/VitalCustomer360'
import VitalSalesDashboard from './components/vital/VitalSalesDashboard'
import VitalMemberExperienceDashboard from './components/vital/VitalMemberExperienceDashboard'
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
  
  // Force deployment trigger - Parts Inventory Turns feature

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('token')
    if (token) {
      validateToken(token)
    } else {
      setLoading(false)
    }

    // Check URL params for billing redirect
    const urlParams = new URLSearchParams(window.location.search)
    if (urlParams.get('billing') || urlParams.get('page') === 'billing') {
      setCurrentPage('billing')
    }

    // Listen for custom navigation events
    const handleNavigate = (event) => {
      if (event.detail) {
        setCurrentPage(event.detail)
      }
    }
    window.addEventListener('navigate', handleNavigate)
    return () => window.removeEventListener('navigate', handleNavigate)
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
          // Menu order: Dashboard, Finance first, then other items (removed vital-quickbooks)
          const desiredOrder = ['dashboard', 'vital-finance', 'vital-mobile-app', 'vital-case-data', 'vital-financial', 'vital-marketing', 'vital-hubspot', 'vital-azure-sql', 'vital-zoom', 'parts', 'service', 'rental', 'accounting', 'knowledge-base', 'financial', 'qbr', 'my-commissions', 'minitrac', 'database-explorer', 'schema-explorer', 'vital-data-sources', 'user-management', 'rep-comp-admin', 'tenant-admin']
          const firstAvailablePage = desiredOrder.find(id => navigation[id]) || Object.keys(navigation)[0] || 'dashboard'
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
    // Menu order: Dashboard, Finance first, then other items (removed vital-quickbooks)
    const desiredOrder = ['dashboard', 'vital-finance', 'vital-mobile-app', 'vital-case-data', 'vital-financial', 'vital-marketing', 'vital-hubspot', 'vital-azure-sql', 'vital-zoom', 'parts', 'service', 'rental', 'accounting', 'knowledge-base', 'financial', 'qbr', 'my-commissions', 'minitrac', 'database-explorer', 'schema-explorer', 'vital-data-sources', 'user-management', 'rep-comp-admin', 'tenant-admin']
    const firstAvailablePage = desiredOrder.find(id => navigation[id]) || Object.keys(navigation)[0] || 'dashboard'
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
    // Note: 'billing' and 'settings' are special pages not in navigation, so always allow them
    const specialPages = ['billing', 'settings', 'vital-customer-360', 'vital-sales-dashboard', 'vital-member-experience']
    if (!navigation[currentPage] && !specialPages.includes(currentPage)) {
      // Redirect to first available page using same order as Layout.jsx
      // Menu order: Dashboard, Finance first, then other items (removed vital-quickbooks)
      const desiredOrder = ['dashboard', 'vital-finance', 'vital-mobile-app', 'vital-case-data', 'vital-financial', 'vital-marketing', 'vital-hubspot', 'vital-azure-sql', 'vital-zoom', 'parts', 'service', 'rental', 'accounting', 'knowledge-base', 'financial', 'qbr', 'my-commissions', 'minitrac', 'database-explorer', 'schema-explorer', 'vital-data-sources', 'user-management', 'rep-comp-admin', 'tenant-admin']
      const firstAvailablePage = desiredOrder.find(id => navigation[id]) || Object.keys(navigation)[0] || 'dashboard'
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
      case 'database-explorer':
        return <DatabaseExplorer user={user} organization={organization} />
      case 'schema-explorer':
        return <SchemaExplorer user={user} organization={organization} />
      case 'user-management':
        return <UserManagement user={user} />
      case 'tenant-admin':
        return <TenantManagement user={user} />
      case 'knowledge-base':
        return <KnowledgeBase user={user} organization={organization} />
      case 'currie':
        return <Currie user={user} organization={organization} />
      case 'financial':
        return <Financial user={user} organization={organization} />
      case 'qbr':
        return <QBRDashboard user={user} organization={organization} />
      case 'settings':
        return <div className="p-8 text-center text-gray-500">Settings coming soon...</div>
      case 'billing':
        return <Billing user={user} organization={organization} />
      case 'my-commissions':
        return <MyCommissions user={user} organization={organization} />
      case 'rep-comp-admin':
        return <RepCompAdmin user={user} organization={organization} />
      case 'schema-explorer':
        return <SchemaExplorer user={user} organization={organization} />
      case 'vital-case-data':
        return <VitalCaseData user={user} organization={organization} />
      case 'vital-financial':
        return <VitalFinancial user={user} organization={organization} />
      case 'vital-marketing':
        return <VitalMarketing user={user} organization={organization} />
      case 'vital-data-sources':
        return <VitalDataSources user={user} organization={organization} />
      case 'vital-hubspot':
        return <VitalHubSpotDashboard user={user} organization={organization} />
      case 'vital-quickbooks':
        return <VitalQuickBooksDashboard user={user} organization={organization} />
      case 'vital-azure-sql':
        return <VitalCustomer360 user={user} onBack={null} />
      case 'vital-zoom':
        return <VitalZoomDashboard user={user} organization={organization} />
      case 'vital-finance':
        return <VitalFinanceBilling user={user} organization={organization} />
      case 'vital-mobile-app':
        return <VitalMobileAppDashboard user={user} organization={organization} />
      case 'vital-customer-360':
        return <VitalCustomer360 user={user} onBack={() => setCurrentPage('vital-case-data')} />
      case 'vital-sales-dashboard':
        return <VitalSalesDashboard user={user} onBack={() => setCurrentPage('dashboard')} />
      case 'vital-member-experience':
        return <VitalMemberExperienceDashboard user={user} onBack={() => setCurrentPage('dashboard')} />
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

