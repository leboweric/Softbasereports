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
              Debug: Parts Tables Information
            </CardTitle>
            <CardDescription>
              Temporary debug information to identify correct tables and column names
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* NationalParts Info */}
            <div>
              <h4 className="font-semibold mb-2">NationalParts Table:</h4>
              <Table>
                <TableBody>
                  {partsData.debug.nationalparts && (
                    <>
                      <TableRow>
                        <TableCell className="font-medium">Exists:</TableCell>
                        <TableCell>
                          <Badge variant={partsData.debug.nationalparts.table_exists ? "success" : "destructive"}>
                            {partsData.debug.nationalparts.table_exists ? "Yes" : "No"}
                          </Badge>
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell className="font-medium">Row Count:</TableCell>
                        <TableCell>{partsData.debug.nationalparts.row_count || "0"}</TableCell>
                      </TableRow>
                      {partsData.debug.nationalparts.error && (
                        <TableRow>
                          <TableCell className="font-medium">Error:</TableCell>
                          <TableCell className="text-red-600">{partsData.debug.nationalparts.error}</TableCell>
                        </TableRow>
                      )}
                    </>
                  )}
                </TableBody>
              </Table>
            </div>

            {/* WOParts Info */}
            <div>
              <h4 className="font-semibold mb-2">WOParts Table:</h4>
              <Table>
                <TableBody>
                  {partsData.debug.woparts && (
                    <>
                      <TableRow>
                        <TableCell className="font-medium">Exists:</TableCell>
                        <TableCell>
                          <Badge variant={partsData.debug.woparts.table_exists ? "success" : "destructive"}>
                            {partsData.debug.woparts.table_exists ? "Yes" : "No"}
                          </Badge>
                        </TableCell>
                      </TableRow>
                      {partsData.debug.woparts.columns && (
                        <TableRow>
                          <TableCell className="font-medium">Columns:</TableCell>
                          <TableCell>
                            <div className="flex flex-wrap gap-2">
                              {partsData.debug.woparts.columns.map((col) => (
                                <Badge key={col} variant="secondary">{col}</Badge>
                              ))}
                            </div>
                          </TableCell>
                        </TableRow>
                      )}
                    </>
                  )}
                </TableBody>
              </Table>
            </div>

            {/* Parts Table Info */}
            {partsData.debug.parts && (
              <div>
                <h4 className="font-semibold mb-2">Parts Table (Main Inventory):</h4>
                <Table>
                  <TableBody>
                    <TableRow>
                      <TableCell className="font-medium">Exists:</TableCell>
                      <TableCell>
                        <Badge variant={partsData.debug.parts.table_exists ? "success" : "destructive"}>
                          {partsData.debug.parts.table_exists ? "Yes" : "No"}
                        </Badge>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium">Row Count:</TableCell>
                      <TableCell>{partsData.debug.parts.row_count || "0"}</TableCell>
                    </TableRow>
                    {partsData.debug.parts.inventory_columns && (
                      <TableRow>
                        <TableCell className="font-medium">Inventory Columns:</TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-2">
                            {partsData.debug.parts.inventory_columns.map((col) => (
                              <Badge key={col} variant="success">{col}</Badge>
                            ))}
                          </div>
                        </TableCell>
                      </TableRow>
                    )}
                    {partsData.debug.parts.sample_columns && (
                      <TableRow>
                        <TableCell className="font-medium">Sample Columns:</TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-2">
                            {partsData.debug.parts.sample_columns.map((col) => (
                              <Badge key={col} variant="secondary">{col}</Badge>
                            ))}
                          </div>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
            )}

            {/* Other Parts Tables */}
            {partsData.debug.parts_tables && (
              <div>
                <h4 className="font-semibold mb-2">All Parts/Inventory Tables in Database:</h4>
                <div className="flex flex-wrap gap-2">
                  {partsData.debug.parts_tables.length > 0 ? (
                    partsData.debug.parts_tables.map((table) => (
                      <Badge key={table} variant="outline">{table}</Badge>
                    ))
                  ) : (
                    <span className="text-muted-foreground">No parts/inventory tables found</span>
                  )}
                </div>
              </div>
            )}
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