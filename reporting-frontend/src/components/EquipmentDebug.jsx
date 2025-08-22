import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { apiUrl } from '@/lib/api';

export default function EquipmentDebug() {
  const [debugData, setDebugData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchDebugData = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(apiUrl('/api/dashboard-optimized/equipment-debug'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setDebugData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="mt-4">
      <CardHeader>
        <CardTitle>Equipment Sales Debug</CardTitle>
      </CardHeader>
      <CardContent>
        <Button onClick={fetchDebugData} disabled={loading}>
          {loading ? 'Loading...' : 'Test Equipment Data'}
        </Button>
        
        {error && (
          <div className="mt-4 p-4 bg-red-100 text-red-700 rounded">
            Error: {error}
          </div>
        )}
        
        {debugData && (
          <div className="mt-4 space-y-4">
            <div>
              <h3 className="font-bold">Invoice Samples (New Equipment):</h3>
              <pre className="bg-gray-100 p-2 rounded text-xs overflow-auto">
                {JSON.stringify(debugData.invoice_samples, null, 2)}
              </pre>
            </div>
            
            <div>
              <h3 className="font-bold">InvoiceSales Count:</h3>
              <pre className="bg-gray-100 p-2 rounded text-xs">
                {JSON.stringify(debugData.invoice_sales_count, null, 2)}
              </pre>
            </div>
            
            <div>
              <h3 className="font-bold">InvoiceSales Samples:</h3>
              <pre className="bg-gray-100 p-2 rounded text-xs overflow-auto">
                {JSON.stringify(debugData.invoice_sales_samples, null, 2)}
              </pre>
            </div>
            
            <div>
              <h3 className="font-bold">Monthly Aggregation:</h3>
              <pre className="bg-gray-100 p-2 rounded text-xs overflow-auto">
                {JSON.stringify(debugData.monthly_aggregation, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}