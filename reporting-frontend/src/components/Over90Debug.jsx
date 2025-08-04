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
      
      const response = await fetch(apiUrl('/api/reports/departments/accounting/over90-debug'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error('Failed to fetch data');
      
      const result = await response.json();
      setData(result);
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
              <span>90-120 Days:</span>
              <span className="font-bold">{formatCurrency(data.totals['90-120'] || data.totals['90-119'] || 0)}</span>
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
              Total invoices over 90 days: {data.total_count || data.invoices.length}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}