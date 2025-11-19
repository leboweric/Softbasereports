import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import * as Icons from 'lucide-react'

const Layout = ({ children, user, onLogout, currentPage, onNavigate, permissions = [], accessibleDepartments = [] }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  
  // Layout rendering
  
  const navigation = user?.navigation || {}
  const hasNavigation = Object.keys(navigation).length > 0
  
  // Navigation data processed

  // Build navigation items with HARDCODED ORDER to fix menu
  const desiredOrder = ['dashboard', 'parts', 'service', 'rental', 'accounting', 'knowledge-base', 'financial', 'minitrac', 'database-explorer', 'user-management', 'tenant-admin']
  
  const navItems = hasNavigation 
    ? desiredOrder
        .filter(id => navigation[id]) // Only include items user has access to
        .map(id => {
          const config = navigation[id]
          const IconComponent = Icons[config.icon] || Icons.Circle
          
          return {
            id,
            label: config.label,
            icon: IconComponent,
            order: config.order || 999,
          }
        })
    : []

  // Navigation items built

  const handleNavigation = (pageId) => {
    onNavigate(pageId)
    setSidebarOpen(false)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar */}
      <div className={`fixed inset-0 z-50 lg:hidden ${sidebarOpen ? 'block' : 'hidden'}`}>
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
        <div className="fixed inset-y-0 left-0 flex w-64 flex-col bg-white">
          <div className="flex h-16 items-center justify-between px-4 border-b">
            <div className="flex items-center space-x-3">
              {/* Company Logo - Replace src with your company logo */}
              <img 
                src="/bennett-logo.png" 
                alt="Bennett Equipment" 
                className="h-10 w-auto"
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'block';
                }}
              />
              <h1 className="text-lg font-bold text-gray-900" style={{ display: 'none' }}>BIS</h1>
            </div>
            <Button variant="ghost" size="sm" onClick={() => setSidebarOpen(false)}>
              <Icons.X className="h-5 w-5" />
            </Button>
          </div>
          <nav className="flex-1 space-y-1 px-2 py-4">
            {!hasNavigation ? (
              <div className="p-4 text-gray-500">Loading menu...</div>
            ) : (
              navItems.map((item) => {
                const Icon = item.icon
                return (
                  <button
                    key={item.label}
                    onClick={() => handleNavigation(item.id)}
                    className={`group flex w-full items-center rounded-md px-2 py-2 text-sm font-medium ${
                      currentPage === item.id
                        ? 'bg-blue-100 text-blue-900'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                  >
                    <Icon className="mr-3 h-5 w-5 flex-shrink-0" />
                    {item.label}
                    {(item.id === 'ai-query' || item.id === 'ai-query-tester') && (
                      <Badge variant="secondary" className="ml-auto text-xs">
                        AI
                      </Badge>
                    )}
                  </button>
                )
              })
            )}
          </nav>
          <div className="border-t p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center">
                  <span className="text-sm font-medium text-white">
                    {user?.first_name?.[0] || 'U'}
                  </span>
                </div>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-700">
                  {user?.first_name} {user?.last_name}
                </p>
                <p className="text-xs text-gray-500">{user?.email}</p>
              </div>
            </div>
            <Button
              onClick={onLogout}
              variant="ghost"
              size="sm"
              className="mt-3 w-full justify-start"
            >
              <Icons.LogOut className="mr-2 h-4 w-4" />
              Sign out
            </Button>
          </div>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex flex-col flex-grow bg-white border-r border-gray-200">
          <div className="flex h-16 items-center px-4 border-b">
            <div className="flex items-center space-x-3">
              {/* Company Logo - Replace src with your company logo */}
              <img 
                src="/bennett-logo.png" 
                alt="Bennett Equipment" 
                className="h-10 w-auto"
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'block';
                }}
              />
              <h1 className="text-lg font-bold text-gray-900" style={{ display: 'none' }}>BIS</h1>
            </div>
          </div>
          <nav className="flex-1 space-y-1 px-2 py-4">
            {!hasNavigation ? (
              <div className="p-4 text-gray-500">Loading menu...</div>
            ) : (
              navItems.map((item) => {
                const Icon = item.icon
                return (
                  <button
                    key={item.label}
                    onClick={() => handleNavigation(item.id)}
                    className={`group flex w-full items-center rounded-md px-2 py-2 text-sm font-medium ${
                      currentPage === item.id
                        ? 'bg-blue-100 text-blue-900'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                  >
                    <Icon className="mr-3 h-5 w-5 flex-shrink-0" />
                    {item.label}
                    {(item.id === 'ai-query' || item.id === 'ai-query-tester') && (
                      <Badge variant="secondary" className="ml-auto text-xs">
                        AI
                      </Badge>
                    )}
                  </button>
                )
              })
            )}
          </nav>
          <div className="border-t p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center">
                  <span className="text-sm font-medium text-white">
                    {user?.first_name?.[0] || 'U'}
                  </span>
                </div>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-700">
                  {user?.first_name} {user?.last_name}
                </p>
                <p className="text-xs text-gray-500">{user?.email}</p>
              </div>
            </div>
            <Button
              onClick={onLogout}
              variant="ghost"
              size="sm"
              className="mt-3 w-full justify-start"
            >
              <Icons.LogOut className="mr-2 h-4 w-4" />
              Sign out
            </Button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Mobile header */}
        <div className="sticky top-0 z-40 flex h-16 items-center gap-x-4 border-b border-gray-200 bg-white px-4 shadow-sm lg:hidden">
          <Button variant="ghost" size="sm" onClick={() => setSidebarOpen(true)}>
            <Icons.Menu className="h-5 w-5" />
          </Button>
          <div className="flex-1 text-sm font-semibold leading-6 text-gray-900">
            {navItems.find(item => item.id === currentPage)?.name || 'Dashboard'}
          </div>
        </div>

        {/* Page content */}
        <main className="py-6">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}

export default Layout

