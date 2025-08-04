import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiUrl } from '@/lib/api';

export default function ARAgingDebug() {
  const [debugData, setDebugData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDebugData();
  }, []);

  const fetchDebugData = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(apiUrl('/api/reports/departments/accounting/ar-aging-debug'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch debug data');
      }

      const data = await response.json();
      setDebugData(data);
      console.log('AR Aging Debug Data:', data);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching debug data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading debug data...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!debugData) return <div>No debug data available</div>;

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount);
  };

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold">AR Aging Debug Information</h1>
      
      <Card>
        <CardHeader>
          <CardTitle>Summary Comparison</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold mb-2">Calculated Values</h3>
              <div className="space-y-1">
                <p>Total AR: {formatCurrency(debugData.calculated.total_ar)}</p>
                <p>Bucket Sum: {formatCurrency(debugData.calculated.bucket_sum)}</p>
                <p>Difference: {formatCurrency(debugData.calculated.difference)}</p>
                <p>Over 90 Days: {formatCurrency(debugData.calculated.over_90_amount)} ({debugData.calculated.over_90_percentage}%)</p>
              </div>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Expected Values</h3>
              <div className="space-y-1">
                <p>Total AR: {formatCurrency(debugData.expected.total_ar)}</p>
                <p>Over 90 Days: {formatCurrency(debugData.expected.over_90)} ({debugData.expected.over_90_percentage}%)</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Aging Buckets</CardTitle>
        </CardHeader>
        <CardContent>
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2">Bucket</th>
                <th className="text-right p-2">Calculated</th>
                <th className="text-right p-2">Expected</th>
                <th className="text-right p-2">Difference</th>
                <th className="text-right p-2">Records</th>
              </tr>
            </thead>
            <tbody>
              {['Current', '1-30', '30-60', '60-90', '90-120', '120+'].map(bucket => {
                const calculated = debugData.buckets[bucket]?.amount || 0;
                const expected = debugData.expected[bucket.toLowerCase().replace('-', '_')] || 0;
                const diff = debugData.differences[`${bucket.toLowerCase().replace('-', '_')}_diff`] || 0;
                const count = debugData.buckets[bucket]?.count || 0;
                
                return (
                  <tr key={bucket} className="border-b">
                    <td className="p-2">{bucket}</td>
                    <td className="text-right p-2">{formatCurrency(calculated)}</td>
                    <td className="text-right p-2">{formatCurrency(expected)}</td>
                    <td className={`text-right p-2 ${Math.abs(diff) > 1 ? 'text-red-600' : ''}`}>
                      {formatCurrency(diff)}
                    </td>
                    <td className="text-right p-2">{count}</td>
                  </tr>
                );
              })}
              {debugData.buckets['No Due Date'] && (
                <tr className="border-b bg-yellow-50">
                  <td className="p-2">No Due Date</td>
                  <td className="text-right p-2">{formatCurrency(debugData.buckets['No Due Date'].amount)}</td>
                  <td className="text-right p-2">-</td>
                  <td className="text-right p-2">-</td>
                  <td className="text-right p-2">{debugData.buckets['No Due Date'].count}</td>
                </tr>
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>NULL Due Dates</CardTitle>
        </CardHeader>
        <CardContent>
          <p>Records: {debugData.null_due_dates.count || 0}</p>
          <p>Amount: {formatCurrency(debugData.null_due_dates.amount || 0)}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Entry Types</CardTitle>
        </CardHeader>
        <CardContent>
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2">Entry Type</th>
                <th className="text-right p-2">Count</th>
                <th className="text-right p-2">Amount</th>
              </tr>
            </thead>
            <tbody>
              {debugData.entry_types.map(entry => (
                <tr key={entry.EntryType || 'null'} className="border-b">
                  <td className="p-2">{entry.EntryType || '(NULL)'}</td>
                  <td className="text-right p-2">{entry.count}</td>
                  <td className="text-right p-2">{formatCurrency(entry.amount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Sample Records Around 90 Days</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Invoice#</th>
                  <th className="text-left p-2">Customer</th>
                  <th className="text-left p-2">Type</th>
                  <th className="text-right p-2">Amount</th>
                  <th className="text-right p-2">Days Old</th>
                </tr>
              </thead>
              <tbody>
                {debugData.sample_90_days.map((record, idx) => (
                  <tr key={idx} className="border-b">
                    <td className="p-2">{record.InvoiceNo}</td>
                    <td className="p-2">{record.CustomerNo}</td>
                    <td className="p-2">{record.EntryType}</td>
                    <td className="text-right p-2">{formatCurrency(record.Amount)}</td>
                    <td className="text-right p-2">{record.DaysOld}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}