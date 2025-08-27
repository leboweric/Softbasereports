import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { apiUrl } from '@/lib/api'

const TestUserUpdate = () => {
  const [result, setResult] = useState('')
  const [loading, setLoading] = useState(false)

  const testUpdate = async () => {
    setLoading(true)
    setResult('Testing...')
    
    try {
      const token = localStorage.getItem('token')
      
      // Test with user ID 7 (jchristensen)
      const response = await fetch(apiUrl('/api/users/7/update-info'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          first_name: 'TestName',
          last_name: 'TestLast'
        })
      })
      
      console.log('Response status:', response.status)
      const data = await response.json()
      console.log('Response data:', data)
      
      setResult(`Status: ${response.status}\nData: ${JSON.stringify(data, null, 2)}`)
    } catch (err) {
      console.error('Error:', err)
      setResult(`Error: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card className="mt-4">
      <CardHeader>
        <CardTitle>Test User Update Endpoint</CardTitle>
      </CardHeader>
      <CardContent>
        <Button onClick={testUpdate} disabled={loading}>
          {loading ? 'Testing...' : 'Test Update User 7'}
        </Button>
        {result && (
          <pre className="mt-4 p-2 bg-gray-100 rounded text-xs overflow-auto">
            {result}
          </pre>
        )}
      </CardContent>
    </Card>
  )
}

export default TestUserUpdate