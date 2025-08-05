import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { apiUrl } from '@/lib/api'

const PartsWOStructureDiagnostic = () => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/parts/wo-parts-diagnostic'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const result = await response.json()
        setData(result)
      }
    } catch (error) {
      console.error('Error fetching diagnostic data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <LoadingSpinner />
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Parts WO Structure Diagnostic</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h3 className="font-semibold mb-2">Parts Work Orders Summary (showing parts_in_woparts vs quote_lines)</h3>
            <div className="text-xs overflow-auto">
              <table className="w-full border">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="border p-1">WO#</th>
                    <th className="border p-1">Open Date</th>
                    <th className="border p-1">Closed Date</th>
                    <th className="border p-1">Parts in WOParts</th>
                    <th className="border p-1">Quote Lines</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.parts_wo_summary?.map((wo) => (
                    <tr key={wo.WONo}>
                      <td className="border p-1">{wo.WONo}</td>
                      <td className="border p-1">{wo.OpenDate ? new Date(wo.OpenDate).toLocaleDateString() : 'N/A'}</td>
                      <td className="border p-1">{wo.ClosedDate ? new Date(wo.ClosedDate).toLocaleDateString() : 'Open'}</td>
                      <td className="border p-1 text-center font-bold">{wo.parts_in_woparts}</td>
                      <td className="border p-1 text-center font-bold">{wo.quote_lines}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div>
            <h3 className="font-semibold mb-2">Sample WOParts entries for Type='P'</h3>
            <div className="text-xs overflow-auto">
              {data?.sample_woparts?.length > 0 ? (
                <table className="w-full border">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="border p-1">WO#</th>
                      <th className="border p-1">Part#</th>
                      <th className="border p-1">Description</th>
                      <th className="border p-1">Qty</th>
                      <th className="border p-1">Sell</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.sample_woparts.map((part, idx) => (
                      <tr key={idx}>
                        <td className="border p-1">{part.WONo}</td>
                        <td className="border p-1">{part.PartNo}</td>
                        <td className="border p-1">{part.Description}</td>
                        <td className="border p-1">{part.Qty}</td>
                        <td className="border p-1">${part.Sell}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="text-red-600">No WOParts entries found for Parts work orders!</p>
              )}
            </div>
          </div>

          <div>
            <h3 className="font-semibold mb-2">Sample WOQuote entries for Type='P'</h3>
            <div className="text-xs overflow-auto">
              {data?.sample_woquote?.length > 0 ? (
                <table className="w-full border">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="border p-1">WO#</th>
                      <th className="border p-1">Quote Type</th>
                      <th className="border p-1">Line#</th>
                      <th className="border p-1">Description</th>
                      <th className="border p-1">Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.sample_woquote.map((quote, idx) => (
                      <tr key={idx}>
                        <td className="border p-1">{quote.WONo}</td>
                        <td className="border p-1">{quote.QuoteType}</td>
                        <td className="border p-1">{quote.QuoteLine}</td>
                        <td className="border p-1">{quote.Description}</td>
                        <td className="border p-1">${quote.Amount}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p>No WOQuote entries found for Parts work orders</p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default PartsWOStructureDiagnostic