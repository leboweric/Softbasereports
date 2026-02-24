import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { apiUrl } from '@/lib/api';
// Employee mapping no longer needed - we have real names now!
import { Users, TrendingUp, Calendar, DollarSign, Package, Award, ChevronDown, ChevronUp, FileText } from 'lucide-react';

const PartsEmployeePerformance = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dateRange, setDateRange] = useState('contest');
  const [customStartDate, setCustomStartDate] = useState('2025-11-01');
  const [customEndDate, setCustomEndDate] = useState(new Date().toISOString().split('T')[0]);
  const [showCustomDates, setShowCustomDates] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [invoiceDetails, setInvoiceDetails] = useState({});
  const [loadingInvoices, setLoadingInvoices] = useState({});

  useEffect(() => {
    fetchData();
  }, [dateRange, customStartDate, customEndDate]);

  const fetchData = async () => {
    try {
      setLoading(true);
      let url;
      
      if (dateRange === 'contest') {
        // Contest period: November 1, 2025 to today
        url = apiUrl(`/api/reports/departments/parts/employee-performance?start_date=2025-11-01&end_date=${new Date().toISOString().split('T')[0]}`);
      } else if (dateRange === 'custom') {
        url = apiUrl(`/api/reports/departments/parts/employee-performance?start_date=${customStartDate}&end_date=${customEndDate}`);
      } else {
        url = apiUrl(`/api/reports/departments/parts/employee-performance?days=${dateRange}`);
      }
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch employee performance data');
      }

      const result = await response.json();
      
      // No longer need to map names - they come directly from the backend!
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchInvoiceDetails = async (employeeId) => {
    if (invoiceDetails[employeeId]) {
      // Already have the data, just toggle
      return;
    }

    setLoadingInvoices(prev => ({ ...prev, [employeeId]: true }));
    
    try {
      let url;
      if (dateRange === 'contest') {
        url = apiUrl(`/api/reports/departments/parts/employee-invoice-details?employee_id=${employeeId}&start_date=2025-11-01&end_date=${new Date().toISOString().split('T')[0]}`);
      } else if (dateRange === 'custom') {
        url = apiUrl(`/api/reports/departments/parts/employee-invoice-details?employee_id=${employeeId}&start_date=${customStartDate}&end_date=${customEndDate}`);
      } else {
        url = apiUrl(`/api/reports/departments/parts/employee-invoice-details?employee_id=${employeeId}&days=${dateRange}`);
      }
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch invoice details');
      }

      const result = await response.json();
      setInvoiceDetails(prev => ({ ...prev, [employeeId]: result.invoices }));
    } catch (err) {
      console.error('Error fetching invoice details:', err);
      setInvoiceDetails(prev => ({ ...prev, [employeeId]: [] }));
    } finally {
      setLoadingInvoices(prev => ({ ...prev, [employeeId]: false }));
    }
  };

  const toggleEmployeeDetails = async (employeeId) => {
    if (selectedEmployee === employeeId) {
      setSelectedEmployee(null);
    } else {
      setSelectedEmployee(employeeId);
      await fetchInvoiceDetails(employeeId);
    }
  };

  const exportToCSV = () => {
    if (!data || !data.employees) return;

    const headers = ['Employee Name', 'Total Invoices', 'Days Worked', 'Total Sales', 'Avg Invoice Value', 'Avg Daily Sales', 'Avg Daily Invoices', '% of Total', 'Last Sale Date', 'Days Since Last Sale'];
    const rows = data.employees.map(emp => [
      emp.employeeName || emp.employeeId || 'Unknown',
      emp.totalInvoices,
      emp.daysWorked,
      emp.totalSales.toFixed(2),
      emp.avgInvoiceValue.toFixed(2),
      emp.avgDailySales.toFixed(2),
      emp.avgDailyInvoices.toFixed(1),
      emp.percentOfTotal + '%',
      emp.lastSaleDate || 'N/A',
      emp.daysSinceLastSale
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `parts-employee-performance-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="animate-pulse">Loading employee performance data...</div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-red-500">Error: {error}</div>
        </CardContent>
      </Card>
    );
  }

  if (!data) return null;

  const { employees, summary } = data;

  return (
    <div className="space-y-6">
      {/* Contest Leaderboard Banner - Only show for contest period */}
      {dateRange === 'contest' && data && data.employees.length > 0 && (
        <Card className="bg-gradient-to-r from-amber-50 to-yellow-50 border-amber-300">
          <CardHeader>
            <CardTitle className="text-xl flex items-center gap-2">
              <span className="text-2xl">🏆</span>
              Parts Counter Sales Contest (CSTPRT Only)
              <span className="text-sm font-normal text-gray-600 ml-2">
                (Nov 1 - Today)
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {data.employees.slice(0, 3).map((emp, index) => (
                <div
                  key={emp.employeeId}
                  className={`p-4 rounded-lg text-center ${
                    index === 0 ? 'bg-yellow-100 border-2 border-yellow-400' :
                    index === 1 ? 'bg-gray-100 border-2 border-gray-400' :
                    'bg-orange-100 border-2 border-orange-400'
                  }`}
                >
                  <div className="text-3xl mb-2">
                    {index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉'}
                  </div>
                  <div className="font-bold text-lg">
                    {emp.employeeName || emp.employeeId || 'Unknown'}
                  </div>
                  <div className="text-2xl font-bold mt-2">
                    ${emp.totalSales.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                  </div>
                  <div className="text-sm text-gray-600 mt-1">
                    {emp.totalInvoices} sales • {emp.percentOfTotal}% of total
                  </div>
                  <div className="text-xs text-gray-500 mt-2">
                    Avg/Day: ${emp.avgDailySales.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Employees</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.totalEmployees}</div>
            <p className="text-xs text-muted-foreground">Active in period</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Parts Sales</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${summary.totalSales.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</div>
            <p className="text-xs text-muted-foreground">{summary.period}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Top Performer</CardTitle>
            <Award className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold">
              {summary.topPerformer?.employeeName || summary.topPerformer?.employeeId || 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              ${summary.topPerformer?.totalSales.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })} in sales
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg per Employee</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${(summary.totalEmployees > 0 ? (summary.totalSales / summary.totalEmployees) : 0).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
            </div>
            <p className="text-xs text-muted-foreground">Average sales</p>
          </CardContent>
        </Card>
      </div>

      {/* Employee Performance Table */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle>Parts Counter Performance (CSTPRT Sale Code)</CardTitle>
              {dateRange === 'contest' && (
                <p className="text-sm text-amber-600 font-semibold mt-1">
                  🏆 Contest Period: November 1, 2025 - Today (Counter Sales Only)
                </p>
              )}
            </div>
            <div className="flex gap-2 items-center">
              <select
                value={dateRange}
                onChange={(e) => {
                  setDateRange(e.target.value);
                  setShowCustomDates(e.target.value === 'custom');
                }}
                className="px-3 py-1 border rounded-md text-sm"
              >
                <option value="contest">🏆 Contest (Nov 1 - Today)</option>
                <option value="7">Last 7 Days</option>
                <option value="30">Last 30 Days</option>
                <option value="60">Last 60 Days</option>
                <option value="90">Last 90 Days</option>
                <option value="365">Last Year</option>
                <option value="custom">Custom Dates</option>
              </select>
              
              {showCustomDates && (
                <>
                  <input
                    type="date"
                    value={customStartDate}
                    onChange={(e) => setCustomStartDate(e.target.value)}
                    className="px-2 py-1 border rounded-md text-sm"
                  />
                  <span className="text-sm">to</span>
                  <input
                    type="date"
                    value={customEndDate}
                    onChange={(e) => setCustomEndDate(e.target.value)}
                    className="px-2 py-1 border rounded-md text-sm"
                  />
                </>
              )}
              
              <button
                onClick={exportToCSV}
                className="px-3 py-1 bg-blue-500 text-white rounded-md hover:bg-blue-600 text-sm"
              >
                Export CSV
              </button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Rank</th>
                  <th className="text-left p-2">Employee</th>
                  <th className="text-right p-2">Total Sales</th>
                  <th className="text-right p-2">% of Total</th>
                  <th className="text-right p-2">Invoices</th>
                  <th className="text-right p-2">Days Worked</th>
                  <th className="text-right p-2">Avg/Day</th>
                  <th className="text-right p-2">Avg Invoice</th>
                  <th className="text-right p-2">Last Sale</th>
                  <th className="text-right p-2">Days Inactive</th>
                  <th className="text-center p-2" width="40">Details</th>
                </tr>
              </thead>
              <tbody>
                {employees.map((emp, index) => (
                  <React.Fragment key={emp.employeeId}>
                  <tr 
                    className={`border-b hover:bg-gray-50 cursor-pointer ${index === 0 ? 'bg-green-50' : ''} ${selectedEmployee === emp.employeeId ? 'bg-blue-50' : ''}`}
                    onClick={() => toggleEmployeeDetails(emp.employeeId)}
                  >
                    <td className="p-2">
                      {index === 0 && <span className="text-xl">🏆</span>}
                      {index === 1 && <span className="text-xl">🥈</span>}
                      {index === 2 && <span className="text-xl">🥉</span>}
                      {index > 2 && <span className="text-gray-500">{index + 1}</span>}
                    </td>
                    <td className="p-2 font-medium">
                      <div className="font-semibold">{emp.employeeName || emp.employeeId || 'Unknown'}</div>
                    </td>
                    <td className="p-2 text-right font-semibold">
                      ${emp.totalSales.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="p-2 text-right">
                      <span className={`px-2 py-1 rounded text-xs ${
                        emp.percentOfTotal >= 20 ? 'bg-green-100 text-green-800' :
                        emp.percentOfTotal >= 10 ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {emp.percentOfTotal}%
                      </span>
                    </td>
                    <td className="p-2 text-right">{emp.totalInvoices}</td>
                    <td className="p-2 text-right">{emp.daysWorked}</td>
                    <td className="p-2 text-right">
                      ${emp.avgDailySales.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="p-2 text-right">
                      ${emp.avgInvoiceValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="p-2 text-right text-xs">
                      {emp.lastSaleDate ? new Date(emp.lastSaleDate).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="p-2 text-right">
                      {emp.daysSinceLastSale > 0 && (
                        <span className={`px-2 py-1 rounded text-xs ${
                          emp.daysSinceLastSale > 7 ? 'bg-red-100 text-red-800' :
                          emp.daysSinceLastSale > 3 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-green-100 text-green-800'
                        }`}>
                          {emp.daysSinceLastSale}d
                        </span>
                      )}
                    </td>
                    <td className="p-2 text-center">
                      {selectedEmployee === emp.employeeId ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </td>
                  </tr>
                  
                  {/* Invoice Details Row */}
                  {selectedEmployee === emp.employeeId && (
                    <tr>
                      <td colSpan="11" className="p-0">
                        <div className="bg-gray-50 p-4 border-t border-b">
                          <div className="flex items-center gap-2 mb-3">
                            <FileText className="h-5 w-5 text-blue-600" />
                            <h4 className="font-semibold text-lg">
                              Invoice Details for {emp.employeeName || emp.employeeId || 'Unknown'}
                            </h4>
                            <span className="text-sm text-gray-500">
                              ({invoiceDetails[emp.employeeId]?.length || 0} invoices)
                            </span>
                          </div>
                          
                          {loadingInvoices[emp.employeeId] ? (
                            <div className="text-center py-4">Loading invoice details...</div>
                          ) : invoiceDetails[emp.employeeId] && invoiceDetails[emp.employeeId].length > 0 ? (
                            <div className="overflow-x-auto">
                              <table className="w-full text-xs">
                                <thead>
                                  <tr className="border-b bg-white">
                                    <th className="text-left p-2">Invoice #</th>
                                    <th className="text-left p-2">Date/Time</th>
                                    <th className="text-left p-2">Bill To</th>
                                    <th className="text-left p-2">Customer Name</th>
                                    <th className="text-right p-2">Parts (Tax)</th>
                                    <th className="text-right p-2">Parts (Non-Tax)</th>
                                    <th className="text-right p-2 font-semibold">Total Parts</th>
                                    <th className="text-right p-2">Labor</th>
                                    <th className="text-right p-2">Misc</th>
                                    <th className="text-right p-2">Grand Total</th>
                                    <th className="text-center p-2">Sale Code</th>
                                    <th className="text-left p-2">Modified By</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {invoiceDetails[emp.employeeId].map((inv, idx) => (
                                    <tr key={inv.invoiceNo} className={`border-b ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}>
                                      <td className="p-2 font-mono">{inv.invoiceNo}</td>
                                      <td className="p-2">{inv.invoiceDate}</td>
                                      <td className="p-2">{inv.billTo}</td>
                                      <td className="p-2">{inv.billToName}</td>
                                      <td className="p-2 text-right">${inv.partsTaxable.toFixed(2)}</td>
                                      <td className="p-2 text-right">${inv.partsNonTax.toFixed(2)}</td>
                                      <td className="p-2 text-right font-semibold bg-green-50">
                                        ${inv.totalParts.toFixed(2)}
                                      </td>
                                      <td className="p-2 text-right">
                                        {inv.totalLabor > 0 ? `$${inv.totalLabor.toFixed(2)}` : '-'}
                                      </td>
                                      <td className="p-2 text-right">
                                        {inv.totalMisc > 0 ? `$${inv.totalMisc.toFixed(2)}` : '-'}
                                      </td>
                                      <td className="p-2 text-right">${inv.grandTotal.toFixed(2)}</td>
                                      <td className="p-2 text-center">
                                        <span className="px-1 py-0.5 bg-blue-100 text-blue-800 rounded text-xs">
                                          {inv.saleCode || '-'}
                                        </span>
                                      </td>
                                      <td className="p-2 text-xs">{inv.lastModifiedBy || inv.employeeId}</td>
                                    </tr>
                                  ))}
                                  <tr className="font-semibold bg-yellow-50">
                                    <td colSpan="6" className="p-2 text-right">Total:</td>
                                    <td className="p-2 text-right bg-green-100">
                                      ${invoiceDetails[emp.employeeId].reduce((sum, inv) => sum + inv.totalParts, 0).toFixed(2)}
                                    </td>
                                    <td className="p-2 text-right">
                                      ${invoiceDetails[emp.employeeId].reduce((sum, inv) => sum + inv.totalLabor, 0).toFixed(2)}
                                    </td>
                                    <td className="p-2 text-right">
                                      ${invoiceDetails[emp.employeeId].reduce((sum, inv) => sum + inv.totalMisc, 0).toFixed(2)}
                                    </td>
                                    <td className="p-2 text-right">
                                      ${invoiceDetails[emp.employeeId].reduce((sum, inv) => sum + inv.grandTotal, 0).toFixed(2)}
                                    </td>
                                    <td colSpan="2"></td>
                                  </tr>
                                </tbody>
                              </table>
                            </div>
                          ) : (
                            <div className="text-center py-4 text-gray-500">No invoice details available</div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>

          {/* Performance Insights */}
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h4 className="font-semibold text-sm mb-2">Performance Insights</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
              <div>
                <span className="font-medium">Top 3 Employees:</span> Generate {
                  employees.slice(0, 3).reduce((sum, emp) => sum + emp.percentOfTotal, 0).toFixed(1)
                }% of total sales
              </div>
              <div>
                <span className="font-medium">Average Daily Sales:</span> ${
                  (employees.reduce((sum, emp) => sum + emp.daysWorked, 0) > 0 ? (summary.totalSales / employees.reduce((sum, emp) => sum + emp.daysWorked, 0)) : 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                } per employee/day
              </div>
              <div>
                <span className="font-medium">Most Productive:</span> {
                  employees.reduce((best, emp) => emp.avgDailyInvoices > best.avgDailyInvoices ? emp : best, employees[0])?.employeeId
                } ({employees[0]?.avgDailyInvoices.toFixed(1)} invoices/day)
              </div>
              <div>
                <span className="font-medium">Highest Avg Invoice:</span> {
                  employees.reduce((best, emp) => emp.avgInvoiceValue > best.avgInvoiceValue ? emp : best, employees[0])?.employeeId
                } (${employees.reduce((best, emp) => emp.avgInvoiceValue > best.avgInvoiceValue ? emp : best, employees[0])?.avgInvoiceValue.toFixed(2)})
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PartsEmployeePerformance;