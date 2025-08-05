import React, { useState, useEffect } from 'react';
import { apiUrl } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function InvoiceDiagnostic() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchDiagnostic = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        apiUrl('/api/reports/departments/service/invoice-diagnostic?start_date=2025-07-29&end_date=2025-08-01'),
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDiagnostic();
  }, []);

  if (loading) return <div>Loading diagnostic data...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!data) return <div>No data available</div>;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Invoice Diagnostic for July 29 - Aug 1, 2025</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold">All Departments Total:</h3>
              {data.total_all_departments && (
                <ul className="ml-4">
                  <li>Total Invoices: {data.total_all_departments.total_invoices}</li>
                  <li>Unique Customers: {data.total_all_departments.unique_customers}</li>
                  <li>Total Revenue: ${data.total_all_departments.total_revenue?.toLocaleString()}</li>
                </ul>
              )}
            </div>

            <div>
              <h3 className="font-semibold">Service Department Only:</h3>
              {data.total_service_only && (
                <ul className="ml-4">
                  <li>Service Invoices: {data.total_service_only.service_invoices}</li>
                  <li>Service Customers: {data.total_service_only.service_customers}</li>
                  <li>Service Revenue: ${data.total_service_only.service_revenue?.toLocaleString()}</li>
                </ul>
              )}
            </div>

            <div>
              <h3 className="font-semibold">Breakdown by Sale Code:</h3>
              <div className="max-h-60 overflow-y-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left">Sale Code</th>
                      <th className="text-left">Dept</th>
                      <th className="text-right">Invoices</th>
                      <th className="text-right">Customers</th>
                      <th className="text-right">Revenue</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.breakdown_by_sale_code?.map((row, idx) => (
                      <tr key={idx} className="border-b">
                        <td>{row.SaleCode || 'N/A'}</td>
                        <td>{row.SaleDept || 'N/A'}</td>
                        <td className="text-right">{row.invoice_count}</td>
                        <td className="text-right">{row.customer_count}</td>
                        <td className="text-right">${row.total_revenue?.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div>
              <h3 className="font-semibold">Service Customers ({data.service_customer_count} total):</h3>
              <div className="max-h-60 overflow-y-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left">Customer</th>
                      <th className="text-right">Invoices</th>
                      <th className="text-right">Revenue</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.service_customers_list?.slice(0, 20).map((customer, idx) => (
                      <tr key={idx} className="border-b">
                        <td>{customer.BillToName || customer.BillTo}</td>
                        <td className="text-right">{customer.invoice_count}</td>
                        <td className="text-right">${customer.total_revenue?.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {data.service_customers_list?.length > 20 && (
                  <p className="text-sm text-gray-500 mt-2">
                    Showing first 20 of {data.service_customers_list.length} customers
                  </p>
                )}
              </div>
            </div>
          </div>

          <Button onClick={fetchDiagnostic} className="mt-4">
            Refresh Diagnostic
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}