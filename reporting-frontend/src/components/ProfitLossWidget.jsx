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

// Helper: compute linear regression over a set of (x, y) points
const linearRegression = (points) => {
  const n = points.length
  if (n < 2) return null
  const sumX = points.reduce((s, p) => s + p.x, 0)
  const sumY = points.reduce((s, p) => s + p.y, 0)
  const sumXY = points.reduce((s, p) => s + p.x * p.y, 0)
  const sumX2 = points.reduce((s, p) => s + p.x * p.x, 0)
  const denom = n * sumX2 - sumX * sumX
  if (denom === 0) return null
  const slope = (n * sumXY - sumX * sumY) / denom
  const intercept = (sumY - slope * sumX) / n
  return { slope, intercept }
}

const ProfitLossWidget = () => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Calculate both full-period and trailing 3-month trendlines
  const { chartData, longSlope, shortSlope } = useMemo(() => {
    if (!data?.trend || data.trend.length < 2) return { chartData: null, longSlope: null, shortSlope: null }

    // Find the first month with data
    const firstDataIndex = data.trend.findIndex(item => item.profit_loss !== null && item.profit_loss !== undefined)
    if (firstDataIndex === -1) return { chartData: null, longSlope: null, shortSlope: null }

    // Build points from first data month onward
    const allPoints = data.trend.map((item, i) => ({ x: i, y: parseFloat(item.profit_loss) || 0 }))
    const dataPoints = allPoints.slice(firstDataIndex)

    // Full-period trendline (exclude current month for stability)
    const fullPoints = dataPoints.length > 2 ? dataPoints.slice(0, -1) : dataPoints
    const fullReg = linearRegression(fullPoints.map((p, i) => ({ x: i, y: p.y })))

    // Trailing 3-month trendline
    const TRAILING = 3
    const trailingStartIdx = Math.max(firstDataIndex, data.trend.length - TRAILING)
    const trailingPoints = allPoints.slice(trailingStartIdx)
    const shortReg = trailingPoints.length >= 2
      ? linearRegression(trailingPoints.map((p, i) => ({ x: i, y: p.y })))
      : null

    const points = data.trend.map((item, i) => ({
      ...item,
      profit_loss: parseFloat(item.profit_loss) || 0,
      trendValue: (fullReg && i >= firstDataIndex)
        ? fullReg.intercept + fullReg.slope * (i - firstDataIndex)
        : undefined,
      shortTrend: (shortReg && i >= trailingStartIdx)
        ? shortReg.intercept + shortReg.slope * (i - trailingStartIdx)
        : undefined
    }))

    return {
      chartData: points,
      longSlope: fullReg ? fullReg.slope : null,
      shortSlope: shortReg ? shortReg.slope : null
    }
  }, [data])

  useEffect(() => {
    fetchPLData()
  }, [])

  const fetchPLData = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      
      const response = await fetch(apiUrl('/api/pl/widget?refresh=true'), {
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

        {/* Trailing Trend Chart with Dual Trendlines */}
        {chartData && chartData.length > 0 && (
          <div className="mt-6">
            <h4 className="text-sm font-medium mb-4">Profit/Loss Trend</h4>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={chartData}>
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
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                          <p className="font-semibold mb-2">{label}</p>
                          {payload.map((entry, index) => {
                            // For trendlines, show slope (rate of change per month)
                            if (entry.dataKey === 'trendValue' && longSlope !== null) {
                              return (
                                <p key={index} style={{ color: entry.color }}>
                                  {entry.name}: {longSlope >= 0 ? '+' : ''}{formatCurrency(longSlope)}/mo
                                </p>
                              )
                            }
                            if (entry.dataKey === 'shortTrend' && shortSlope !== null) {
                              return (
                                <p key={index} style={{ color: entry.color }}>
                                  {entry.name}: {shortSlope >= 0 ? '+' : ''}{formatCurrency(shortSlope)}/mo
                                </p>
                              )
                            }
                            // For P&L, color based on positive/negative
                            const color = entry.value >= 0 ? '#10b981' : '#ef4444'
                            return (
                              <p key={index} style={{ color }}>
                                {entry.name}: {formatCurrency(entry.value)}
                              </p>
                            )
                          })}
                        </div>
                      )
                    }
                    return null
                  }}
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
                {/* Long-term Trend Line */}
                {chartData && (
                  <Line 
                    type="linear" 
                    dataKey="trendValue" 
                    stroke="#f97316" 
                    strokeWidth={2} 
                    strokeDasharray="6 3" 
                    name="Long-term Trend"
                    dot={false}
                    activeDot={false}
                    connectNulls={false}
                  />
                )}
                {/* 3-Month Trailing Trend Line */}
                {chartData && (
                  <Line 
                    type="linear" 
                    dataKey="shortTrend" 
                    stroke="#ef4444" 
                    strokeWidth={2} 
                    strokeDasharray="4 2" 
                    name="3-Month Trend"
                    dot={false}
                    activeDot={false}
                    connectNulls={false}
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default ProfitLossWidget
