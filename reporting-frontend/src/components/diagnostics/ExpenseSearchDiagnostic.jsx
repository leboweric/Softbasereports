import React, { useState } from 'react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { apiUrl } from '@/lib/api';

export default function ExpenseSearchDiagnostic() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const runDiagnostic = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch(apiUrl('/api/diagnostics/expense-search'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Diagnostic failed');
      }
      
      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Expense Search Diagnostic</CardTitle>
          <p className="text-sm text-gray-600">
            Search for G&A expense data across different tables and schemas
          </p>
        </CardHeader>
        <CardContent>
          <Button onClick={runDiagnostic} disabled={loading}>
            {loading ? 'Running...' : 'Search for Expense Data'}
          </Button>
          
          {error && (
            <div className="mt-4 p-4 bg-red-50 text-red-700 rounded">
              Error: {error}
            </div>
          )}
          
          {results && (
            <div className="mt-6 space-y-6">
              {/* Numeric Columns in InvoiceReg */}
              <div>
                <h3 className="text-lg font-semibold mb-2">InvoiceReg Numeric Fields</h3>
                <div className="bg-gray-50 p-4 rounded">
                  <p className="text-sm mb-2">Found {results.potential_expense_fields?.length || 0} numeric columns that could contain expense data:</p>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    {results.potential_expense_fields?.map((field, idx) => (
                      <div key={idx} className="bg-white p-2 rounded border">
                        <span className="font-medium">{field.column}</span>
                        <span className="text-gray-500 ml-2">({field.data_type})</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Department Patterns */}
              {results.invoice_expenses?.department_patterns?.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-2">Department/SaleCode Patterns</h3>
                  <div className="overflow-x-auto">
                    <table className="min-w-full bg-white border">
                      <thead>
                        <tr className="bg-gray-50">
                          <th className="px-4 py-2 border text-left">Department</th>
                          <th className="px-4 py-2 border text-left">Sale Code</th>
                          <th className="px-4 py-2 border text-right">Record Count</th>
                        </tr>
                      </thead>
                      <tbody>
                        {results.invoice_expenses.department_patterns.map((pattern, idx) => (
                          <tr key={idx} className="hover:bg-gray-50">
                            <td className="px-4 py-2 border">{pattern.department || 'NULL'}</td>
                            <td className="px-4 py-2 border">{pattern.sale_code || 'NULL'}</td>
                            <td className="px-4 py-2 border text-right">{pattern.count}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Sample Invoice Records */}
              {results.invoice_expenses?.sample_records?.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-2">Sample Invoice Records</h3>
                  <div className="overflow-x-auto">
                    <table className="min-w-full bg-white border text-sm">
                      <thead>
                        <tr className="bg-gray-50">
                          <th className="px-4 py-2 border text-left">Invoice #</th>
                          <th className="px-4 py-2 border text-left">Date</th>
                          <th className="px-4 py-2 border text-left">Dept</th>
                          <th className="px-4 py-2 border text-left">Sale Code</th>
                          <th className="px-4 py-2 border text-right">Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {results.invoice_expenses.sample_records.map((inv, idx) => (
                          <tr key={idx} className="hover:bg-gray-50">
                            <td className="px-4 py-2 border">{inv.invoice_no}</td>
                            <td className="px-4 py-2 border">{inv.date?.split('T')[0]}</td>
                            <td className="px-4 py-2 border">{inv.department || 'NULL'}</td>
                            <td className="px-4 py-2 border">{inv.sale_code || 'NULL'}</td>
                            <td className="px-4 py-2 border text-right">${inv.total?.toFixed(2)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Other Schemas */}
              {results.other_schemas && Object.keys(results.other_schemas).length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-2">GL/Account Tables in Other Schemas</h3>
                  <div className="bg-yellow-50 p-4 rounded">
                    {Object.entries(results.other_schemas).map(([schema, tables]) => (
                      <div key={schema} className="mb-2">
                        <p className="font-medium">Schema: {schema}</p>
                        <p className="text-sm text-gray-600">Tables: {tables.length} fields found</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommendations */}
              {results.recommendations?.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-2">Recommendations</h3>
                  <ul className="list-disc pl-5 space-y-1">
                    {results.recommendations.map((rec, idx) => (
                      <li key={idx} className="text-sm">{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}