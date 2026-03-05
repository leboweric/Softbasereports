import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { apiUrl } from '@/lib/api'
import {
  Package,
  RefreshCw,
  Building2,
  Warehouse,
  Search,
  Filter
} from 'lucide-react'

const AlohaInventory = ({ user, organization }) => {
  const [loading, setLoading] = useState(true)
  const [inventoryData, setInventoryData] = useState(null)
  const [subsidiaryFilter, setSubsidiaryFilter] = useState('all')

  useEffect(() => {
    fetchInventory()
  }, [subsidiaryFilter])

  const fetchInventory = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl(`/api/aloha/dashboard/inventory?subsidiary=${subsidiaryFilter}`), {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setInventoryData(data)
      }
    } catch (err) {
      console.error('Inventory fetch error:', err)
    }
    setLoading(false)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-teal-500" />
        <span className="ml-3 text-gray-600">Loading inventory...</span>
      </div>
    )
  }

  const isAwaitingConnection = inventoryData?.status === 'awaiting_erp_connection' || inventoryData?.status === 'awaiting_sap_connection'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Package className="h-7 w-7 text-purple-600" />
            Consolidated Inventory
          </h1>
          <p className="text-gray-500 mt-1">
            Inventory across all subsidiary warehouses
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
            value={subsidiaryFilter}
            onChange={(e) => setSubsidiaryFilter(e.target.value)}
          >
            <option value="all">All Subsidiaries</option>
            <optgroup label="SAP">
              <option value="sap_sandia">Sandia</option>
              <option value="sap_mercury">Mercury</option>
              <option value="sap_ultimate_solutions">Ultimate Solutions</option>
              <option value="sap_avalon">Avalon</option>
              <option value="sap_orbot">Orbot</option>
            </optgroup>
            <optgroup label="NetSuite">
              <option value="ns_hawaii_care">Hawaii Care and Cleaning</option>
              <option value="ns_kauai_exclusive">Kauai Exclusive</option>
              <option value="ns_heavenly_vacations">Heavenly Vacations</option>
            </optgroup>
          </select>
          <Button variant="outline" size="sm" onClick={fetchInventory}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {isAwaitingConnection ? (
        <Card className="border-2 border-dashed border-gray-200">
          <CardContent className="py-16 text-center">
            <Package className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-600">Inventory Data Unavailable</h3>
            <p className="text-gray-400 mt-2 max-w-md mx-auto">
              Connect your ERP systems (SAP and NetSuite) to view consolidated inventory data.
              Stock levels, warehouse locations, and valuations will sync automatically.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="pt-4">
                <div className="flex items-center gap-2">
                  <Package className="h-5 w-5 text-purple-500" />
                  <span className="text-sm text-gray-500">Total Items</span>
                </div>
                <p className="text-2xl font-bold mt-1">
                  {inventoryData?.summary?.total_items?.toLocaleString() || '—'}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <div className="flex items-center gap-2">
                  <Warehouse className="h-5 w-5 text-blue-500" />
                  <span className="text-sm text-gray-500">Warehouses</span>
                </div>
                <p className="text-2xl font-bold mt-1">
                  {inventoryData?.summary?.by_warehouse?.length || '—'}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <div className="flex items-center gap-2">
                  <Package className="h-5 w-5 text-green-500" />
                  <span className="text-sm text-gray-500">Total Value</span>
                </div>
                <p className="text-2xl font-bold mt-1">
                  {inventoryData?.summary?.total_value ? `$${inventoryData.summary.total_value.toLocaleString()}` : '—'}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Inventory table placeholder */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Inventory Items</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-center h-48 text-gray-400">
                <p>Inventory data will populate once ERP ETL is configured</p>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}

export default AlohaInventory
