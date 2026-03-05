import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { apiUrl } from '@/lib/api'
import {
  ShoppingCart,
  RefreshCw,
  Building2,
  Clock,
  CheckCircle,
  Filter
} from 'lucide-react'

const AlohaOrders = ({ user, organization }) => {
  const [loading, setLoading] = useState(true)
  const [orderData, setOrderData] = useState(null)
  const [subsidiaryFilter, setSubsidiaryFilter] = useState('all')
  const [days, setDays] = useState(30)
  const [allowedSubs, setAllowedSubs] = useState(null)

  useEffect(() => {
    fetchMyAccess()
  }, [])

  useEffect(() => {
    fetchOrders()
  }, [subsidiaryFilter, days])

  const fetchMyAccess = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/aloha/subsidiary-access'), {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setAllowedSubs(data.subsidiary_details || [])
      }
    } catch (err) {
      console.error('Access fetch error:', err)
    }
  }

  const fetchOrders = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl(`/api/aloha/dashboard/orders?subsidiary=${subsidiaryFilter}&days=${days}`), {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setOrderData(data)
      }
    } catch (err) {
      console.error('Orders fetch error:', err)
    }
    setLoading(false)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-teal-500" />
        <span className="ml-3 text-gray-600">Loading orders...</span>
      </div>
    )
  }

  const isAwaitingConnection = orderData?.status === 'awaiting_erp_connection' || orderData?.status === 'awaiting_sap_connection'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <ShoppingCart className="h-7 w-7 text-blue-600" />
            Consolidated Orders
          </h1>
          <p className="text-gray-500 mt-1">
            Sales and purchase orders across all subsidiaries
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
            value={subsidiaryFilter}
            onChange={(e) => setSubsidiaryFilter(e.target.value)}
          >
            <option value="all">All Subsidiaries</option>
            {allowedSubs && allowedSubs.filter(s => s.erp_type === 'SAP').length > 0 && (
              <optgroup label="SAP">
                {allowedSubs.filter(s => s.erp_type === 'SAP').map(s => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </optgroup>
            )}
            {allowedSubs && allowedSubs.filter(s => s.erp_type === 'NetSuite').length > 0 && (
              <optgroup label="NetSuite">
                {allowedSubs.filter(s => s.erp_type === 'NetSuite').map(s => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </optgroup>
            )}
          </select>
          <select
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
            value={days}
            onChange={(e) => setDays(parseInt(e.target.value))}
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
          <Button variant="outline" size="sm" onClick={fetchOrders}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {isAwaitingConnection ? (
        <Card className="border-2 border-dashed border-gray-200">
          <CardContent className="py-16 text-center">
            <ShoppingCart className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-600">Order Data Unavailable</h3>
            <p className="text-gray-400 mt-2 max-w-md mx-auto">
              Connect your ERP systems (SAP and NetSuite) to view consolidated order data.
              Sales orders, purchase orders, and delivery status will sync automatically.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-4">
                <p className="text-sm text-gray-500">Total Orders</p>
                <p className="text-2xl font-bold mt-1">
                  {orderData?.summary?.total_orders?.toLocaleString() || '—'}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <p className="text-sm text-gray-500">Order Value</p>
                <p className="text-2xl font-bold mt-1">
                  {orderData?.summary?.total_value ? `$${orderData.summary.total_value.toLocaleString()}` : '—'}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <div className="flex items-center gap-1">
                  <Clock className="h-4 w-4 text-yellow-500" />
                  <p className="text-sm text-gray-500">Open</p>
                </div>
                <p className="text-2xl font-bold mt-1">
                  {orderData?.summary?.open_orders?.toLocaleString() || '—'}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <div className="flex items-center gap-1">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <p className="text-sm text-gray-500">Completed</p>
                </div>
                <p className="text-2xl font-bold mt-1">
                  {orderData?.summary?.completed_orders?.toLocaleString() || '—'}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Orders table placeholder */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Recent Orders</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-center h-48 text-gray-400">
                <p>Order data will populate once ERP ETL is configured</p>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}

export default AlohaOrders
