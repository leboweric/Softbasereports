import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Download, 
  Filter, 
  Search, 
  Plus,
  FileText,
  BarChart3,
  Calendar
} from 'lucide-react'

const Reports = () => {
  const [reportData, setReportData] = useState([])
  const [templates, setTemplates] = useState([])
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState({
    query_type: 'sales',
    start_date: '',
    end_date: '',
    search: ''
  })

  useEffect(() => {
    fetchTemplates()
    fetchReportData()
  }, [])

  const fetchTemplates = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/reports/templates', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setTemplates(data)
      }
    } catch (error) {
      console.error('Failed to fetch templates:', error)
    }
  }

  const fetchReportData = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/reports/data', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query_type: filters.query_type,
          filters: {
            search: filters.search
          },
          date_range: {
            start_date: filters.start_date,
            end_date: filters.end_date
          }
        }),
      })

      if (response.ok) {
        const data = await response.json()
        setReportData(data.data || [])
      }
    } catch (error) {
      console.error('Failed to fetch report data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  const handleExport = async (format) => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`/api/reports/export/${format}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query_type: filters.query_type,
          filters: {
            search: filters.search
          },
          date_range: {
            start_date: filters.start_date,
            end_date: filters.end_date
          }
        }),
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.style.display = 'none'
        a.href = url
        a.download = `report.${format}`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
      }
    } catch (error) {
      console.error('Failed to export:', error)
    }
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount)
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString()
  }

  const renderTableHeaders = () => {
    switch (filters.query_type) {
      case 'sales':
        return (
          <TableRow>
            <TableHead>Date</TableHead>
            <TableHead>Customer</TableHead>
            <TableHead>Product</TableHead>
            <TableHead>Quantity</TableHead>
            <TableHead>Unit Price</TableHead>
            <TableHead>Total</TableHead>
            <TableHead>Salesperson</TableHead>
          </TableRow>
        )
      case 'inventory':
        return (
          <TableRow>
            <TableHead>Model</TableHead>
            <TableHead>Serial Number</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Location</TableHead>
            <TableHead>Cost</TableHead>
            <TableHead>Retail Price</TableHead>
          </TableRow>
        )
      case 'customers':
        return (
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Contact Person</TableHead>
            <TableHead>Email</TableHead>
            <TableHead>Phone</TableHead>
            <TableHead>Total Purchases</TableHead>
            <TableHead>Last Purchase</TableHead>
          </TableRow>
        )
      default:
        return null
    }
  }

  const renderTableRow = (item, index) => {
    switch (filters.query_type) {
      case 'sales':
        return (
          <TableRow key={index}>
            <TableCell>{formatDate(item.date)}</TableCell>
            <TableCell>{item.customer_name}</TableCell>
            <TableCell>{item.product}</TableCell>
            <TableCell>{item.quantity}</TableCell>
            <TableCell>{formatCurrency(item.unit_price)}</TableCell>
            <TableCell className="font-medium">{formatCurrency(item.total_amount)}</TableCell>
            <TableCell>{item.salesperson}</TableCell>
          </TableRow>
        )
      case 'inventory':
        return (
          <TableRow key={index}>
            <TableCell>{item.model}</TableCell>
            <TableCell>{item.serial_number}</TableCell>
            <TableCell>
              <Badge variant={item.status === 'Available' ? 'default' : 'secondary'}>
                {item.status}
              </Badge>
            </TableCell>
            <TableCell>{item.location}</TableCell>
            <TableCell>{formatCurrency(item.cost)}</TableCell>
            <TableCell>{formatCurrency(item.retail_price)}</TableCell>
          </TableRow>
        )
      case 'customers':
        return (
          <TableRow key={index}>
            <TableCell className="font-medium">{item.name}</TableCell>
            <TableCell>{item.contact_person}</TableCell>
            <TableCell>{item.email}</TableCell>
            <TableCell>{item.phone}</TableCell>
            <TableCell>{formatCurrency(item.total_purchases)}</TableCell>
            <TableCell>{formatDate(item.last_purchase_date)}</TableCell>
          </TableRow>
        )
      default:
        return null
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Reports</h1>
          <p className="text-muted-foreground">
            Generate and manage your business reports
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <Plus className="mr-2 h-4 w-4" />
            New Template
          </Button>
        </div>
      </div>

      <Tabs defaultValue="generate" className="space-y-4">
        <TabsList>
          <TabsTrigger value="generate">Generate Report</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
        </TabsList>

        <TabsContent value="generate" className="space-y-4">
          {/* Filters */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Filter className="mr-2 h-5 w-5" />
                Filters
              </CardTitle>
              <CardDescription>
                Configure your report parameters
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <div>
                  <Label htmlFor="query_type">Report Type</Label>
                  <Select value={filters.query_type} onValueChange={(value) => handleFilterChange('query_type', value)}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select report type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="sales">Sales Report</SelectItem>
                      <SelectItem value="inventory">Inventory Report</SelectItem>
                      <SelectItem value="customers">Customer Report</SelectItem>
                      <SelectItem value="service">Service Report</SelectItem>
                      <SelectItem value="financial">Financial Summary</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="start_date">Start Date</Label>
                  <Input
                    id="start_date"
                    type="date"
                    value={filters.start_date}
                    onChange={(e) => handleFilterChange('start_date', e.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="end_date">End Date</Label>
                  <Input
                    id="end_date"
                    type="date"
                    value={filters.end_date}
                    onChange={(e) => handleFilterChange('end_date', e.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="search">Search</Label>
                  <div className="relative">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="search"
                      placeholder="Search..."
                      className="pl-8"
                      value={filters.search}
                      onChange={(e) => handleFilterChange('search', e.target.value)}
                    />
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-2 mt-4">
                <Button onClick={fetchReportData} disabled={loading}>
                  {loading ? 'Loading...' : 'Generate Report'}
                </Button>
                <Button variant="outline" onClick={() => handleExport('csv')}>
                  <Download className="mr-2 h-4 w-4" />
                  CSV
                </Button>
                <Button variant="outline" onClick={() => handleExport('excel')}>
                  <Download className="mr-2 h-4 w-4" />
                  Excel
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Results */}
          <Card>
            <CardHeader>
              <CardTitle>Report Results</CardTitle>
              <CardDescription>
                {reportData.length} records found
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center h-32">
                  <div className="text-muted-foreground">Loading...</div>
                </div>
              ) : reportData.length > 0 ? (
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      {renderTableHeaders()}
                    </TableHeader>
                    <TableBody>
                      {reportData.map((item, index) => renderTableRow(item, index))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="flex items-center justify-center h-32">
                  <div className="text-muted-foreground">No data found</div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="templates" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {templates.map((template) => (
              <Card key={template.id}>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <FileText className="mr-2 h-5 w-5" />
                    {template.name}
                  </CardTitle>
                  <CardDescription>
                    {template.description}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <Badge variant="outline">
                      {new Date(template.created_at).toLocaleDateString()}
                    </Badge>
                    <Button size="sm" variant="outline">
                      Use Template
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
            {templates.length === 0 && (
              <Card className="col-span-full">
                <CardContent className="flex items-center justify-center h-32">
                  <div className="text-muted-foreground">No templates found</div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default Reports

