import React, { useState, useEffect } from 'react';
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown, 
  CreditCard, 
  RefreshCw, 
  Link, 
  Unlink,
  FileText,
  Users,
  AlertCircle,
  CheckCircle,
  Clock
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || '';

const VitalQuickBooksDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [connected, setConnected] = useState(false);
  const [dashboardData, setDashboardData] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  const checkConnectionStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/vital/quickbooks/status`, {
        headers: getAuthHeaders()
      });
      const data = await response.json();
      setConnected(data.connected);
      return data.connected;
    } catch (err) {
      console.error('Error checking QB status:', err);
      setConnected(false);
      return false;
    }
  };

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const isConnected = await checkConnectionStatus();
      
      if (!isConnected) {
        setLoading(false);
        return;
      }

      const response = await fetch(`${API_BASE}/api/vital/quickbooks/dashboard`, {
        headers: getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error('Failed to fetch QuickBooks data');
      }

      const result = await response.json();
      console.log('QuickBooks Dashboard Data:', result.data);
      setDashboardData(result.data);
      setLastUpdated(new Date().toLocaleString());
    } catch (err) {
      console.error('Error fetching QB dashboard:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/vital/quickbooks/connect`, {
        headers: getAuthHeaders()
      });
      const data = await response.json();
      
      if (data.authorization_url) {
        window.location.href = data.authorization_url;
      }
    } catch (err) {
      console.error('Error connecting to QB:', err);
      setError('Failed to initiate QuickBooks connection');
    }
  };

  const handleDisconnect = async () => {
    try {
      await fetch(`${API_BASE}/api/vital/quickbooks/disconnect`, {
        method: 'POST',
        headers: getAuthHeaders()
      });
      setConnected(false);
      setDashboardData(null);
    } catch (err) {
      console.error('Error disconnecting QB:', err);
    }
  };

  useEffect(() => {
    // Check URL params for OAuth callback
    const urlParams = new URLSearchParams(window.location.search);
    const isConnected = urlParams.get('connected');
    const error = urlParams.get('error');

    if (error) {
      setError(`QuickBooks connection failed: ${error}`);
    }

    if (isConnected === 'true') {
      // Clear URL params
      window.history.replaceState({}, document.title, window.location.pathname);
    }

    fetchDashboardData();
  }, []);

  const formatCurrency = (value) => {
    if (!value && value !== 0) return '$0';
    const num = parseFloat(value);
    if (isNaN(num)) return '$0';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(num);
  };

  /**
   * Extract financial metrics from P&L report
   * QuickBooks P&L structure:
   * - Income section (Total Income)
   * - Cost of Goods Sold section
   * - Gross Profit
   * - Expenses section (Total Expenses)
   * - Net Operating Income
   * - Other Income/Expenses
   * - Net Income
   */
  const extractFinancialMetrics = (plData) => {
    if (!plData || !plData.sections) {
      console.log('No P&L sections found');
      return { revenue: 0, expenses: 0, netIncome: 0 };
    }
    
    let revenue = 0;
    let costOfGoodsSold = 0;
    let expenses = 0;
    let netIncome = 0;
    let grossProfit = 0;

    console.log('P&L Sections:', plData.sections.map(s => ({ name: s.name, total: s.total })));

    plData.sections.forEach(section => {
      const name = (section.name || '').toLowerCase().trim();
      const total = parseFloat(section.total) || 0;

      // Match Income/Revenue sections
      if (name === 'income' || name === 'total income' || name === 'revenue' || name === 'total revenue') {
        revenue = Math.abs(total);
        console.log('Found Revenue:', revenue);
      }
      // Match Cost of Goods Sold
      else if (name.includes('cost of goods sold') || name === 'cogs' || name.includes('cost of sales')) {
        costOfGoodsSold = Math.abs(total);
        console.log('Found COGS:', costOfGoodsSold);
      }
      // Match Gross Profit
      else if (name === 'gross profit' || name === 'gross margin') {
        grossProfit = total;
        console.log('Found Gross Profit:', grossProfit);
      }
      // Match Expenses sections
      else if (name === 'expenses' || name === 'total expenses' || name === 'operating expenses') {
        expenses = Math.abs(total);
        console.log('Found Expenses:', expenses);
      }
      // Match Net Income
      else if (name === 'net income' || name === 'net profit' || name === 'net operating income' || name === 'net earnings') {
        netIncome = total;
        console.log('Found Net Income:', netIncome);
      }

      // Also check nested rows for totals
      if (section.rows) {
        section.rows.forEach(row => {
          const rowName = (row.name || '').toLowerCase().trim();
          const rowValue = parseFloat(row.value) || 0;
          
          if (rowName === 'total income' || rowName === 'total revenue') {
            if (revenue === 0) revenue = Math.abs(rowValue);
          }
          if (rowName === 'total expenses') {
            if (expenses === 0) expenses = Math.abs(rowValue);
          }
          if (rowName === 'net income') {
            if (netIncome === 0) netIncome = rowValue;
          }
        });
      }
    });

    // Total expenses should include COGS + Operating Expenses
    const totalExpenses = costOfGoodsSold + expenses;

    // Calculate net income if not found
    if (netIncome === 0 && revenue > 0) {
      netIncome = revenue - totalExpenses;
    }

    console.log('Final metrics:', { revenue, expenses: totalExpenses, netIncome });

    return { 
      revenue, 
      expenses: totalExpenses, 
      netIncome 
    };
  };

  /**
   * Extract AR aging metrics from Aged Receivables report
   * QuickBooks AR Aging buckets are typically:
   * - Current (not yet due)
   * - 1-30 days past due
   * - 31-60 days past due
   * - 61-90 days past due
   * - 91+ days past due (or "91 and over")
   */
  const extractARMetrics = (arData) => {
    if (!arData) {
      console.log('No AR data');
      return { current: 0, overdue30: 0, overdue60: 0, overdue90: 0, total: 0 };
    }
    
    console.log('AR Data:', arData);
    console.log('AR Totals:', arData.totals);
    console.log('AR Buckets:', arData.buckets);

    const totals = arData.totals || {};
    const buckets = arData.buckets || [];

    // Try to match various bucket naming conventions
    const getValue = (keys) => {
      for (const key of keys) {
        // Check exact match
        if (totals[key] !== undefined) {
          return parseFloat(totals[key]) || 0;
        }
        // Check case-insensitive match
        const lowerKey = key.toLowerCase();
        for (const totalKey of Object.keys(totals)) {
          if (totalKey.toLowerCase() === lowerKey || totalKey.toLowerCase().includes(lowerKey)) {
            return parseFloat(totals[totalKey]) || 0;
          }
        }
      }
      return 0;
    };

    // Current (not yet due)
    const current = getValue(['Current', 'current', '0', 'Not Due', 'not due']);
    
    // 1-30 days
    const overdue30 = getValue(['1 - 30', '1-30', '1 to 30', '1-30 days', '1 - 30 days']);
    
    // 31-60 days
    const overdue60 = getValue(['31 - 60', '31-60', '31 to 60', '31-60 days', '31 - 60 days']);
    
    // 61-90 days
    const overdue90_61 = getValue(['61 - 90', '61-90', '61 to 90', '61-90 days', '61 - 90 days']);
    
    // 91+ days
    const overdue90_plus = getValue(['91 and over', '91+', '> 90', 'over 90', '91 - 120', '91-120', '> 90 days']);

    // Combine 61-90 and 91+ into one bucket for display
    const overdue90 = overdue90_61 + overdue90_plus;

    // Calculate total - either from totals or sum of buckets
    let total = getValue(['Total', 'total', 'Grand Total']);
    if (total === 0) {
      total = current + overdue30 + overdue60 + overdue90;
    }

    console.log('Extracted AR:', { current, overdue30, overdue60, overdue90, total });

    return {
      current,
      overdue30,
      overdue60,
      overdue90,
      total
    };
  };

  // Not connected state
  if (!connected && !loading) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">QuickBooks Financial Dashboard</h1>
          <p className="text-gray-600">Connect your QuickBooks account to view financial data</p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <DollarSign className="w-8 h-8 text-green-600" />
          </div>
          <h2 className="text-xl font-semibold mb-2">Connect to QuickBooks</h2>
          <p className="text-gray-600 mb-6">
            Link your QuickBooks Online account to see real-time financial data, 
            P&L reports, and accounts receivable aging.
          </p>
          <button
            onClick={handleConnect}
            className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2 mx-auto"
          >
            <Link className="w-5 h-5" />
            Connect QuickBooks
          </button>
        </div>

        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <span className="text-red-700">{error}</span>
          </div>
        )}
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">QuickBooks Financial Dashboard</h1>
        </div>
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-green-600" />
          <span className="ml-2 text-gray-600">Loading financial data...</span>
        </div>
      </div>
    );
  }

  const currentMonth = dashboardData?.current_month ? extractFinancialMetrics(dashboardData.current_month) : null;
  const ytd = dashboardData?.year_to_date ? extractFinancialMetrics(dashboardData.year_to_date) : null;
  const arMetrics = dashboardData?.ar_aging ? extractARMetrics(dashboardData.ar_aging) : null;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">QuickBooks Financial Dashboard</h1>
          <p className="text-gray-600">
            {dashboardData?.company?.name || 'VITAL WorkLife, Inc.'} - Financial Overview
          </p>
        </div>
        <div className="flex items-center gap-4">
          {lastUpdated && (
            <span className="text-sm text-gray-500 flex items-center gap-1">
              <Clock className="w-4 h-4" />
              Updated: {lastUpdated}
            </span>
          )}
          <button
            onClick={fetchDashboardData}
            className="bg-white border border-gray-300 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button
            onClick={handleDisconnect}
            className="bg-red-50 text-red-600 border border-red-200 px-4 py-2 rounded-lg hover:bg-red-100 transition-colors flex items-center gap-2"
          >
            <Unlink className="w-4 h-4" />
            Disconnect
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <span className="text-red-700">{error}</span>
        </div>
      )}

      {/* Connection Status */}
      <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-2">
        <CheckCircle className="w-5 h-5 text-green-500" />
        <span className="text-green-700">QuickBooks Connected</span>
      </div>

      {/* Current Month Metrics */}
      {currentMonth && (
        <>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Current Month Performance</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Revenue</p>
                  <p className="text-2xl font-bold text-gray-900">{formatCurrency(currentMonth.revenue)}</p>
                </div>
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-green-600" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Expenses</p>
                  <p className="text-2xl font-bold text-gray-900">{formatCurrency(currentMonth.expenses)}</p>
                </div>
                <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                  <TrendingDown className="w-6 h-6 text-red-600" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Net Income</p>
                  <p className={`text-2xl font-bold ${currentMonth.netIncome >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(currentMonth.netIncome)}
                  </p>
                </div>
                <div className={`w-12 h-12 ${currentMonth.netIncome >= 0 ? 'bg-green-100' : 'bg-red-100'} rounded-full flex items-center justify-center`}>
                  <DollarSign className={`w-6 h-6 ${currentMonth.netIncome >= 0 ? 'text-green-600' : 'text-red-600'}`} />
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* YTD Metrics */}
      {ytd && (
        <>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Year-to-Date Performance</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">YTD Revenue</p>
                  <p className="text-2xl font-bold text-gray-900">{formatCurrency(ytd.revenue)}</p>
                </div>
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-blue-600" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">YTD Expenses</p>
                  <p className="text-2xl font-bold text-gray-900">{formatCurrency(ytd.expenses)}</p>
                </div>
                <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
                  <CreditCard className="w-6 h-6 text-orange-600" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">YTD Net Income</p>
                  <p className={`text-2xl font-bold ${ytd.netIncome >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(ytd.netIncome)}
                  </p>
                </div>
                <div className={`w-12 h-12 ${ytd.netIncome >= 0 ? 'bg-green-100' : 'bg-red-100'} rounded-full flex items-center justify-center`}>
                  <DollarSign className={`w-6 h-6 ${ytd.netIncome >= 0 ? 'text-green-600' : 'text-red-600'}`} />
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* AR Aging */}
      {arMetrics && (
        <>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Accounts Receivable Aging</h2>
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <p className="text-sm text-gray-500">Current</p>
                <p className="text-xl font-bold text-green-600">{formatCurrency(arMetrics.current)}</p>
              </div>
              <div className="text-center p-4 bg-yellow-50 rounded-lg">
                <p className="text-sm text-gray-500">1-30 Days</p>
                <p className="text-xl font-bold text-yellow-600">{formatCurrency(arMetrics.overdue30)}</p>
              </div>
              <div className="text-center p-4 bg-orange-50 rounded-lg">
                <p className="text-sm text-gray-500">31-60 Days</p>
                <p className="text-xl font-bold text-orange-600">{formatCurrency(arMetrics.overdue60)}</p>
              </div>
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <p className="text-sm text-gray-500">61-90+ Days</p>
                <p className="text-xl font-bold text-red-600">{formatCurrency(arMetrics.overdue90)}</p>
              </div>
              <div className="text-center p-4 bg-gray-100 rounded-lg">
                <p className="text-sm text-gray-500">Total AR</p>
                <p className="text-xl font-bold text-gray-900">{formatCurrency(arMetrics.total)}</p>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Debug Info - Remove in production */}
      {dashboardData && (
        <details className="mb-8">
          <summary className="text-sm text-gray-500 cursor-pointer">Debug: Raw API Response</summary>
          <pre className="mt-2 p-4 bg-gray-100 rounded-lg text-xs overflow-auto max-h-96">
            {JSON.stringify(dashboardData, null, 2)}
          </pre>
        </details>
      )}

      {/* No Data State */}
      {!currentMonth && !ytd && !arMetrics && !loading && (
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Financial Data Available</h3>
          <p className="text-gray-600">
            QuickBooks is connected but no financial data was returned. 
            This could mean the account is new or there's no transaction data yet.
          </p>
        </div>
      )}
    </div>
  );
};

export default VitalQuickBooksDashboard;
