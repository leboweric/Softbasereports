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
  Activity,
  Camera,
  Calendar
} from 'lucide-react'
import { apiUrl } from '@/lib/api'

const ForecastAccuracy = () => {
  const [accuracyData, setAccuracyData] = useState(null)
  const [snapshotData, setSnapshotData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [snapshotsLoading, setSnapshotsLoading] = useState(true)
  const [backfilling, setBackfilling] = useState(false)
  const [lastUpdated, setLastUpdated] = useState(null)

  useEffect(() => {
    fetchAccuracyData()
    fetchSnapshotData()
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

  const fetchSnapshotData = async () => {
    try {
      setSnapshotsLoading(true)
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/dashboard/forecast-accuracy/snapshots'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to fetch snapshot data')
      }

      const data = await response.json()
      setSnapshotData(data)
    } catch (error) {
      console.error('Error fetching snapshot data:', error)
    } finally {
      setSnapshotsLoading(false)
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
                <Bar dataKey="mape" fill="#3b82f6" radius={[4, 4, 0, 0]} />
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

      {/* Mid-Month Snapshots Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Camera className="h-5 w-5 text-purple-600" />
            Forecast vs Actual Comparison
          </CardTitle>
          <CardDescription>
            Side-by-side comparison of 15th forecasts vs end-of-month actuals
          </CardDescription>
        </CardHeader>
        <CardContent>
          {snapshotsLoading ? (
            <div className="flex items-center justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : snapshotData && snapshotData.snapshots && snapshotData.snapshots.length > 0 ? (
            <>
              {/* Snapshot Summary */}
              {snapshotData.summary && (
                <div className="grid gap-4 md:grid-cols-4 mb-6">
                  <div className="bg-purple-50 rounded-lg p-4">
                    <p className="text-sm text-purple-600 font-medium">Total Snapshots</p>
                    <p className="text-2xl font-bold">{snapshotData.summary.total_snapshots}</p>
                  </div>
                  <div className="bg-green-50 rounded-lg p-4">
                    <p className="text-sm text-green-600 font-medium">Avg Error</p>
                    <p className="text-2xl font-bold">
                      {snapshotData.summary.avg_accuracy ? `${snapshotData.summary.avg_accuracy.toFixed(1)}%` : 'N/A'}
                    </p>
                  </div>
                  <div className="bg-blue-50 rounded-lg p-4">
                    <p className="text-sm text-blue-600 font-medium">Within Range</p>
                    <p className="text-2xl font-bold">
                      {snapshotData.summary.within_range_count || 0} / {snapshotData.summary.completed_count || 0}
                    </p>
                  </div>
                  <div className="bg-amber-50 rounded-lg p-4">
                    <p className="text-sm text-amber-600 font-medium">Avg Variance</p>
                    <p className="text-2xl font-bold">
                      {snapshotData.summary.avg_variance ? formatCurrency(snapshotData.summary.avg_variance) : 'N/A'}
                    </p>
                  </div>
                </div>
              )}
              
              {/* Snapshots Table - Side by Side Comparison */}
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Month</TableHead>
                    <TableHead className="text-center bg-purple-50">15th Snapshot</TableHead>
                    <TableHead className="text-center bg-green-50">End of Month</TableHead>
                    <TableHead className="text-right">Variance</TableHead>
                    <TableHead className="text-right">Error %</TableHead>
                    <TableHead className="text-center">Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {snapshotData.snapshots.map((snapshot, index) => (
                    <TableRow key={index}>
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                          <Calendar className="h-4 w-4 text-muted-foreground" />
                          {getMonthName(snapshot.target_month)} {snapshot.target_year}
                        </div>
                      </TableCell>
                      {/* 15th Snapshot Column */}
                      <TableCell className="bg-purple-50/50">
                        <div className="text-center">
                          <p className="font-semibold text-purple-700">
                            {formatCurrency(snapshot.projected_total)}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            Range: {formatCurrency(snapshot.forecast_low)} - {formatCurrency(snapshot.forecast_high)}
                          </p>
                          {snapshot.mtd_sales_at_15th && (
                            <p className="text-xs text-muted-foreground">
                              MTD at 15th: {formatCurrency(snapshot.mtd_sales_at_15th)}
                            </p>
                          )}
                        </div>
                      </TableCell>
                      {/* End of Month Column */}
                      <TableCell className="bg-green-50/50">
                        <div className="text-center">
                          {snapshot.actual_total ? (
                            <>
                              <p className="font-semibold text-green-700">
                                {formatCurrency(snapshot.actual_total)}
                              </p>
                              {snapshot.actual_invoice_count && (
                                <p className="text-xs text-muted-foreground">
                                  {snapshot.actual_invoice_count} invoices
                                </p>
                              )}
                            </>
                          ) : (
                            <p className="text-muted-foreground">Pending...</p>
                          )}
                        </div>
                      </TableCell>
                      {/* Variance Column */}
                      <TableCell className="text-right">
                        {snapshot.variance_amount !== null ? (
                          <span className={snapshot.variance_amount > 0 ? 'text-green-600' : 'text-red-600'}>
                            {snapshot.variance_amount > 0 ? '+' : ''}{formatCurrency(snapshot.variance_amount)}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </TableCell>
                      {/* Error % Column */}
                      <TableCell className="text-right">
                        {snapshot.accuracy_pct !== null ? (
                          <Badge 
                            variant={snapshot.accuracy_pct < 10 ? 'success' : snapshot.accuracy_pct < 20 ? 'default' : 'destructive'}
                          >
                            {snapshot.accuracy_pct.toFixed(1)}%
                          </Badge>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </TableCell>
                      {/* Status Column */}
                      <TableCell className="text-center">
                        {snapshot.actual_total ? (
                          snapshot.within_range ? (
                            <Badge className="bg-green-100 text-green-800">
                              <CheckCircle2 className="h-3 w-3 mr-1" />
                              In Range
                            </Badge>
                          ) : (
                            <Badge className="bg-orange-100 text-orange-800">
                              <AlertCircle className="h-3 w-3 mr-1" />
                              Outside
                            </Badge>
                          )
                        ) : (
                          <Badge variant="outline">
                            <RefreshCw className="h-3 w-3 mr-1" />
                            In Progress
                          </Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              
              {/* Schedule Info */}
              <div className="mt-4 p-3 bg-muted/50 rounded-lg text-sm text-muted-foreground">
                <p><strong>Automatic Capture Schedule:</strong></p>
                <ul className="list-disc list-inside mt-1">
                  <li>15th of each month at 8:00 AM - Forecast snapshot</li>
                  <li>Last day of each month at 7:00 PM - Actual revenue capture</li>
                </ul>
              </div>
            </>
          ) : (
            <div className="text-center py-8">
              <Camera className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">No snapshots captured yet</p>
              <p className="text-sm text-muted-foreground mt-2">
                Snapshots are automatically captured on the 15th at 8 AM and actuals on the last day at 7 PM
              </p>
            </div>
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
