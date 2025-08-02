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
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer
} from 'recharts'
import { AlertCircle } from 'lucide-react'
import { apiUrl } from '@/lib/api'

const PartsReport = ({ user, onNavigate }) => {
  const [partsData, setPartsData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchPartsData()
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

      {/* Debug Information */}
      {partsData?.debug && (
        <Card className="border-orange-200 bg-orange-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-orange-600" />
              Debug: NationalParts Table Information
            </CardTitle>
            <CardDescription>
              Temporary debug information to identify correct column names
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableBody>
                <TableRow>
                  <TableCell className="font-medium">Table Exists:</TableCell>
                  <TableCell>
                    <Badge variant={partsData.debug.table_exists ? "success" : "destructive"}>
                      {partsData.debug.table_exists ? "Yes" : "No"}
                    </Badge>
                  </TableCell>
                </TableRow>
                {partsData.debug.table_exists && (
                  <>
                    <TableRow>
                      <TableCell className="font-medium">Total Columns:</TableCell>
                      <TableCell>{partsData.debug.total_columns}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium">Has OnHand Column:</TableCell>
                      <TableCell>
                        <Badge variant={partsData.debug.has_OnHand ? "success" : "destructive"}>
                          {partsData.debug.has_OnHand ? "Yes" : "No"}
                        </Badge>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium">Has QtyOnHand Column:</TableCell>
                      <TableCell>
                        <Badge variant={partsData.debug.has_QtyOnHand ? "success" : "destructive"}>
                          {partsData.debug.has_QtyOnHand ? "Yes" : "No"}
                        </Badge>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium">Inventory Related Columns:</TableCell>
                      <TableCell>
                        {partsData.debug.inventory_columns?.length > 0 ? (
                          <div className="flex flex-wrap gap-2">
                            {partsData.debug.inventory_columns.map((col) => (
                              <Badge key={col} variant="outline">{col}</Badge>
                            ))}
                          </div>
                        ) : (
                          <span className="text-muted-foreground">None found</span>
                        )}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium">Sample Columns:</TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-2">
                          {partsData.debug.sample_columns?.map((col) => (
                            <Badge key={col} variant="secondary">{col}</Badge>
                          ))}
                        </div>
                      </TableCell>
                    </TableRow>
                  </>
                )}
                {partsData.debug.error && (
                  <TableRow>
                    <TableCell className="font-medium">Error:</TableCell>
                    <TableCell className="text-red-600">{partsData.debug.error}</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
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