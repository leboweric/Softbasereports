import React, { useState, useEffect, useMemo } from 'react'
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
  ReferenceLine,
  Legend
} from 'recharts'
import { TrendingUp, TrendingDown, AlertTriangle, DollarSign } from 'lucide-react'
import { apiUrl } from '@/lib/api'

// Utility function to calculate linear regression trendline for P&L data
// Modified to handle negative values (losses)
const calculateLinearTrend = (data, yKey, excludeCurrentMonth = true) => {
  if (!data || data.length === 0) return []

  // Ensure all data has a numeric value for the yKey
  const cleanedData = data.map(item => ({
    ...item,
    [yKey]: parseFloat(item[yKey]) || 0
  }))

  // For P&L, we want to include all data points (including negative/loss months)
  // Find the first month with any data (non-null)
  const firstDataIndex = cleanedData.findIndex(item => item[yKey] !== null && item[yKey] !== undefined)

  if (firstDataIndex === -1) {
    return cleanedData.map(item => ({ ...item, trendValue: null }))
  }

  // Get data from the first month with data
  const dataFromFirstMonth = cleanedData.slice(firstDataIndex)

  let trendData = dataFromFirstMonth
  if (excludeCurrentMonth && dataFromFirstMonth.length > 1) {
    trendData = dataFromFirstMonth.slice(0, -1)
  }

  if (trendData.length < 2) {
    return cleanedData.map(item => ({ ...item, trendValue: null }))
  }

  // Calculate linear regression
  const n = trendData.length
  const sumX = trendData.reduce((sum, _, index) => sum + index, 0)
  const sumY = trendData.reduce((sum, item) => sum + item[yKey], 0)
  const sumXY = trendData.reduce((sum, item, index) => sum + (index * item[yKey]), 0)
  const sumXX = trendData.reduce((sum, _, index) => sum + (index * index), 0)

  const denominator = (n * sumXX - sumX * sumX)
  if (denominator === 0) {
    return cleanedData.map(item => ({ ...item, trendValue: null }))
  }

  const slope = (n * sumXY - sumX * sumY) / denominator
  const intercept = (sumY - slope * sumX) / n

  return cleanedData.map((item, index) => {
    if (index < firstDataIndex) {
      return { ...item, trendValue: null }
    }
    const adjustedIndex = index - firstDataIndex
    return {
      ...item,
      trendValue: slope * adjustedIndex + intercept
    }
  })
}

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

  // Calculate trend data with linear regression
  const trendDataWithRegression = useMemo(() => {
    if (!data?.trend || data.trend.length === 0) return []
    return calculateLinearTrend(data.trend, 'profit_loss', true)
  }, [data?.trend])

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
              Net profit/loss trends and metrics
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
              ? 'bg-green-50 dark:bg-green-900/20' 
              : 'bg-red-50 dark:bg-red-900/20'
          } p-4 rounded-lg`}>
            <div className={`flex items-center gap-2 mb-2 ${
              data.ytd_pl >= 0 
                ? 'text-green-600 dark:text-green-400' 
                : 'text-red-600 dark:text-red-400'
            }`}>
              {data.ytd_pl >= 0 ? (
                <TrendingUp className="h-4 w-4" />
              ) : (
                <TrendingDown className="h-4 w-4" />
              )}
              <span className="text-sm font-medium">YTD P&L</span>
            </div>
            <div className={`text-2xl font-bold ${
              data.ytd_pl >= 0 
                ? 'text-green-900 dark:text-green-100' 
                : 'text-red-900 dark:text-red-100'
            }`}>
              {formatCurrency(data.ytd_pl)}
            </div>
            <div className={`text-xs mt-1 ${
              data.ytd_pl >= 0 
                ? 'text-green-600 dark:text-green-400' 
                : 'text-red-600 dark:text-red-400'
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
              Trailing average
            </div>
          </div>
        </div>

        {/* Trailing Trend Chart with Linear Regression */}
        {trendDataWithRegression && trendDataWithRegression.length > 0 && (
          <div className="mt-6">
            <h4 className="text-sm font-medium mb-4">Profit/Loss Trend</h4>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={trendDataWithRegression}>
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
                  formatter={(value, name) => {
                    if (name === 'trendValue') {
                      return [formatCurrency(value), 'Trend']
                    }
                    const color = value >= 0 ? '#10b981' : '#ef4444'
                    return [
                      <span style={{ color }}>{formatCurrency(value)}</span>,
                      'P&L'
                    ]
                  }}
                  labelFormatter={(label) => `Month: ${label}`}
                />
                <Legend />
                <ReferenceLine y={0} stroke="#666" strokeDasharray="3 3" />
                {/* Actual P&L Line */}
                <Line 
                  type="monotone" 
                  dataKey="profit_loss" 
                  stroke="#10b981" 
                  strokeWidth={2}
                  name="P&L"
                  dot={(props) => {
                    const { cx, cy, payload } = props
                    const color = payload.profit_loss >= 0 ? '#10b981' : '#ef4444'
                    return <circle cx={cx} cy={cy} r={4} fill={color} />
                  }}
                  activeDot={{ r: 6 }}
                />
                {/* Linear Regression Trend Line */}
                <Line 
                  type="monotone" 
                  dataKey="trendValue" 
                  stroke="#8b5cf6" 
                  strokeWidth={2} 
                  strokeDasharray="5 5" 
                  name="Trend"
                  dot={false}
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
