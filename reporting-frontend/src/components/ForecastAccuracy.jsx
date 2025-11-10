import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine
} from 'recharts'
import { 
  TrendingUp, 
  TrendingDown,
  Target,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Activity
} from 'lucide-react'
import { apiUrl } from '@/lib/api'

const ForecastAccuracy = () => {
  const [accuracyData, setAccuracyData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [backfilling, setBackfilling] = useState(false)
  const [lastUpdated, setLastUpdated] = useState(null)

  useEffect(() => {
    fetchAccuracyData()
  }, [])

  const fetchAccuracyData = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/dashboard/forecast-accuracy'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to fetch accuracy data')
      }

      const data = await response.json()
      setAccuracyData(data)
      setLastUpdated(new Date())
    } catch (error) {
      console.error('Error fetching accuracy data:', error)
    } finally {
      setLoading(false)
    }
  }

  const backfillActuals = async () => {
    try {
      setBackfilling(true)
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/dashboard/forecast-accuracy/backfill'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to backfill actuals')
      }

      const result = await response.json()
      console.log('Backfill result:', result)
      
      // Refresh accuracy data after backfill
      await fetchAccuracyData()
    } catch (error) {
      console.error('Error backfilling actuals:', error)
    } finally {
      setBackfilling(false)
    }
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  const getPerformanceBadge = (rating) => {
    const variants = {
      'Excellent': 'bg-green-100 text-green-800 border-green-300',
      'Good': 'bg-blue-100 text-blue-800 border-blue-300',
      'Fair': 'bg-yellow-100 text-yellow-800 border-yellow-300',
      'Needs Improvement': 'bg-red-100 text-red-800 border-red-300',
      'Unknown': 'bg-gray-100 text-gray-800 border-gray-300'
    }
    return variants[rating] || variants['Unknown']
  }

  const getMonthName = (month) => {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    return months[month - 1] || month
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    )
  }

  if (!accuracyData) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-center text-muted-foreground">No accuracy data available</p>
        </CardContent>
      </Card>
    )
  }

  const { summary, monthly_accuracy, accuracy_by_day, recent_forecasts } = accuracyData

  return (
    <div className="space-y-6">
      {/* Header with Actions */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Target className="h-6 w-6 text-blue-600" />
            Forecast Accuracy Tracking
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Measure and improve forecast performance over time
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={backfillActuals}
            disabled={backfilling}
          >
            {backfilling ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Updating...
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4 mr-2" />
                Update Actuals
              </>
            )}
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={fetchAccuracyData}
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Overall MAPE</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-end justify-between">
              <div>
                <p className="text-3xl font-bold">{summary.mape?.toFixed(1) || 'N/A'}%</p>
                <Badge className={`mt-2 ${getPerformanceBadge(summary.performance_rating)}`}>
                  {summary.performance_rating}
                </Badge>
              </div>
              <Activity className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Within Range</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-end justify-between">
              <div>
                <p className="text-3xl font-bold">{summary.within_range_pct?.toFixed(0) || 0}%</p>
                <p className="text-xs text-muted-foreground mt-2">
                  of forecasts hit confidence interval
                </p>
              </div>
              <CheckCircle2 className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Average Bias</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-end justify-between">
              <div>
                <p className="text-3xl font-bold">{formatCurrency(summary.avg_bias || 0)}</p>
                <p className="text-xs text-muted-foreground mt-2">
                  {(summary.avg_bias || 0) > 0 ? 'Over-forecasting' : 'Under-forecasting'}
                </p>
              </div>
              {(summary.avg_bias || 0) > 0 ? (
                <TrendingUp className="h-8 w-8 text-orange-500" />
              ) : (
                <TrendingDown className="h-8 w-8 text-blue-500" />
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Forecasts Tracked</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-end justify-between">
              <div>
                <p className="text-3xl font-bold">{summary.completed_forecasts || 0}</p>
                <p className="text-xs text-muted-foreground mt-2">
                  of {summary.total_forecasts || 0} total
                </p>
              </div>
              <Target className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Monthly Accuracy Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Monthly Forecast Accuracy</CardTitle>
          <CardDescription>MAPE (Mean Absolute Percentage Error) by month - lower is better</CardDescription>
        </CardHeader>
        <CardContent>
          {monthly_accuracy && monthly_accuracy.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={monthly_accuracy.slice().reverse()}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="month" 
                  tickFormatter={(month, index) => {
                    const item = monthly_accuracy.slice().reverse()[index]
                    return `${getMonthName(item.month)} ${item.year}`
                  }}
                />
                <YAxis label={{ value: 'MAPE (%)', angle: -90, position: 'insideLeft' }} />
                <Tooltip 
                  formatter={(value, name) => {
                    if (name === 'mape') return [`${value.toFixed(1)}%`, 'MAPE']
                    return [value, name]
                  }}
                  labelFormatter={(label, payload) => {
                    if (payload && payload[0]) {
                      const item = payload[0].payload
                      return `${getMonthName(item.month)} ${item.year}`
                    }
                    return label
                  }}
                />
                <ReferenceLine y={10} stroke="green" strokeDasharray="3 3" label="Excellent" />
                <ReferenceLine y={20} stroke="orange" strokeDasharray="3 3" label="Good" />
                <Bar dataKey="mape" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-center text-muted-foreground py-8">No monthly data available yet</p>
          )}
        </CardContent>
      </Card>

      {/* Accuracy by Day of Month */}
      <Card>
        <CardHeader>
          <CardTitle>Accuracy by Day of Month</CardTitle>
          <CardDescription>How forecast accuracy improves as the month progresses</CardDescription>
        </CardHeader>
        <CardContent>
          {accuracy_by_day && accuracy_by_day.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={accuracy_by_day}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="day" 
                  label={{ value: 'Day of Month', position: 'insideBottom', offset: -5 }}
                />
                <YAxis label={{ value: 'Accuracy (%)', angle: -90, position: 'insideLeft' }} />
                <Tooltip 
                  formatter={(value, name) => {
                    if (name === 'avg_accuracy') return [`${value.toFixed(1)}%`, 'Avg MAPE']
                    if (name === 'within_range_pct') return [`${value.toFixed(0)}%`, 'Within Range']
                    return [value, name]
                  }}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="avg_accuracy" 
                  stroke="#3b82f6" 
                  name="Avg MAPE"
                  strokeWidth={2}
                />
                <Line 
                  type="monotone" 
                  dataKey="within_range_pct" 
                  stroke="#10b981" 
                  name="Within Range %"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-center text-muted-foreground py-8">No daily trend data available yet</p>
          )}
        </CardContent>
      </Card>

      {/* Recent Forecasts Table */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Forecast Performance</CardTitle>
          <CardDescription>Detailed view of recent forecasts vs actuals</CardDescription>
        </CardHeader>
        <CardContent>
          {recent_forecasts && recent_forecasts.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Forecast Date</TableHead>
                  <TableHead>Target Month</TableHead>
                  <TableHead>Day</TableHead>
                  <TableHead className="text-right">Projected</TableHead>
                  <TableHead className="text-right">Actual</TableHead>
                  <TableHead className="text-right">Error</TableHead>
                  <TableHead className="text-right">MAPE</TableHead>
                  <TableHead className="text-center">In Range</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recent_forecasts.map((forecast, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-medium">{forecast.forecast_date}</TableCell>
                    <TableCell>{forecast.target_month}</TableCell>
                    <TableCell>{forecast.days_into_month}</TableCell>
                    <TableCell className="text-right">{formatCurrency(forecast.projected)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(forecast.actual)}</TableCell>
                    <TableCell className={`text-right ${forecast.error > 0 ? 'text-orange-600' : 'text-blue-600'}`}>
                      {forecast.error > 0 ? '+' : ''}{formatCurrency(forecast.error)}
                    </TableCell>
                    <TableCell className="text-right">
                      <Badge variant={forecast.accuracy_pct < 10 ? 'success' : forecast.accuracy_pct < 20 ? 'default' : 'destructive'}>
                        {forecast.accuracy_pct.toFixed(1)}%
                      </Badge>
                    </TableCell>
                    <TableCell className="text-center">
                      {forecast.within_range ? (
                        <CheckCircle2 className="h-4 w-4 text-green-500 inline" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-orange-500 inline" />
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="text-center text-muted-foreground py-8">No forecast history available yet</p>
          )}
        </CardContent>
      </Card>

      {/* Info Footer */}
      {lastUpdated && (
        <p className="text-xs text-muted-foreground text-center">
          Last updated: {lastUpdated.toLocaleString()}
        </p>
      )}
    </div>
  )
}

export default ForecastAccuracy
