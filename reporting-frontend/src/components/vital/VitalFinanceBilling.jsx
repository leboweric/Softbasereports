import React, { useState, useEffect, useRef, useMemo } from 'react'
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
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
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
  const [tierProductPivotData, setTierProductPivotData] = useState(null)
  const [tierProductRevenueTiming, setTierProductRevenueTiming] = useState('revrec')
  const [newClient, setNewClient] = useState({
    billing_name: '',
    hubspot_company_name: '',
    industry: '',
    tier: '',
    solution_type: '',
    status: 'active'
  })

  // Column visibility state - all 44 Excel columns
  const [visibleColumns, setVisibleColumns] = useState({
    // Core columns (always visible by default)
    revenue_type: true,
    wpo_name: false,
    at_risk: false,
    billing_name: true,
    inception_date: false,
    renewal_date: true,
    contract_length: false,
    // Year months active
    year_2026: false,
    year_2027: false,
    year_2028: false,
    year_2029: false,
    year_2030: false,
    year_2031: false,
    session_product: false,
    billing_terms: true,
    // Monthly values
    jan: true, feb: true, mar: true, apr: true, may: true, jun: true,
    jul: true, aug: true, sep: true, oct: true, nov: true, dec: true,
    annual_total: true,
    population: true,
    // PEPM rates by year
    pepm_2025: false,
    pepm_2026: true,
    pepm_2027: false,
    pepm_2028: false,
    pepm_2029: false,
    pepm_2030: false,
    pepm_2031: false,
    contract_value_total: false,
    wpo_product: false,
    wpo_billing: false,
    wpo_account_number: false,
    industry: false,
    tier: true,
    applicable_law_state: false,
    nexus_state: false
  })

  // Sorting state
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' })

  // Column definitions for the table
  const allColumns = [
    { key: 'revenue_type', label: 'Type', group: 'core' },
    { key: 'wpo_name', label: 'WPO Name', group: 'wpo' },
    { key: 'at_risk', label: 'At Risk', group: 'core' },
    { key: 'billing_name', label: 'Company Name', group: 'core' },
    { key: 'inception_date', label: 'Inception Date', group: 'contract' },
    { key: 'renewal_date', label: 'Renewal', group: 'contract' },
    { key: 'contract_length', label: 'Contract Length', group: 'contract' },
    { key: 'year_2026', label: '2026', group: 'years' },
    { key: 'year_2027', label: '2027', group: 'years' },
    { key: 'year_2028', label: '2028', group: 'years' },
    { key: 'year_2029', label: '2029', group: 'years' },
    { key: 'year_2030', label: '2030', group: 'years' },
    { key: 'year_2031', label: '2031', group: 'years' },
    { key: 'session_product', label: 'Session Product', group: 'product' },
    { key: 'billing_terms', label: 'Billing Terms', group: 'billing' },
    { key: 'jan', label: 'Jan', group: 'monthly', bg: 'bg-blue-50' },
    { key: 'feb', label: 'Feb', group: 'monthly', bg: 'bg-blue-50' },
    { key: 'mar', label: 'Mar', group: 'monthly', bg: 'bg-blue-50' },
    { key: 'apr', label: 'Apr', group: 'monthly', bg: 'bg-green-50' },
    { key: 'may', label: 'May', group: 'monthly', bg: 'bg-green-50' },
    { key: 'jun', label: 'Jun', group: 'monthly', bg: 'bg-green-50' },
    { key: 'jul', label: 'Jul', group: 'monthly', bg: 'bg-yellow-50' },
    { key: 'aug', label: 'Aug', group: 'monthly', bg: 'bg-yellow-50' },
    { key: 'sep', label: 'Sep', group: 'monthly', bg: 'bg-yellow-50' },
    { key: 'oct', label: 'Oct', group: 'monthly', bg: 'bg-orange-50' },
    { key: 'nov', label: 'Nov', group: 'monthly', bg: 'bg-orange-50' },
    { key: 'dec', label: 'Dec', group: 'monthly', bg: 'bg-orange-50' },
    { key: 'annual_total', label: 'Total', group: 'summary' },
    { key: 'population', label: 'Current Pop', group: 'billing' },
    { key: 'pepm_2025', label: '2025 PEPM', group: 'pepm' },
    { key: 'pepm_2026', label: '2026 PEPM', group: 'pepm' },
    { key: 'pepm_2027', label: '2027 PEPM', group: 'pepm' },
    { key: 'pepm_2028', label: '2028 PEPM', group: 'pepm' },
    { key: 'pepm_2029', label: '2029 PEPM', group: 'pepm' },
    { key: 'pepm_2030', label: '2030 PEPM', group: 'pepm' },
    { key: 'pepm_2031', label: '2031 PEPM', group: 'pepm' },
    { key: 'contract_value_total', label: 'Contract Value', group: 'contract' },
    { key: 'wpo_product', label: 'WPO Product', group: 'wpo' },
    { key: 'wpo_billing', label: 'WPO Billing', group: 'wpo' },
    { key: 'wpo_account_number', label: 'WPO Account', group: 'wpo' },
    { key: 'industry', label: 'Industry', group: 'classification' },
    { key: 'tier', label: 'Tier', group: 'classification' },
    { key: 'applicable_law_state', label: 'App Law State', group: 'location' },
    { key: 'nexus_state', label: 'Nexus State', group: 'location' }
  ]

  useEffect(() => {
    fetchData()
  }, [selectedYear, revenueType])

  useEffect(() => {
    if (activeTab === 'wpo_pivot') {
      fetchWpoPivot(wpoSessionProduct, wpoRevenueTiming)
    }
    if (activeTab === 'tier_product') {
      fetchTierProductPivot(tierProductRevenueTiming)
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

  const fetchTierProductPivot = async (revenueTiming = 'revrec') => {
    try {
      const token = localStorage.getItem('token')
      const headers = { 'Authorization': `Bearer ${token}` }
      const params = new URLSearchParams({
        year: selectedYear,
        revenue_timing: revenueTiming
      })
      const res = await fetch(apiUrl(`/api/vital/finance/pivot/tier-product?${params}`), { headers })
      if (res.ok) {
        const data = await res.json()
        setTierProductPivotData(data)
      }
    } catch (error) {
      console.error('Error fetching Tier & Product pivot:', error)
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

  // Sort function
  const handleSort = (columnKey) => {
    let direction = 'asc'
    if (sortConfig.key === columnKey && sortConfig.direction === 'asc') {
      direction = 'desc'
    }
    setSortConfig({ key: columnKey, direction })
  }

  // Get sort icon for column header
  const getSortIcon = (columnKey) => {
    if (sortConfig.key !== columnKey) {
      return <ArrowUpDown className="h-3 w-3 ml-1 opacity-50" />
    }
    return sortConfig.direction === 'asc' 
      ? <ArrowUp className="h-3 w-3 ml-1" />
      : <ArrowDown className="h-3 w-3 ml-1" />
  }

  // Filter and sort spreadsheet rows
  const filteredSpreadsheetRows = React.useMemo(() => {
    let rows = spreadsheetData?.rows?.filter(row =>
      row.billing_name?.toLowerCase().includes(searchTerm.toLowerCase())
    ) || []
    
    // Apply sorting if a sort column is selected
    if (sortConfig.key) {
      rows = [...rows].sort((a, b) => {
        let aVal = a[sortConfig.key]
        let bVal = b[sortConfig.key]
        
        // Handle null/undefined values
        if (aVal == null) aVal = ''
        if (bVal == null) bVal = ''
        
        // Numeric columns
        const numericCols = ['population', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec', 'annual_total', 'contract_value_total', 'wpo_billing', 'contract_length', 'year_2026', 'year_2027', 'year_2028', 'year_2029', 'year_2030', 'year_2031']
        const pepmCols = ['pepm_2025', 'pepm_2026', 'pepm_2027', 'pepm_2028', 'pepm_2029', 'pepm_2030', 'pepm_2031']
        
        if (numericCols.includes(sortConfig.key) || pepmCols.includes(sortConfig.key)) {
          aVal = parseFloat(aVal) || 0
          bVal = parseFloat(bVal) || 0
        } else if (typeof aVal === 'string') {
          aVal = aVal.toLowerCase()
          bVal = (bVal || '').toLowerCase()
        }
        
        if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1
        if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1
        return 0
      })
    }
    
    return rows
  }, [spreadsheetData?.rows, searchTerm, sortConfig])

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

  // Helper to render cell value based on column type
  const renderCellValue = (row, colKey) => {
    const value = row[colKey]
    
    // Special rendering for specific columns
    switch(colKey) {
      case 'revenue_type':
        return <Badge variant={value === 'CASH' ? 'default' : 'secondary'}>{value}</Badge>
      case 'billing_terms':
        return getBillingTermsBadge(value)
      case 'at_risk':
        return value ? <Badge variant="destructive">{value}</Badge> : '-'
      case 'population':
        return value?.toLocaleString() || '-'
      case 'renewal_date':
      case 'inception_date':
        return value ? new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '-'
      case 'contract_length':
        return value ? `${value} yr` : '-'
      case 'year_2026':
      case 'year_2027':
      case 'year_2028':
      case 'year_2029':
      case 'year_2030':
      case 'year_2031':
        return value || '-'
      case 'pepm_2025':
      case 'pepm_2026':
      case 'pepm_2027':
      case 'pepm_2028':
      case 'pepm_2029':
      case 'pepm_2030':
      case 'pepm_2031':
        return value ? `$${value.toFixed(2)}` : '-'
      case 'jan':
      case 'feb':
      case 'mar':
      case 'apr':
      case 'may':
      case 'jun':
      case 'jul':
      case 'aug':
      case 'sep':
      case 'oct':
      case 'nov':
      case 'dec':
      case 'annual_total':
      case 'contract_value_total':
        return formatCurrency(value)
      case 'wpo_billing':
        return value ? `$${value.toFixed(2)}` : '-'
      default:
        return value || '-'
    }
  }

  // Get visible columns for rendering
  const getVisibleColumns = () => {
    return allColumns.filter(col => visibleColumns[col.key])
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
          <TabsTrigger value="tier_product">Tier & Product</TabsTrigger>
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
                  {/* Column Selector */}
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button variant="outline">
                        <Columns className="h-4 w-4 mr-2" />
                        Columns
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                      <DialogHeader>
                        <DialogTitle>Show/Hide Columns</DialogTitle>
                        <DialogDescription>
                          Select which columns to display in the billing table
                        </DialogDescription>
                      </DialogHeader>
                      <div className="grid grid-cols-3 gap-4 py-4">
                        {/* Group columns by category */}
                        {['core', 'contract', 'years', 'product', 'billing', 'monthly', 'summary', 'pepm', 'wpo', 'classification', 'location'].map(group => (
                          <div key={group} className="space-y-2">
                            <h4 className="font-semibold capitalize text-sm text-gray-500">{group}</h4>
                            {allColumns.filter(col => col.group === group).map(col => (
                              <div key={col.key} className="flex items-center space-x-2">
                                <Switch
                                  id={col.key}
                                  checked={visibleColumns[col.key]}
                                  onCheckedChange={(checked) => setVisibleColumns(prev => ({...prev, [col.key]: checked}))}
                                />
                                <Label htmlFor={col.key} className="text-sm">{col.label}</Label>
                              </div>
                            ))}
                          </div>
                        ))}
                      </div>
                      <DialogFooter>
                        <Button variant="outline" onClick={() => {
                          // Show all columns
                          const all = {};
                          allColumns.forEach(col => all[col.key] = true);
                          setVisibleColumns(all);
                        }}>Show All</Button>
                        <Button variant="outline" onClick={() => {
                          // Reset to default
                          setVisibleColumns({
                            revenue_type: true, billing_name: true, tier: true, billing_terms: true,
                            population: true, renewal_date: true, pepm_2026: true,
                            jan: true, feb: true, mar: true, apr: true, may: true, jun: true,
                            jul: true, aug: true, sep: true, oct: true, nov: true, dec: true,
                            annual_total: true
                          });
                        }}>Reset Default</Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
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
                      {getVisibleColumns().map((col, idx) => {
                        const isSticky = col.key === 'billing_name' || (col.key === 'revenue_type' && revenueType === 'dual')
                        const isNumeric = ['population', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec', 'annual_total', 'contract_value_total', 'wpo_billing'].includes(col.key) || col.key.startsWith('pepm_') || col.key.startsWith('year_')
                        return (
                          <TableHead 
                            key={col.key}
                            className={`min-w-[90px] ${col.bg || ''} ${isNumeric ? 'text-right' : ''} ${isSticky ? 'sticky left-0 bg-gray-50 z-20' : ''} ${col.key === 'annual_total' ? 'bg-gray-100 font-bold' : ''} cursor-pointer hover:bg-gray-100 select-none`}
                            onClick={() => handleSort(col.key)}
                          >
                            <div className={`flex items-center ${isNumeric ? 'justify-end' : ''}`}>
                              {col.label}
                              {getSortIcon(col.key)}
                            </div>
                          </TableHead>
                        )
                      })}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredSpreadsheetRows.map((row, idx) => (
                      <TableRow 
                        key={`${row.id}-${row.revenue_type}-${idx}`} 
                        className={row.revenue_type === 'CASH' ? 'bg-blue-50/30' : ''}
                      >
                        {getVisibleColumns().map((col) => {
                          const isSticky = col.key === 'billing_name' || (col.key === 'revenue_type' && revenueType === 'dual')
                          const isNumeric = ['population', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec', 'annual_total', 'contract_value_total', 'wpo_billing'].includes(col.key) || col.key.startsWith('pepm_') || col.key.startsWith('year_')
                          return (
                            <TableCell 
                              key={col.key}
                              className={`${col.bg ? col.bg + '/50' : ''} ${isNumeric ? 'text-right' : ''} ${isSticky ? 'sticky left-0 bg-white z-10 font-medium' : ''} ${col.key === 'annual_total' ? 'bg-gray-100 font-bold' : ''}`}
                            >
                              {renderCellValue(row, col.key)}
                            </TableCell>
                          )
                        })}
                      </TableRow>
                    ))}
                    {/* Totals Row(s) - Dynamically calculated from filtered data */}
                    {revenueType === 'dual' ? (
                      // In dual/Both mode, show separate CASH and REVREC total rows
                      <>
                        {/* CASH Total Row */}
                        <TableRow className="bg-blue-100 font-bold">
                          {getVisibleColumns().map((col) => {
                            const cashRows = filteredSpreadsheetRows.filter(r => r.revenue_type === 'CASH')
                            const isNumeric = ['population', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec', 'annual_total', 'contract_value_total'].includes(col.key)
                            if (col.key === 'revenue_type') return <TableCell key={col.key} className="sticky left-0 bg-blue-100 z-10"><Badge>CASH</Badge></TableCell>
                            if (col.key === 'billing_name') return <TableCell key={col.key} className="sticky left-0 bg-blue-100 z-10">TOTAL</TableCell>
                            if (col.key === 'population') return <TableCell key={col.key} className="text-right">{cashRows.reduce((sum, r) => sum + (r.population || 0), 0).toLocaleString()}</TableCell>
                            if (['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec', 'annual_total'].includes(col.key)) {
                              return <TableCell key={col.key} className={`text-right ${col.key === 'annual_total' ? 'bg-blue-200' : ''}`}>{formatCurrency(cashRows.reduce((sum, r) => sum + (r[col.key] || 0), 0))}</TableCell>
                            }
                            return <TableCell key={col.key}></TableCell>
                          })}
                        </TableRow>
                        {/* REVREC Total Row */}
                        <TableRow className="bg-gray-200 font-bold sticky bottom-0">
                          {getVisibleColumns().map((col) => {
                            const revrecRows = filteredSpreadsheetRows.filter(r => r.revenue_type === 'REVREC')
                            if (col.key === 'revenue_type') return <TableCell key={col.key} className="sticky left-0 bg-gray-200 z-10"><Badge variant="secondary">REVREC</Badge></TableCell>
                            if (col.key === 'billing_name') return <TableCell key={col.key} className="sticky left-0 bg-gray-200 z-10">TOTAL</TableCell>
                            if (col.key === 'population') return <TableCell key={col.key} className="text-right">{revrecRows.reduce((sum, r) => sum + (r.population || 0), 0).toLocaleString()}</TableCell>
                            if (['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec', 'annual_total'].includes(col.key)) {
                              return <TableCell key={col.key} className={`text-right ${col.key === 'annual_total' ? 'bg-gray-300' : ''}`}>{formatCurrency(revrecRows.reduce((sum, r) => sum + (r[col.key] || 0), 0))}</TableCell>
                            }
                            return <TableCell key={col.key}></TableCell>
                          })}
                        </TableRow>
                      </>
                    ) : (
                      // In single mode (Cash or RevRec), show one total row
                      <TableRow className="bg-gray-200 font-bold sticky bottom-0">
                        {getVisibleColumns().map((col) => {
                          if (col.key === 'billing_name') return <TableCell key={col.key} className="sticky left-0 bg-gray-200 z-10">TOTAL</TableCell>
                          if (col.key === 'population') return <TableCell key={col.key} className="text-right">{filteredSpreadsheetRows.reduce((sum, r) => sum + (r.population || 0), 0).toLocaleString()}</TableCell>
                          if (['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec', 'annual_total'].includes(col.key)) {
                            return <TableCell key={col.key} className={`text-right ${col.key === 'annual_total' ? 'bg-gray-300' : ''}`}>{formatCurrency(filteredSpreadsheetRows.reduce((sum, r) => sum + (r[col.key] || 0), 0))}</TableCell>
                          }
                          return <TableCell key={col.key}></TableCell>
                        })}
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
          {/* Revenue by Session Product Summary */}
          {wpoPivotData?.revenue_by_product && wpoPivotData.revenue_by_product.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Summary Cards */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg">Revenue by Session Product</CardTitle>
                  <CardDescription>Breakdown of {wpoRevenueTiming === 'cash' ? 'Cash' : 'RevRec'} revenue</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {wpoPivotData.revenue_by_product.map((item, idx) => {
                      const colors = ['bg-blue-500', 'bg-green-500', 'bg-yellow-500', 'bg-purple-500', 'bg-pink-500', 'bg-indigo-500', 'bg-orange-500', 'bg-teal-500', 'bg-red-500']
                      const color = colors[idx % colors.length]
                      return (
                        <div key={item.session_product} className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className={`w-3 h-3 rounded-full ${color}`}></div>
                            <div>
                              <span className="font-medium">{item.session_product}</span>
                              <span className="text-gray-500 text-sm ml-2">({item.client_count} clients)</span>
                            </div>
                          </div>
                          <div className="text-right">
                            <span className="font-semibold">{formatCurrency(item.revenue)}</span>
                            <span className="text-gray-500 text-sm ml-2">({item.percentage}%)</span>
                          </div>
                        </div>
                      )
                    })}
                    <div className="border-t pt-3 mt-3 flex items-center justify-between font-bold">
                      <span>Total</span>
                      <span>{formatCurrency(wpoPivotData.grand_total_revenue)}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              {/* Pie Chart */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg">Revenue Distribution</CardTitle>
                  <CardDescription>Visual breakdown by product type</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-center">
                    <div className="relative w-64 h-64">
                      <svg viewBox="0 0 100 100" className="w-full h-full transform -rotate-90">
                        {(() => {
                          const colors = ['#3B82F6', '#22C55E', '#EAB308', '#A855F7', '#EC4899', '#6366F1', '#F97316', '#14B8A6', '#EF4444']
                          let cumulativePercent = 0
                          return wpoPivotData.revenue_by_product.map((item, idx) => {
                            const percent = item.percentage
                            const startAngle = cumulativePercent * 3.6 // 360 / 100
                            cumulativePercent += percent
                            const endAngle = cumulativePercent * 3.6
                            
                            // Calculate arc path
                            const startX = 50 + 40 * Math.cos((startAngle - 90) * Math.PI / 180)
                            const startY = 50 + 40 * Math.sin((startAngle - 90) * Math.PI / 180)
                            const endX = 50 + 40 * Math.cos((endAngle - 90) * Math.PI / 180)
                            const endY = 50 + 40 * Math.sin((endAngle - 90) * Math.PI / 180)
                            const largeArc = percent > 50 ? 1 : 0
                            
                            return (
                              <path
                                key={item.session_product}
                                d={`M 50 50 L ${startX} ${startY} A 40 40 0 ${largeArc} 1 ${endX} ${endY} Z`}
                                fill={colors[idx % colors.length]}
                                stroke="white"
                                strokeWidth="0.5"
                              />
                            )
                          })
                        })()}
                        {/* Center circle for donut effect */}
                        <circle cx="50" cy="50" r="25" fill="white" />
                      </svg>
                      {/* Center text */}
                      <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <span className="text-2xl font-bold">{wpoPivotData.revenue_by_product.length}</span>
                        <span className="text-sm text-gray-500">Products</span>
                      </div>
                    </div>
                  </div>
                  {/* Legend */}
                  <div className="flex flex-wrap justify-center gap-3 mt-4">
                    {wpoPivotData.revenue_by_product.slice(0, 6).map((item, idx) => {
                      const colors = ['bg-blue-500', 'bg-green-500', 'bg-yellow-500', 'bg-purple-500', 'bg-pink-500', 'bg-indigo-500']
                      return (
                        <div key={item.session_product} className="flex items-center gap-1 text-sm">
                          <div className={`w-2 h-2 rounded-full ${colors[idx % colors.length]}`}></div>
                          <span>{item.session_product}</span>
                        </div>
                      )
                    })}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
          
          {/* Detailed Table */}
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

        {/* Tier & Product Pivot Tab */}
        <TabsContent value="tier_product" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Pivot by Tier & Product - {selectedYear}</CardTitle>
                  <CardDescription>
                    Revenue analysis by client tier and session product
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex rounded-md overflow-hidden border">
                    <Button
                      variant={tierProductRevenueTiming === 'cash' ? 'default' : 'ghost'}
                      size="sm"
                      onClick={() => {
                        setTierProductRevenueTiming('cash')
                        fetchTierProductPivot('cash')
                      }}
                    >
                      Cash
                    </Button>
                    <Button
                      variant={tierProductRevenueTiming === 'revrec' ? 'default' : 'ghost'}
                      size="sm"
                      onClick={() => {
                        setTierProductRevenueTiming('revrec')
                        fetchTierProductPivot('revrec')
                      }}
                    >
                      RevRec
                    </Button>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {!tierProductPivotData ? (
                <div className="text-center py-8 text-gray-500">Loading pivot data...</div>
              ) : (
                <div className="space-y-8">
                  {/* Count of Companies Pivot */}
                  <div>
                    <h3 className="text-lg font-semibold mb-3">Count of Companies</h3>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm border-collapse">
                        <thead>
                          <tr className="bg-gray-100">
                            <th className="border px-3 py-2 text-left font-semibold">Tier</th>
                            {tierProductPivotData.products?.map(product => (
                              <th key={product} className="border px-3 py-2 text-right font-semibold">{product}</th>
                            ))}
                            <th className="border px-3 py-2 text-right font-semibold bg-gray-200">Grand Total</th>
                          </tr>
                        </thead>
                        <tbody>
                          {tierProductPivotData.count_pivot?.map((row, idx) => (
                            <tr key={idx} className={row.tier === 'Grand Total' ? 'bg-gray-200 font-semibold' : 'hover:bg-gray-50'}>
                              <td className="border px-3 py-2 font-medium">{row.tier}</td>
                              {tierProductPivotData.products?.map(product => (
                                <td key={product} className="border px-3 py-2 text-right">
                                  {row[product] || '-'}
                                </td>
                              ))}
                              <td className="border px-3 py-2 text-right bg-gray-100 font-semibold">{row['Grand Total']}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Sum of Population Pivot */}
                  <div>
                    <h3 className="text-lg font-semibold mb-3">Sum of Population</h3>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm border-collapse">
                        <thead>
                          <tr className="bg-gray-100">
                            <th className="border px-3 py-2 text-left font-semibold">Tier</th>
                            {tierProductPivotData.products?.map(product => (
                              <th key={product} className="border px-3 py-2 text-right font-semibold">{product}</th>
                            ))}
                            <th className="border px-3 py-2 text-right font-semibold bg-gray-200">Grand Total</th>
                          </tr>
                        </thead>
                        <tbody>
                          {tierProductPivotData.population_pivot?.map((row, idx) => (
                            <tr key={idx} className={row.tier === 'Grand Total' ? 'bg-gray-200 font-semibold' : 'hover:bg-gray-50'}>
                              <td className="border px-3 py-2 font-medium">{row.tier}</td>
                              {tierProductPivotData.products?.map(product => (
                                <td key={product} className="border px-3 py-2 text-right">
                                  {row[product]?.toLocaleString() || '-'}
                                </td>
                              ))}
                              <td className="border px-3 py-2 text-right bg-gray-100 font-semibold">{row['Grand Total']?.toLocaleString()}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Sum of Revenue Pivot */}
                  <div>
                    <h3 className="text-lg font-semibold mb-3">Sum of Annual Revenue ({tierProductRevenueTiming === 'cash' ? 'Cash' : 'RevRec'})</h3>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm border-collapse">
                        <thead>
                          <tr className="bg-gray-100">
                            <th className="border px-3 py-2 text-left font-semibold">Tier</th>
                            {tierProductPivotData.products?.map(product => (
                              <th key={product} className="border px-3 py-2 text-right font-semibold">{product}</th>
                            ))}
                            <th className="border px-3 py-2 text-right font-semibold bg-gray-200">Grand Total</th>
                          </tr>
                        </thead>
                        <tbody>
                          {tierProductPivotData.revenue_pivot?.map((row, idx) => (
                            <tr key={idx} className={row.tier === 'Grand Total' ? 'bg-gray-200 font-semibold' : 'hover:bg-gray-50'}>
                              <td className="border px-3 py-2 font-medium">{row.tier}</td>
                              {tierProductPivotData.products?.map(product => (
                                <td key={product} className="border px-3 py-2 text-right">
                                  {row[product] ? `$${row[product].toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0})}` : '-'}
                                </td>
                              ))}
                              <td className="border px-3 py-2 text-right bg-gray-100 font-semibold">
                                ${row['Grand Total']?.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0})}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Average PEPM Pivot */}
                  <div>
                    <h3 className="text-lg font-semibold mb-3">Average {selectedYear} PEPM</h3>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm border-collapse">
                        <thead>
                          <tr className="bg-gray-100">
                            <th className="border px-3 py-2 text-left font-semibold">Tier</th>
                            {tierProductPivotData.products?.map(product => (
                              <th key={product} className="border px-3 py-2 text-right font-semibold">{product}</th>
                            ))}
                            <th className="border px-3 py-2 text-right font-semibold bg-gray-200">Grand Total</th>
                          </tr>
                        </thead>
                        <tbody>
                          {tierProductPivotData.pepm_pivot?.map((row, idx) => (
                            <tr key={idx} className={row.tier === 'Grand Total' ? 'bg-gray-200 font-semibold' : 'hover:bg-gray-50'}>
                              <td className="border px-3 py-2 font-medium">{row.tier}</td>
                              {tierProductPivotData.products?.map(product => (
                                <td key={product} className="border px-3 py-2 text-right">
                                  {row[product] ? `$${row[product].toFixed(2)}` : '-'}
                                </td>
                              ))}
                              <td className="border px-3 py-2 text-right bg-gray-100 font-semibold">
                                ${row['Grand Total']?.toFixed(2)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Grand Totals Summary */}
                  <div className="grid grid-cols-4 gap-4 mt-6">
                    <Card>
                      <CardContent className="pt-4">
                        <div className="text-sm text-gray-500">Total Clients</div>
                        <div className="text-2xl font-bold">{tierProductPivotData.grand_totals?.count?.toLocaleString()}</div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-4">
                        <div className="text-sm text-gray-500">Total Population</div>
                        <div className="text-2xl font-bold">{tierProductPivotData.grand_totals?.population?.toLocaleString()}</div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-4">
                        <div className="text-sm text-gray-500">Total Revenue</div>
                        <div className="text-2xl font-bold">${tierProductPivotData.grand_totals?.revenue?.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0})}</div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-4">
                        <div className="text-sm text-gray-500">Avg PEPM</div>
                        <div className="text-2xl font-bold">${tierProductPivotData.grand_totals?.avg_pepm?.toFixed(2)}</div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Renewals Tab */}
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
