import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiUrl } from '@/lib/api';

export default function Over90Debug() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Run a custom query to see what's in over 90
      const query = `
        WITH InvoiceBalances AS (
            SELECT 
                ar.InvoiceNo,
                ar.CustomerNo,
                MIN(ar.Due) as Due,
                SUM(ar.Amount) as NetBalance
            FROM ben002.ARDetail ar
            WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
                AND ar.DeletionTime IS NULL
                AND ar.InvoiceNo IS NOT NULL
            GROUP BY ar.InvoiceNo, ar.CustomerNo
            HAVING SUM(ar.Amount) > 0.01
        )
        SELECT 
            ib.InvoiceNo,
            ib.CustomerNo,
            c.Name as CustomerName,
            ib.Due,
            DATEDIFF(day, ib.Due, GETDATE()) as DaysOld,
            ib.NetBalance
        FROM InvoiceBalances ib
        LEFT JOIN ben002.Customer c ON ib.CustomerNo = c.Number
        WHERE DATEDIFF(day, ib.Due, GETDATE()) >= 90
        ORDER BY ib.NetBalance DESC
      `;

      const response = await fetch(apiUrl('/api/query'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query })
      });

      if (!response.ok) throw new Error('Failed to fetch data');
      
      const result = await response.json();
      
      // Calculate totals by days old ranges
      const totals = {
        '90-119': 0,
        '120+': 0,
        'total': 0
      };
      
      const invoices = result.data || [];
      invoices.forEach(inv => {
        const amount = parseFloat(inv.NetBalance || 0);
        const days = parseInt(inv.DaysOld || 0);
        
        if (days >= 90 && days < 120) {
          totals['90-119'] += amount;
        } else if (days >= 120) {
          totals['120+'] += amount;
        }
        totals.total += amount;
      });
      
      setData({ invoices, totals });
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading over 90 debug data...</div>;
  if (!data) return <div>No data available</div>;

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount);
  };

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold">Over 90 Days Debug</h1>
      
      <Card>
        <CardHeader>
          <CardTitle>Totals Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>90-119 Days:</span>
              <span className="font-bold">{formatCurrency(data.totals['90-119'])}</span>
            </div>
            <div className="flex justify-between">
              <span>120+ Days:</span>
              <span className="font-bold">{formatCurrency(data.totals['120+'])}</span>
            </div>
            <div className="flex justify-between border-t pt-2">
              <span>Total Over 90:</span>
              <span className="font-bold">{formatCurrency(data.totals.total)}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Invoice Details (Top 50)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Invoice#</th>
                  <th className="text-left p-2">Customer</th>
                  <th className="text-left p-2">Due Date</th>
                  <th className="text-right p-2">Days Old</th>
                  <th className="text-right p-2">Balance</th>
                </tr>
              </thead>
              <tbody>
                {data.invoices.slice(0, 50).map((inv, idx) => (
                  <tr key={idx} className="border-b">
                    <td className="p-2">{inv.InvoiceNo}</td>
                    <td className="p-2">{inv.CustomerName || inv.CustomerNo}</td>
                    <td className="p-2">{inv.Due ? new Date(inv.Due).toLocaleDateString() : 'N/A'}</td>
                    <td className="text-right p-2">{inv.DaysOld}</td>
                    <td className="text-right p-2">{formatCurrency(inv.NetBalance)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="mt-2 text-sm text-gray-500">
              Total invoices over 90 days: {data.invoices.length}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}