import React, { useState } from 'react';
import { apiUrl } from '@/lib/api';

const InvoiceFieldDiagnostic = () => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);

  const runDiagnostic = async () => {
    setLoading(true);
    try {
      const response = await fetch(apiUrl('/api/diagnostic/invoice-fields'), {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to run diagnostic');
      }

      const data = await response.json();
      setResults(data);
      console.log('=== INVOICE FIELD DIAGNOSTIC RESULTS ===');
      console.log('All Columns:', data.all_columns);
      console.log('Employee Name Columns:', data.employee_name_columns);
      console.log('Possible Name Fields:', data.possible_name_fields);
      console.log('Sample Invoices:', data.sample_invoices);
      console.log('Full Results:', data);
    } catch (err) {
      console.error('Diagnostic failed:', err);
      alert('Diagnostic failed. Check console for details.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 border rounded-lg bg-white">
      <h3 className="text-lg font-semibold mb-4">Invoice Field Diagnostic</h3>
      
      <button
        onClick={runDiagnostic}
        disabled={loading}
        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
      >
        {loading ? 'Running...' : 'Run Invoice Field Diagnostic'}
      </button>

      {results && (
        <div className="mt-4 space-y-4">
          <div>
            <h4 className="font-semibold">Employee Name Columns Found:</h4>
            <pre className="bg-gray-100 p-2 rounded text-xs overflow-auto">
              {JSON.stringify(results.employee_name_columns, null, 2)}
            </pre>
          </div>

          <div>
            <h4 className="font-semibold">Possible Name Fields (Sample Data):</h4>
            <pre className="bg-gray-100 p-2 rounded text-xs overflow-auto">
              {JSON.stringify(results.possible_name_fields, null, 2)}
            </pre>
          </div>

          <div>
            <h4 className="font-semibold">All Columns in InvoiceReg:</h4>
            <div className="max-h-60 overflow-y-auto">
              <pre className="bg-gray-100 p-2 rounded text-xs">
                {JSON.stringify(results.all_columns, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InvoiceFieldDiagnostic;