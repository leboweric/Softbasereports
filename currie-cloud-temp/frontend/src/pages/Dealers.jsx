import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { get } from '../lib/api'
import { Building2, Plus, Search } from 'lucide-react'

export default function Dealers() {
  const [searchTerm, setSearchTerm] = useState('')

  const { data, isLoading, error } = useQuery({
    queryKey: ['dealers'],
    queryFn: () => get('/api/dealers'),
  })

  const dealers = data?.dealers || []

  const filteredDealers = dealers.filter(dealer =>
    dealer.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    dealer.code?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dealers</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage dealer accounts and ERP connections
          </p>
        </div>
        <button className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-currie-600 hover:bg-currie-700">
          <Plus className="w-4 h-4 mr-2" />
          Add Dealer
        </button>
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search dealers..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 w-full max-w-md px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-currie-500 focus:border-currie-500"
          />
        </div>
      </div>

      {/* Dealers Table */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Loading dealers...</div>
        ) : error ? (
          <div className="p-8 text-center text-red-500">
            Error loading dealers: {error.message}
          </div>
        ) : filteredDealers.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <Building2 className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>No dealers found</p>
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Dealer
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ERP System
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Subscription
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredDealers.map((dealer) => (
                <tr key={dealer.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <Building2 className="w-8 h-8 text-gray-400 mr-3" />
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {dealer.name}
                        </div>
                        <div className="text-sm text-gray-500">
                          {dealer.code}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {dealer.erp_system || 'Not configured'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                      {dealer.subscription_tier}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      dealer.is_active
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {dealer.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button className="text-currie-600 hover:text-currie-900">
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
