import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Database,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  FileText,
  Columns,
  ChevronLeft,
  ChevronRight,
  Building2,
  Users
} from 'lucide-react'

const VitalAzureSQLDashboard = ({ user }) => {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [dashboardData, setDashboardData] = useState(null)
  const [caseData, setCaseData] = useState(null)
  const [pagination, setPagination] = useState({ offset: 0, limit: 25 })
  const [lastUpdated, setLastUpdated] = useState(null)
  const [activeTab, setActiveTab] = useState('overview') // 'overview' or 'data'

  const fetchDashboardData = async () => {
    setLoading(true)
    setError(null)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/vital/azure-sql/dashboard', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to fetch Azure SQL data')
      }
      
      const result = await response.json()
      if (result.success) {
        setDashboardData(result.data)
        setLastUpdated(new Date().toLocaleTimeString())
      } else {
        throw new Error(result.error || 'Unknown error')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const fetchCaseData = async (offset = 0) => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`/api/vital/azure-sql/data?limit=${pagination.limit}&offset=${offset}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch case data')
      }
      
      const result = await response.json()
      if (result.success) {
        setCaseData(result.data)
        setPagination(prev => ({ ...prev, ...result.pagination, offset }))
      }
    } catch (err) {
      console.error('Error fetching case data:', err)
    }
  }

  useEffect(() => {
    fetchDashboardData()
  }, [])

  useEffect(() => {
    if (activeTab === 'data' && !caseData) {
      fetchCaseData(0)
    }
  }, [activeTab])

  const formatNumber = (value) => {
    return new Intl.NumberFormat('en-US').format(value)
  }

  const StatCard = ({ title, value, icon: Icon, color, subtitle }) => (
    <Card className="shadow-lg hover:shadow-xl transition-shadow">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-gray-600">{title}</CardTitle>
        <div className={`p-2 rounded-lg bg-${color}-100`}>
          <Icon className={`h-5 w-5 text-${color}-600`} />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold text-gray-900">{value}</div>
        {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
      </CardContent>
    </Card>
  )

  if (loading) {
    return (
      <div className="flex flex-col justify-center items-center h-96">
        <LoadingSpinner size={50} />
        <p className="mt-4 text-gray-500">Loading Azure SQL data...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col justify-center items-center h-96">
        <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
        <p className="text-red-600 font-medium">Error loading Azure SQL data</p>
        <p className="text-gray-500 text-sm mt-2 max-w-md text-center">{error}</p>
        <Button onClick={fetchDashboardData} className="mt-4" variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Case Data Dashboard</h1>
          <p className="text-gray-500">VITAL WorkLife Case Data Summary (No PHI)</p>
        </div>
        <div className="flex items-center gap-4">
          {lastUpdated && (
            <span className="text-sm text-gray-500">Last updated: {lastUpdated}</span>
          )}
          <Button 
            onClick={() => {
              // Navigate to Customer 360
              const event = new CustomEvent('navigate', { detail: 'vital-customer-360' })
              window.dispatchEvent(event)
            }} 
            variant="default" 
            size="sm"
            className="bg-teal-600 hover:bg-teal-700"
          >
            <Building2 className="h-4 w-4 mr-2" />
            Customer 360
          </Button>
          <Button onClick={fetchDashboardData} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Connection Status */}
      <Card className="bg-green-50 border-green-200">
        <CardContent className="flex items-center gap-3 py-4">
          <CheckCircle className="h-5 w-5 text-green-600" />
          <span className="text-green-700 font-medium">Connected to Azure SQL</span>
          <Badge variant="outline" className="ml-2 bg-white">
            {dashboardData?.table_name}
          </Badge>
        </CardContent>
      </Card>

      {/* Tabs */}
      <div className="flex gap-2 border-b">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'overview'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Overview
        </button>
        <button
          onClick={() => setActiveTab('data')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'data'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Browse Data
        </button>
      </div>

      {activeTab === 'overview' && (
        <>
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <StatCard
              title="Total Records"
              value={formatNumber(dashboardData?.total_records || 0)}
              icon={FileText}
              color="blue"
              subtitle="Case data entries"
            />
            <StatCard
              title="Columns"
              value={dashboardData?.column_count || 0}
              icon={Columns}
              color="purple"
              subtitle="Data fields available"
            />
            <StatCard
              title="Table"
              value={dashboardData?.table_name?.replace('_', ' ') || 'N/A'}
              icon={Database}
              color="green"
              subtitle="Source table"
            />
          </div>

          {/* Column Schema */}
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle>Table Schema</CardTitle>
              <CardDescription>Available columns in {dashboardData?.table_name}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                {dashboardData?.columns?.map((col, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg text-sm"
                  >
                    <span className="font-medium text-gray-700">{col.name}</span>
                    <Badge variant="secondary" className="text-xs">
                      {col.type}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Sample Data Preview */}
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle>Sample Data Preview</CardTitle>
              <CardDescription>First 10 records from the table</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      {dashboardData?.columns?.slice(0, 6).map((col, index) => (
                        <TableHead key={index} className="whitespace-nowrap">
                          {col.name}
                        </TableHead>
                      ))}
                      {dashboardData?.columns?.length > 6 && (
                        <TableHead className="text-gray-400">
                          +{dashboardData.columns.length - 6} more
                        </TableHead>
                      )}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {dashboardData?.sample_data?.map((row, rowIndex) => (
                      <TableRow key={rowIndex}>
                        {dashboardData?.columns?.slice(0, 6).map((col, colIndex) => (
                          <TableCell key={colIndex} className="max-w-[200px] truncate">
                            {row[col.name] !== null && row[col.name] !== undefined
                              ? String(row[col.name])
                              : '-'}
                          </TableCell>
                        ))}
                        {dashboardData?.columns?.length > 6 && (
                          <TableCell className="text-gray-400">...</TableCell>
                        )}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {activeTab === 'data' && (
        <Card className="shadow-lg">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Case Data</CardTitle>
              <CardDescription>
                Showing {pagination.offset + 1} - {Math.min(pagination.offset + pagination.limit, pagination.total || 0)} of {formatNumber(pagination.total || 0)} records
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => fetchCaseData(Math.max(0, pagination.offset - pagination.limit))}
                disabled={pagination.offset === 0}
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => fetchCaseData(pagination.offset + pagination.limit)}
                disabled={!pagination.has_more}
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    {dashboardData?.columns?.map((col, index) => (
                      <TableHead key={index} className="whitespace-nowrap text-xs">
                        {col.name}
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {caseData?.map((row, rowIndex) => (
                    <TableRow key={rowIndex}>
                      {dashboardData?.columns?.map((col, colIndex) => (
                        <TableCell key={colIndex} className="max-w-[150px] truncate text-xs">
                          {row[col.name] !== null && row[col.name] !== undefined
                            ? String(row[col.name])
                            : '-'}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default VitalAzureSQLDashboard
