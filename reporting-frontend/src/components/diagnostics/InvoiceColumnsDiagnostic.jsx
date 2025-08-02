import React, { useState } from 'react';
import { Button } from '../ui/button';
import { apiUrl } from '@/lib/api';

export default function InvoiceColumnsDiagnostic() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const runDiagnostic = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('authToken') || localStorage.getItem('token');
      const response = await fetch(apiUrl('/api/diagnostics/invoice-columns'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log('Response status:', response.status);
      const result = await response.json();
      console.log('Result:', result);
      
      if (!response.ok) {
        setError(result.error || 'Failed to get columns');
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
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Invoice Columns Diagnostic</h2>
      <Button onClick={runDiagnostic} disabled={loading}>
        {loading ? 'Running...' : 'Get Invoice Columns'}
      </Button>
      
      {error && (
        <div className="mt-4 p-4 bg-red-100 text-red-700 rounded">
          Error: {error}
        </div>
      )}
      
      {data && (
        <div className="mt-4 space-y-4">
          <div>
            <h3 className="font-semibold">Total Columns: {data.total_columns}</h3>
          </div>
          
          {data.potential_dept_columns?.length > 0 && (
            <div>
              <h3 className="font-semibold">Potential Department/Account Columns:</h3>
              <ul className="list-disc pl-5">
                {data.potential_dept_columns.map((col, idx) => (
                  <li key={idx}>
                    <strong>{col.column}</strong> ({col.data_type})
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {data.expense_columns?.length > 0 && (
            <div>
              <h3 className="font-semibold">Columns with values starting with '6':</h3>
              <ul className="list-disc pl-5">
                {data.expense_columns.map((col, idx) => (
                  <li key={idx}>
                    <strong>{col.column}</strong>: {col.sample_value}
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          <div>
            <h3 className="font-semibold">All Columns:</h3>
            <div className="bg-gray-100 p-2 rounded text-xs">
              {data.all_columns?.join(', ')}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}