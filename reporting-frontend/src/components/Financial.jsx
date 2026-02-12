import { useState } from 'react';
import PLReport from './PLReport';
import BalanceSheet from './BalanceSheet';
import CashFlowWidget from './CashFlowWidget';
import ProfitLossWidget from './ProfitLossWidget';

const Financial = ({ user, organization }) => {
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Financial Reports</h1>
        <p className="mt-2 text-sm text-gray-600">
          Comprehensive financial reporting and analysis
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8" aria-label="Tabs">
          <button
            onClick={() => setActiveTab('overview')}
            className={`
              whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm
              ${activeTab === 'overview'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }
            `}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('pl')}
            className={`
              whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm
              ${activeTab === 'pl'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }
            `}
          >
            P&L Report
          </button>
          <button
            onClick={() => setActiveTab('balance-sheet')}
            className={`
              whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm
              ${activeTab === 'balance-sheet'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }
            `}
          >
            Balance Sheet
          </button>

        </nav>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ProfitLossWidget />
            <CashFlowWidget />
          </div>
        )}
        {activeTab === 'pl' && <PLReport user={user} organization={organization} />}
        {activeTab === 'balance-sheet' && <BalanceSheet />}
      </div>
    </div>
  );
};

export default Financial;
