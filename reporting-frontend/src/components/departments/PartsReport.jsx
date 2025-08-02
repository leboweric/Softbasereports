import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Badge } from '@/components/ui/badge'
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
  LineChart,
  Line,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer
} from 'recharts'
import { TrendingUp, TrendingDown, Package, AlertTriangle, Clock, ShoppingCart, Info, Zap, Turtle } from 'lucide-react'
import { apiUrl } from '@/lib/api'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

const PartsReport = ({ user, onNavigate }) => {
  const [partsData, setPartsData] = useState(null)
  const [fillRateData, setFillRateData] = useState(null)
  const [reorderAlertData, setReorderAlertData] = useState(null)
  const [velocityData, setVelocityData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [fillRateLoading, setFillRateLoading] = useState(true)
  const [reorderAlertLoading, setReorderAlertLoading] = useState(true)
  const [velocityLoading, setVelocityLoading] = useState(true)
  const [selectedCategory, setSelectedCategory] = useState(null)
  const [categoryModalOpen, setCategoryModalOpen] = useState(false)

  useEffect(() => {
    fetchPartsData()
    fetchFillRateData()
    fetchReorderAlertData()
    fetchVelocityData()
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
      setFillRateLoading(false)
    }
  }

  const fetchReorderAlertData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/parts/reorder-alert'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setReorderAlertData(data)
      } else {
        console.error('Failed to fetch reorder alert data:', response.status)
        setReorderAlertData(null)
      }
    } catch (error) {
      console.error('Error fetching reorder alert data:', error)
      setReorderAlertData(null)
    } finally {
      setReorderAlertLoading(false)
    }
  }

  const fetchVelocityData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/parts/velocity'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setVelocityData(data)
      } else {
        console.error('Failed to fetch velocity data:', response.status)
        setVelocityData(null)
      }
    } catch (error) {
      console.error('Error fetching velocity data:', error)
      setVelocityData(null)
    } finally {
      setVelocityLoading(false)
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

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="stock-alerts">Stock Alerts</TabsTrigger>
          <TabsTrigger value="velocity">Velocity</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
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
        </TabsContent>

        <TabsContent value="stock-alerts" className="space-y-6">
          {/* Parts Fill Rate Card */}
          {fillRateData && (
            <Card>
              <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Package className="h-5 w-5" />
                Linde Parts Fill Rate
              </span>
              <Badge variant={fillRateData.summary?.fillRate >= 90 ? "success" : "destructive"}>
                {fillRateData.summary?.fillRate?.toFixed(1)}%
              </Badge>
            </CardTitle>
            <CardDescription>
              {fillRateData.period} - Target: 90% fill rate
            </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
            {/* Summary Stats */}
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold">{fillRateData.summary?.totalOrders || 0}</p>
                <p className="text-sm text-muted-foreground">Total Orders</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">{fillRateData.summary?.filledOrders || 0}</p>
                <p className="text-sm text-muted-foreground">Filled Orders</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-red-600">{fillRateData.summary?.unfilledOrders || 0}</p>
                <p className="text-sm text-muted-foreground">Stockouts</p>
              </div>
            </div>

            {/* Fill Rate Trend */}
            {fillRateData.fillRateTrend && fillRateData.fillRateTrend.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2">Fill Rate Trend</h4>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={fillRateData.fillRateTrend}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis domain={[0, 100]} />
                    <RechartsTooltip 
                      formatter={(value, name) => {
                        if (name === 'fillRate') return `${value.toFixed(1)}%`
                        return value
                      }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="fillRate" 
                      stroke="#10b981" 
                      strokeWidth={2}
                      dot={{ r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Problem Parts Table */}
            {fillRateData.problemParts && fillRateData.problemParts.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2">Parts Frequently Out of Stock</h4>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Part Number</TableHead>
                      <TableHead>Description</TableHead>
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
                        <TableCell className="text-right">
                          {part.stockoutCount} / {part.totalOrders}
                        </TableCell>
                        <TableCell className="text-right">{part.currentStock}</TableCell>
                        <TableCell className="text-right">
                          <Badge variant={part.stockoutRate > 20 ? "destructive" : "secondary"}>
                            {part.stockoutRate.toFixed(1)}%
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
            </Card>
          )}

          {/* Reorder Alert Card */}
          {reorderAlertData && (
            <Card>
              <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5" />
                Parts Reorder Alerts
              </span>
              <div className="flex gap-2">
                <Badge variant="destructive" className="flex items-center gap-1">
                  <span className="text-xs">Out of Stock</span>
                  <span className="font-bold">{reorderAlertData.summary?.outOfStock || 0}</span>
                </Badge>
                <Badge variant="destructive" className="bg-orange-500 flex items-center gap-1">
                  <span className="text-xs">Critical</span>
                  <span className="font-bold">{reorderAlertData.summary?.critical || 0}</span>
                </Badge>
                <Badge variant="secondary" className="flex items-center gap-1">
                  <span className="text-xs">Low</span>
                  <span className="font-bold">{reorderAlertData.summary?.low || 0}</span>
                </Badge>
              </div>
            </CardTitle>
            <CardDescription>
              Parts needing reorder based on {reorderAlertData.analysisInfo?.period} usage • Lead time: {reorderAlertData.leadTimeAssumption} days
            </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
            {/* Alert Summary Stats */}
            <div className="grid grid-cols-5 gap-4 text-center">
              <div>
                <p className="text-sm text-muted-foreground">Tracked Parts</p>
                <p className="text-2xl font-bold">{reorderAlertData.summary?.totalTracked || 0}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Out of Stock</p>
                <p className="text-2xl font-bold text-red-600">{reorderAlertData.summary?.outOfStock || 0}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Critical (&lt;7 days)</p>
                <p className="text-2xl font-bold text-orange-600">{reorderAlertData.summary?.critical || 0}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Low (&lt;14 days)</p>
                <p className="text-2xl font-bold text-yellow-600">{reorderAlertData.summary?.low || 0}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Need Reorder</p>
                <p className="text-2xl font-bold text-blue-600">{reorderAlertData.summary?.needsReorder || 0}</p>
              </div>
            </div>

            {/* Reorder Alerts Table */}
            {reorderAlertData.alerts && reorderAlertData.alerts.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2">Parts Requiring Immediate Attention</h4>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Part Number</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead className="text-center">Alert</TableHead>
                      <TableHead className="text-right">Stock</TableHead>
                      <TableHead className="text-right">Days Left</TableHead>
                      <TableHead className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          Daily Usage
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger>
                                <Info className="h-3 w-3 text-muted-foreground" />
                              </TooltipTrigger>
                              <TooltipContent className="max-w-xs">
                                <p>Average quantity consumed per day over the last 90 days. Calculated by dividing total quantity used by the number of days in the period.</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        </div>
                      </TableHead>
                      <TableHead className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          Reorder Point
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger>
                                <Info className="h-3 w-3 text-muted-foreground" />
                              </TooltipTrigger>
                              <TooltipContent className="max-w-xs">
                                <p>The inventory level that triggers a new order. Calculated as: (14 days lead time + 7 days safety stock) × Average Daily Usage. When stock drops below this point, it's time to reorder.</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        </div>
                      </TableHead>
                      <TableHead className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          Order Qty
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger>
                                <Info className="h-3 w-3 text-muted-foreground" />
                              </TooltipTrigger>
                              <TooltipContent className="max-w-xs">
                                <p>Suggested order quantity to maintain adequate stock. Calculated as 30 days × Average Daily Usage, providing approximately one month of inventory after considering lead time.</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        </div>
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {reorderAlertData.alerts.map((alert) => (
                      <TableRow key={alert.partNo}>
                        <TableCell className="font-medium">{alert.partNo}</TableCell>
                        <TableCell>{alert.description}</TableCell>
                        <TableCell className="text-center">
                          <Badge 
                            variant={
                              alert.alertLevel === 'Out of Stock' ? 'destructive' :
                              alert.alertLevel === 'Critical' ? 'destructive' :
                              alert.alertLevel === 'Low' ? 'secondary' : 'default'
                            }
                            className={
                              alert.alertLevel === 'Critical' ? 'bg-orange-500' :
                              alert.alertLevel === 'Low' ? 'bg-yellow-500' : ''
                            }
                          >
                            {alert.alertLevel}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          {alert.currentStock}
                          {alert.onOrder > 0 && (
                            <span className="text-sm text-muted-foreground ml-1">
                              (+{alert.onOrder})
                            </span>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <span className={alert.daysOfStock < 7 ? 'text-red-600 font-bold' : ''}>
                            {alert.daysOfStock === 999 ? '∞' : alert.daysOfStock}
                          </span>
                        </TableCell>
                        <TableCell className="text-right">{alert.avgDailyUsage.toFixed(1)}</TableCell>
                        <TableCell className="text-right">{alert.suggestedReorderPoint}</TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-1">
                            <ShoppingCart className="h-4 w-4 text-muted-foreground" />
                            {alert.suggestedOrderQty}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}

            {/* Calculation Info */}
            <div className="text-sm text-muted-foreground border-t pt-4">
              <p><strong>Reorder Formula:</strong> {reorderAlertData.analysisInfo?.reorderFormula}</p>
              <p className="mt-1">Safety Stock: {reorderAlertData.safetyStockDays} days • Lead Time: {reorderAlertData.leadTimeAssumption} days</p>
            </div>
          </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="velocity" className="space-y-6">
          {/* Parts Velocity Analysis */}
          {velocityData && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5" />
                  Parts Velocity Analysis
                </CardTitle>
                <CardDescription>
                  Inventory turnover and movement patterns • {velocityData.analysisInfo?.period}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Velocity Summary Cards */}
                <div className="grid grid-cols-4 gap-4">
                  {Object.entries(velocityData.summary || {}).map(([category, data]) => {
                    const getCategoryColor = (cat) => {
                      if (cat === 'Very Fast' || cat === 'Fast') return 'text-green-600'
                      if (cat === 'Medium') return 'text-blue-600'
                      if (cat === 'Slow' || cat === 'Very Slow') return 'text-yellow-600'
                      if (cat === 'Dead Stock' || cat === 'No Movement') return 'text-red-600'
                      return 'text-gray-600'
                    }
                    
                    const getCategoryIcon = (cat) => {
                      if (cat === 'Very Fast' || cat === 'Fast') return <Zap className="h-4 w-4" />
                      if (cat === 'Dead Stock' || cat === 'No Movement') return <Turtle className="h-4 w-4" />
                      return <Clock className="h-4 w-4" />
                    }
                    
                    return (
                      <div 
                        key={category} 
                        className="border rounded-lg p-3 cursor-pointer hover:bg-gray-50 transition-colors"
                        onClick={() => {
                          setSelectedCategory(category)
                          setCategoryModalOpen(true)
                        }}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className={`flex items-center gap-1 text-sm font-medium ${getCategoryColor(category)}`}>
                            {getCategoryIcon(category)}
                            {category}
                          </span>
                          <Badge variant="secondary">{data.partCount}</Badge>
                        </div>
                        <p className="text-lg font-bold">${(data.totalValue / 1000).toFixed(1)}k</p>
                        <p className="text-xs text-muted-foreground">
                          {data.avgTurnoverRate > 0 ? `${data.avgTurnoverRate.toFixed(1)}x/yr` : 'No turnover'}
                        </p>
                      </div>
                    )
                  })}
                </div>

                {/* Movement Trend Chart */}
                {velocityData.movementTrend && velocityData.movementTrend.length > 0 && (
                  <div>
                    <h4 className="font-semibold mb-2">Monthly Parts Movement Trend</h4>
                    <ResponsiveContainer width="100%" height={200}>
                      <LineChart data={velocityData.movementTrend}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis yAxisId="left" orientation="left" />
                        <YAxis yAxisId="right" orientation="right" />
                        <RechartsTooltip />
                        <Line 
                          yAxisId="left"
                          type="monotone" 
                          dataKey="totalQuantity" 
                          stroke="#10b981" 
                          name="Total Quantity"
                        />
                        <Line 
                          yAxisId="right"
                          type="monotone" 
                          dataKey="uniqueParts" 
                          stroke="#3b82f6" 
                          name="Unique Parts"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Parts List Table */}
                {velocityData.parts && velocityData.parts.length > 0 && (
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold">Parts Inventory Analysis</h4>
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger>
                            <Info className="h-4 w-4 text-muted-foreground" />
                          </TooltipTrigger>
                          <TooltipContent className="max-w-md">
                            <div className="space-y-2">
                              <p className="font-semibold">Velocity Categories:</p>
                              {Object.entries(velocityData.analysisInfo?.velocityCategories || {}).map(([cat, desc]) => (
                                <p key={cat} className="text-sm">
                                  <span className="font-medium">{cat}:</span> {desc}
                                </p>
                              ))}
                            </div>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Part Number</TableHead>
                          <TableHead>Description</TableHead>
                          <TableHead className="text-center">Velocity</TableHead>
                          <TableHead className="text-center">Health</TableHead>
                          <TableHead className="text-right">Stock</TableHead>
                          <TableHead className="text-right">Value</TableHead>
                          <TableHead className="text-right">Turnover</TableHead>
                          <TableHead className="text-right">Last Move</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {velocityData.parts.slice(0, 20).map((part) => (
                          <TableRow key={part.partNo}>
                            <TableCell className="font-medium">{part.partNo}</TableCell>
                            <TableCell>{part.description}</TableCell>
                            <TableCell className="text-center">
                              <Badge 
                                variant={
                                  part.velocityCategory === 'Very Fast' || part.velocityCategory === 'Fast' ? 'success' :
                                  part.velocityCategory === 'Medium' ? 'default' :
                                  part.velocityCategory === 'Dead Stock' || part.velocityCategory === 'No Movement' ? 'destructive' :
                                  'secondary'
                                }
                              >
                                {part.velocityCategory}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-center">
                              <Badge 
                                variant={
                                  part.stockHealth === 'Normal' ? 'outline' :
                                  part.stockHealth === 'Stockout Risk' ? 'destructive' :
                                  'secondary'
                                }
                                className={
                                  part.stockHealth === 'Obsolete Risk' ? 'bg-orange-500' :
                                  part.stockHealth === 'Overstock Risk' ? 'bg-yellow-500' : ''
                                }
                              >
                                {part.stockHealth}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-right">{part.currentStock}</TableCell>
                            <TableCell className="text-right">${part.inventoryValue.toFixed(0)}</TableCell>
                            <TableCell className="text-right">
                              {part.annualTurnoverRate > 0 ? `${part.annualTurnoverRate.toFixed(1)}x` : '-'}
                            </TableCell>
                            <TableCell className="text-right">
                              {part.daysSinceLastMovement !== null ? `${part.daysSinceLastMovement}d` : 'Never'}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Category Parts Modal */}
      <Dialog open={categoryModalOpen} onOpenChange={setCategoryModalOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedCategory && (
                <>
                  {selectedCategory === 'Very Fast' || selectedCategory === 'Fast' ? <Zap className="h-5 w-5 text-green-600" /> :
                   selectedCategory === 'Dead Stock' || selectedCategory === 'No Movement' ? <Turtle className="h-5 w-5 text-red-600" /> :
                   <Clock className="h-5 w-5 text-yellow-600" />}
                  {selectedCategory} Parts
                </>
              )}
            </DialogTitle>
            <DialogDescription>
              {velocityData?.summary[selectedCategory] && (
                <span>
                  {velocityData.summary[selectedCategory].partCount} parts • 
                  ${(velocityData.summary[selectedCategory].totalValue / 1000).toFixed(1)}k total value
                  {velocityData.summary[selectedCategory].avgTurnoverRate > 0 && 
                    ` • ${velocityData.summary[selectedCategory].avgTurnoverRate.toFixed(1)}x average turnover`
                  }
                </span>
              )}
            </DialogDescription>
          </DialogHeader>
          
          <div className="mt-4">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Part Number</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="text-right">Stock</TableHead>
                  <TableHead className="text-right">Value</TableHead>
                  <TableHead className="text-right">Turnover</TableHead>
                  <TableHead className="text-right">Last Movement</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {velocityData?.parts
                  .filter(part => part.velocityCategory === selectedCategory)
                  .map((part) => (
                    <TableRow key={part.partNo}>
                      <TableCell className="font-medium">{part.partNo}</TableCell>
                      <TableCell>{part.description}</TableCell>
                      <TableCell className="text-right">{part.currentStock}</TableCell>
                      <TableCell className="text-right">${part.inventoryValue.toFixed(0)}</TableCell>
                      <TableCell className="text-right">
                        {part.annualTurnoverRate > 0 ? `${part.annualTurnoverRate.toFixed(1)}x` : '-'}
                      </TableCell>
                      <TableCell className="text-right">
                        {part.daysSinceLastMovement !== null ? `${part.daysSinceLastMovement}d ago` : 'Never'}
                      </TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default PartsReport