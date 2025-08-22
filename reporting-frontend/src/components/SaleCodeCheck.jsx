import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { apiUrl } from '@/lib/api';

export default function SaleCodeCheck() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const checkCodes = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(apiUrl('/api/dashboard-optimized/equipment-salecodes'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const result = await response.json();
      setData(result);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="mt-4">
      <CardHeader>
        <CardTitle>Equipment Sale Codes Check</CardTitle>
      </CardHeader>
      <CardContent>
        <Button onClick={checkCodes} disabled={loading}>
          {loading ? 'Checking...' : 'Check Sale Codes'}
        </Button>
        
        {data && (
          <div className="mt-4 space-y-4">
            <div>
              <h3 className="font-bold mb-2">Target Codes (LINDE, LINDEN, NEWEQ, KOM):</h3>
              <div className="bg-gray-100 p-2 rounded">
                {data.target_codes_check?.map(item => (
                  <div key={item.code}>
                    {item.code}: {item.count} invoices total
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <h3 className="font-bold mb-2">All Equipment Sale Codes Since March 2025:</h3>
              <div className="bg-gray-100 p-2 rounded text-sm">
                {data.equipment_sale_codes?.length > 0 ? (
                  data.equipment_sale_codes.map((item, idx) => (
                    <div key={idx} className="border-b py-1">
                      <strong>{item.SaleCode || '(blank)'}</strong>: 
                      {item.invoice_count} invoices, 
                      ${(item.total_revenue || 0).toLocaleString()}
                    </div>
                  ))
                ) : (
                  <div>No equipment sales found since March 2025</div>
                )}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}