import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer,
  LineChart,
  Line
} from 'recharts'
import { Package, AlertTriangle, TrendingUp } from 'lucide-react'
import { apiUrl } from '@/lib/api'

const PartsReport = ({ user, onNavigate }) => {
  const [partsData, setPartsData] = useState(null)
  const [fillRateData, setFillRateData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadingFillRate, setLoadingFillRate] = useState(true)

  useEffect(() => {
    fetchPartsData()
    fetchFillRateData()
  }, [])

  const fetchPartsData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/parts'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setPartsData(data)
      } else {
        console.error('Failed to fetch parts data:', response.status)
        // Set default empty data structure
        setPartsData({
          monthlyPartsRevenue: []
        })
      }
    } catch (error) {
      console.error('Error fetching parts data:', error)
      // Set default empty data structure on error
      setPartsData({
        monthlyPartsRevenue: []
      })
    } finally {
      setLoading(false)
    }
  }

  const fetchFillRateData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/parts/fill-rate'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setFillRateData(data)
      } else {
        console.error('Failed to fetch fill rate data:', response.status)
        setFillRateData(null)
      }
    } catch (error) {
      console.error('Error fetching fill rate data:', error)
      setFillRateData(null)
    } finally {
      setLoadingFillRate(false)
    }
  }

  if (loading) {
    return (
      <LoadingSpinner 
        title="Loading Parts Department" 
        description="Fetching parts data..."
        size="large"
      />
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Parts Department</h1>
        <p className="text-muted-foreground">Monitor parts sales and inventory performance</p>
      </div>

      {/* Parts Fill Rate Card */}
      {fillRateData && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Package className="h-5 w-5" />
              Linde Parts Fill Rate
            </CardTitle>
            <CardDescription>
              {fillRateData.period} - Target: 90% fill rate
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Summary Metrics */}
              <div className="grid gap-4 md:grid-cols-4">
                <div className="space-y-2">
                  <p className="text-sm font-medium text-muted-foreground">Fill Rate</p>
                  <div className="flex items-baseline gap-2">
                    <span className={`text-2xl font-bold ${fillRateData.summary.fillRate >= 90 ? 'text-green-600' : 'text-red-600'}`}>
                      {fillRateData.summary.fillRate.toFixed(1)}%
                    </span>
                    {fillRateData.summary.fillRate < 90 && (
                      <AlertTriangle className="h-5 w-5 text-red-600" />
                    )}
                  </div>
                  <Progress 
                    value={fillRateData.summary.fillRate} 
                    className="h-2" 
                  />
                </div>
                <div className="space-y-2">
                  <p className="text-sm font-medium text-muted-foreground">Total Orders</p>
                  <p className="text-2xl font-bold">{fillRateData.summary.totalOrders}</p>
                </div>
                <div className="space-y-2">
                  <p className="text-sm font-medium text-muted-foreground">Filled Orders</p>
                  <p className="text-2xl font-bold text-green-600">{fillRateData.summary.filledOrders}</p>
                </div>
                <div className="space-y-2">
                  <p className="text-sm font-medium text-muted-foreground">Stockouts</p>
                  <p className="text-2xl font-bold text-red-600">{fillRateData.summary.unfilledOrders}</p>
                </div>
              </div>

              {/* Fill Rate Trend */}
              {fillRateData.fillRateTrend && fillRateData.fillRateTrend.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium mb-3">Fill Rate Trend</h4>
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={fillRateData.fillRateTrend}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="month" />
                      <YAxis domain={[0, 100]} tickFormatter={(value) => `${value}%`} />
                      <RechartsTooltip formatter={(value) => `${value}%`} />
                      <Line 
                        type="monotone" 
                        dataKey="fillRate" 
                        stroke="#3b82f6" 
                        strokeWidth={2}
                        dot={{ fill: '#3b82f6' }}
                      />
                      {/* Target line at 90% */}
                      <Line 
                        type="monotone" 
                        dataKey={() => 90} 
                        stroke="#10b981" 
                        strokeDasharray="5 5"
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* Problem Parts Table */}
              {fillRateData.problemParts && fillRateData.problemParts.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium mb-3">Parts with Frequent Stockouts</h4>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Part Number</TableHead>
                        <TableHead>Description</TableHead>
                        <TableHead className="text-right">Total Orders</TableHead>
                        <TableHead className="text-right">Stockouts</TableHead>
                        <TableHead className="text-right">Current Stock</TableHead>
                        <TableHead className="text-right">Stockout Rate</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {fillRateData.problemParts.map((part) => (
                        <TableRow key={part.partNo}>
                          <TableCell className="font-medium">{part.partNo}</TableCell>
                          <TableCell>{part.description}</TableCell>
                          <TableCell className="text-right">{part.totalOrders}</TableCell>
                          <TableCell className="text-right">
                            <Badge variant="destructive">{part.stockoutCount}</Badge>
                          </TableCell>
                          <TableCell className="text-right">{part.currentStock}</TableCell>
                          <TableCell className="text-right">
                            <span className={part.stockoutRate > 20 ? 'text-red-600 font-medium' : ''}>
                              {part.stockoutRate.toFixed(1)}%
                            </span>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Monthly Parts Revenue */}
      <Card>
        <CardHeader>
          <CardTitle>Monthly Parts Revenue</CardTitle>
          <CardDescription>Parts revenue over the last 12 months</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={partsData?.monthlyPartsRevenue || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis 
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
              />
              <RechartsTooltip 
                formatter={(value) => `$${value.toLocaleString()}`}
              />
              <Bar dataKey="amount" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}

export default PartsReport