import { useAuth } from '../hooks/useAuth'
import { Building2, Users, TrendingUp, Calendar } from 'lucide-react'

export default function Dashboard() {
  const { user, dealer, isCurrieAdmin } = useAuth()

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back, {user?.first_name || user?.username}
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          {isCurrieAdmin
            ? 'Currie Cloud Platform Administration'
            : `${dealer?.name || 'Your Dealership'} Dashboard`}
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title={isCurrieAdmin ? 'Total Dealers' : 'Active Users'}
          value={isCurrieAdmin ? '—' : '—'}
          icon={Building2}
          change="+12%"
        />
        <StatCard
          title={isCurrieAdmin ? 'Active Users' : 'Open Work Orders'}
          value="—"
          icon={Users}
          change="+5%"
        />
        <StatCard
          title="MTD Revenue"
          value="—"
          icon={TrendingUp}
          change="+8%"
        />
        <StatCard
          title="Last Sync"
          value="—"
          icon={Calendar}
          subtitle="Never"
        />
      </div>

      {/* Getting Started Section */}
      <div className="mt-8 bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Getting Started
        </h2>
        <div className="space-y-4">
          <div className="flex items-start">
            <div className="flex-shrink-0 w-8 h-8 bg-currie-100 text-currie-600 rounded-full flex items-center justify-center font-semibold text-sm">
              1
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-900">
                Configure ERP Connection
              </h3>
              <p className="text-sm text-gray-500">
                Connect your Softbase Evolution database to start syncing data.
              </p>
            </div>
          </div>
          <div className="flex items-start">
            <div className="flex-shrink-0 w-8 h-8 bg-gray-100 text-gray-400 rounded-full flex items-center justify-center font-semibold text-sm">
              2
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-900">
                Initial Data Sync
              </h3>
              <p className="text-sm text-gray-500">
                Run your first data synchronization to import historical data.
              </p>
            </div>
          </div>
          <div className="flex items-start">
            <div className="flex-shrink-0 w-8 h-8 bg-gray-100 text-gray-400 rounded-full flex items-center justify-center font-semibold text-sm">
              3
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-900">
                Generate Reports
              </h3>
              <p className="text-sm text-gray-500">
                Access your Currie Financial Model and benchmark reports.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({ title, value, icon: Icon, change, subtitle }) {
  return (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="p-5">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <Icon className="h-6 w-6 text-gray-400" />
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 truncate">
                {title}
              </dt>
              <dd className="flex items-baseline">
                <div className="text-2xl font-semibold text-gray-900">
                  {value}
                </div>
                {change && (
                  <div className="ml-2 flex items-baseline text-sm font-semibold text-green-600">
                    {change}
                  </div>
                )}
                {subtitle && (
                  <div className="ml-2 text-sm text-gray-500">
                    {subtitle}
                  </div>
                )}
              </dd>
            </dl>
          </div>
        </div>
      </div>
    </div>
  )
}
