import { useState, useEffect, useRef } from 'react';
import { FileSpreadsheet, Download, Calendar, RefreshCw, ChevronDown, ChevronRight, Loader2 } from 'lucide-react';
import axios from 'axios';
import { apiUrl } from '../lib/api';

const PLReport = ({ user, organization }) => {
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [data, setData] = useState(null);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [error, setError] = useState(null);
  const [expandedDepts, setExpandedDepts] = useState({});
  const [viewMode, setViewMode] = useState('mtd'); // 'mtd', 'ytd', 'custom'

  // Initialize with current month
  useEffect(() => {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const firstDay = `${year}-${month}-01`;
    const lastDay = new Date(year, now.getMonth() + 1, 0).getDate();
    const lastDayStr = `${year}-${month}-${String(lastDay).padStart(2, '0')}`;

    setStartDate(firstDay);
    setEndDate(lastDayStr);
  }, []);

  // Auto-fetch when dates are set (debounced to avoid race conditions when both dates change)
  const fetchTimerRef = useRef(null);
  useEffect(() => {
    if (startDate && endDate) {
      if (fetchTimerRef.current) clearTimeout(fetchTimerRef.current);
      fetchTimerRef.current = setTimeout(() => {
        fetchData(startDate, endDate);
      }, 300);
    }
    return () => { if (fetchTimerRef.current) clearTimeout(fetchTimerRef.current); };
  }, [startDate, endDate]);

  const setMTD = () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const firstDay = `${year}-${month}-01`;
    const lastDay = new Date(year, now.getMonth() + 1, 0).getDate();
    const lastDayStr = `${year}-${month}-${String(lastDay).padStart(2, '0')}`;

    setStartDate(firstDay);
    setEndDate(lastDayStr);
    setViewMode('mtd');
  };

  const setYTD = () => {
    const now = new Date();
    const year = now.getFullYear();
    setStartDate(`${year}-01-01`);
    setEndDate(`${year}-12-31`);
    setViewMode('ytd');
  };

  const fetchControllerRef = useRef(null);
  const fetchData = async (sd, ed) => {
    const start = sd || startDate;
    const end = ed || endDate;
    if (!start || !end) {
      setError('Please select a date range');
      return;
    }

    // Cancel any in-flight request
    if (fetchControllerRef.current) fetchControllerRef.current.abort();
    const controller = new AbortController();
    fetchControllerRef.current = controller;

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');

      const response = await axios.get(
        apiUrl('/api/reports/pl'),
        {
          params: {
            start_date: start,
            end_date: end,
            detail: false, // Set to true if you want account-level detail
            refresh: true
          },
          headers: { Authorization: `Bearer ${token}` },
          signal: controller.signal
        }
      );

      setData(response.data);
    } catch (err) {
      if (err.name === 'CanceledError' || err.code === 'ERR_CANCELED') return;
      console.error('Error fetching P&L data:', err);
      setError(err.response?.data?.error || 'Failed to fetch P&L data');
    } finally {
      setLoading(false);
    }
  };

  const toggleDepartment = (deptKey) => {
    setExpandedDepts(prev => ({
      ...prev,
      [deptKey]: !prev[deptKey]
    }));
  };

  const formatCurrency = (value) => {
    if (value === null || value === undefined) return '$0.00';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const formatPercent = (value) => {
    if (value === null || value === undefined || isNaN(value)) return '0.00%';
    return `${value.toFixed(2)}%`;
  };

  const departmentOrder = [
    'new_equipment',
    'used_equipment',
    'parts',
    'service',
    'rental',
    'transportation',
    'administrative'
  ];

  return (
    <div>
      {/* Controls */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex flex-wrap items-center gap-4">
          {/* View Mode Buttons */}
          <div className="flex gap-2">
            <button
              onClick={setMTD}
              className={`px-4 py-2 rounded-md text-sm font-medium ${viewMode === 'mtd'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
            >
              MTD
            </button>
            <button
              onClick={setYTD}
              className={`px-4 py-2 rounded-md text-sm font-medium ${viewMode === 'ytd'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
            >
              YTD
            </button>
          </div>

          {/* Date Inputs */}
          <div className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-gray-400" />
            <input
              type="date"
              value={startDate}
              onChange={(e) => {
                setStartDate(e.target.value);
                setViewMode('custom');
              }}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
            <span className="text-gray-500">to</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => {
                setEndDate(e.target.value);
                setViewMode('custom');
              }}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
          </div>

          {/* Refresh Button */}
          <button
            onClick={() => fetchData()}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 text-sm font-medium"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>

          {/* Strande Export Button - BMH only (matches accounting firm format) */}
          {organization && organization.database_schema !== 'ind004' && (
            <button
              disabled={exporting}
              onClick={async () => {
                setExporting(true);
                try {
                  const [year, month] = startDate.split('-').map(Number);
                  const token = localStorage.getItem('token');
                  const response = await axios.get(
                    apiUrl('/api/reports/pl/detailed/export'),
                    {
                      params: { month, year },
                      headers: { Authorization: `Bearer ${token}` },
                      responseType: 'blob'
                    }
                  );

                  const url = window.URL.createObjectURL(new Blob([response.data]));
                  const link = document.createElement('a');
                  link.href = url;
                  const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
                  link.setAttribute('download', `ProfitLoss_Detailed_${monthNames[month-1]}${year}.xlsx`);
                  document.body.appendChild(link);
                  link.click();
                  link.remove();
                  window.URL.revokeObjectURL(url);
                } catch (error) {
                  console.error('Error downloading detailed Excel file:', error);
                  alert('Failed to download detailed Excel file');
                } finally {
                  setExporting(false);
                }
              }}
              className={`flex items-center gap-2 px-4 py-2 text-white rounded-md text-sm font-medium ${
                exporting
                  ? 'bg-emerald-400 cursor-not-allowed'
                  : 'bg-emerald-600 hover:bg-emerald-700'
              }`}
              title="Export with department tabs and GL account detail (matches accounting firm format)"
            >
              {exporting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <FileSpreadsheet className="h-4 w-4" />
              )}
              {exporting ? 'Exporting...' : 'Strande'}
            </button>
          )}

          {/* Detailed Export Button - IPS only (EVO template) */}
          {organization && organization.database_schema === 'ind004' && (
            <button
              disabled={exporting}
              onClick={async () => {
                setExporting(true);
                try {
                  const [year, month] = startDate.split('-').map(Number);
                  const token = localStorage.getItem('token');
                  const response = await axios.get(
                    apiUrl('/api/reports/pl/evo/export'),
                    {
                      params: { month, year },
                      headers: { Authorization: `Bearer ${token}` },
                      responseType: 'blob'
                    }
                  );

                  const url = window.URL.createObjectURL(new Blob([response.data]));
                  const link = document.createElement('a');
                  link.href = url;
                  link.setAttribute('download', `${String(month).padStart(2, '0')}-${year}EVO.xlsx`);
                  document.body.appendChild(link);
                  link.click();
                  link.remove();
                  window.URL.revokeObjectURL(url);
                } catch (error) {
                  console.error('Error downloading EVO Excel file:', error);
                  if (error.response && error.response.status === 404) {
                    alert('No EVO template configured for this organization. Please contact support.');
                  } else {
                    alert('Failed to download EVO Excel file');
                  }
                } finally {
                  setExporting(false);
                }
              }}
              className={`flex items-center gap-2 px-4 py-2 text-white rounded-md text-sm font-medium ${
                exporting
                  ? 'bg-emerald-400 cursor-not-allowed'
                  : 'bg-emerald-600 hover:bg-emerald-700'
              }`}
              title="Export using your organization's custom detailed template"
            >
              {exporting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <FileSpreadsheet className="h-4 w-4" />
              )}
              {exporting ? 'Exporting...' : 'Detailed Export'}
            </button>
          )}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <RefreshCw className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading P&L data...</p>
        </div>
      )}

      {/* P&L Report */}
      {!loading && data && data.consolidated && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {/* Header */}
          <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-gray-900">Profit & Loss Statement</h2>
                <p className="text-sm text-gray-600 mt-1">
                  {startDate ? new Date(startDate + 'T00:00:00').toLocaleDateString() : ''} - {endDate ? new Date(endDate + 'T00:00:00').toLocaleDateString() : ''}
                </p>
              </div>
              <button
                className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-md hover:bg-gray-50 text-sm font-medium"
              >
                <Download className="h-4 w-4" />
                Export
              </button>
            </div>
          </div>

          {/* Consolidated Summary */}
          <div className="px-6 py-4 bg-blue-50 border-b border-blue-100">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Consolidated Summary</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-600">Total Revenue</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(data.consolidated.revenue)}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Total COGS</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(data.consolidated.cogs)}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Gross Profit</p>
                <p className="text-2xl font-bold text-green-600">
                  {formatCurrency(data.consolidated.gross_profit)}
                </p>
                <p className="text-sm text-gray-600">
                  {formatPercent(data.consolidated.gross_margin)} margin
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Operating Profit</p>
                <p className="text-2xl font-bold text-blue-600">
                  {formatCurrency(data.consolidated.operating_profit)}
                </p>
                <p className="text-sm text-gray-600">
                  {formatPercent(data.consolidated.operating_margin)} margin
                </p>
              </div>
            </div>
          </div>

          {/* Department Details */}
          <div className="px-6 py-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Department Breakdown</h3>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Department
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Revenue
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      COGS
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Gross Profit
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      GP Margin
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {departmentOrder.map((deptKey) => {
                    const dept = data.departments[deptKey];
                    if (!dept) return null;

                    return (
                      <tr key={deptKey} className="hover:bg-gray-50">
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="text-sm font-medium text-gray-900">
                              {dept.dept_name}
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-900">
                          {formatCurrency(dept.revenue)}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-900">
                          {formatCurrency(dept.cogs)}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-medium text-gray-900">
                          {formatCurrency(dept.gross_profit)}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-600">
                          {formatPercent(dept.gross_margin)}
                        </td>
                      </tr>
                    );
                  })}

                  {/* Total Row */}
                  <tr className="bg-gray-100 font-bold">
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                      Total
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-900">
                      {formatCurrency(data.consolidated.revenue)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-900">
                      {formatCurrency(data.consolidated.cogs)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-900">
                      {formatCurrency(data.consolidated.gross_profit)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-900">
                      {formatPercent(data.consolidated.gross_margin)}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Operating Expenses */}
          <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Operating Expenses</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.expenses && Object.entries(data.expenses).map(([category, amount]) => {
                if (category === 'total_expenses') return null;

                const categoryLabels = {
                  depreciation: 'Depreciation',
                  salaries_wages: 'Salaries & Wages',
                  payroll_benefits: 'Payroll Benefits',
                  rent_facilities: 'Rent & Facilities',
                  utilities: 'Utilities',
                  insurance: 'Insurance',
                  marketing: 'Marketing & Advertising',
                  professional_fees: 'Professional Fees',
                  office_admin: 'Office & Administrative',
                  vehicle_equipment: 'Vehicle & Equipment',
                  interest_finance: 'Interest & Finance',
                  other_expenses: 'Other Expenses'
                };

                return (
                  <div key={category} className="bg-white p-3 rounded border border-gray-200">
                    <p className="text-xs text-gray-600">{categoryLabels[category]}</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {formatCurrency(amount)}
                    </p>
                  </div>
                );
              })}
            </div>

            <div className="mt-4 pt-4 border-t border-gray-300">
              <div className="flex justify-between items-center">
                <span className="text-base font-semibold text-gray-900">Total Operating Expenses</span>
                <span className="text-xl font-bold text-gray-900">
                  {formatCurrency(data.expenses.total_expenses)}
                </span>
              </div>
            </div>
          </div>

          {/* Bottom Line */}
          <div className="px-6 py-4 bg-blue-50 border-t border-blue-100">
            <div className="flex justify-between items-center">
              <span className="text-lg font-semibold text-gray-900">Operating Profit</span>
              <div className="text-right">
                <span className="text-2xl font-bold text-blue-600">
                  {formatCurrency(data.consolidated.operating_profit)}
                </span>
                <p className="text-sm text-gray-600">
                  {formatPercent(data.consolidated.operating_margin)} margin
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PLReport;
