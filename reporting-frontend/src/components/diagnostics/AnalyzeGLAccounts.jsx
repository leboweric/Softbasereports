import React, { useState } from 'react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { apiUrl } from '@/lib/api';

export default function AnalyzeGLAccounts() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const analyzeAccounts = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('authToken') || localStorage.getItem('token');
      const response = await fetch(apiUrl('/api/diagnostics/analyze-gl-accounts'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      const result = await response.json();
      console.log('GL Analysis Results:', result);
      
      if (!response.ok) {
        setError(result.error || 'Analysis failed');
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
          <CardTitle>GL Account Analysis</CardTitle>
          <p className="text-sm text-gray-600">
            Comprehensive analysis of expense accounts (6xxxxx) in GL tables
          </p>
        </CardHeader>
        <CardContent>
          <Button onClick={analyzeAccounts} disabled={loading} className="mb-4">
            {loading ? 'Analyzing GL accounts...' : 'Analyze GL Accounts'}
          </Button>
          
          {error && (
            <div className="mt-4 p-4 bg-red-50 text-red-700 rounded">
              Error: {error}
            </div>
          )}
          
          {data && (
            <div className="mt-6 space-y-6">
              {/* Chart of Accounts */}
              {data.chart_of_accounts?.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-2">Chart of Accounts (6xxxxx)</h3>
                  <div className="overflow-x-auto">
                    <table className="min-w-full bg-white border text-sm">
                      <thead>
                        <tr className="bg-gray-50">
                          <th className="px-4 py-2 border text-left">Account No</th>
                          <th className="px-4 py-2 border text-left">Description</th>
                          <th className="px-4 py-2 border text-left">Type</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.chart_of_accounts.slice(0, 20).map((acct, idx) => (
                          <tr key={idx} className="hover:bg-gray-50">
                            <td className="px-4 py-2 border font-mono">{acct.AccountNo}</td>
                            <td className="px-4 py-2 border">{acct.AccountDescription}</td>
                            <td className="px-4 py-2 border">{acct.AccountType}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {data.chart_of_accounts.length > 20 && (
                      <p className="text-sm text-gray-600 mt-2">
                        Showing 20 of {data.chart_of_accounts.length} accounts
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* GL Summary */}
              {data.gl_summary?.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-2">GLDetail Summary by Account</h3>
                  <div className="overflow-x-auto">
                    <table className="min-w-full bg-white border text-sm">
                      <thead>
                        <tr className="bg-gray-50">
                          <th className="px-4 py-2 border text-left">Account</th>
                          <th className="px-4 py-2 border text-left">Description</th>
                          <th className="px-4 py-2 border text-right">Trans Count</th>
                          <th className="px-4 py-2 border text-right">Total Amount</th>
                          <th className="px-4 py-2 border text-left">Date Range</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.gl_summary.slice(0, 15).map((item, idx) => (
                          <tr key={idx} className="hover:bg-gray-50">
                            <td className="px-4 py-2 border font-mono">{item.AccountNo}</td>
                            <td className="px-4 py-2 border">{item.AccountDescription || 'N/A'}</td>
                            <td className="px-4 py-2 border text-right">{item.transaction_count}</td>
                            <td className="px-4 py-2 border text-right">
                              ${(item.total_amount || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </td>
                            <td className="px-4 py-2 border text-xs">
                              {item.first_transaction?.split('T')[0]} to {item.last_transaction?.split('T')[0]}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* 2025 Monthly Data */}
              {data.monthly_2025?.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-2">2025 Monthly Expense Data</h3>
                  <div className="bg-green-50 p-4 rounded">
                    <table className="min-w-full bg-white border">
                      <thead>
                        <tr className="bg-gray-50">
                          <th className="px-4 py-2 border text-left">Month</th>
                          <th className="px-4 py-2 border text-right">Transactions</th>
                          <th className="px-4 py-2 border text-right">Total Expenses</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.monthly_2025.map((month, idx) => (
                          <tr key={idx}>
                            <td className="px-4 py-2 border">{month.year}-{String(month.month).padStart(2, '0')}</td>
                            <td className="px-4 py-2 border text-right">{month.transaction_count}</td>
                            <td className="px-4 py-2 border text-right">
                              ${(month.total_expenses || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Sample Transactions */}
              {data.sample_transactions?.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-2">Recent Sample Transactions</h3>
                  <div className="overflow-x-auto">
                    <table className="min-w-full bg-white border text-xs">
                      <thead>
                        <tr className="bg-gray-50">
                          <th className="px-2 py-1 border text-left">Date</th>
                          <th className="px-2 py-1 border text-left">Account</th>
                          <th className="px-2 py-1 border text-left">Description</th>
                          <th className="px-2 py-1 border text-right">Amount</th>
                          <th className="px-2 py-1 border text-left">Trans Desc</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.sample_transactions.map((trans, idx) => (
                          <tr key={idx} className="hover:bg-gray-50">
                            <td className="px-2 py-1 border">{trans.EffectiveDate?.split('T')[0]}</td>
                            <td className="px-2 py-1 border font-mono">{trans.AccountNo}</td>
                            <td className="px-2 py-1 border">{trans.AccountDescription}</td>
                            <td className="px-2 py-1 border text-right">
                              ${(trans.Amount || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                            </td>
                            <td className="px-2 py-1 border">{trans.TransactionDescription || trans.Reference || 'N/A'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* GLDetail Columns */}
              {data.gldetail_columns?.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-2">GLDetail Table Structure</h3>
                  <div className="bg-gray-50 p-4 rounded">
                    <div className="grid grid-cols-3 gap-2 text-xs">
                      {data.gldetail_columns.map((col, idx) => (
                        <div key={idx}>
                          <span className="font-mono">{col.COLUMN_NAME}</span>
                          <span className="text-gray-500 ml-2">({col.DATA_TYPE})</span>
                        </div>
                      ))}
                    </div>
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