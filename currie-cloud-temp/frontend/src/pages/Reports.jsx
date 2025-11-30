import { useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { FileBarChart, Download, Calendar } from 'lucide-react'

export default function Reports() {
  const { dealer, isCurrieAdmin } = useAuth()
  const [dateRange, setDateRange] = useState({
    start: '',
    end: ''
  })

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
        <p className="mt-1 text-sm text-gray-500">
          Generate and download financial reports
        </p>
      </div>

      {/* Report Selection */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Currie Financial Model */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center mb-4">
            <FileBarChart className="w-8 h-8 text-currie-600 mr-3" />
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                Currie Financial Model
              </h2>
              <p className="text-sm text-gray-500">
                Complete P&L breakdown by department
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Start Date
                </label>
                <input
                  type="date"
                  value={dateRange.start}
                  onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-currie-500 focus:border-currie-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  End Date
                </label>
                <input
                  type="date"
                  value={dateRange.end}
                  onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-currie-500 focus:border-currie-500"
                />
              </div>
            </div>

            <button
              disabled={!dateRange.start || !dateRange.end}
              className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-currie-600 hover:bg-currie-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FileBarChart className="w-4 h-4 mr-2" />
              Generate Report
            </button>
          </div>
        </div>

        {/* Benchmark Report */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center mb-4">
            <FileBarChart className="w-8 h-8 text-green-600 mr-3" />
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                Industry Benchmarks
              </h2>
              <p className="text-sm text-gray-500">
                Compare your performance to industry averages
              </p>
            </div>
          </div>

          <div className="p-4 bg-gray-50 rounded-md text-center">
            <p className="text-sm text-gray-600">
              Benchmarking requires Professional or Enterprise subscription.
            </p>
            <button className="mt-3 text-sm text-currie-600 hover:text-currie-800 font-medium">
              Upgrade Subscription
            </button>
          </div>
        </div>
      </div>

      {/* Recent Reports */}
      <div className="mt-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Recent Reports
        </h2>
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="p-8 text-center text-gray-500">
            <Calendar className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>No reports generated yet</p>
            <p className="text-sm mt-1">
              Generate your first report using the options above
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
