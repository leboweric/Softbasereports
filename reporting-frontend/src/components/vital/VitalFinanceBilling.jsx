import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
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
  ArrowDownRight
} from 'lucide-react'

const VitalFinanceBilling = ({ user, organization }) => {
  const [clients, setClients] = useState([])
  const [summary, setSummary] = useState(null)
  const [renewals, setRenewals] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear())
  const [showAddClient, setShowAddClient] = useState(false)
  const [newClient, setNewClient] = useState({
    billing_name: '',
    hubspot_company_name: '',
    industry: '',
    tier: '',
    solution_type: '',
    status: 'active'
  })

  useEffect(() => {
    fetchData()
  }, [selectedYear])

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

  const filteredClients = clients.filter(client =>
    client.billing_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    client.hubspot_company_name?.toLowerCase().includes(searchTerm.toLowerCase())
  )

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
        <div className="flex gap-2">
          <Select value={selectedYear.toString()} onValueChange={(v) => setSelectedYear(parseInt(v))}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="2024">2024</SelectItem>
              <SelectItem value="2025">2025</SelectItem>
              <SelectItem value="2026">2026</SelectItem>
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
            <CardTitle className="text-sm font-medium">Book of Business</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(summary?.book_value)}</div>
            <p className="text-xs text-muted-foreground">Annual value</p>
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
      <Tabs defaultValue="clients" className="space-y-4">
        <TabsList>
          <TabsTrigger value="clients">Clients</TabsTrigger>
          <TabsTrigger value="renewals">Renewals</TabsTrigger>
          <TabsTrigger value="summary">Summary</TabsTrigger>
        </TabsList>

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
