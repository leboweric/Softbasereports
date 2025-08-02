import React, { useState } from 'react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { apiUrl } from '@/lib/api';

export default function MonthlyExpenseDebug() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const runDebug = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('authToken') || localStorage.getItem('token');
      const response = await fetch(apiUrl('/api/diagnostics/monthly-expense-debug'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      const result = await response.json();
      console.log('Monthly Expense Debug:', result);
      
      if (!response.ok) {
        setError(result.error || 'Debug failed');
      } else {
        setData(result);
      }
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Monthly Expense Debug</CardTitle>
          <p className="text-sm text-gray-600">
            Debug why some months are missing expense data
          </p>
        </CardHeader>
        <CardContent>
          <Button onClick={runDebug} disabled={loading} className="mb-4">
            {loading ? 'Running debug...' : 'Debug Monthly Expenses'}
          </Button>
          
          {error && (
            <div className="mt-4 p-4 bg-red-50 text-red-700 rounded">
              Error: {error}
            </div>
          )}
          
          {data && (
            <div className="mt-6 space-y-6">
              {/* Raw Monthly Data */}
              {data.raw_monthly_data && (
                <div>
                  <h3 className="text-lg font-semibold mb-2">Raw Monthly Data (2025)</h3>
                  <table className="min-w-full bg-white border text-sm">
                    <thead>
                      <tr className="bg-gray-50">
                        <th className="px-4 py-2 border text-left">Month</th>
                        <th className="px-4 py-2 border text-right">Transactions</th>
                        <th className="px-4 py-2 border text-right">Total Amount</th>
                        <th className="px-4 py-2 border text-left">Date Range</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.raw_monthly_data.map((row, idx) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="px-4 py-2 border">{row.year}-{String(row.month).padStart(2, '0')}</td>
                          <td className="px-4 py-2 border text-right">{row.transaction_count}</td>
                          <td className="px-4 py-2 border text-right">
                            ${(row.total_amount || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                          </td>
                          <td className="px-4 py-2 border text-xs">
                            {row.first_date?.split('T')[0]} to {row.last_date?.split('T')[0]}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Endpoint Query Results */}
              {data.endpoint_query_results && (
                <div>
                  <h3 className="text-lg font-semibold mb-2">Accounting Endpoint Query Results</h3>
                  <div className="bg-yellow-50 p-4 rounded">
                    <table className="min-w-full bg-white border">
                      <thead>
                        <tr className="bg-gray-50">
                          <th className="px-4 py-2 border text-left">Month</th>
                          <th className="px-4 py-2 border text-right">Expenses</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.endpoint_query_results.map((row, idx) => (
                          <tr key={idx}>
                            <td className="px-4 py-2 border">{row.month}</td>
                            <td className="px-4 py-2 border text-right">
                              ${(row.expenses || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Record Counts */}
              {data.record_counts?.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-2">Record Counts by Month</h3>
                  <div className="bg-blue-50 p-4 rounded">
                    <pre className="text-xs">{JSON.stringify(data.record_counts[0], null, 2)}</pre>
                  </div>
                </div>
              )}

              {/* Sample Transactions */}
              {data.sample_transactions && (
                <div>
                  <h3 className="text-lg font-semibold mb-2">Sample Transactions by Month</h3>
                  <div className="overflow-x-auto">
                    <table className="min-w-full bg-white border text-xs">
                      <thead>
                        <tr className="bg-gray-50">
                          <th className="px-2 py-1 border text-left">Month</th>
                          <th className="px-2 py-1 border text-left">Date</th>
                          <th className="px-2 py-1 border text-left">Account</th>
                          <th className="px-2 py-1 border text-right">Amount</th>
                          <th className="px-2 py-1 border text-left">Description</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.sample_transactions.map((trans, idx) => (
                          <tr key={idx} className="hover:bg-gray-50">
                            <td className="px-2 py-1 border">{trans.month}</td>
                            <td className="px-2 py-1 border">{trans.date?.split('T')[0]}</td>
                            <td className="px-2 py-1 border font-mono">{trans.AccountNo}</td>
                            <td className="px-2 py-1 border text-right">
                              ${(trans.Amount || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                            </td>
                            <td className="px-2 py-1 border">{trans.Description || 'N/A'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}