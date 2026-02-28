import React, { useState, useEffect, useCallback } from 'react';
import { Eye, EyeOff, ChevronDown, ChevronRight, Building2, Save, RefreshCw, Check, AlertCircle } from 'lucide-react';
import { apiUrl } from '@/lib/api';

const getToken = () => localStorage.getItem('token');

const REPORT_REGISTRY = {
  'dashboard': {
    label: 'Sales',
    icon: '📊',
    tabs: {
      'sales': { label: 'Sales' },
      'sales-breakdown': { label: 'Sales Breakdown' },
      'customers': { label: 'Customers' },
      'workorders': { label: 'Work Orders' },
      'forecast': { label: 'AI Sales Forecast' },
      'accuracy': { label: 'AI Forecast Accuracy' },
    }
  },
  'parts': {
    label: 'Parts',
    icon: '📦',
    tabs: {
      'overview': { label: 'Overview' },
      'work-orders': { label: 'Work Orders' },
      'inventory-location': { label: 'Inventory by Location' },
      'stock-alerts': { label: 'Stock Alerts' },
      'forecast': { label: 'Forecast' },
      'employee-performance': { label: 'Parts Contest' },
      'velocity': { label: 'Velocity' },
      'inventory-turns': { label: 'Inventory Turns' },
    }
  },
  'service': {
    label: 'Service',
    icon: '🔧',
    tabs: {
      'overview': { label: 'Overview' },
      'work-orders': { label: 'Work Orders' },
    }
  },
  'rental': {
    label: 'Rental',
    icon: '🚛',
    tabs: {
      'overview': { label: 'Overview' },
      'availability': { label: 'Availability' },
    }
  },
  'accounting': {
    label: 'Accounting',
    icon: '💰',
    tabs: {
      'overview': { label: 'Overview' },
      'ar': { label: 'Accounts Receivable' },
      'ap': { label: 'Accounts Payable' },
      'commissions': { label: 'Sales Commissions' },
      'control': { label: 'Control Numbers' },
      'inventory': { label: 'Inventory' },
    }
  },
  'customer-churn': {
    label: 'Customers',
    icon: '👥',
    tabs: {
      'sales-by-customer': { label: 'Sales by Customer' },
      'customer-churn': { label: 'Customer Churn' },
    }
  },
  'financial': {
    label: 'Finance',
    icon: '📑',
    tabs: {}
  },
  'knowledge-base': {
    label: 'Knowledge Base',
    icon: '📚',
    tabs: {}
  },
  'qbr': {
    label: 'QBR',
    icon: '📈',
    tabs: {}
  },
  'my-commissions': {
    label: 'My Commissions',
    icon: '💵',
    tabs: {}
  },
  'minitrac': {
    label: 'Minitrac',
    icon: '🔍',
    tabs: {}
  },
};

const Toggle = ({ enabled, onChange, size = 'md' }) => {
  const sizeClasses = size === 'sm' 
    ? 'w-8 h-4' 
    : 'w-11 h-6';
  const dotSize = size === 'sm'
    ? 'w-3 h-3'
    : 'w-5 h-5';
  const dotTranslate = size === 'sm'
    ? (enabled ? 'translate-x-4' : 'translate-x-0.5')
    : (enabled ? 'translate-x-5' : 'translate-x-0.5');

  return (
    <button
      type="button"
      onClick={onChange}
      className={`relative inline-flex items-center rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${sizeClasses} ${
        enabled ? 'bg-blue-600' : 'bg-gray-300'
      }`}
    >
      <span
        className={`inline-block rounded-full bg-white shadow transform transition-transform duration-200 ${dotSize} ${dotTranslate}`}
      />
    </button>
  );
};

