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
import { TrendingUp, TrendingDown, AlertTriangle, DollarSign } from 'lucide-react'
import { apiUrl } from '@/lib/api'

const ProfitLossWidget = () => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchPLData()
  }, [])

  const fetchPLData = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      
      const response = await fetch(apiUrl('/api/pl/widget'), {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error('Failed to fetch P&L data')
      }

      const result = await response.json()
      setData(result)
      setError(null)
    } catch (err) {
      console.error('Error fetching P&L data:', err)
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
      profitable: { variant: 'default', color: 'bg-green-500', label: 'Profitable' },
      break_even: { variant: 'secondary', color: 'bg-yellow-500', label: 'Break Even' },
      loss: { variant: 'destructive', color: 'bg-red-500', label: 'Loss' }
    }
    
    const config = variants[status] || variants.break_even
    
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
          <CardTitle>Monthly Profit & Loss</CardTitle>
          <CardDescription>Net profit/loss trends and metrics</CardDescription>
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
          <CardTitle>Monthly Profit & Loss</CardTitle>
          <CardDescription>Net profit/loss trends and metrics</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-red-500">
            <AlertTriangle className="h-5 w-5" />
            <span>Error loading P&L data: {error}</span>
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
            <CardTitle>Monthly Profit & Loss</CardTitle>
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
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {/* Current Month P&L */}
          <div className={`${
            data.current_pl >= 0 
              ? 'bg-green-50 dark:bg-green-900/20' 
              : 'bg-red-50 dark:bg-red-900/20'
          } p-4 rounded-lg`}>
            <div className={`flex items-center gap-2 mb-2 ${
              data.current_pl >= 0 
                ? 'text-green-600 dark:text-green-400' 
                : 'text-red-600 dark:text-red-400'
            }`}>
              {data.current_pl >= 0 ? (
                <TrendingUp className="h-4 w-4" />
              ) : (
                <TrendingDown className="h-4 w-4" />
              )}
              <span className="text-sm font-medium">Current Month P&L</span>
            </div>
            <div className={`text-2xl font-bold ${
              data.current_pl >= 0 
                ? 'text-green-900 dark:text-green-100' 
                : 'text-red-900 dark:text-red-100'
            }`}>
              {formatCurrency(data.current_pl)}
            </div>
            <div className={`text-xs mt-1 ${
              data.current_pl >= 0 
                ? 'text-green-600 dark:text-green-400' 
                : 'text-red-600 dark:text-red-400'
            }`}>
              Net profit/loss
            </div>
          </div>

          {/* YTD P&L */}
          <div className={`${
            data.ytd_pl >= 0 
              ? 'bg-blue-50 dark:bg-blue-900/20' 
              : 'bg-orange-50 dark:bg-orange-900/20'
          } p-4 rounded-lg`}>
            <div className={`flex items-center gap-2 mb-2 ${
              data.ytd_pl >= 0 
                ? 'text-blue-600 dark:text-blue-400' 
                : 'text-orange-600 dark:text-orange-400'
            }`}>
              <DollarSign className="h-4 w-4" />
              <span className="text-sm font-medium">YTD P&L</span>
            </div>
            <div className={`text-2xl font-bold ${
              data.ytd_pl >= 0 
                ? 'text-blue-900 dark:text-blue-100' 
                : 'text-orange-900 dark:text-orange-100'
            }`}>
              {formatCurrency(data.ytd_pl)}
            </div>
            <div className={`text-xs mt-1 ${
              data.ytd_pl >= 0 
                ? 'text-blue-600 dark:text-blue-400' 
                : 'text-orange-600 dark:text-orange-400'
            }`}>
              Year-to-date
            </div>
          </div>

          {/* Average Monthly P&L */}
          <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
            <div className="flex items-center gap-2 text-purple-600 dark:text-purple-400 mb-2">
              <TrendingUp className="h-4 w-4" />
              <span className="text-sm font-medium">Avg Monthly P&L</span>
            </div>
            <div className="text-2xl font-bold text-purple-900 dark:text-purple-100">
              {formatCurrency(data.avg_monthly_pl)}
            </div>
            <div className="text-xs text-purple-600 dark:text-purple-400 mt-1">
              12-month average
            </div>
          </div>
        </div>

        {/* 12-Month Trend Chart */}
        {data.trend && data.trend.length > 0 && (
          <div className="mt-6">
            <h4 className="text-sm font-medium mb-4">12-Month Profit/Loss Trend</h4>
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
                  formatter={(value) => {
                    const color = value >= 0 ? '#10b981' : '#ef4444'
                    return [
                      <span style={{ color }}>{formatCurrency(value)}</span>,
                      'P&L'
                    ]
                  }}
                  labelFormatter={(label) => `Month: ${label}`}
                />
                <ReferenceLine y={0} stroke="#666" strokeDasharray="3 3" />
                <Line 
                  type="monotone" 
                  dataKey="profit_loss" 
                  stroke="#10b981" 
                  strokeWidth={2}
                  dot={(props) => {
                    const { cx, cy, payload } = props
                    const color = payload.profit_loss >= 0 ? '#10b981' : '#ef4444'
                    return <circle cx={cx} cy={cy} r={4} fill={color} />
                  }}
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

export default ProfitLossWidget
