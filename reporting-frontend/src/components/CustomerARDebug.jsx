import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiUrl } from '@/lib/api';

export default function CustomerARDebug() {
  const [debugData, setDebugData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDebugData();
  }, []);

  const fetchDebugData = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(apiUrl('/api/reports/departments/accounting/customer-ar-debug'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch debug data');
      }

      const data = await response.json();
      setDebugData(data);
      console.log('Customer AR Debug Data:', data);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching debug data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading customer debug data...</div>;
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
      <h1 className="text-2xl font-bold">Customer AR Debug - Polaris, Grede, Owens</h1>
      
      <Card>
        <CardHeader>
          <CardTitle>Customer List</CardTitle>
        </CardHeader>
        <CardContent>
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2">Customer Number</th>
                <th className="text-left p-2">Customer Name</th>
              </tr>
            </thead>
            <tbody>
              {debugData.customer_list?.map((customer, idx) => (
                <tr key={idx} className="border-b">
                  <td className="p-2">{customer.Number}</td>
                  <td className="p-2">{customer.Name}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Customer AR Balances</CardTitle>
        </CardHeader>
        <CardContent>
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2">Customer Name</th>
                <th className="text-right p-2">Invoices Over 90</th>
                <th className="text-right p-2">Amount Over 90</th>
                <th className="text-right p-2">Total Open Invoices</th>
                <th className="text-right p-2">Total AR Balance</th>
              </tr>
            </thead>
            <tbody>
              {debugData.customer_balances?.map((balance, idx) => (
                <tr key={idx} className="border-b">
                  <td className="p-2">{balance.CustomerName}</td>
                  <td className="text-right p-2">{balance.InvoicesOver90}</td>
                  <td className="text-right p-2 text-red-600">{formatCurrency(balance.AmountOver90)}</td>
                  <td className="text-right p-2">{balance.TotalOpenInvoices}</td>
                  <td className="text-right p-2">{formatCurrency(balance.TotalARBalance)}</td>
                </tr>
              ))}
              <tr className="font-bold">
                <td className="p-2">TOTAL</td>
                <td className="text-right p-2">
                  {debugData.customer_balances?.reduce((sum, b) => sum + b.InvoicesOver90, 0)}
                </td>
                <td className="text-right p-2 text-red-600">
                  {formatCurrency(debugData.customer_balances?.reduce((sum, b) => sum + b.AmountOver90, 0) || 0)}
                </td>
                <td className="text-right p-2">
                  {debugData.customer_balances?.reduce((sum, b) => sum + b.TotalOpenInvoices, 0)}
                </td>
                <td className="text-right p-2">
                  {formatCurrency(debugData.customer_balances?.reduce((sum, b) => sum + b.TotalARBalance, 0) || 0)}
                </td>
              </tr>
            </tbody>
          </table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Invoice Details (Over 90 Days)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Customer</th>
                  <th className="text-left p-2">Invoice#</th>
                  <th className="text-left p-2">Due Date</th>
                  <th className="text-right p-2">Days Overdue</th>
                  <th className="text-right p-2">Balance</th>
                </tr>
              </thead>
              <tbody>
                {debugData.invoice_details?.map((invoice, idx) => (
                  <tr key={idx} className="border-b">
                    <td className="p-2">{invoice.CustomerName}</td>
                    <td className="p-2">{invoice.InvoiceNo}</td>
                    <td className="p-2">{invoice.Due ? new Date(invoice.Due).toLocaleDateString() : 'N/A'}</td>
                    <td className="text-right p-2">{invoice.DaysOverdue}</td>
                    <td className="text-right p-2">{formatCurrency(invoice.NetBalance)}</td>
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