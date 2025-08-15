import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { apiUrl } from '@/lib/api'

const RentalShipToResearch = () => {
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)

  const runResearch = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      
      const response = await fetch(apiUrl('/api/reports/departments/rental/shipto-research'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setResults(data)
        console.log('Research Results:', data)
      }
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Rental Ship To Research</CardTitle>
      </CardHeader>
      <CardContent>
        <Button onClick={runResearch} disabled={loading}>
          {loading ? 'Running Research...' : 'Run Ship To Research'}
        </Button>
        
        {results && (
          <div className="mt-4 space-y-4">
            <div>
              <h3 className="font-semibold">Research Results:</h3>
              <pre className="text-xs overflow-auto bg-gray-50 p-2 rounded">
                {JSON.stringify(results, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default RentalShipToResearch