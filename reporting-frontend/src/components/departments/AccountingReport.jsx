import { useState, useEffect } from 'react'
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
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  Area,
  AreaChart
} from 'recharts'
import { 
  DollarSign,
  TrendingUp,
  TrendingDown,
  Receipt,
  CreditCard,
  AlertCircle,
  FileText,
  Calculator,
  Database
} from 'lucide-react'
import { apiUrl } from '@/lib/api'
import AccountingDiagnostics from './AccountingDiagnostics'

const AccountingReport = ({ user }) => {
  const [accountingData, setAccountingData] = useState(null)
  const [monthlyExpenses, setMonthlyExpenses] = useState([])
  const [loading, setLoading] = useState(true)
  const [diagnosticsOpen, setDiagnosticsOpen] = useState(false)

  useEffect(() => {
    fetchAccountingData()
  }, [])

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
        setMonthlyExpenses(data.monthly_expenses || [])
        setAccountingData(data)
      }
    } catch (error) {
      console.error('Error fetching accounting data:', error)
    } finally {
      setLoading(false)
    }
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

  const mockData = {
    summary: {
      totalRevenue: 2456780,
      totalExpenses: 1845320,
      netProfit: 611460,
      profitMargin: 24.9,
      accountsReceivable: 456230,
      accountsPayable: 234560,
      cashFlow: 178900,
      overdueInvoices: 23
    },
    revenueByDepartment: [
      { department: 'Service', revenue: 887450, percentage: 36.1 },
      { department: 'Parts', revenue: 654320, percentage: 26.6 },
      { department: 'Rental', revenue: 785640, percentage: 32.0 },
      { department: 'Other', revenue: 129370, percentage: 5.3 }
    ],
    expenseCategories: [
      { category: 'Labor', amount: 645000, percentage: 35.0 },
      { category: 'Parts & Materials', amount: 456780, percentage: 24.8 },
      { category: 'Equipment', amount: 345670, percentage: 18.7 },
      { category: 'Overhead', amount: 234560, percentage: 12.7 },
      { category: 'Other', amount: 163310, percentage: 8.8 }
    ],
    monthlyFinancials: [
      { month: 'Jan', revenue: 385000, expenses: 298000, profit: 87000 },
      { month: 'Feb', revenue: 412000, expenses: 315000, profit: 97000 },
      { month: 'Mar', revenue: 398000, expenses: 302000, profit: 96000 },
      { month: 'Apr', revenue: 425000, expenses: 318000, profit: 107000 },
      { month: 'May', revenue: 418000, expenses: 305000, profit: 113000 },
      { month: 'Jun', revenue: 418780, expenses: 307320, profit: 111460 }
    ],
    cashFlowTrend: [
      { week: 'W1', inflow: 125000, outflow: 98000, net: 27000 },
      { week: 'W2', inflow: 115000, outflow: 102000, net: 13000 },
      { week: 'W3', inflow: 135000, outflow: 95000, net: 40000 },
      { week: 'W4', inflow: 145000, outflow: 89000, net: 56000 }
    ],
    outstandingInvoices: [
      { invoiceNumber: 'INV-2024-0145', customer: 'ABC Construction', amount: 45670, daysOverdue: 15, status: 'Overdue' },
      { invoiceNumber: 'INV-2024-0156', customer: 'XYZ Builders', amount: 32450, daysOverdue: 0, status: 'Current' },
      { invoiceNumber: 'INV-2024-0167', customer: 'DEF Mining', amount: 78900, daysOverdue: 30, status: 'Overdue' },
      { invoiceNumber: 'INV-2024-0178', customer: 'GHI Contractors', amount: 12340, daysOverdue: 5, status: 'Late' },
      { invoiceNumber: 'INV-2024-0189', customer: 'JKL Logistics', amount: 56780, daysOverdue: 0, status: 'Current' }
    ],
    pendingPayables: [
      { vendor: 'CAT Parts Direct', amount: 45670, dueDate: '2024-06-25', status: 'Due Soon' },
      { vendor: 'Hydraulic Supply Co', amount: 23450, dueDate: '2024-06-30', status: 'Current' },
      { vendor: 'Fleet Insurance Inc', amount: 18900, dueDate: '2024-06-20', status: 'Overdue' },
      { vendor: 'Utility Services', amount: 5670, dueDate: '2024-07-05', status: 'Current' },
      { vendor: 'Equipment Finance', amount: 34560, dueDate: '2024-06-28', status: 'Due Soon' }
    ]
  }

  const data = accountingData || mockData

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Accounting Department</h1>
          <p className="text-muted-foreground">Financial overview and accounting metrics</p>
        </div>
        <Button 
          variant="outline" 
          size="sm"
          onClick={() => setDiagnosticsOpen(true)}
        >
          <Database className="mr-2 h-4 w-4" />
          Table Diagnostics
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${(data.summary.totalRevenue / 1000000).toFixed(2)}M</div>
            <p className="text-xs text-muted-foreground">Year to date</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Expenses</CardTitle>
            <TrendingDown className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${(data.summary.totalExpenses / 1000000).toFixed(2)}M</div>
            <p className="text-xs text-muted-foreground">Year to date</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Net Profit</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">${(data.summary.netProfit / 1000).toFixed(0)}K</div>
            <p className="text-xs text-muted-foreground">{data.summary.profitMargin}% margin</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Cash Flow</CardTitle>
            <Calculator className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${(data.summary.cashFlow / 1000).toFixed(0)}K</div>
            <p className="text-xs text-muted-foreground">This month</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Receivables</CardTitle>
            <Receipt className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${(data.summary.accountsReceivable / 1000).toFixed(0)}K</div>
            <p className="text-xs text-muted-foreground">Outstanding</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Payables</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${(data.summary.accountsPayable / 1000).toFixed(0)}K</div>
            <p className="text-xs text-muted-foreground">Outstanding</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overdue</CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{data.summary.overdueInvoices}</div>
            <p className="text-xs text-muted-foreground">Invoices</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">YTD Growth</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">+12.5%</div>
            <p className="text-xs text-muted-foreground">vs last year</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {/* Revenue by Department */}
        <Card>
          <CardHeader>
            <CardTitle>Revenue by Department</CardTitle>
            <CardDescription>Year-to-date revenue distribution</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <PieChart>
                <Pie
                  data={data.revenueByDepartment}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ department, percentage }) => `${department}: ${percentage}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="revenue"
                >
                  {data.revenueByDepartment.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* G&A Expenses Over Time */}
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle>G&A Expenses Over Time</CardTitle>
                <CardDescription>General & Administrative expenses (Payroll, Professional Services, etc.)</CardDescription>
              </div>
              {monthlyExpenses && monthlyExpenses.length > 1 && (() => {
                const completeMonths = monthlyExpenses.slice(0, -1)
                const average = completeMonths.reduce((sum, item) => sum + item.expenses, 0) / completeMonths.length
                return (
                  <div className="text-right">
                    <p className="text-sm text-muted-foreground">Average</p>
                    <p className="text-lg font-semibold">${(average / 1000).toFixed(0)}k</p>
                  </div>
                )
              })()}
            </div>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={monthlyExpenses.slice(0, -1)} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                <Tooltip content={({ active, payload, label }) => {
                  if (active && payload && payload.length && monthlyExpenses) {
                    const data = monthlyExpenses.slice(0, -1)
                    const currentIndex = data.findIndex(item => item.month === label)
                    const currentValue = payload[0].value
                    const previousValue = currentIndex > 0 ? data[currentIndex - 1].expenses : null
                    
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
                        <p className="font-semibold mb-1">{label}</p>
                        <p className="text-gray-900">
                          {formatCurrency(currentValue)}
                          {previousValue && formatPercentage(calculatePercentageChange(currentValue, previousValue))}
                        </p>
                      </div>
                    )
                  }
                  return null
                }} />
                <Bar 
                  dataKey="expenses" 
                  fill="#ef4444"
                />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Expense Categories */}
      <Card>
        <CardHeader>
          <CardTitle>Expense Breakdown</CardTitle>
          <CardDescription>Major expense categories</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.expenseCategories} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="category" type="category" />
              <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
              <Bar dataKey="amount" fill="#ef4444" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Monthly Financial Trend */}
      <Card>
        <CardHeader>
          <CardTitle>Financial Performance</CardTitle>
          <CardDescription>Monthly revenue, expenses, and profit trends</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={data.monthlyFinancials}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
              <Area type="monotone" dataKey="revenue" stackId="1" stroke="#3b82f6" fill="#3b82f6" name="Revenue" />
              <Area type="monotone" dataKey="expenses" stackId="2" stroke="#ef4444" fill="#ef4444" name="Expenses" />
              <Line type="monotone" dataKey="profit" stroke="#10b981" strokeWidth={3} name="Profit" />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Weekly Cash Flow */}
      <Card>
        <CardHeader>
          <CardTitle>Weekly Cash Flow</CardTitle>
          <CardDescription>Cash inflows and outflows for the current month</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data.cashFlowTrend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="week" />
              <YAxis />
              <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
              <Bar dataKey="inflow" fill="#10b981" name="Inflow" />
              <Bar dataKey="outflow" fill="#ef4444" name="Outflow" />
              <Line type="monotone" dataKey="net" stroke="#3b82f6" strokeWidth={2} name="Net" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        {/* Outstanding Invoices */}
        <Card>
          <CardHeader>
            <CardTitle>Outstanding Invoices</CardTitle>
            <CardDescription>Customer invoices pending payment</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Invoice</TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.outstandingInvoices.map((invoice) => (
                  <TableRow key={invoice.invoiceNumber}>
                    <TableCell className="font-medium">{invoice.invoiceNumber}</TableCell>
                    <TableCell>{invoice.customer}</TableCell>
                    <TableCell className="text-right">${invoice.amount.toLocaleString()}</TableCell>
                    <TableCell>
                      <Badge 
                        variant={
                          invoice.status === 'Overdue' ? 'destructive' : 
                          invoice.status === 'Late' ? 'default' : 'success'
                        }
                      >
                        {invoice.status}
                        {invoice.daysOverdue > 0 && ` (${invoice.daysOverdue}d)`}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Pending Payables */}
        <Card>
          <CardHeader>
            <CardTitle>Pending Payables</CardTitle>
            <CardDescription>Vendor payments due</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Vendor</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead>Due Date</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.pendingPayables.map((payable, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-medium">{payable.vendor}</TableCell>
                    <TableCell className="text-right">${payable.amount.toLocaleString()}</TableCell>
                    <TableCell>{new Date(payable.dueDate).toLocaleDateString()}</TableCell>
                    <TableCell>
                      <Badge 
                        variant={
                          payable.status === 'Overdue' ? 'destructive' : 
                          payable.status === 'Due Soon' ? 'default' : 'secondary'
                        }
                      >
                        {payable.status}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      {/* Diagnostics Modal */}
      {diagnosticsOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-7xl w-full max-h-[90vh] overflow-y-auto p-6">
            <AccountingDiagnostics onClose={() => setDiagnosticsOpen(false)} />
          </div>
        </div>
      )}
    </div>
  )
}

export default AccountingReport