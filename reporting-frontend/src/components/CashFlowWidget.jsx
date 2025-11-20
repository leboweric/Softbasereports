import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  ReferenceLine
} from 'recharts'
import { DollarSign, TrendingUp, TrendingDown, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react'
import { apiUrl } from '@/lib/api'

const CashFlowWidget = () => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showBreakdown, setShowBreakdown] = useState(false)

  useEffect(() => {
    fetchCashFlowData()
  }, [])

  const fetchCashFlowData = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      
      const response = await fetch(apiUrl('/api/cashflow/widget'), {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error('Failed to fetch cash flow data')
      }

      const result = await response.json()
      setData(result)
      setError(null)
    } catch (err) {
      console.error('Error fetching cash flow data:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (value) => {
    if (value === null || value === undefined) return '$0'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  const getHealthBadge = (status) => {
    const variants = {
      healthy: { variant: 'default', color: 'bg-green-500', label: 'Healthy' },
      warning: { variant: 'secondary', color: 'bg-yellow-500', label: 'Warning' },
      critical: { variant: 'destructive', color: 'bg-red-500', label: 'Critical' }
    }
    
    const config = variants[status] || variants.healthy
    
    return (
      <Badge variant={config.variant} className={config.color}>
        {config.label}
      </Badge>
    )
  }

  if (loading) {
    return (
      <Card className="col-span-full">
        <CardHeader>
          <CardTitle>Cash Flow Overview</CardTitle>
          <CardDescription>Current cash position and trends</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-8">
          <LoadingSpinner />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="col-span-full">
        <CardHeader>
          <CardTitle>Cash Flow Overview</CardTitle>
          <CardDescription>Current cash position and trends</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-red-500">
            <AlertTriangle className="h-5 w-5" />
            <span>Error loading cash flow data: {error}</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!data) {
    return null
  }

  return (
    <Card className="col-span-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Cash Flow Overview</CardTitle>
            <CardDescription>
              As of {data.as_of_date ? new Date(data.as_of_date + 'T12:00:00').toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              }) : 'Loading...'}
            </CardDescription>
          </div>
          {getHealthBadge(data.health_status)}
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {/* Cash Balance */}
          <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
            <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400 mb-2">
              <DollarSign className="h-4 w-4" />
              <span className="text-sm font-medium">Cash Balance</span>
            </div>
            <div className="text-2xl font-bold text-blue-900 dark:text-blue-100">
              {formatCurrency(data.cash_balance)}
            </div>
            <div className="text-xs text-blue-600 dark:text-blue-400 mt-1">
              Actual cash on hand
            </div>
          </div>

          {/* Operating Cash Flow */}
          <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
            <div className="flex items-center gap-2 text-green-600 dark:text-green-400 mb-2">
              {data.operating_cashflow >= 0 ? (
                <TrendingUp className="h-4 w-4" />
              ) : (
                <TrendingDown className="h-4 w-4" />
              )}
              <span className="text-sm font-medium">Operating CF</span>
            </div>
            <div className={`text-2xl font-bold ${
              data.operating_cashflow >= 0 
                ? 'text-green-900 dark:text-green-100' 
                : 'text-red-900 dark:text-red-100'
            }`}>
              {formatCurrency(data.operating_cashflow)}
            </div>
            <div className="text-xs text-green-600 dark:text-green-400 mt-1">
              From operations
            </div>
          </div>


        </div>

        {/* 12-Month Trend Chart */}
        {data.trend && data.trend.length > 0 && (
          <div className="mt-6">
            <h4 className="text-sm font-medium mb-4">12-Month Cash Balance Trend</h4>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={data.trend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="month" 
                  tick={{ fontSize: 12 }}
                />
                <YAxis 
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                />
                <Tooltip 
                  formatter={(value) => [formatCurrency(value), 'Cash Balance']}
                  labelFormatter={(label) => `Month: ${label}`}
                />
                <Line 
                  type="monotone" 
                  dataKey="cashflow" 
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6', r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default CashFlowWidget
