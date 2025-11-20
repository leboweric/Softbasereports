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
              As of {new Date(data.as_of_date).toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              })}
            </CardDescription>
          </div>
          {getHealthBadge(data.health_status)}
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
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

          {/* Total Cash Movement */}
          <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
            <div className="flex items-center gap-2 text-purple-600 dark:text-purple-400 mb-2">
              {data.total_cash_movement >= 0 ? (
                <TrendingUp className="h-4 w-4" />
              ) : (
                <TrendingDown className="h-4 w-4" />
              )}
              <span className="text-sm font-medium">Monthly Change</span>
            </div>
            <div className={`text-2xl font-bold ${
              data.total_cash_movement >= 0 
                ? 'text-purple-900 dark:text-purple-100' 
                : 'text-red-900 dark:text-red-100'
            }`}>
              {formatCurrency(data.total_cash_movement)}
            </div>
            <div className="text-xs text-purple-600 dark:text-purple-400 mt-1">
              Total cash movement
            </div>
          </div>

          {/* Other Activities */}
          <div className="bg-orange-50 dark:bg-orange-900/20 p-4 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 text-orange-600 dark:text-orange-400">
                <DollarSign className="h-4 w-4" />
                <span className="text-sm font-medium">Other Activities</span>
              </div>
              {data.non_operating_breakdown && data.non_operating_breakdown.breakdown.length > 0 && (
                <button 
                  onClick={() => setShowBreakdown(!showBreakdown)}
                  className="text-orange-600 dark:text-orange-400 hover:text-orange-700 dark:hover:text-orange-300 transition-colors"
                  aria-label={showBreakdown ? "Hide breakdown" : "Show breakdown"}
                >
                  {showBreakdown ? (
                    <ChevronUp className="h-4 w-4" />
                  ) : (
                    <ChevronDown className="h-4 w-4" />
                  )}
                </button>
              )}
            </div>
            <div className={`text-2xl font-bold ${
              data.non_operating_cashflow >= 0 
                ? 'text-orange-900 dark:text-orange-100' 
                : 'text-red-900 dark:text-red-100'
            }`}>
              {formatCurrency(data.non_operating_cashflow)}
            </div>
            <div className="text-xs text-orange-600 dark:text-orange-400 mt-1">
              Investing & financing
            </div>
            
            {/* Breakdown Details */}
            {showBreakdown && data.non_operating_breakdown && (
              <div className="mt-4 pt-4 border-t border-orange-200 dark:border-orange-800 space-y-2">
                {/* Summary by Activity Type */}
                <div className="space-y-1">
                  {data.non_operating_breakdown.summary.working_capital !== 0 && (
                    <div className="flex justify-between text-xs">
                      <span className="text-orange-700 dark:text-orange-300">Working Capital:</span>
                      <span className="font-medium text-orange-900 dark:text-orange-100">
                        {formatCurrency(data.non_operating_breakdown.summary.working_capital)}
                      </span>
                    </div>
                  )}
                  {data.non_operating_breakdown.summary.investing !== 0 && (
                    <div className="flex justify-between text-xs">
                      <span className="text-orange-700 dark:text-orange-300">Investing:</span>
                      <span className="font-medium text-orange-900 dark:text-orange-100">
                        {formatCurrency(data.non_operating_breakdown.summary.investing)}
                      </span>
                    </div>
                  )}
                  {data.non_operating_breakdown.summary.financing !== 0 && (
                    <div className="flex justify-between text-xs">
                      <span className="text-orange-700 dark:text-orange-300">Financing:</span>
                      <span className="font-medium text-orange-900 dark:text-orange-100">
                        {formatCurrency(data.non_operating_breakdown.summary.financing)}
                      </span>
                    </div>
                  )}
                  {data.non_operating_breakdown.summary.other !== 0 && (
                    <div className="flex justify-between text-xs">
                      <span className="text-orange-700 dark:text-orange-300">Other:</span>
                      <span className="font-medium text-orange-900 dark:text-orange-100">
                        {formatCurrency(data.non_operating_breakdown.summary.other)}
                      </span>
                    </div>
                  )}
                </div>
                
                {/* Detailed Breakdown */}
                {data.non_operating_breakdown.breakdown.length > 0 && (
                  <details className="mt-2">
                    <summary className="text-xs text-orange-600 dark:text-orange-400 cursor-pointer hover:text-orange-700 dark:hover:text-orange-300">
                      View detailed breakdown
                    </summary>
                    <div className="mt-2 space-y-1 text-xs max-h-48 overflow-y-auto">
                      {data.non_operating_breakdown.breakdown.map((item, idx) => (
                        <div key={idx} className="flex justify-between py-1">
                          <span className="text-orange-700 dark:text-orange-300">{item.category}:</span>
                          <span className="font-medium text-orange-900 dark:text-orange-100">
                            {formatCurrency(item.amount)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </details>
                )}
              </div>
            )}
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
                  formatter={(value) => formatCurrency(value)}
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
