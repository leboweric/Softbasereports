import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import {
  LayoutDashboard,
  Building2,
  FileBarChart,
  LogOut,
  Menu,
  X
} from 'lucide-react'
import { useState } from 'react'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Dealers', href: '/dealers', icon: Building2, adminOnly: true },
  { name: 'Reports', href: '/reports', icon: FileBarChart },
]

export default function Layout() {
  const { user, dealer, logout, isCurrieAdmin } = useAuth()
  const location = useLocation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const filteredNav = navigation.filter(
    item => !item.adminOnly || isCurrieAdmin
  )

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 justify-between items-center">
            {/* Logo */}
            <div className="flex items-center">
              <span className="text-xl font-bold text-currie-600">
                Currie Cloud
              </span>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex space-x-8">
              {filteredNav.map((item) => {
                const isActive = location.pathname === item.href
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`inline-flex items-center px-1 pt-1 text-sm font-medium border-b-2 ${
                      isActive
                        ? 'border-currie-500 text-gray-900'
                        : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    }`}
                  >
                    <item.icon className="w-4 h-4 mr-2" />
                    {item.name}
                  </Link>
                )
              })}
            </nav>

            {/* User Menu */}
            <div className="flex items-center space-x-4">
              <div className="hidden md:block text-sm">
                <span className="text-gray-500">
                  {user?.first_name || user?.username}
                </span>
                {dealer && (
                  <span className="ml-2 text-xs text-gray-400">
                    ({dealer.name})
                  </span>
                )}
              </div>
              <button
                onClick={logout}
                className="text-gray-500 hover:text-gray-700"
                title="Logout"
              >
                <LogOut className="w-5 h-5" />
              </button>

              {/* Mobile menu button */}
              <button
                className="md:hidden"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                {mobileMenuOpen ? (
                  <X className="w-6 h-6" />
                ) : (
                  <Menu className="w-6 h-6" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-gray-200">
            <div className="space-y-1 px-4 py-3">
              {filteredNav.map((item) => {
                const isActive = location.pathname === item.href
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`block px-3 py-2 rounded-md text-base font-medium ${
                      isActive
                        ? 'bg-currie-50 text-currie-700'
                        : 'text-gray-600 hover:bg-gray-50'
                    }`}
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    <div className="flex items-center">
                      <item.icon className="w-5 h-5 mr-3" />
                      {item.name}
                    </div>
                  </Link>
                )
              })}
            </div>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  )
}
