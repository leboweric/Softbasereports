import { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { apiUrl } from '@/lib/api'
import { 
  DollarSign, 
  Users, 
  TrendingUp, 
  AlertTriangle, 
  Calendar, 
  Plus,
  Search,
  RefreshCw,
  Building2,
  FileSpreadsheet,
  ArrowUpRight,
  ArrowDownRight,
  Download,
  ChevronLeft,
  ChevronRight,
  Columns,
  LayoutGrid
} from 'lucide-react'

const VitalFinanceBilling = ({ user, organization }) => {
  const [clients, setClients] = useState([])
  const [summary, setSummary] = useState(null)
  const [renewals, setRenewals] = useState([])
  const [spreadsheetData, setSpreadsheetData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear())
  const [revenueType, setRevenueType] = useState('revrec') // 'cash', 'revrec', or 'dual'
  const [showAddClient, setShowAddClient] = useState(false)
  const [activeTab, setActiveTab] = useState('spreadsheet')
  const tableContainerRef = useRef(null)
  const [wpoPivotData, setWpoPivotData] = useState(null)
  const [wpoSessionProduct, setWpoSessionProduct] = useState('all')
  const [wpoRevenueTiming, setWpoRevenueTiming] = useState('cash')
  const [newClient, setNewClient] = useState({
    billing_name: '',
    hubspot_company_name: '',
    industry: '',
    tier: '',
    solution_type: '',
    status: 'active'
  })

  // Column visibility state
  const [visibleColumns, setVisibleColumns] = useState({
    revenue_type: true,
    billing_name: true,
    tier: true,
    industry: false,
    session_product: false,
    billing_terms: true,
    wpo_flag: false,
    population: true,
    renewal_date: true,
    pepm_2026: true,
    jan: true, feb: true, mar: true, apr: true, may: true, jun: true,
    jul: true, aug: true, sep: true, oct: true, nov: true, dec: true,
    annual_total: true
  })

  useEffect(() => {
    fetchData()
  }, [selectedYear, revenueType])

  useEffect(() => {
    if (activeTab === 'wpo_pivot') {
      fetchWpoPivot(wpoSessionProduct, wpoRevenueTiming)
    }
  }, [activeTab, selectedYear])

  const fetchWpoPivot = async (sessionProduct = 'all', revenueTiming = 'cash') => {
    try {
      const token = localStorage.getItem('token')
      const headers = { 'Authorization': `Bearer ${token}` }
      const params = new URLSearchParams({
        year: selectedYear,
        session_product: sessionProduct,
        revenue_timing: revenueTiming
      })
      const res = await fetch(apiUrl(`/api/vital/finance/pivot/wpo?${params}`), { headers })
      if (res.ok) {
        const data = await res.json()
        setWpoPivotData(data)
      }
    } catch (error) {
      console.error('Error fetching WPO pivot:', error)
    }
  }

  const fetchData = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      const headers = { 'Authorization': `Bearer ${token}` }

      // Fetch clients
      const clientsRes = await fetch(apiUrl('/api/vital/finance/clients'), { headers })
      if (clientsRes.ok) {
        const data = await clientsRes.json()
        setClients(data.clients || [])
      }

      // Fetch summary
      const summaryRes = await fetch(apiUrl(`/api/vital/finance/billing/summary?year=${selectedYear}`), { headers })
      if (summaryRes.ok) {
        const data = await summaryRes.json()
        setSummary(data)
      }

      // Fetch renewals
      const renewalsRes = await fetch(apiUrl('/api/vital/finance/renewals?months=6'), { headers })
      if (renewalsRes.ok) {
        const data = await renewalsRes.json()
        setRenewals(data.renewals || [])
      }

      // Fetch spreadsheet data
      const spreadsheetRes = await fetch(
        apiUrl(`/api/vital/finance/billing/spreadsheet?year=${selectedYear}&type=${revenueType}`), 
        { headers }
      )
      if (spreadsheetRes.ok) {
        const data = await spreadsheetRes.json()
        setSpreadsheetData(data)
      }
    } catch (error) {
      console.error('Error fetching finance data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAddClient = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/vital/finance/clients'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newClient)
      })

      if (response.ok) {
        setShowAddClient(false)
        setNewClient({
          billing_name: '',
          hubspot_company_name: '',
          industry: '',
          tier: '',
          solution_type: '',
          status: 'active'
        })
        fetchData()
      }
    } catch (error) {
      console.error('Error adding client:', error)
    }
  }

  const exportToCSV = () => {
    if (!spreadsheetData?.rows) return
    
    const headers = spreadsheetData.columns.filter(col => visibleColumns[col] !== false)
    const rows = spreadsheetData.rows.map(row => 
      headers.map(col => {
        const val = row[col]
        if (typeof val === 'number') return val
        if (val === null || val === undefined) return ''
        return `"${String(val).replace(/"/g, '""')}"`
      }).join(',')
    )
    
    const csv = [headers.join(','), ...rows].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `billing_${revenueType}_${selectedYear}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const filteredClients = clients.filter(client =>
    client.billing_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    client.hubspot_company_name?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const filteredSpreadsheetRows = spreadsheetData?.rows?.filter(row =>
    row.billing_name?.toLowerCase().includes(searchTerm.toLowerCase())
  ) || []

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value || 0)
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  const getStatusBadge = (status) => {
    const variants = {
      'active': 'bg-green-100 text-green-800',
      'at_risk': 'bg-yellow-100 text-yellow-800',
      'termed': 'bg-red-100 text-red-800'
    }
    return <Badge className={variants[status] || 'bg-gray-100 text-gray-800'}>{status}</Badge>
  }

  const getBillingTermsBadge = (terms) => {
    const colors = {
      'annual': 'bg-blue-100 text-blue-800',
      'qtly': 'bg-purple-100 text-purple-800',
      'quarterly': 'bg-purple-100 text-purple-800',
      'monthly': 'bg-green-100 text-green-800',
      'semi': 'bg-orange-100 text-orange-800'
    }
    return <Badge className={colors[terms?.toLowerCase()] || 'bg-gray-100 text-gray-800'}>{terms}</Badge>
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Finance</h1>
          <p className="text-gray-500">Billing management and revenue tracking</p>
        </div>
        <div className="flex gap-2 items-center">
          <Select value={selectedYear.toString()} onValueChange={(v) => setSelectedYear(parseInt(v))}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="2024">2024</SelectItem>
              <SelectItem value="2025">2025</SelectItem>
              <SelectItem value="2026">2026</SelectItem>
              <SelectItem value="2027">2027</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={fetchData} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Annual Revenue (RevRec)</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(spreadsheetData?.total_annual)}</div>
            <p className="text-xs text-muted-foreground">{selectedYear} projection</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Clients</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{clients.filter(c => c.status === 'active').length}</div>
            <p className="text-xs text-muted-foreground">{clients.length} total</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">At Risk Revenue</CardTitle>
            <AlertTriangle className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {formatCurrency(summary?.at_risk?.monthly_at_risk * 12)}
            </div>
            <p className="text-xs text-muted-foreground">
              {summary?.at_risk?.at_risk_count || 0} clients at risk
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Upcoming Renewals</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{renewals.length}</div>
            <p className="text-xs text-muted-foreground">Next 6 months</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="spreadsheet">
            <FileSpreadsheet className="h-4 w-4 mr-2" />
            Billing Table
          </TabsTrigger>
          <TabsTrigger value="clients">Clients</TabsTrigger>
          <TabsTrigger value="wpo_pivot">WPO Pivot</TabsTrigger>
          <TabsTrigger value="renewals">Renewals</TabsTrigger>
          <TabsTrigger value="summary">Summary</TabsTrigger>
        </TabsList>

        {/* Spreadsheet Tab - NEW */}
        <TabsContent value="spreadsheet" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>Billing Data Table {selectedYear}</CardTitle>
                  <CardDescription>
                    Full spreadsheet view with monthly breakdown • {filteredSpreadsheetRows.length} rows
                  </CardDescription>
                </div>
                <div className="flex gap-2 items-center">
                  {/* Revenue Type Toggle */}
                  <div className="flex items-center gap-2 bg-gray-100 rounded-lg p-1">
                    <Button 
                      size="sm" 
                      variant={revenueType === 'cash' ? 'default' : 'ghost'}
                      onClick={() => setRevenueType('cash')}
                    >
                      Cash
                    </Button>
                    <Button 
                      size="sm" 
                      variant={revenueType === 'revrec' ? 'default' : 'ghost'}
                      onClick={() => setRevenueType('revrec')}
                    >
                      RevRec
                    </Button>
                    <Button 
                      size="sm" 
                      variant={revenueType === 'dual' ? 'default' : 'ghost'}
                      onClick={() => setRevenueType('dual')}
                    >
                      Both
                    </Button>
                  </div>
                  <div className="relative">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-8 w-48"
                    />
                  </div>
                  <Button variant="outline" onClick={exportToCSV}>
                    <Download className="h-4 w-4 mr-2" />
                    Export CSV
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div 
                ref={tableContainerRef}
                className="overflow-x-auto border rounded-lg"
                style={{ maxHeight: '600px' }}
              >
                <Table>
                  <TableHeader className="sticky top-0 bg-white z-10">
                    <TableRow>
                      {revenueType === 'dual' && <TableHead className="sticky left-0 bg-gray-50 z-20 min-w-[80px]">Type</TableHead>}
                      <TableHead className={`sticky ${revenueType === 'dual' ? 'left-[80px]' : 'left-0'} bg-gray-50 z-20 min-w-[200px]`}>Client</TableHead>
                      <TableHead className="min-w-[80px]">Tier</TableHead>
                      <TableHead className="min-w-[80px]">Terms</TableHead>
                      <TableHead className="text-right min-w-[80px]">Pop</TableHead>
                      <TableHead className="min-w-[100px]">Renewal</TableHead>
                      <TableHead className="text-right min-w-[80px]">PEPM</TableHead>
                      <TableHead className="text-right min-w-[90px] bg-blue-50">Jan</TableHead>
                      <TableHead className="text-right min-w-[90px] bg-blue-50">Feb</TableHead>
                      <TableHead className="text-right min-w-[90px] bg-blue-50">Mar</TableHead>
                      <TableHead className="text-right min-w-[90px] bg-green-50">Apr</TableHead>
                      <TableHead className="text-right min-w-[90px] bg-green-50">May</TableHead>
                      <TableHead className="text-right min-w-[90px] bg-green-50">Jun</TableHead>
                      <TableHead className="text-right min-w-[90px] bg-yellow-50">Jul</TableHead>
                      <TableHead className="text-right min-w-[90px] bg-yellow-50">Aug</TableHead>
                      <TableHead className="text-right min-w-[90px] bg-yellow-50">Sep</TableHead>
                      <TableHead className="text-right min-w-[90px] bg-orange-50">Oct</TableHead>
                      <TableHead className="text-right min-w-[90px] bg-orange-50">Nov</TableHead>
                      <TableHead className="text-right min-w-[90px] bg-orange-50">Dec</TableHead>
                      <TableHead className="text-right min-w-[100px] bg-gray-100 font-bold">Total</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredSpreadsheetRows.map((row, idx) => (
                      <TableRow 
                        key={`${row.id}-${row.revenue_type}-${idx}`} 
                        className={row.revenue_type === 'CASH' ? 'bg-blue-50/30' : ''}
                      >
                        {revenueType === 'dual' && (
                          <TableCell className="sticky left-0 bg-white z-10 font-medium">
                            <Badge variant={row.revenue_type === 'CASH' ? 'default' : 'secondary'}>
                              {row.revenue_type}
                            </Badge>
                          </TableCell>
                        )}
                        <TableCell className={`sticky ${revenueType === 'dual' ? 'left-[80px]' : 'left-0'} bg-white z-10 font-medium`}>
                          {row.billing_name}
                        </TableCell>
                        <TableCell>{row.tier || '-'}</TableCell>
                        <TableCell>{getBillingTermsBadge(row.billing_terms)}</TableCell>
                        <TableCell className="text-right">{row.population?.toLocaleString() || '-'}</TableCell>
                        <TableCell>{row.renewal_date ? new Date(row.renewal_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '-'}</TableCell>
                        <TableCell className="text-right">${row[`pepm_${selectedYear}`]?.toFixed(2) || '0.00'}</TableCell>
                        <TableCell className="text-right bg-blue-50/50">{formatCurrency(row.jan)}</TableCell>
                        <TableCell className="text-right bg-blue-50/50">{formatCurrency(row.feb)}</TableCell>
                        <TableCell className="text-right bg-blue-50/50">{formatCurrency(row.mar)}</TableCell>
                        <TableCell className="text-right bg-green-50/50">{formatCurrency(row.apr)}</TableCell>
                        <TableCell className="text-right bg-green-50/50">{formatCurrency(row.may)}</TableCell>
                        <TableCell className="text-right bg-green-50/50">{formatCurrency(row.jun)}</TableCell>
                        <TableCell className="text-right bg-yellow-50/50">{formatCurrency(row.jul)}</TableCell>
                        <TableCell className="text-right bg-yellow-50/50">{formatCurrency(row.aug)}</TableCell>
                        <TableCell className="text-right bg-yellow-50/50">{formatCurrency(row.sep)}</TableCell>
                        <TableCell className="text-right bg-orange-50/50">{formatCurrency(row.oct)}</TableCell>
                        <TableCell className="text-right bg-orange-50/50">{formatCurrency(row.nov)}</TableCell>
                        <TableCell className="text-right bg-orange-50/50">{formatCurrency(row.dec)}</TableCell>
                        <TableCell className="text-right bg-gray-100 font-bold">{formatCurrency(row.annual_total)}</TableCell>
                      </TableRow>
                    ))}
                    {/* Totals Row(s) - Dynamically calculated from filtered data */}
                    {revenueType === 'dual' ? (
                      // In dual/Both mode, show separate CASH and REVREC total rows
                      <>
                        {/* CASH Total Row */}
                        <TableRow className="bg-blue-100 font-bold">
                          <TableCell className="sticky left-0 bg-blue-100 z-10">
                            <Badge>CASH</Badge>
                          </TableCell>
                          <TableCell className="sticky left-[80px] bg-blue-100 z-10">TOTAL</TableCell>
                          <TableCell></TableCell>
                          <TableCell></TableCell>
                          <TableCell className="text-right">
                            {filteredSpreadsheetRows.filter(r => r.revenue_type === 'CASH').reduce((sum, r) => sum + (r.population || 0), 0).toLocaleString()}
                          </TableCell>
                          <TableCell></TableCell>
                          <TableCell></TableCell>
                          <TableCell className="text-right">{formatCurrency(filteredSpreadsheetRows.filter(r => r.revenue_type === 'CASH').reduce((sum, r) => sum + (r.jan || 0), 0))}</TableCell>
                          <TableCell className="text-right">{formatCurrency(filteredSpreadsheetRows.filter(r => r.revenue_type === 'CASH').reduce((sum, r) => sum + (r.feb || 0), 0))}</TableCell>
                          <TableCell className="text-right">{formatCurrency(filteredSpreadsheetRows.filter(r => r.revenue_type === 'CASH').reduce((sum, r) => sum + (r.mar || 0), 0))}</TableCell>
                          <TableCell className="text-right">{formatCurrency(filteredSpreadsheetRows.filter(r => r.revenue_type === 'CASH').reduce((sum, r) => sum + (r.apr || 0), 0))}</TableCell>
                          <TableCell className="text-right">{formatCurrency(filteredSpreadsheetRows.filter(r => r.revenue_type === 'CASH').reduce((sum, r) => sum + (r.may || 0), 0))}</TableCell>
                          <TableCell className="text-right">{formatCurrency(filteredSpreadsheetRows.filter(r => r.revenue_type === 'CASH').reduce((sum, r) => sum + (r.jun || 0), 0))}</TableCell>
                          <TableCell className="text-right">{formatCurrency(filteredSpreadsheetRows.filter(r => r.revenue_type === 'CASH').reduce((sum, r) => sum + (r.jul || 0), 0))}</TableCell>
                          <TableCell className="text-right">{formatCurrency(filteredSpreadsheetRows.filter(r => r.revenue_type === 'CASH').reduce((sum, r) => sum + (r.aug || 0), 0))}</TableCell>
                          <TableCell className="text-right">{formatCurrency(filteredSpreadsheetRows.filter(r => r.revenue_type === 'CASH').reduce((sum, r) => sum + (r.sep || 0), 0))}</TableCell>
                          <TableCell className="text-right">{formatCurrency(filteredSpreadsheetRows.filter(r => r.revenue_type === 'CASH').reduce((sum, r) => sum + (r.oct || 0), 0))}</TableCell>
                          <TableCell className="text-right">{formatCurrency(filteredSpreadsheetRows.filter(r => r.revenue_type === 'CASH').reduce((sum, r) => sum + (r.nov || 0), 0))}</TableCell>
                          <TableCell className="text-right">{formatCurrency(filteredSpreadsheetRows.filter(r => r.revenue_type === 'CASH').reduce((sum, r) => sum + (r.dec || 0), 0))}</TableCell>
                          <TableCell className="text-right bg-blue-200 font-bold">{formatCurrency(filteredSpreadsheetRows.filter(r => r.revenue_type === 'CASH').reduce((sum, r) => sum + (r.annual_total || 0), 0))}</TableCell>
                        </TableRow>
                        {/* REVREC Total Row */}
                        <TableRow className="bg-gray-200 font-bold sticky bottom-0">
                          <TableCell className="sticky left-0 bg-gray-200 z-10">
                            <Badge variant="secondary">REVREC</Badge>
                          </TableCell>
                          <TableCell className="sticky left-[80px] bg-gray-200 z-10">TOTAL</TableCell>
                          <TableCell></TableCell>
                          <TableCell></TableCell>
                          <TableCell className="text-right">
                            {filteredSpreadsheetRows.filter(r => r.revenue_type === 'REVREC').reduce((sum, r) => sum + (r.population || 0), 0).toLocaleString()}
                          </TableCell>
                          <TableCell></TableCell>
                          <TableCell></TableCell>
                          <TableCell className="text-right">{formatCurrency(filteredSpreadsheetRows.filter(r => r.revenue_type === 'REVREC').reduce((sum, r) => sum + (r.jan || 0), 0))}</TableCell>
                          <TableCell className="text-right">{formatCurrency(filteredSpreadsheetRows.filter(r => r.revenue_type === 'REVREC').reduce((sum, r) => sum + (r.feb || 0), 0))}</TableCell>
                          <TableCell className="text-right">{formatCurrency(filteredSpreadsheetRows.filter(r => r.revenue_type === 'REVREC').reduce((sum, r) => sum + (r.mar || 0), 0))}</TableCell>
                          <TableCell className="text-right">{formatCurrency(filteredSpreadsheetRows.filter(r => r.revenue_type === 'REVREC').reduce((sum, r) => sum + (r.apr || 0), 0))}</TableCell>
                          <TableCell className="text-right">{formatCurrency(filteredSpreadsheetRows.filter(r => r.revenue_type === 'REVREC').reduce((sum, r) => sum + (r.may || 0), 0))}</TableCell>
                          <TableCell className="text-right">{formatCurrency(filteredSpreadsheetRows.filter(r => r.revenue_type === 'REVREC').reduce((sum, r) => sum + (r.jun || 0), 0))}</TableCell>
                          <TableCell className="text-right">{formatCurrency(filteredSpreadsheetRows.filter(r => r.revenue_type === 'REVREC').reduce((sum, r) => sum + (r.jul || 0), 0))}</TableCell>
                          <TableCell className="text-right">{formatCurrency(filteredSpreadsheetRows.filter(r => r.revenue_type === 'REVREC').reduce((sum, r) => sum + (r.aug || 0), 0))}</TableCell>
                          <TableCell className="text-right">{formatCurrency(filteredSpreadsheetRows.filter(r => r.revenue_type === 'REVREC').reduce((sum, r) => sum + (r.sep || 0), 0))}</TableCell>
                          <TableCell className="text-right">{formatCurrency(filteredSpreadsheetRows.filter(r => r.revenue_type === 'REVREC').reduce((sum, r) => sum + (r.oct || 0), 0))}</TableCell>
                          <TableCell className="text-right">{formatCurrency(filteredSpreadsheetRows.filter(r => r.revenue_type === 'REVREC').reduce((sum, r) => sum + (r.nov || 0), 0))}</TableCell>
                          <TableCell className="text-right">{formatCurrency(filteredSpreadsheetRows.filter(r => r.revenue_type === 'REVREC').reduce((sum, r) => sum + (r.dec || 0), 0))}</TableCell>
                          <TableCell className="text-right bg-gray-300 font-bold">{formatCurrency(filteredSpreadsheetRows.filter(r => r.revenue_type === 'REVREC').reduce((sum, r) => sum + (r.annual_total || 0), 0))}</TableCell>
                        </TableRow>
                      </>
                    ) : (
                      // In single mode (Cash or RevRec), show one total row
                      <TableRow className="bg-gray-200 font-bold sticky bottom-0">
                        <TableCell className="sticky left-0 bg-gray-200 z-10">TOTAL</TableCell>
                        <TableCell></TableCell>
                        <TableCell></TableCell>
                        <TableCell className="text-right">
                          {filteredSpreadsheetRows.reduce((sum, r) => sum + (r.population || 0), 0).toLocaleString()}
                        </TableCell>
                        <TableCell></TableCell>
                        <TableCell></TableCell>
                        <TableCell className="text-right bg-blue-100">{formatCurrency(filteredSpreadsheetRows.reduce((sum, r) => sum + (r.jan || 0), 0))}</TableCell>
                        <TableCell className="text-right bg-blue-100">{formatCurrency(filteredSpreadsheetRows.reduce((sum, r) => sum + (r.feb || 0), 0))}</TableCell>
                        <TableCell className="text-right bg-blue-100">{formatCurrency(filteredSpreadsheetRows.reduce((sum, r) => sum + (r.mar || 0), 0))}</TableCell>
                        <TableCell className="text-right bg-green-100">{formatCurrency(filteredSpreadsheetRows.reduce((sum, r) => sum + (r.apr || 0), 0))}</TableCell>
                        <TableCell className="text-right bg-green-100">{formatCurrency(filteredSpreadsheetRows.reduce((sum, r) => sum + (r.may || 0), 0))}</TableCell>
                        <TableCell className="text-right bg-green-100">{formatCurrency(filteredSpreadsheetRows.reduce((sum, r) => sum + (r.jun || 0), 0))}</TableCell>
                        <TableCell className="text-right bg-yellow-100">{formatCurrency(filteredSpreadsheetRows.reduce((sum, r) => sum + (r.jul || 0), 0))}</TableCell>
                        <TableCell className="text-right bg-yellow-100">{formatCurrency(filteredSpreadsheetRows.reduce((sum, r) => sum + (r.aug || 0), 0))}</TableCell>
                        <TableCell className="text-right bg-yellow-100">{formatCurrency(filteredSpreadsheetRows.reduce((sum, r) => sum + (r.sep || 0), 0))}</TableCell>
                        <TableCell className="text-right bg-orange-100">{formatCurrency(filteredSpreadsheetRows.reduce((sum, r) => sum + (r.oct || 0), 0))}</TableCell>
                        <TableCell className="text-right bg-orange-100">{formatCurrency(filteredSpreadsheetRows.reduce((sum, r) => sum + (r.nov || 0), 0))}</TableCell>
                        <TableCell className="text-right bg-orange-100">{formatCurrency(filteredSpreadsheetRows.reduce((sum, r) => sum + (r.dec || 0), 0))}</TableCell>
                        <TableCell className="text-right bg-gray-300 font-bold">{formatCurrency(filteredSpreadsheetRows.reduce((sum, r) => sum + (r.annual_total || 0), 0))}</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
              
              {/* Legend */}
              <div className="mt-4 flex gap-4 text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-blue-50 border rounded"></div>
                  <span>Q1 (Jan-Mar)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-green-50 border rounded"></div>
                  <span>Q2 (Apr-Jun)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-yellow-50 border rounded"></div>
                  <span>Q3 (Jul-Sep)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-orange-50 border rounded"></div>
                  <span>Q4 (Oct-Dec)</span>
                </div>
                {revenueType === 'dual' && (
                  <>
                    <div className="flex items-center gap-2 ml-4">
                      <Badge>CASH</Badge>
                      <span>When billed</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary">REVREC</Badge>
                      <span>Revenue recognition</span>
                    </div>
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Clients Tab */}
        <TabsContent value="clients" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>Billing Clients</CardTitle>
                  <CardDescription>Manage client billing and population data</CardDescription>
                </div>
                <div className="flex gap-2">
                  <div className="relative">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search clients..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-8 w-64"
                    />
                  </div>
                  <Dialog open={showAddClient} onOpenChange={setShowAddClient}>
                    <DialogTrigger asChild>
                      <Button>
                        <Plus className="h-4 w-4 mr-2" />
                        Add Client
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Add New Client</DialogTitle>
                        <DialogDescription>
                          Add a new billing client to the system
                        </DialogDescription>
                      </DialogHeader>
                      <div className="grid gap-4 py-4">
                        <div className="grid gap-2">
                          <Label htmlFor="billing_name">Billing Name</Label>
                          <Input
                            id="billing_name"
                            value={newClient.billing_name}
                            onChange={(e) => setNewClient({...newClient, billing_name: e.target.value})}
                          />
                        </div>
                        <div className="grid gap-2">
                          <Label htmlFor="hubspot_company_name">HubSpot Company Name</Label>
                          <Input
                            id="hubspot_company_name"
                            value={newClient.hubspot_company_name}
                            onChange={(e) => setNewClient({...newClient, hubspot_company_name: e.target.value})}
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="grid gap-2">
                            <Label htmlFor="industry">Industry</Label>
                            <Select
                              value={newClient.industry}
                              onValueChange={(v) => setNewClient({...newClient, industry: v})}
                            >
                              <SelectTrigger>
                                <SelectValue placeholder="Select..." />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="Healthcare">Healthcare</SelectItem>
                                <SelectItem value="Manufacturing">Manufacturing</SelectItem>
                                <SelectItem value="Financial Services">Financial Services</SelectItem>
                                <SelectItem value="Education">Education</SelectItem>
                                <SelectItem value="Government">Government</SelectItem>
                                <SelectItem value="Other">Other</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="grid gap-2">
                            <Label htmlFor="tier">Tier</Label>
                            <Select
                              value={newClient.tier}
                              onValueChange={(v) => setNewClient({...newClient, tier: v})}
                            >
                              <SelectTrigger>
                                <SelectValue placeholder="Select..." />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="Tier 1">Tier 1</SelectItem>
                                <SelectItem value="Tier 2">Tier 2</SelectItem>
                                <SelectItem value="Tier 3">Tier 3</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                        </div>
                        <div className="grid gap-2">
                          <Label htmlFor="solution_type">Solution Type</Label>
                          <Select
                            value={newClient.solution_type}
                            onValueChange={(v) => setNewClient({...newClient, solution_type: v})}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select..." />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="EAP">EAP</SelectItem>
                              <SelectItem value="Wellness">Wellness</SelectItem>
                              <SelectItem value="EAP + Wellness">EAP + Wellness</SelectItem>
                              <SelectItem value="Custom">Custom</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      <DialogFooter>
                        <Button variant="outline" onClick={() => setShowAddClient(false)}>Cancel</Button>
                        <Button onClick={handleAddClient}>Add Client</Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {filteredClients.length === 0 ? (
                <div className="text-center py-12">
                  <FileSpreadsheet className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No clients yet</h3>
                  <p className="text-gray-500 mb-4">
                    Add your first billing client or import from the spreadsheet
                  </p>
                  <Button onClick={() => setShowAddClient(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    Add Client
                  </Button>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Client</TableHead>
                      <TableHead>Industry</TableHead>
                      <TableHead>Tier</TableHead>
                      <TableHead>Terms</TableHead>
                      <TableHead className="text-right">Population</TableHead>
                      <TableHead className="text-right">PEPM</TableHead>
                      <TableHead className="text-right">Monthly Revenue</TableHead>
                      <TableHead>Renewal</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredClients.map((client) => (
                      <TableRow key={client.id} className="cursor-pointer hover:bg-gray-50">
                        <TableCell>
                          <div>
                            <div className="font-medium">{client.billing_name}</div>
                            {client.hubspot_company_name && client.hubspot_company_name !== client.billing_name && (
                              <div className="text-xs text-gray-500">{client.hubspot_company_name}</div>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>{client.industry || '-'}</TableCell>
                        <TableCell>{client.tier || '-'}</TableCell>
                        <TableCell>{getBillingTermsBadge(client.billing_terms)}</TableCell>
                        <TableCell className="text-right">
                          {client.current_population?.toLocaleString() || '-'}
                        </TableCell>
                        <TableCell className="text-right">
                          {client.current_rate ? `$${parseFloat(client.current_rate).toFixed(2)}` : '-'}
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          {formatCurrency(client.monthly_revenue)}
                        </TableCell>
                        <TableCell>{formatDate(client.renewal_date)}</TableCell>
                        <TableCell>{getStatusBadge(client.status)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* WPO Pivot Tab */}
        <TabsContent value="wpo_pivot" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>WPO Pivot - {selectedYear}</CardTitle>
                  <CardDescription>
                    WPO billing by client • {wpoPivotData?.client_count || 0} clients
                  </CardDescription>
                </div>
                <div className="flex gap-2 items-center">
                  {/* Session Product Filter */}
                  <Select value={wpoSessionProduct} onValueChange={(v) => {
                    setWpoSessionProduct(v)
                    fetchWpoPivot(v, wpoRevenueTiming)
                  }}>
                    <SelectTrigger className="w-40">
                      <SelectValue placeholder="Session Product" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Products</SelectItem>
                      {wpoPivotData?.available_session_products?.map(sp => (
                        <SelectItem key={sp} value={sp}>{sp}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  
                  {/* Revenue Timing Toggle */}
                  <div className="flex items-center gap-2 bg-gray-100 rounded-lg p-1">
                    <Button 
                      size="sm" 
                      variant={wpoRevenueTiming === 'cash' ? 'default' : 'ghost'}
                      onClick={() => {
                        setWpoRevenueTiming('cash')
                        fetchWpoPivot(wpoSessionProduct, 'cash')
                      }}
                    >
                      Cash
                    </Button>
                    <Button 
                      size="sm" 
                      variant={wpoRevenueTiming === 'revrec' ? 'default' : 'ghost'}
                      onClick={() => {
                        setWpoRevenueTiming('revrec')
                        fetchWpoPivot(wpoSessionProduct, 'revrec')
                      }}
                    >
                      RevRec
                    </Button>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {!wpoPivotData ? (
                <div className="text-center py-12">
                  <RefreshCw className="h-8 w-8 animate-spin text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">Loading WPO data...</p>
                </div>
              ) : wpoPivotData.rows?.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  No WPO data available for the selected filters
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>WPO Name</TableHead>
                        <TableHead>Account Number</TableHead>
                        <TableHead>Session Product</TableHead>
                        <TableHead className="text-right">WPO Billing</TableHead>
                        <TableHead className="text-right">Total Revenue</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {wpoPivotData.rows.map((row, idx) => (
                        <TableRow key={idx}>
                          <TableCell className="font-medium">{row.wpo_name}</TableCell>
                          <TableCell className="text-gray-500">{row.wpo_account_number}</TableCell>
                          <TableCell>
                            <Badge variant="outline">{row.session_product}</Badge>
                          </TableCell>
                          <TableCell className="text-right">
                            ${row.wpo_billing?.toFixed(2) || '0.00'}
                          </TableCell>
                          <TableCell className="text-right font-medium">
                            {formatCurrency(row.total_revenue)}
                          </TableCell>
                        </TableRow>
                      ))}
                      {/* Totals Row */}
                      <TableRow className="bg-gray-50 font-bold">
                        <TableCell>TOTAL</TableCell>
                        <TableCell></TableCell>
                        <TableCell>{wpoPivotData.client_count} clients</TableCell>
                        <TableCell className="text-right">
                          ${wpoPivotData.total_wpo_billing?.toFixed(2) || '0.00'}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatCurrency(wpoPivotData.total_revenue)}
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Renewals Tab */
        <TabsContent value="renewals" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Upcoming Renewals</CardTitle>
              <CardDescription>Clients renewing in the next 6 months</CardDescription>
            </CardHeader>
            <CardContent>
              {renewals.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  No upcoming renewals in the next 6 months
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Client</TableHead>
                      <TableHead>Renewal Date</TableHead>
                      <TableHead>Tier</TableHead>
                      <TableHead className="text-right">Population</TableHead>
                      <TableHead className="text-right">Annual Value</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {renewals.map((renewal) => (
                      <TableRow key={renewal.id}>
                        <TableCell className="font-medium">{renewal.billing_name}</TableCell>
                        <TableCell>{formatDate(renewal.renewal_date)}</TableCell>
                        <TableCell>{renewal.tier || '-'}</TableCell>
                        <TableCell className="text-right">
                          {renewal.population?.toLocaleString() || '-'}
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          {formatCurrency(renewal.annual_value)}
                        </TableCell>
                        <TableCell>
                          <Badge variant={renewal.renewal_status === 'confirmed' ? 'success' : 'secondary'}>
                            {renewal.renewal_status || 'pending'}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Summary Tab */}
        <TabsContent value="summary" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* By Tier */}
            <Card>
              <CardHeader>
                <CardTitle>Revenue by Tier</CardTitle>
              </CardHeader>
              <CardContent>
                {summary?.by_tier?.length > 0 ? (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Tier</TableHead>
                        <TableHead className="text-right">Clients</TableHead>
                        <TableHead className="text-right">Avg PEPM</TableHead>
                        <TableHead className="text-right">Total Revenue</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {summary.by_tier.map((tier, idx) => (
                        <TableRow key={idx}>
                          <TableCell className="font-medium">{tier.tier || 'Unassigned'}</TableCell>
                          <TableCell className="text-right">{tier.client_count}</TableCell>
                          <TableCell className="text-right">
                            ${parseFloat(tier.avg_pepm || 0).toFixed(2)}
                          </TableCell>
                          <TableCell className="text-right font-medium">
                            {formatCurrency(tier.total_revenue)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : (
                  <div className="text-center py-8 text-gray-500">No data available</div>
                )}
              </CardContent>
            </Card>

            {/* By Solution */}
            <Card>
              <CardHeader>
                <CardTitle>Revenue by Solution</CardTitle>
              </CardHeader>
              <CardContent>
                {summary?.by_solution?.length > 0 ? (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Solution</TableHead>
                        <TableHead className="text-right">Clients</TableHead>
                        <TableHead className="text-right">Avg PEPM</TableHead>
                        <TableHead className="text-right">Total Revenue</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {summary.by_solution.map((solution, idx) => (
                        <TableRow key={idx}>
                          <TableCell className="font-medium">{solution.solution_type || 'Unassigned'}</TableCell>
                          <TableCell className="text-right">{solution.client_count}</TableCell>
                          <TableCell className="text-right">
                            ${parseFloat(solution.avg_pepm || 0).toFixed(2)}
                          </TableCell>
                          <TableCell className="text-right font-medium">
                            {formatCurrency(solution.total_revenue)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : (
                  <div className="text-center py-8 text-gray-500">No data available</div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Monthly Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle>Monthly Revenue - {selectedYear}</CardTitle>
            </CardHeader>
            <CardContent>
              {summary?.monthly?.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Month</TableHead>
                      <TableHead className="text-right">Clients</TableHead>
                      <TableHead className="text-right">Total Population</TableHead>
                      <TableHead className="text-right">RevRec</TableHead>
                      <TableHead className="text-right">Cash</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {summary.monthly.map((month) => {
                      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                      return (
                        <TableRow key={month.billing_month}>
                          <TableCell className="font-medium">
                            {monthNames[month.billing_month - 1]}
                          </TableCell>
                          <TableCell className="text-right">{month.client_count}</TableCell>
                          <TableCell className="text-right">
                            {parseInt(month.total_population || 0).toLocaleString()}
                          </TableCell>
                          <TableCell className="text-right">
                            {formatCurrency(month.total_revrec)}
                          </TableCell>
                          <TableCell className="text-right">
                            {formatCurrency(month.total_cash)}
                          </TableCell>
                        </TableRow>
                      )
                    })}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  No billing data for {selectedYear}. Add clients and billing data to see the summary.
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default VitalFinanceBilling
