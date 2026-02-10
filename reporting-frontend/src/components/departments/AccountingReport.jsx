import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { 
  ComposedChart,
  BarChart,
  Bar, 
  Line,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  ReferenceLine,
  Legend,
  Cell
} from 'recharts'
import { apiUrl } from '@/lib/api'
import ARAgingReport from '@/components/ARAgingReport'
import APAgingReport from '@/components/APAgingReport'
import SalesCommissionReport from '@/components/SalesCommissionReport'
import ControlNumberReport from '@/components/ControlNumberReport'
import InventoryReport from '@/components/InventoryReport'


const AccountingReport = ({ user, organization }) => {
  const [monthlyExpenses, setMonthlyExpenses] = useState([])
  const [rawMonthlyExpenses, setRawMonthlyExpenses] = useState([])
  const [includeCurrentMonthGNA, setIncludeCurrentMonthGNA] = useState(false)
  const [monthlyGrossMargin, setMonthlyGrossMargin] = useState([])
  const [includeCurrentMonth, setIncludeCurrentMonth] = useState(false)
  const [rawGrossMarginData, setRawGrossMarginData] = useState([])
  const [professionalServicesExpenses, setProfessionalServicesExpenses] = useState([])
  const [rawProfessionalServicesExpenses, setRawProfessionalServicesExpenses] = useState([])
  const [includeCurrentMonthProfServices, setIncludeCurrentMonthProfServices] = useState(false)
  const [absorptionRateData, setAbsorptionRateData] = useState([])
  const [rawAbsorptionRateData, setRawAbsorptionRateData] = useState([])
  const [includeCurrentMonthAbsorption, setIncludeCurrentMonthAbsorption] = useState(false)
  const [absorptionSummary, setAbsorptionSummary] = useState(null)
  const [arData, setArData] = useState(null)
  const [apTotal, setApTotal] = useState(null)
  const [loading, setLoading] = useState(true)

  // Professional Services detail modal state
  const [profServicesDetailOpen, setProfServicesDetailOpen] = useState(false)
  const [profServicesDetail, setProfServicesDetail] = useState(null)
  const [profServicesDetailLoading, setProfServicesDetailLoading] = useState(false)

  // G&A Expenses detail modal state
  const [gnaDetailOpen, setGnaDetailOpen] = useState(false)
  const [gnaDetail, setGnaDetail] = useState(null)
  const [gnaDetailLoading, setGnaDetailLoading] = useState(false)

  // G&A Account drill-down state (for clicking individual accounts)
  const [selectedGnaAccount, setSelectedGnaAccount] = useState(null)

  useEffect(() => {
    fetchAccountingData()
    fetchARData()
    fetchAPTotal()
    fetchGrossMarginData()
    fetchProfessionalServicesData()
    fetchAbsorptionRateData()
  }, [])

  // Re-filter gross margin data when toggle changes
  useEffect(() => {
    if (rawGrossMarginData.length > 0) {
      const now = new Date()
      const currentMonthStr = now.toLocaleDateString('en-US', { month: 'short', year: '2-digit' }).replace(' ', " '")
      const filteredData = rawGrossMarginData.filter(item => {
        if (!includeCurrentMonth && item.month === currentMonthStr) return false
        return true
      })
      setMonthlyGrossMargin(filteredData)
    }
  }, [includeCurrentMonth, rawGrossMarginData])

  // Re-filter G&A expenses when toggle changes
  useEffect(() => {
    if (rawMonthlyExpenses.length > 0) {
      const now = new Date()
      const currentMonthStr = now.toLocaleDateString('en-US', { month: 'short' })
      const currentMonthStrWithYear = now.toLocaleDateString('en-US', { month: 'short', year: '2-digit' }).replace(' ', " '")
      const filteredExpenses = rawMonthlyExpenses.filter(item => {
        if (!includeCurrentMonthGNA) {
          if (item.month === currentMonthStr && item.year === now.getFullYear()) return false
          if (item.month === currentMonthStrWithYear) return false
        }
        return true
      })
      setMonthlyExpenses(filteredExpenses)
    }
  }, [includeCurrentMonthGNA, rawMonthlyExpenses])

  // Re-filter Professional Services expenses when toggle changes
  useEffect(() => {
    if (rawProfessionalServicesExpenses.length > 0) {
      const now = new Date()
      const currentMonthStr = now.toLocaleDateString('en-US', { month: 'short', year: '2-digit' }).replace(' ', " '")
      const filteredExpenses = rawProfessionalServicesExpenses.filter(item => {
        if (!includeCurrentMonthProfServices && item.month === currentMonthStr) return false
        return true
      })
      setProfessionalServicesExpenses(filteredExpenses)
    }
  }, [includeCurrentMonthProfServices, rawProfessionalServicesExpenses])

  // Re-filter absorption rate data when toggle changes
  useEffect(() => {
    if (rawAbsorptionRateData.length > 0) {
      const now = new Date()
      const currentMonthStr = now.toLocaleDateString('en-US', { month: 'short', year: '2-digit' }).replace(' ', " '")
      const filteredData = rawAbsorptionRateData.filter(item => {
        if (!includeCurrentMonthAbsorption && item.month === currentMonthStr) return false
        return true
      })
      setAbsorptionRateData(filteredData)
    }
  }, [includeCurrentMonthAbsorption, rawAbsorptionRateData])

  const fetchAccountingData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/accounting'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        // Filter out months before the organization's data_start_date (if set)
        const parseMonthItem = (item) => {
          if (item.month_num && item.year) return new Date(item.year, item.month_num - 1, 1)
          // Parse from month string like "Mar '25"
          const parsed = new Date(Date.parse(item.month?.replace("'", "20") + " 1"))
          return isNaN(parsed) ? null : parsed
        }
        const baseFilteredExpenses = (data.monthly_expenses || []).filter(item => {
          if (organization?.data_start_date) {
            const startDate = new Date(organization.data_start_date)
            const itemDate = parseMonthItem(item)
            return itemDate ? itemDate >= startDate : true
          }
          return true
        })
        setRawMonthlyExpenses(baseFilteredExpenses)
        
        // Apply current month filter based on toggle state
        const now = new Date()
        const currentMonthStr = now.toLocaleDateString('en-US', { month: 'short' })
        const currentMonthStrWithYear = now.toLocaleDateString('en-US', { month: 'short', year: '2-digit' }).replace(' ', " '")
        const filteredExpenses = baseFilteredExpenses.filter(item => {
          if (!includeCurrentMonthGNA) {
            if (item.month === currentMonthStr && item.year === now.getFullYear()) return false
            if (item.month === currentMonthStrWithYear) return false
          }
          return true
        })
        setMonthlyExpenses(filteredExpenses)
      }
    } catch (error) {
      console.error('Error fetching accounting data:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchARData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/accounting/ar-report'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setArData(data)
        // Debug: log what buckets we're getting
        if (data.debug_buckets) {
          console.log('AR Debug - Buckets:', data.debug_buckets)
          console.log('AR Debug - Over 90 calculation:', data.over_90_amount)
        }
      } else {
        console.error('AR report error:', response.status, response.statusText)
        const errorText = await response.text()
        console.error('Error details:', errorText)
      }
    } catch (error) {
      console.error('Error fetching AR data:', error)
    }
  }

  const fetchAPTotal = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/accounting/ap-total'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setApTotal(data)
      } else {
        console.error('AP total error:', response.status, response.statusText)
      }
    } catch (error) {
      console.error('Error fetching AP total:', error)
    }
  }

  const fetchGrossMarginData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/dashboard/summary-optimized'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        // Filter out months before the organization's data_start_date (if set)
        const parseMonthItem2 = (item) => {
          if (item.month_num && item.year) return new Date(item.year, item.month_num - 1, 1)
          // Parse from month string like "Mar '25"
          const parsed = new Date(Date.parse(item.month?.replace("'", "20") + " 1"))
          return isNaN(parsed) ? null : parsed
        }
        const baseFilteredData = (data.monthly_sales || []).filter(item => {
          if (organization?.data_start_date) {
            const startDate = new Date(organization.data_start_date)
            const itemDate = parseMonthItem2(item)
            return itemDate ? itemDate >= startDate : true
          }
          return true
        })
        setRawGrossMarginData(baseFilteredData)
        
        // Apply current month filter based on toggle state
        const now = new Date()
        const currentMonthStr = now.toLocaleDateString('en-US', { month: 'short', year: '2-digit' }).replace(' ', " '")
        const filteredData = baseFilteredData.filter(item => {
          if (!includeCurrentMonth && item.month === currentMonthStr) return false
          return true
        })
        setMonthlyGrossMargin(filteredData)
      } else {
        console.error('Dashboard data error:', response.status, response.statusText)
      }
    } catch (error) {
      console.error('Error fetching gross margin data:', error)
    }
  }

  const fetchProfessionalServicesData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/accounting/professional-services'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        // Filter out months before the organization's data_start_date (if set)
        const parseMonthItem3 = (item) => {
          if (item.month_num && item.year) return new Date(item.year, item.month_num - 1, 1)
          // Parse from month string like "Mar '25"
          const parsed = new Date(Date.parse(item.month?.replace("'", "20") + " 1"))
          return isNaN(parsed) ? null : parsed
        }
        const baseFilteredExpenses = (data.monthly_expenses || []).filter(item => {
          if (organization?.data_start_date) {
            const startDate = new Date(organization.data_start_date)
            const itemDate = parseMonthItem3(item)
            return itemDate ? itemDate >= startDate : true
          }
          return true
        })
        setRawProfessionalServicesExpenses(baseFilteredExpenses)
        
        // Apply current month filter based on toggle state
        const now = new Date()
        const currentMonthStr = now.toLocaleDateString('en-US', { month: 'short', year: '2-digit' }).replace(' ', " '")
        const filteredExpenses = baseFilteredExpenses.filter(item => {
          if (!includeCurrentMonthProfServices && item.month === currentMonthStr) return false
          return true
        })
        setProfessionalServicesExpenses(filteredExpenses)
      } else {
        console.error('Professional Services data error:', response.status, response.statusText)
      }
    } catch (error) {
      console.error('Error fetching professional services data:', error)
    }
  }

  const fetchProfessionalServicesDetails = async (year, month, monthLabel) => {
    setProfServicesDetailLoading(true)
    setProfServicesDetailOpen(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl(`/api/reports/departments/accounting/professional-services/details?year=${year}&month=${month}`), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setProfServicesDetail({ ...data, monthLabel })
      } else {
        console.error('Professional Services details error:', response.status, response.statusText)
        setProfServicesDetail({ error: 'Failed to load details', monthLabel })
      }
    } catch (error) {
      console.error('Error fetching professional services details:', error)
      setProfServicesDetail({ error: 'Failed to load details', monthLabel })
    } finally {
      setProfServicesDetailLoading(false)
    }
  }

  const fetchAbsorptionRateData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/accounting/absorption-rate'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        // Filter out months before the organization's data_start_date (if set)
        const baseFilteredData = (data.monthly_data || []).filter(item => {
          if (organization?.data_start_date) {
            const startDate = new Date(organization.data_start_date)
            const itemDate = new Date(item.year, item.month_num - 1, 1)
            return itemDate >= startDate
          }
          return true
        })
        setRawAbsorptionRateData(baseFilteredData)
        setAbsorptionSummary(data.summary)
        
        // Apply current month filter based on toggle state
        const now = new Date()
        const currentMonthStr = now.toLocaleDateString('en-US', { month: 'short', year: '2-digit' }).replace(' ', " '")
        const filteredData = baseFilteredData.filter(item => {
          if (!includeCurrentMonthAbsorption && item.month === currentMonthStr) return false
          return true
        })
        setAbsorptionRateData(filteredData)
      } else {
        console.error('Absorption rate data error:', response.status, response.statusText)
      }
    } catch (error) {
      console.error('Error fetching absorption rate data:', error)
    }
  }

  const fetchGnaExpensesDetails = async (year, month, monthLabel) => {
    setGnaDetailLoading(true)
    setGnaDetailOpen(true)
    setSelectedGnaAccount(null) // Reset selected account when loading new month
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl(`/api/reports/departments/accounting/gna-expenses/details?year=${year}&month=${month}`), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setGnaDetail({ ...data, monthLabel })
      } else {
        console.error('G&A Expenses details error:', response.status, response.statusText)
        setGnaDetail({ error: 'Failed to load details', monthLabel })
      }
    } catch (error) {
      console.error('Error fetching G&A expenses details:', error)
      setGnaDetail({ error: 'Failed to load details', monthLabel })
    } finally {
      setGnaDetailLoading(false)
    }
  }

  // Helper function to format currency
  const formatCurrency = (value) => {
    if (value === null || value === undefined) return '$0'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  // Helper function for percentage change
  const calculatePercentageChange = (current, previous) => {
    if (!previous || previous === 0) return null
    return ((current - previous) / previous) * 100
  }

  const formatPercentage = (value) => {
    if (value === null || value === undefined) return ''
    const sign = value > 0 ? '+' : ''
    return ` (${sign}${value.toFixed(1)}%)`
  }

  if (loading) {
    return (
      <LoadingSpinner 
        title="Loading Accounting Data" 
        description="Fetching financial information..."
        size="large"
      />
    )
  }


  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Accounting Department</h1>
        <p className="text-muted-foreground">Financial overview and accounting metrics</p>
      </div>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="ar-aging">AR Aging</TabsTrigger>
          <TabsTrigger value="ap-aging">AP Aging</TabsTrigger>
          <TabsTrigger value="commissions">Sales Commissions</TabsTrigger>
          <TabsTrigger value="control">Control Numbers</TabsTrigger>
          <TabsTrigger value="inventory">Inventory</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Summary Cards */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Total Accounts Receivable</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  ${arData ? (arData.total_ar >= 1000000 ? 
                    `${(arData.total_ar / 1000000).toFixed(2)}M` : 
                    `${(arData.total_ar / 1000).toFixed(0)}k`) : 
                    '...'}
                </div>
              </CardContent>
            </Card>
            
            {arData && (
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">AR Over 90 Days</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className={`text-2xl font-bold ${arData.over_90_percentage < 10 ? 'text-green-600' : 'text-red-600'}`}>
                    {arData.over_90_percentage}%
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">${(arData.over_90_amount / 1000).toFixed(0)}k of total AR</p>
                </CardContent>
              </Card>
            )}
            
            {apTotal && (
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Total Accounts Payable</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{apTotal.formatted}</div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Monthly Absorption Rate - Moved to Currie KPI's tab */}

          {/* Monthly Gross Margin Dollars */}
          <Card>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle>Monthly Gross Margin Dollars</CardTitle>
                  <CardDescription>Revenue minus Cost of Goods Sold - March 2025 onwards</CardDescription>
                  <div className="flex items-center gap-2 mt-2">
                    <Switch
                      id="include-current-month"
                      checked={includeCurrentMonth}
                      onCheckedChange={setIncludeCurrentMonth}
                    />
                    <Label htmlFor="include-current-month" className="text-sm text-muted-foreground cursor-pointer">
                      Include current month
                    </Label>
                  </div>
                </div>
                {monthlyGrossMargin && monthlyGrossMargin.length > 0 && (() => {
                  const avgGrossMargin = monthlyGrossMargin.reduce((sum, item) => sum + (item.gross_margin_dollars || 0), 0) / monthlyGrossMargin.length
                  const totalGrossMargin = monthlyGrossMargin.reduce((sum, item) => sum + (item.gross_margin_dollars || 0), 0)
                  return (
                    <div className="flex gap-6 text-right">
                      <div>
                        <p className="text-sm text-muted-foreground">Average</p>
                        <p className="text-lg font-semibold">{formatCurrency(avgGrossMargin)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Total</p>
                        <p className="text-lg font-semibold">{formatCurrency(totalGrossMargin)}</p>
                      </div>
                    </div>
                  )
                })()}
              </div>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={350}>
                <ComposedChart data={(() => {
                  const data = monthlyGrossMargin || []
                  if (data.length === 0) return data

                  // Calculate linear regression for trendline
                  const monthsWithData = data.filter(item => item.gross_margin_dollars > 0)
                  let trendSlope = 0
                  let trendIntercept = 0

                  if (monthsWithData.length >= 2) {
                    const n = monthsWithData.length
                    const sumX = monthsWithData.reduce((sum, item, i) => sum + i, 0)
                    const sumY = monthsWithData.reduce((sum, item) => sum + item.gross_margin_dollars, 0)
                    const meanX = sumX / n
                    const meanY = sumY / n

                    let numerator = 0
                    let denominator = 0
                    monthsWithData.forEach((item, i) => {
                      numerator += (i - meanX) * (item.gross_margin_dollars - meanY)
                      denominator += (i - meanX) * (i - meanX)
                    })

                    trendSlope = denominator !== 0 ? numerator / denominator : 0
                    trendIntercept = meanY - trendSlope * meanX
                  }

                  // Add trendline to each data point
                  return data.map((item, index) => ({
                    ...item,
                    trendline: item.gross_margin_dollars > 0 ? trendSlope * index + trendIntercept : null
                  }))
                })()} margin={{ top: 40, right: 60, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis yAxisId="left" tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                  <YAxis yAxisId="right" orientation="right" tickFormatter={(value) => `${value}%`} />
                  <Tooltip content={({ active, payload, label }) => {
                    if (active && payload && payload.length && monthlyGrossMargin) {
                      const data = monthlyGrossMargin
                      const currentIndex = data.findIndex(item => item.month === label)
                      const monthData = data[currentIndex]
                      const currentValue = monthData?.gross_margin_dollars || 0
                      const priorYearValue = monthData?.prior_year_gross_margin_dollars || 0

                      return (
                        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                          <p className="font-semibold mb-1">{label}</p>
                          <p className="text-green-600">
                            Gross Margin: {formatCurrency(currentValue)}
                            {priorYearValue > 0 && (
                              <span className="text-sm ml-2">
                                ({formatPercentage(calculatePercentageChange(currentValue, priorYearValue))} vs last year)
                              </span>
                            )}
                          </p>
                          {monthData?.margin !== null && monthData?.margin !== undefined && (
                            <p className="text-blue-600 text-sm">
                              Margin %: {monthData.margin.toFixed(1)}%
                            </p>
                          )}
                        </div>
                      )
                    }
                    return null
                  }} />
                  <Legend />
                  <Bar yAxisId="left" dataKey="gross_margin_dollars" fill="#10b981" name="Gross Margin $" maxBarSize={60} radius={[4, 4, 0, 0]} />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="trendline"
                    stroke="#f97316"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    dot={false}
                    name="Trend"
                    connectNulls
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="margin"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={{ fill: '#3b82f6' }}
                    name="Gross Margin %"
                  />
                  {monthlyGrossMargin && monthlyGrossMargin.length > 0 && (() => {
                    const average = monthlyGrossMargin.reduce((sum, item) => sum + (item.gross_margin_dollars || 0), 0) / monthlyGrossMargin.length
                    return (
                      <ReferenceLine
                        yAxisId="left"
                        y={average}
                        stroke="#666"
                        strokeDasharray="3 3"
                        label={{ value: "Average", position: "insideTopRight" }}
                      />
                    )
                  })()}
                </ComposedChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* G&A Expenses Over Time */}
          <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle>G&A Expenses Over Time</CardTitle>
                <CardDescription>General & Administrative expenses - March 2025 onwards • Click a bar for details</CardDescription>
                <div className="flex items-center gap-2 mt-2">
                  <Switch
                    id="include-current-month-gna"
                    checked={includeCurrentMonthGNA}
                    onCheckedChange={setIncludeCurrentMonthGNA}
                  />
                  <Label htmlFor="include-current-month-gna" className="text-sm text-muted-foreground cursor-pointer">
                    Include current month
                  </Label>
                </div>
              </div>
              {monthlyExpenses && monthlyExpenses.length > 0 && (() => {
                const monthsWithData = monthlyExpenses.filter(item => item.expenses > 0)
                if (monthsWithData.length === 0) return null
                const avgExpenses = monthsWithData.reduce((sum, item) => sum + item.expenses, 0) / monthsWithData.length

                return (
                  <div className="text-right">
                    <div>
                      <p className="text-sm text-muted-foreground">Avg Expenses</p>
                      <p className="text-lg font-semibold">${(avgExpenses / 1000).toFixed(0)}k</p>
                    </div>
                  </div>
                )
              })()}
            </div>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <ComposedChart data={(() => {
                const data = monthlyExpenses || []
                if (data.length === 0) return data

                // Calculate average for all months (already filtered)
                const monthsWithData = data.filter(item => item.expenses > 0)
                const avgExpenses = monthsWithData.length > 0
                  ? monthsWithData.reduce((sum, item) => sum + item.expenses, 0) / monthsWithData.length
                  : 0

                // Calculate linear regression for trendline
                let trendSlope = 0
                let trendIntercept = 0

                if (monthsWithData.length >= 2) {
                  const n = monthsWithData.length
                  const sumX = monthsWithData.reduce((sum, item, i) => sum + i, 0)
                  const sumY = monthsWithData.reduce((sum, item) => sum + item.expenses, 0)
                  const meanX = sumX / n
                  const meanY = sumY / n

                  let numerator = 0
                  let denominator = 0
                  monthsWithData.forEach((item, i) => {
                    numerator += (i - meanX) * (item.expenses - meanY)
                    denominator += (i - meanX) * (i - meanX)
                  })

                  trendSlope = denominator !== 0 ? numerator / denominator : 0
                  trendIntercept = meanY - trendSlope * meanX
                }

                // Add average and trendline to each data point
                return data.map((item, index) => ({
                  ...item,
                  avgExpenses: avgExpenses,
                  trendline: item.expenses > 0 ? trendSlope * index + trendIntercept : null
                }))
              })()} margin={{ top: 20, right: 70, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                <Tooltip content={({ active, payload, label }) => {
                  if (active && payload && payload.length && monthlyExpenses) {
                    const currentIndex = monthlyExpenses.findIndex(item => item.month === label)
                    const currentData = monthlyExpenses[currentIndex]
                    const previousData = currentIndex > 0 ? monthlyExpenses[currentIndex - 1] : null
                    
                    const formatCurrency = (value) => {
                      return new Intl.NumberFormat('en-US', {
                        style: 'currency',
                        currency: 'USD',
                        minimumFractionDigits: 0,
                        maximumFractionDigits: 0,
                      }).format(value)
                    }
                    
                    const calculatePercentageChange = (current, previous) => {
                      if (!previous || previous === 0) return null
                      const change = ((current - previous) / previous) * 100
                      return change
                    }
                    
                    const formatPercentage = (percentage) => {
                      if (percentage === null) return ''
                      const sign = percentage >= 0 ? '+' : ''
                      const color = percentage >= 0 ? 'text-red-600' : 'text-green-600'
                      return <span className={`ml-2 ${color}`}>({sign}{percentage.toFixed(1)}%)</span>
                    }
                    
                    return (
                      <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                        <p className="font-semibold mb-2">{label}</p>
                        <div className="space-y-1">
                          <p className="text-red-600">
                            Expenses: {formatCurrency(currentData.expenses)}
                            {previousData && previousData.expenses > 0 && formatPercentage(calculatePercentageChange(currentData.expenses, previousData.expenses))}
                          </p>
                        </div>
                      </div>
                    )
                  }
                  return null
                }} />
                <Legend />
                <Bar
                  dataKey="expenses"
                  fill="#ef4444"
                  name="G&A Expenses"
                  maxBarSize={60}
                  cursor="pointer"
                  onClick={(data) => {
                    if (data && data.year) {
                      // Parse month from the month label (e.g., "Mar '25" -> 3)
                      const monthMap = { 'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                                        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12 }
                      const monthAbbr = data.month.split(' ')[0]
                      const monthNum = monthMap[monthAbbr]
                      if (monthNum) {
                        fetchGnaExpensesDetails(data.year, monthNum, data.month)
                      }
                    }
                  }}
                />
                {/* Average Expenses Line */}
                <Line 
                  type="monotone"
                  dataKey="avgExpenses"
                  stroke="#666"
                  strokeDasharray="5 5"
                  strokeWidth={2}
                  name="Average"
                  dot={false}
                />
                {/* Trendline */}
                <Line 
                  type="monotone"
                  dataKey="trendline"
                  stroke="#2563eb"
                  strokeWidth={2}
                  name="Trend"
                  dot={false}
                  connectNulls={false}
                />
                {/* Add ReferenceLine for the label */}
                {monthlyExpenses && monthlyExpenses.length > 0 && (() => {
                  const currentDate = new Date()
                  const currentMonthIndex = currentDate.getMonth()
                  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                  const currentMonthName = monthNames[currentMonthIndex]
                  
                  // Calculate average excluding current month and incomplete months
                  const monthsWithData = monthlyExpenses.filter(item => item.expenses > 0)
                  const roughAverage = monthsWithData.length > 0 
                    ? monthsWithData.reduce((sum, item) => sum + item.expenses, 0) / monthsWithData.length 
                    : 0
                  
                  const completeMonths = monthlyExpenses.filter(item => {
                    return item.month !== currentMonthName && 
                           item.expenses > 0 && 
                           item.expenses > (roughAverage * 0.5)
                  })
                  
                  const avgExpenses = completeMonths.length > 0 
                    ? completeMonths.reduce((sum, item) => sum + item.expenses, 0) / completeMonths.length 
                    : 0
                  
                  if (avgExpenses > 0) {
                    return (
                      <ReferenceLine 
                        y={avgExpenses} 
                        stroke="none"
                        label={{ value: "Average", position: "insideTopRight" }}
                      />
                    )
                  }
                  return null
                })()}
              </ComposedChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

          {/* Professional Services Expenses Over Time - Hidden for IPS */}
          {organization?.name !== 'Industrial Parts & Service' && (
          <Card>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle>Professional Services Expenses Over Time</CardTitle>
                  <CardDescription>Account 603000 - March 2025 onwards • Click a bar for invoice details</CardDescription>
                  <div className="flex items-center gap-2 mt-2">
                    <Switch
                      id="include-current-month-prof-services"
                      checked={includeCurrentMonthProfServices}
                      onCheckedChange={setIncludeCurrentMonthProfServices}
                    />
                    <Label htmlFor="include-current-month-prof-services" className="text-sm text-muted-foreground cursor-pointer">
                      Include current month
                    </Label>
                  </div>
                </div>
                {professionalServicesExpenses && professionalServicesExpenses.length > 0 && (() => {
                  const monthsWithData = professionalServicesExpenses.filter(item => item.expenses > 0)
                  if (monthsWithData.length === 0) return null
                  const avgExpenses = monthsWithData.reduce((sum, item) => sum + item.expenses, 0) / monthsWithData.length

                  return (
                    <div className="text-right">
                      <div>
                        <p className="text-sm text-muted-foreground">Avg Expenses</p>
                        <p className="text-lg font-semibold">${(avgExpenses / 1000).toFixed(0)}k</p>
                      </div>
                    </div>
                  )
                })()}
              </div>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={350}>
                <ComposedChart data={(() => {
                  const data = professionalServicesExpenses || []
                  if (data.length === 0) return data

                  // Calculate average for all months (already filtered)
                  const monthsWithData = data.filter(item => item.expenses > 0)
                  const avgExpenses = monthsWithData.length > 0
                    ? monthsWithData.reduce((sum, item) => sum + item.expenses, 0) / monthsWithData.length
                    : 0

                  // Calculate linear regression for trendline
                  let trendSlope = 0
                  let trendIntercept = 0

                  if (monthsWithData.length >= 2) {
                    const n = monthsWithData.length
                    const sumX = monthsWithData.reduce((sum, item, i) => sum + i, 0)
                    const sumY = monthsWithData.reduce((sum, item) => sum + item.expenses, 0)
                    const meanX = sumX / n
                    const meanY = sumY / n

                    let numerator = 0
                    let denominator = 0
                    monthsWithData.forEach((item, i) => {
                      numerator += (i - meanX) * (item.expenses - meanY)
                      denominator += (i - meanX) * (i - meanX)
                    })

                    trendSlope = denominator !== 0 ? numerator / denominator : 0
                    trendIntercept = meanY - trendSlope * meanX
                  }

                  // Add average and trendline to each data point
                  return data.map((item, index) => ({
                    ...item,
                    avgExpenses: avgExpenses,
                    trendline: item.expenses > 0 ? trendSlope * index + trendIntercept : null
                  }))
                })()} margin={{ top: 20, right: 70, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                  <Tooltip content={({ active, payload, label }) => {
                    if (active && payload && payload.length && professionalServicesExpenses) {
                      const currentIndex = professionalServicesExpenses.findIndex(item => item.month === label)
                      const currentData = professionalServicesExpenses[currentIndex]
                      const previousData = currentIndex > 0 ? professionalServicesExpenses[currentIndex - 1] : null

                      const formatCurrency = (value) => {
                        return new Intl.NumberFormat('en-US', {
                          style: 'currency',
                          currency: 'USD',
                          minimumFractionDigits: 0,
                          maximumFractionDigits: 0,
                        }).format(value)
                      }

                      const calculatePercentageChange = (current, previous) => {
                        if (!previous || previous === 0) return null
                        const change = ((current - previous) / previous) * 100
                        return change
                      }

                      const formatPercentage = (percentage) => {
                        if (percentage === null) return ''
                        const sign = percentage >= 0 ? '+' : ''
                        const color = percentage >= 0 ? 'text-red-600' : 'text-green-600'
                        return <span className={`ml-2 ${color}`}>({sign}{percentage.toFixed(1)}%)</span>
                      }

                      return (
                        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                          <p className="font-semibold mb-2">{label}</p>
                          <div className="space-y-1">
                            <p className="text-purple-600">
                              Prof. Services: {formatCurrency(currentData.expenses)}
                              {previousData && previousData.expenses > 0 && formatPercentage(calculatePercentageChange(currentData.expenses, previousData.expenses))}
                            </p>
                          </div>
                        </div>
                      )
                    }
                    return null
                  }} />
                  <Legend />
                  <Bar
                    dataKey="expenses"
                    fill="#8b5cf6"
                    name="Professional Services"
                    maxBarSize={60}
                    cursor="pointer"
                    onClick={(data) => {
                      if (data && data.year) {
                        // Parse month from the month label (e.g., "Mar '25" -> 3)
                        const monthMap = { 'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                                          'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12 }
                        const monthAbbr = data.month.split(' ')[0]
                        const monthNum = monthMap[monthAbbr]
                        if (monthNum) {
                          fetchProfessionalServicesDetails(data.year, monthNum, data.month)
                        }
                      }
                    }}
                  />
                  {/* Average Expenses Line */}
                  <Line
                    type="monotone"
                    dataKey="avgExpenses"
                    stroke="#666"
                    strokeDasharray="5 5"
                    strokeWidth={2}
                    name="Average"
                    dot={false}
                  />
                  {/* Trendline */}
                  <Line
                    type="monotone"
                    dataKey="trendline"
                    stroke="#2563eb"
                    strokeWidth={2}
                    name="Trend"
                    dot={false}
                    connectNulls={false}
                  />
                  {/* Add ReferenceLine for the label */}
                  {professionalServicesExpenses && professionalServicesExpenses.length > 0 && (() => {
                    const currentDate = new Date()
                    const currentMonthIndex = currentDate.getMonth()
                    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                    const currentMonthName = monthNames[currentMonthIndex]

                    // Calculate average excluding current month and incomplete months
                    const monthsWithData = professionalServicesExpenses.filter(item => item.expenses > 0)
                    const roughAverage = monthsWithData.length > 0
                      ? monthsWithData.reduce((sum, item) => sum + item.expenses, 0) / monthsWithData.length
                      : 0

                    const completeMonths = professionalServicesExpenses.filter(item => {
                      return item.month !== currentMonthName &&
                             item.expenses > 0 &&
                             item.expenses > (roughAverage * 0.5)
                    })

                    const avgExpenses = completeMonths.length > 0
                      ? completeMonths.reduce((sum, item) => sum + item.expenses, 0) / completeMonths.length
                      : 0

                    if (avgExpenses > 0) {
                      return (
                        <ReferenceLine
                          y={avgExpenses}
                          stroke="none"
                          label={{ value: "Average", position: "insideTopRight" }}
                        />
                      )
                    }
                    return null
                  })()}
                </ComposedChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
          )}
      {/* Key Customers Over 90 Days */}
      {arData && arData.specific_customers && arData.specific_customers.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Key Customers Over 90 Days</CardTitle>
            <CardDescription>Polaris, Grede, and Owens accounts</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {arData.specific_customers.map((customer, index) => (
                <div key={index} className="space-y-1">
                  <div className="flex justify-between items-start">
                    <span className="font-medium">{customer.name}</span>
                    <span className="font-bold text-red-600">
                      ${customer.amount.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>{customer.invoice_count} invoices</span>
                    <span>Oldest: {customer.max_days_overdue} days</span>
                  </div>
                </div>
              ))}
              <div className="pt-3 mt-3 border-t">
                <div className="flex justify-between font-bold">
                  <span>Total</span>
                  <span className="text-red-600">
                    ${arData.specific_customers.reduce((sum, c) => sum + c.amount, 0).toLocaleString()}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
        </TabsContent>

        <TabsContent value="ar-aging" className="space-y-6">
          <ARAgingReport user={user} />
        </TabsContent>

        <TabsContent value="ap-aging" className="space-y-6">
          <APAgingReport user={user} />
        </TabsContent>

        <TabsContent value="commissions" className="space-y-6">
          <SalesCommissionReport user={user} />
        </TabsContent>

        <TabsContent value="control" className="space-y-6">
          <ControlNumberReport />
        </TabsContent>
        <TabsContent value="inventory" className="space-y-6">
          <InventoryReport user={user} />
        </TabsContent>


      </Tabs>

      {/* Professional Services Detail Sheet */}
      <Sheet open={profServicesDetailOpen} onOpenChange={setProfServicesDetailOpen}>
        <SheetContent className="w-[600px] sm:max-w-[600px] overflow-y-auto">
          <SheetHeader>
            <SheetTitle>Professional Services Details</SheetTitle>
            <SheetDescription>
              {profServicesDetail?.monthLabel ? `Invoices for ${profServicesDetail.monthLabel}` : 'Loading...'}
            </SheetDescription>
          </SheetHeader>

          {profServicesDetailLoading ? (
            <div className="flex items-center justify-center py-8">
              <LoadingSpinner size="medium" />
            </div>
          ) : profServicesDetail?.error ? (
            <div className="text-red-500 py-4">{profServicesDetail.error}</div>
          ) : profServicesDetail?.invoices ? (
            <div className="mt-4">
              <div className="flex justify-between items-center mb-4 pb-2 border-b">
                <span className="text-sm text-muted-foreground">{profServicesDetail.count} invoices</span>
                <span className="font-semibold text-lg">{formatCurrency(profServicesDetail.total)}</span>
              </div>

              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Vendor</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {profServicesDetail.invoices.map((invoice, idx) => (
                    <TableRow key={idx}>
                      <TableCell>
                        <div className="font-medium">{invoice.vendor_name}</div>
                        {invoice.description && (
                          <div className="text-xs text-muted-foreground truncate max-w-[250px]" title={invoice.description}>
                            {invoice.description}
                          </div>
                        )}
                      </TableCell>
                      <TableCell className="text-sm">
                        {invoice.date ? new Date(invoice.date).toLocaleDateString() : '-'}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrency(invoice.amount)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : null}
        </SheetContent>
      </Sheet>

      {/* G&A Expenses Detail Sheet */}
      <Sheet open={gnaDetailOpen} onOpenChange={(open) => {
        setGnaDetailOpen(open)
        if (!open) setSelectedGnaAccount(null) // Reset selection when closing
      }}>
        <SheetContent className="w-[700px] sm:max-w-[700px] overflow-y-auto">
          <SheetHeader>
            <SheetTitle>G&A Expenses Details</SheetTitle>
            <SheetDescription>
              {gnaDetail?.monthLabel ? `Expenses for ${gnaDetail.monthLabel}` : 'Loading...'}
            </SheetDescription>
          </SheetHeader>

          {gnaDetailLoading ? (
            <div className="flex items-center justify-center py-8">
              <LoadingSpinner size="medium" />
            </div>
          ) : gnaDetail?.error ? (
            <div className="text-red-500 py-4">{gnaDetail.error}</div>
          ) : gnaDetail?.by_account ? (
            <div className="mt-4">
              <div className="flex justify-between items-center mb-4 pb-2 border-b">
                <span className="text-sm text-muted-foreground">{gnaDetail.count} transactions</span>
                <span className="font-semibold text-lg">{formatCurrency(gnaDetail.total)}</span>
              </div>

              {/* Summary by Account - Accordion style */}
              <div>
                <h4 className="font-semibold text-sm mb-2">By Account <span className="text-muted-foreground font-normal">(click to expand)</span></h4>
                <div className="space-y-1">
                  {gnaDetail.by_account.map((account, idx) => {
                    const isExpanded = selectedGnaAccount?.account_no === account.account_no
                    const accountTransactions = gnaDetail.expenses.filter(exp => exp.account_no === account.account_no)

                    return (
                      <div key={idx} className="border rounded">
                        {/* Account Header Row */}
                        <div
                          className={`flex justify-between items-center text-sm p-2 cursor-pointer transition-colors ${
                            isExpanded
                              ? 'bg-blue-100 dark:bg-blue-900'
                              : 'hover:bg-muted'
                          }`}
                          onClick={() => setSelectedGnaAccount(isExpanded ? null : account)}
                        >
                          <div className="flex-1 flex items-center">
                            <span className={`mr-2 transition-transform ${isExpanded ? 'rotate-90' : ''}`}>▶</span>
                            <span className="text-muted-foreground">{account.account_no}</span>
                            <span className="ml-2 font-medium">{account.account_title || 'Unknown'}</span>
                            <span className="text-muted-foreground ml-1">({account.count})</span>
                          </div>
                          <span className="font-medium">{formatCurrency(account.total)}</span>
                        </div>

                        {/* Expanded Transactions */}
                        {isExpanded && (
                          <div className="border-t bg-muted/30 p-2">
                            <Table>
                              <TableHeader>
                                <TableRow>
                                  <TableHead className="text-xs">Description</TableHead>
                                  <TableHead className="text-xs">Date</TableHead>
                                  <TableHead className="text-xs text-right">Amount</TableHead>
                                </TableRow>
                              </TableHeader>
                              <TableBody>
                                {accountTransactions.slice(0, 100).map((expense, expIdx) => (
                                  <TableRow key={expIdx}>
                                    <TableCell>
                                      <div className="text-sm truncate max-w-[280px]" title={expense.description}>
                                        {expense.description || '-'}
                                      </div>
                                    </TableCell>
                                    <TableCell className="text-sm">
                                      {expense.date ? new Date(expense.date).toLocaleDateString() : '-'}
                                    </TableCell>
                                    <TableCell className="text-right font-medium">
                                      {formatCurrency(expense.amount)}
                                    </TableCell>
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                            {accountTransactions.length > 100 && (
                              <div className="text-xs text-muted-foreground mt-2 text-center">
                                Showing first 100 of {accountTransactions.length} transactions
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          ) : null}
        </SheetContent>
      </Sheet>

    </div>
  )
}

export default AccountingReport