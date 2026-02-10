import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, 
  TrendingDown, 
  Users, 
  DollarSign, 
  Calendar,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Phone,
  Mail,
  ExternalLink,
  Info
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const API_BASE = import.meta.env.VITE_API_URL || '';

const CustomerChurnAnalysis = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [churnData, setChurnData] = useState(null);
  const [atRiskData, setAtRiskData] = useState(null);
  const [aiInsights, setAiInsights] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('churned');
  const [expandedCustomer, setExpandedCustomer] = useState(null);
  const [monthsBack, setMonthsBack] = useState(3);

  const fetchChurnData = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/api/customer-churn/analysis?months=${monthsBack}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch churn analysis');
      }
      
      const data = await response.json();
      setChurnData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchAtRiskData = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/api/customer-churn/at-risk`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch at-risk customers');
      }
      
      const data = await response.json();
      setAtRiskData(data);
    } catch (err) {
      console.error('At-risk fetch error:', err);
    }
  };

  const generateAiInsights = async () => {
    if (!churnData) return;
    
    setAiLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/api/customer-churn/ai-insights`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(churnData)
      });
      
      if (!response.ok) {
        throw new Error('Failed to generate AI insights');
      }
      
      const data = await response.json();
      setAiInsights(data);
    } catch (err) {
      console.error('AI insights error:', err);
    } finally {
      setAiLoading(false);
    }
  };

  useEffect(() => {
    fetchChurnData();
    fetchAtRiskData();
  }, [monthsBack]);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        <span className="ml-2 text-gray-600">Analyzing customer data...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 m-4">
        <div className="flex items-center">
          <AlertTriangle className="w-5 h-5 text-red-500 mr-2" />
          <span className="text-red-700">{error}</span>
        </div>
        <button 
          onClick={fetchChurnData}
          className="mt-2 px-4 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200"
        >
          Retry
        </button>
      </div>
    );
  }

  const summary = churnData?.summary || {};
  const churnedCustomers = churnData?.churned_customers || [];
  const atRiskCustomers = atRiskData?.at_risk_customers || [];

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center">
          <TrendingDown className="w-7 h-7 mr-2 text-red-500" />
          Customer Churn Analysis
        </h1>
        <p className="text-gray-600 mt-1">
          Understand why customers are leaving and identify at-risk accounts
        </p>
      </div>

      {/* Period Selector */}
      <div className="mb-6 flex items-center gap-4">
        <label className="text-sm font-medium text-gray-700">Analysis Period:</label>
        <select
          value={monthsBack}
          onChange={(e) => setMonthsBack(parseInt(e.target.value))}
          className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
        >
          <option value={1}>Last 1 month vs previous 1 month</option>
          <option value={3}>Last 3 months vs previous 3 months</option>
          <option value={6}>Last 6 months vs previous 6 months</option>
        </select>
        <button
          onClick={() => { fetchChurnData(); fetchAtRiskData(); }}
          className="flex items-center px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
        >
          <RefreshCw className="w-4 h-4 mr-1" />
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-red-500 relative group">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 flex items-center">
                Churned Customers
                <Info className="w-4 h-4 ml-1 text-gray-400 cursor-help" />
              </p>
              <p className="text-2xl font-bold text-red-600">{summary.total_churned_customers || 0}</p>
            </div>
            <Users className="w-10 h-10 text-red-200" />
          </div>
          <p className="text-xs text-gray-400 mt-2">
            {summary.churn_rate_percent?.toFixed(1)}% churn rate
          </p>
          {/* Tooltip */}
          <div className="absolute z-10 invisible group-hover:visible bg-gray-900 text-white text-xs rounded-lg p-3 w-72 -top-2 left-1/2 transform -translate-x-1/2 -translate-y-full shadow-lg">
            <p className="font-semibold mb-2">Churned Customer Criteria:</p>
            <p className="mb-1">A customer is considered "churned" if they meet both conditions:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>Had at least one invoice in the previous 90 days (days 91-180 ago)</li>
              <li>Have had zero invoices in the last 90 days</li>
            </ul>
            <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-full">
              <div className="border-8 border-transparent border-t-gray-900"></div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-orange-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Lost Revenue</p>
              <p className="text-2xl font-bold text-orange-600">{formatCurrency(summary.total_lost_revenue || 0)}</p>
            </div>
            <DollarSign className="w-10 h-10 text-orange-200" />
          </div>
          <p className="text-xs text-gray-400 mt-2">
            Lifetime value of churned customers
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-yellow-500 relative group">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 flex items-center">
                At-Risk Customers
                <Info className="w-4 h-4 ml-1 text-gray-400 cursor-help" />
              </p>
              <p className="text-2xl font-bold text-yellow-600">{atRiskData?.total_at_risk || 0}</p>
            </div>
            <AlertTriangle className="w-10 h-10 text-yellow-200" />
          </div>
          <p className="text-xs text-gray-400 mt-2">
            Activity dropped 50%+ recently
          </p>
          {/* Tooltip */}
          <div className="absolute z-10 invisible group-hover:visible bg-gray-900 text-white text-xs rounded-lg p-3 w-72 -top-2 left-1/2 transform -translate-x-1/2 -translate-y-full shadow-lg">
            <p className="font-semibold mb-2">At-Risk Customer Criteria:</p>
            <p className="mb-1">A customer is "at-risk" if:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>They had activity in both periods</li>
              <li>Their recent period revenue dropped by 50% or more compared to the previous period</li>
            </ul>
            <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-full">
              <div className="border-8 border-transparent border-t-gray-900"></div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-green-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Current Active (90 days)</p>
              <p className="text-2xl font-bold text-green-600">{summary.current_active_customers || 0}</p>
            </div>
            <Users className="w-10 h-10 text-green-200" />
          </div>
          <p className="text-xs text-gray-400 mt-2">
            Customers with invoices in last 90 days
          </p>
        </div>
      </div>

      {/* AI Insights Button */}
      <div className="mb-6">
        <button
          onClick={generateAiInsights}
          disabled={aiLoading || !churnData}
          className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Sparkles className="w-5 h-5 mr-2" />
          {aiLoading ? 'Generating AI Insights...' : 'Generate AI Insights'}
        </button>
      </div>

      {/* AI Insights Panel */}
      {aiInsights && (
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-6 mb-6">
          <h3 className="text-lg font-semibold text-purple-800 flex items-center mb-4">
            <Sparkles className="w-5 h-5 mr-2" />
            AI-Powered Insights
          </h3>
          <div className="prose prose-sm max-w-none text-gray-700">
            <ReactMarkdown>{aiInsights.insights}</ReactMarkdown>
          </div>
          <p className="text-xs text-purple-400 mt-4">
            Generated at {new Date(aiInsights.generated_at).toLocaleString()}
          </p>
        </div>
      )}

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            <button
              onClick={() => setActiveTab('churned')}
              className={`px-6 py-3 text-sm font-medium border-b-2 ${
                activeTab === 'churned'
                  ? 'border-red-500 text-red-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Churned Customers ({churnedCustomers.length})
            </button>
            <button
              onClick={() => setActiveTab('at-risk')}
              className={`px-6 py-3 text-sm font-medium border-b-2 ${
                activeTab === 'at-risk'
                  ? 'border-yellow-500 text-yellow-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              At-Risk Customers ({atRiskCustomers.length})
            </button>
          </nav>
        </div>

        {/* Churned Customers Tab */}
        {activeTab === 'churned' && (
          <div className="p-4">
            {churnedCustomers.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No churned customers found in this period</p>
            ) : (
              <div className="space-y-2">
                {churnedCustomers.map((customer, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg">
                    <div 
                      className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50"
                      onClick={() => setExpandedCustomer(expandedCustomer === index ? null : index)}
                    >
                      <div className="flex items-center">
                        <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center mr-3">
                          <span className="text-red-600 font-semibold text-sm">{index + 1}</span>
                        </div>
                        <div>
                          <h4 className="font-medium text-gray-800">{customer.customer_name}</h4>
                          <p className="text-sm text-gray-500">
                            Last invoice: {formatDate(customer.last_invoice)} ({customer.days_since_last_invoice} days ago)
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-6">
                        <div className="text-right">
                          <p className="text-sm text-gray-500">Lifetime Revenue</p>
                          <p className="font-semibold text-gray-800">{formatCurrency(customer.total_revenue)}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-gray-500">Invoices</p>
                          <p className="font-semibold text-gray-800">{customer.total_invoices}</p>
                        </div>
                        {expandedCustomer === index ? (
                          <ChevronUp className="w-5 h-5 text-gray-400" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-gray-400" />
                        )}
                      </div>
                    </div>
                    
                    {expandedCustomer === index && (
                      <div className="border-t border-gray-200 p-4 bg-gray-50">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {/* Work Order Breakdown */}
                          <div>
                            <h5 className="font-medium text-gray-700 mb-2">Work Order History</h5>
                            {customer.work_order_breakdown?.length > 0 ? (
                              <div className="space-y-1">
                                {customer.work_order_breakdown.map((wo, i) => (
                                  <div key={i} className="flex justify-between text-sm">
                                    <span className="text-gray-600">
                                      {wo.type === 'S' ? 'Service' : 
                                       wo.type === 'PM' ? 'Preventive Maintenance' :
                                       wo.type === 'R' ? 'Rental' :
                                       wo.type === 'P' ? 'Parts' :
                                       wo.type === 'I' ? 'Internal' : wo.type}
                                    </span>
                                    <span className="text-gray-800">
                                      {wo.count} WOs • {formatCurrency(wo.revenue)}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <p className="text-sm text-gray-500">No work order history</p>
                            )}
                          </div>
                          
                          {/* Revenue Trend */}
                          <div>
                            <h5 className="font-medium text-gray-700 mb-2">Revenue Trend (Last 12 Months)</h5>
                            {customer.revenue_trend?.length > 0 ? (
                              <div className="space-y-1">
                                {customer.revenue_trend.slice(-6).map((month, i) => (
                                  <div key={i} className="flex justify-between text-sm">
                                    <span className="text-gray-600">{month.month}</span>
                                    <span className="text-gray-800">
                                      {formatCurrency(month.revenue)} ({month.invoices} inv)
                                    </span>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <p className="text-sm text-gray-500">No revenue trend data</p>
                            )}
                          </div>
                        </div>
                        
                        {/* Action Buttons */}
                        <div className="mt-4 pt-4 border-t border-gray-200 flex gap-2">
                          <button className="flex items-center px-3 py-1.5 bg-blue-100 text-blue-700 rounded text-sm hover:bg-blue-200">
                            <Phone className="w-4 h-4 mr-1" />
                            Schedule Call
                          </button>
                          <button className="flex items-center px-3 py-1.5 bg-green-100 text-green-700 rounded text-sm hover:bg-green-200">
                            <Mail className="w-4 h-4 mr-1" />
                            Send Email
                          </button>
                          <button className="flex items-center px-3 py-1.5 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200">
                            <ExternalLink className="w-4 h-4 mr-1" />
                            View in Softbase
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* At-Risk Customers Tab */}
        {activeTab === 'at-risk' && (
          <div className="p-4">
            {atRiskCustomers.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No at-risk customers identified</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Risk Level</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Previous Revenue</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Recent Revenue</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Change</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Invoice</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Days Inactive</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {atRiskCustomers.map((customer, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className="font-medium text-gray-800">{customer.customer_name}</span>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                            customer.risk_level === 'High' 
                              ? 'bg-red-100 text-red-700' 
                              : 'bg-yellow-100 text-yellow-700'
                          }`}>
                            {customer.risk_level}
                          </span>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-right text-gray-800">
                          {formatCurrency(customer.previous_revenue)}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-right text-gray-800">
                          {formatCurrency(customer.recent_revenue)}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-right">
                          <span className="text-red-600 font-medium">
                            {customer.revenue_change_percent.toFixed(0)}%
                          </span>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-gray-600">
                          {formatDate(customer.last_invoice)}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-right text-gray-800">
                          {customer.days_since_activity}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Analysis Period Info */}
      <div className="mt-4 text-sm text-gray-500 text-center">
        Analysis comparing {summary.analysis_period?.previous_start} - {summary.analysis_period?.previous_end} 
        {' '}vs{' '}
        {summary.analysis_period?.current_start} - {summary.analysis_period?.current_end}
      </div>
    </div>
  );
};

export default CustomerChurnAnalysis;
