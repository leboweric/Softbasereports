import React, { useState } from 'react';
import { Users, TrendingDown, DollarSign } from 'lucide-react';
import SalesByCustomer from './SalesByCustomer';
import CustomerChurnAnalysis from './CustomerChurnAnalysis';

const CustomersPage = ({ user, organization }) => {
  const [activeView, setActiveView] = useState('sales-by-customer');

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

      {/* Tab Navigation */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            <button
              onClick={() => setActiveView('sales-by-customer')}
              className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeView === 'sales-by-customer'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <DollarSign className="w-4 h-4" />
                Sales by Customer
              </div>
            </button>
            <button
              onClick={() => setActiveView('customer-churn')}
              className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeView === 'customer-churn'
                  ? 'border-red-500 text-red-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <TrendingDown className="w-4 h-4" />
                Customer Churn
              </div>
            </button>
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      {activeView === 'sales-by-customer' && (
        <SalesByCustomer />
      )}
      {activeView === 'customer-churn' && (
        <CustomerChurnAnalysis user={user} organization={organization} />
      )}
    </div>
  );
};

export default CustomersPage;
