import React, { useState } from 'react';
import { Users, TrendingDown, DollarSign } from 'lucide-react';
import { getAccessibleTabs } from '@/contexts/PermissionsContext';
import SalesByCustomer from './SalesByCustomer';
import CustomerChurnAnalysis from './CustomerChurnAnalysis';

const CustomersPage = ({ user, organization }) => {
  // Tab visibility based on admin settings
  const customerTabs = getAccessibleTabs(user, 'customer-churn');
  const showAllTabs = Object.keys(customerTabs).length === 0;

  const allTabDefs = [
    { value: 'sales-by-customer', label: 'Sales by Customer', icon: DollarSign, activeColor: 'blue' },
    { value: 'customer-churn', label: 'Customer Churn', icon: TrendingDown, activeColor: 'red' },
  ];

  const visibleTabs = allTabDefs.filter(t => showAllTabs || customerTabs[t.value]);
  const defaultTab = visibleTabs.length > 0 ? visibleTabs[0].value : 'sales-by-customer';
  const [activeView, setActiveView] = useState(defaultTab);

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center">
          <Users className="w-7 h-7 mr-2 text-blue-500" />
          Customers
        </h1>
        <p className="text-gray-600 mt-1">
          Customer revenue analysis and churn monitoring
        </p>
      </div>

      {/* Tab Navigation - only show if more than one tab */}
      {visibleTabs.length > 1 && (
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              {visibleTabs.map(tab => {
                const Icon = tab.icon;
                const isActive = activeView === tab.value;
                return (
                  <button
                    key={tab.value}
                    onClick={() => setActiveView(tab.value)}
                    className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                      isActive
                        ? `border-${tab.activeColor}-500 text-${tab.activeColor}-600`
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <Icon className="w-4 h-4" />
                      {tab.label}
                    </div>
                  </button>
                );
              })}
            </nav>
          </div>
        </div>
      )}

      {/* Tab Content */}
      {activeView === 'sales-by-customer' && (showAllTabs || customerTabs['sales-by-customer']) && (
        <SalesByCustomer />
      )}
      {activeView === 'customer-churn' && (showAllTabs || customerTabs['customer-churn']) && (
        <CustomerChurnAnalysis user={user} organization={organization} />
      )}
    </div>
  );
};

export default CustomersPage;