const ReportVisibility = ({ user }) => {
  const [organizations, setOrganizations] = useState([]);
  const [selectedOrgId, setSelectedOrgId] = useState(null);
  const [visibility, setVisibility] = useState({});
  const [expandedPages, setExpandedPages] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState(null); // 'success' | 'error' | null
  const [error, setError] = useState('');
  const [hasChanges, setHasChanges] = useState(false);

  // Fetch organizations
  useEffect(() => {
    const fetchOrgs = async () => {
      try {
        const res = await fetch(apiUrl('/api/admin/organizations'), {
          headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        if (!res.ok) throw new Error('Failed to fetch organizations');
        const data = await res.json();
        setOrganizations(data);
        if (data.length > 0) {
          setSelectedOrgId(data[0].id);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchOrgs();
  }, []);

  // Fetch visibility settings when org changes
  const fetchVisibility = useCallback(async (orgId) => {
    if (!orgId) return;
    try {
      const res = await fetch(apiUrl(`/api/admin/report-visibility/${orgId}`), {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      if (!res.ok) throw new Error('Failed to fetch visibility settings');
      const data = await res.json();
      setVisibility(data.visibility || {});
      setHasChanges(false);
      setSaveStatus(null);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    if (selectedOrgId) {
      fetchVisibility(selectedOrgId);
    }
  }, [selectedOrgId, fetchVisibility]);

  // Toggle page visibility
  const togglePage = (pageId) => {
    setVisibility(prev => {
      const current = prev[pageId] || { visible: true, tabs: {} };
      return {
        ...prev,
        [pageId]: { ...current, visible: !current.visible }
      };
    });
    setHasChanges(true);
    setSaveStatus(null);
  };

  // Toggle tab visibility
  const toggleTab = (pageId, tabId) => {
    setVisibility(prev => {
      const current = prev[pageId] || { visible: true, tabs: {} };
      const currentTabs = current.tabs || {};
      return {
        ...prev,
        [pageId]: {
          ...current,
          tabs: {
            ...currentTabs,
            [tabId]: currentTabs[tabId] === undefined ? false : !currentTabs[tabId]
          }
        }
      };
    });
    setHasChanges(true);
    setSaveStatus(null);
  };

  // Toggle expand/collapse for a page's tabs
  const toggleExpand = (pageId) => {
    setExpandedPages(prev => ({ ...prev, [pageId]: !prev[pageId] }));
  };

  // Save settings
  const saveSettings = async () => {
    if (!selectedOrgId) return;
    setSaving(true);
    setSaveStatus(null);
    try {
      const res = await fetch(apiUrl(`/api/admin/report-visibility/${selectedOrgId}`), {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${getToken()}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(visibility)
      });
      if (!res.ok) throw new Error('Failed to save settings');
      setSaveStatus('success');
      setHasChanges(false);
      setTimeout(() => setSaveStatus(null), 3000);
    } catch (err) {
      setSaveStatus('error');
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  // Count visible/total for an org
  const getVisibilitySummary = () => {
    let totalPages = Object.keys(REPORT_REGISTRY).length;
    let visiblePages = 0;
    let totalTabs = 0;
    let visibleTabs = 0;

    Object.entries(REPORT_REGISTRY).forEach(([pageId, pageConfig]) => {
      const pageVis = visibility[pageId];
      const isPageVisible = !pageVis || pageVis.visible !== false;
      if (isPageVisible) visiblePages++;

      const tabs = pageConfig.tabs || {};
      Object.keys(tabs).forEach(tabId => {
        totalTabs++;
        const isTabVisible = isPageVisible && (!pageVis || !pageVis.tabs || pageVis.tabs[tabId] !== false);
        if (isTabVisible) visibleTabs++;
      });
    });

    return { totalPages, visiblePages, totalTabs, visibleTabs };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading...</span>
      </div>
    );
  }

  const summary = getVisibilitySummary();
  const selectedOrg = organizations.find(o => o.id === selectedOrgId);

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <Eye className="w-7 h-7 text-blue-500" />
          Report Visibility
        </h1>
        <p className="text-gray-600 mt-1">
          Control which reports and tabs are visible for each organization
        </p>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          {error}
          <button onClick={() => setError('')} className="ml-auto text-red-500 hover:text-red-700">&times;</button>
        </div>
      )}

      {/* Org Selector + Save */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Building2 className="w-5 h-5 text-gray-500" />
              <label className="text-sm font-medium text-gray-700">Organization:</label>
            </div>
            <select
              value={selectedOrgId || ''}
              onChange={(e) => setSelectedOrgId(Number(e.target.value))}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white min-w-[200px]"
            >
              {organizations.map(org => (
                <option key={org.id} value={org.id}>{org.name}</option>
              ))}
            </select>
            <button
              onClick={() => fetchVisibility(selectedOrgId)}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              title="Refresh"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          <div className="flex items-center gap-3">
            {/* Summary */}
            <div className="text-sm text-gray-500">
              <span className="font-medium text-gray-700">{summary.visiblePages}</span>/{summary.totalPages} pages &middot;{' '}
              <span className="font-medium text-gray-700">{summary.visibleTabs}</span>/{summary.totalTabs} tabs visible
            </div>

            {/* Save Button */}
            <button
              onClick={saveSettings}
              disabled={!hasChanges || saving}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                hasChanges
                  ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm'
                  : 'bg-gray-100 text-gray-400 cursor-not-allowed'
              }`}
            >
              {saving ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : saveStatus === 'success' ? (
                <Check className="w-4 h-4" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              {saving ? 'Saving...' : saveStatus === 'success' ? 'Saved!' : 'Save Changes'}
            </button>
          </div>
        </div>
      </div>

      {/* Report Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {Object.entries(REPORT_REGISTRY).map(([pageId, pageConfig]) => {
          const pageVis = visibility[pageId] || { visible: true, tabs: {} };
          const isPageVisible = pageVis.visible !== false;
          const hasTabs = Object.keys(pageConfig.tabs || {}).length > 0;
          const isExpanded = expandedPages[pageId];
          const tabEntries = Object.entries(pageConfig.tabs || {});
          const hiddenTabCount = tabEntries.filter(([tabId]) => 
            pageVis.tabs && pageVis.tabs[tabId] === false
          ).length;

          return (
            <div
              key={pageId}
              className={`bg-white rounded-xl border transition-all ${
                isPageVisible ? 'border-gray-200 shadow-sm' : 'border-red-200 bg-red-50/30 shadow-none'
              }`}
            >
              {/* Page Header */}
              <div className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {hasTabs && (
                    <button
                      onClick={() => toggleExpand(pageId)}
                      className="p-1 hover:bg-gray-100 rounded transition-colors"
                    >
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-gray-500" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-gray-500" />
                      )}
                    </button>
                  )}
                  <span className="text-lg">{pageConfig.icon}</span>
                  <div>
                    <div className={`font-semibold ${isPageVisible ? 'text-gray-800' : 'text-gray-400 line-through'}`}>
                      {pageConfig.label}
                    </div>
                    {hasTabs && (
                      <div className="text-xs text-gray-500">
                        {tabEntries.length} tabs
                        {hiddenTabCount > 0 && (
                          <span className="text-red-500 ml-1">({hiddenTabCount} hidden)</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {isPageVisible ? (
                    <Eye className="w-4 h-4 text-green-500" />
                  ) : (
                    <EyeOff className="w-4 h-4 text-red-400" />
                  )}
                  <Toggle enabled={isPageVisible} onChange={() => togglePage(pageId)} />
                </div>
              </div>

              {/* Tabs */}
              {hasTabs && isExpanded && (
                <div className={`border-t ${isPageVisible ? 'border-gray-100' : 'border-red-100'}`}>
                  {tabEntries.map(([tabId, tabConfig]) => {
                    const isTabVisible = isPageVisible && (pageVis.tabs?.[tabId] !== false);
                    return (
                      <div
                        key={tabId}
                        className={`px-4 py-2.5 flex items-center justify-between border-b last:border-b-0 ${
                          isPageVisible ? 'border-gray-50' : 'border-red-50'
                        }`}
                      >
                        <span className={`text-sm pl-8 ${
                          isTabVisible ? 'text-gray-700' : 'text-gray-400 line-through'
                        }`}>
                          {tabConfig.label}
                        </span>
                        <Toggle
                          enabled={isTabVisible}
                          onChange={() => isPageVisible && toggleTab(pageId, tabId)}
                          size="sm"
                        />
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Info Note */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-700">
        <strong>Note:</strong> Changes take effect after the user refreshes their browser or logs in again. 
        Hiding a page removes it from the sidebar. Hiding a tab removes it from within the page. 
        If all tabs in a page are hidden, the page will still appear but show no content.
      </div>
    </div>
  );
};

export default ReportVisibility;
