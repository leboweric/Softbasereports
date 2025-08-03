import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { apiUrl } from '@/lib/api'

const Check145Debug = () => {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      
      const response = await fetch(apiUrl('/api/reports/departments/rental/check-145'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to fetch 145 work orders')
      }

      const result = await response.json()
      setData(result)
      setError(null)
    } catch (err) {
      setError(err.message || 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-red-600 text-center py-4">
        Error: {error}
      </div>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>145 Work Orders Debug (Found: {data?.count || 0})</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>WO#</TableHead>
                <TableHead>Bill To</TableHead>
                <TableHead>Sale Dept</TableHead>
                <TableHead>Sale Code</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Open Date</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data?.workOrders?.map((wo) => (
                <TableRow key={wo.woNumber}>
                  <TableCell className="font-mono">{wo.woNumber}</TableCell>
                  <TableCell>{wo.billTo}</TableCell>
                  <TableCell>{wo.saleDept}</TableCell>
                  <TableCell>{wo.saleCode}</TableCell>
                  <TableCell>{wo.type}</TableCell>
                  <TableCell>{wo.openDate}</TableCell>
                  <TableCell>
                    {wo.closedDate ? 'Closed' : 
                     wo.invoiceDate ? 'Invoiced' :
                     wo.completedDate ? 'Completed' : 'Open'}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}

export default Check145Debug