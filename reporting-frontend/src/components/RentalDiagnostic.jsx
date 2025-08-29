import React, { useState, useEffect } from 'react';
import { apiUrl } from '@/lib/api';
import { LoadingSpinner } from '@/components/ui/loading-spinner';

const RentalDiagnostic = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState({});
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDiagnosticData();
  }, []);

  const fetchDiagnosticData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // Fetch all diagnostic endpoints
      const endpoints = [
        '/api/rental-diagnostic/equipment-schema',
        '/api/rental-diagnostic/rental-status-values', 
        '/api/rental-diagnostic/problem-units',
        '/api/rental-diagnostic/find-sold-pattern',
        '/api/rental-diagnostic/units-on-hold',
        '/api/rental-diagnostic/check-equipment-removed'
      ];

      const results = {};
      
      for (const endpoint of endpoints) {
        try {
          const response = await fetch(apiUrl(endpoint), {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          });
          
          if (response.ok) {
            const data = await response.json();
            results[endpoint] = data;
          } else {
            results[endpoint] = { error: 'Failed to fetch' };
          }
        } catch (err) {
          results[endpoint] = { error: err.message };
        }
      }
      
      setData(results);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          Error: {error}
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Rental Availability Diagnostic</h1>
      
      {/* Equipment Schema */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Equipment Table Columns</h2>
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left">Column Name</th>
                  <th className="px-4 py-2 text-left">Data Type</th>
                </tr>
              </thead>
              <tbody>
                {data['/api/rental-diagnostic/equipment-schema']?.columns?.slice(0, 30).map((col, i) => (
                  <tr key={i} className="border-t">
                    <td className="px-4 py-2">{col.COLUMN_NAME}</td>
                    <td className="px-4 py-2">{col.DATA_TYPE}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Rental Status Values */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Rental Status Values</h2>
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left">Status</th>
                  <th className="px-4 py-2 text-left">Count</th>
                </tr>
              </thead>
              <tbody>
                {data['/api/rental-diagnostic/rental-status-values']?.statuses?.map((status, i) => (
                  <tr key={i} className="border-t">
                    <td className="px-4 py-2">{status.RentalStatus || '(null)'}</td>
                    <td className="px-4 py-2">{status.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Problem Units Analysis */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Problem Units (Manager's Sold List)</h2>
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left">Unit</th>
                  <th className="px-4 py-2 text-left">Status</th>
                  <th className="px-4 py-2 text-left">Dept</th>
                  <th className="px-4 py-2 text-left">Deleted</th>
                  <th className="px-4 py-2 text-left">Customer</th>
                  <th className="px-4 py-2 text-left">Last Rental</th>
                </tr>
              </thead>
              <tbody>
                {data['/api/rental-diagnostic/problem-units']?.units_data?.map((unit, i) => (
                  <tr key={i} className="border-t">
                    <td className="px-4 py-2">{unit.UnitNo}</td>
                    <td className="px-4 py-2">{unit.RentalStatus}</td>
                    <td className="px-4 py-2">{unit.InventoryDept}</td>
                    <td className="px-4 py-2">{unit.DeletionTime ? 'Yes' : 'No'}</td>
                    <td className="px-4 py-2">{unit.CustomerNo}</td>
                    <td className="px-4 py-2">{unit.LastRentalMonth || 'Never'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        
        {data['/api/rental-diagnostic/problem-units']?.patterns && (
          <div className="mt-4 p-4 bg-yellow-50 rounded">
            <h3 className="font-semibold mb-2">Patterns Found:</h3>
            <pre className="text-sm">
              {JSON.stringify(data['/api/rental-diagnostic/problem-units'].patterns, null, 2)}
            </pre>
          </div>
        )}
      </div>

      {/* Equipment Removed Check */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Equipment Removed Analysis</h2>
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-semibold mb-2">Checking if sold units are in EquipmentRemoved view:</h3>
          
          {data['/api/rental-diagnostic/check-equipment-removed']?.equipment_removed_records?.length > 0 ? (
            <div className="mb-4">
              <p className="text-green-600 mb-2">Found in EquipmentRemoved:</p>
              <pre className="text-sm bg-gray-100 p-2 rounded">
                {JSON.stringify(data['/api/rental-diagnostic/check-equipment-removed'].equipment_removed_records, null, 2)}
              </pre>
            </div>
          ) : (
            <p className="text-red-600 mb-4">No units found in EquipmentRemoved view</p>
          )}
          
          <h3 className="font-semibold mb-2">Current status in Equipment table:</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left">Unit</th>
                  <th className="px-4 py-2 text-left">RentalStatus</th>
                  <th className="px-4 py-2 text-left">InventoryDept</th>
                  <th className="px-4 py-2 text-left">Customer</th>
                </tr>
              </thead>
              <tbody>
                {data['/api/rental-diagnostic/check-equipment-removed']?.current_equipment_status?.map((unit, i) => (
                  <tr key={i} className="border-t">
                    <td className="px-4 py-2">{unit.UnitNo}</td>
                    <td className="px-4 py-2">{unit.RentalStatus || 'null'}</td>
                    <td className="px-4 py-2">{unit.InventoryDept}</td>
                    <td className="px-4 py-2">{unit.Customer ? 'Yes' : 'No'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Units on Hold */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Units on Hold Analysis</h2>
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left">Unit</th>
                  <th className="px-4 py-2 text-left">Make/Model</th>
                  <th className="px-4 py-2 text-left">Customer</th>
                  <th className="px-4 py-2 text-left">Location</th>
                  <th className="px-4 py-2 text-left">Last Rental</th>
                  <th className="px-4 py-2 text-left">Current Month Days</th>
                  <th className="px-4 py-2 text-left">YTD Revenue</th>
                </tr>
              </thead>
              <tbody>
                {data['/api/rental-diagnostic/units-on-hold']?.units?.map((unit, i) => (
                  <tr key={i} className="border-t">
                    <td className="px-4 py-2">{unit.UnitNo}</td>
                    <td className="px-4 py-2">{unit.Make} {unit.Model}</td>
                    <td className="px-4 py-2">{unit.CustomerName || unit.CustomerNo || 'None'}</td>
                    <td className="px-4 py-2">{unit.Location}</td>
                    <td className="px-4 py-2">{unit.LastRentalMonth || 'Never'}</td>
                    <td className="px-4 py-2">{unit.CurrentMonthDaysRented || 0}</td>
                    <td className="px-4 py-2">${unit.RentalYTD || 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        
        {data['/api/rental-diagnostic/units-on-hold']?.units && (
          <div className="mt-4 p-4 bg-yellow-50 rounded">
            <h3 className="font-semibold mb-2">Analysis:</h3>
            <p className="text-sm">
              Total units on hold: {data['/api/rental-diagnostic/units-on-hold'].total_on_hold}
            </p>
            <p className="text-sm mt-2">
              These units have RentalStatus = 'Hold' which may indicate they are being held for a specific customer or undergoing maintenance/inspection.
            </p>
          </div>
        )}
      </div>

      {/* Raw JSON for debugging */}
      <details className="mt-8">
        <summary className="cursor-pointer text-blue-600 hover:text-blue-800">
          Show Raw JSON Data
        </summary>
        <pre className="mt-4 p-4 bg-gray-100 rounded overflow-x-auto text-xs">
          {JSON.stringify(data, null, 2)}
        </pre>
      </details>
    </div>
  );
};

export default RentalDiagnostic;