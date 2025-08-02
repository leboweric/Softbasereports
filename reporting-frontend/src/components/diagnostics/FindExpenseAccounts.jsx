import React, { useState } from 'react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { apiUrl } from '@/lib/api';

export default function FindExpenseAccounts() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const searchForAccounts = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('authToken') || localStorage.getItem('token');
      const response = await fetch(apiUrl('/api/diagnostics/find-expense-accounts'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      const data = await response.json();
      console.log('Find expense accounts results:', data);
      
      if (!response.ok) {
        setError(data.error || 'Search failed');
      } else {
        setResults(data);
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
          <CardTitle>Find Expense Accounts (6xxxxx)</CardTitle>
          <p className="text-sm text-gray-600">
            Comprehensive search across ALL tables for account codes starting with 6
          </p>
        </CardHeader>
        <CardContent>
          <Button onClick={searchForAccounts} disabled={loading} className="mb-4">
            {loading ? 'Searching all tables...' : 'Search for 6xxxxx Accounts'}
          </Button>
          
          {error && (
            <div className="mt-4 p-4 bg-red-50 text-red-700 rounded">
              Error: {error}
            </div>
          )}
          
          {results && (
            <div className="mt-6 space-y-6">
              {/* GL Table Check */}
              <div>
                <h3 className="text-lg font-semibold mb-2">GL Tables Check</h3>
                <div className="bg-gray-50 p-4 rounded">
                  {Object.entries(results.gl_table_check || {}).map(([table, info]) => (
                    <div key={table} className="mb-2">
                      <strong>{table}:</strong> 
                      {info.error ? (
                        <span className="text-red-600 ml-2">Error: {info.error}</span>
                      ) : (
                        <span className="ml-2">
                          {info.total_rows} total rows, 
                          <span className={info.accounts_with_6 > 0 ? "text-green-600 font-bold" : ""}>
                            {info.accounts_with_6} accounts starting with 6
                          </span>
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Tables with 6xxxxx accounts */}
              {results.tables_with_6_accounts?.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-2 text-green-600">
                    ✓ Found Tables with 6xxxxx Accounts!
                  </h3>
                  <div className="space-y-4">
                    {results.tables_with_6_accounts.map((item, idx) => (
                      <div key={idx} className="bg-green-50 p-4 rounded border border-green-200">
                        <h4 className="font-semibold text-green-800">
                          Table: {item.table} - Column: {item.column}
                        </h4>
                        <p className="text-sm text-gray-600">
                          Data Type: {item.data_type} | 
                          Total Matching Rows: {item.total_matching_rows}
                        </p>
                        <div className="mt-2">
                          <p className="text-sm font-medium">Sample Values:</p>
                          <div className="flex gap-2 flex-wrap mt-1">
                            {item.sample_values.map((val, i) => (
                              <span key={i} className="bg-white px-2 py-1 rounded text-xs border">
                                {val}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* No results found */}
              {results.tables_with_6_accounts?.length === 0 && (
                <div className="bg-yellow-50 p-4 rounded">
                  <p className="text-yellow-800">
                    No tables found with account codes starting with 6.
                  </p>
                </div>
              )}

              {/* Potential transaction tables */}
              {results.potential_transaction_tables?.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-2">Potential Transaction Tables</h3>
                  <div className="bg-gray-50 p-4 rounded">
                    <div className="grid grid-cols-3 gap-2">
                      {results.potential_transaction_tables.map((table, idx) => (
                        <div key={idx} className="bg-white p-2 rounded text-sm">
                          {table}
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