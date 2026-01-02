import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { DollarSign, TrendingUp, TrendingDown, CreditCard, Receipt, PiggyBank, AlertCircle, ArrowUpRight, ArrowDownRight } from 'lucide-react';

const VitalFinancial = ({ user }) => {
  const [activeTab, setActiveTab] = useState('overview');

  // Sample/placeholder data for demo
  const sampleMetrics = {
    revenue: 2847500,
    revenueChange: 12.4,
    expenses: 1923400,
    expenseChange: 8.2,
    netIncome: 924100,
    netIncomeChange: 18.7,
    cashOnHand: 1456000,
    accountsReceivable: 342500,
    accountsPayable: 187300,
  };

  const sampleRevenueByService = [
    { service: 'EAP Services', amount: 1245000, percentage: 44 },
    { service: 'Coaching Programs', amount: 678000, percentage: 24 },
    { service: 'Crisis Support', amount: 452000, percentage: 16 },
    { service: 'Training & Workshops', amount: 284000, percentage: 10 },
    { service: 'Other Services', amount: 188500, percentage: 6 },
  ];

  const sampleExpenseCategories = [
    { category: 'Personnel', amount: 1154000, percentage: 60 },
    { category: 'Technology', amount: 288500, percentage: 15 },
    { category: 'Facilities', amount: 192300, percentage: 10 },
    { category: 'Marketing', amount: 134700, percentage: 7 },
    { category: 'Operations', amount: 153900, percentage: 8 },
  ];

  const sampleMonthlyRevenue = [
    { month: 'Jan', revenue: 215000, expenses: 148000 },
    { month: 'Feb', revenue: 228000, expenses: 152000 },
    { month: 'Mar', revenue: 242000, expenses: 158000 },
    { month: 'Apr', revenue: 235000, expenses: 161000 },
    { month: 'May', revenue: 251000, expenses: 165000 },
    { month: 'Jun', revenue: 268000, expenses: 172000 },
    { month: 'Jul', revenue: 245000, expenses: 168000 },
    { month: 'Aug', revenue: 238000, expenses: 159000 },
    { month: 'Sep', revenue: 256000, expenses: 163000 },
    { month: 'Oct', revenue: 272000, expenses: 171000 },
    { month: 'Nov', revenue: 285000, expenses: 178000 },
    { month: 'Dec', revenue: 312000, expenses: 188000 },
  ];

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const MetricCard = ({ title, value, change, icon: Icon, positive }) => (
    <Card>
      <CardContent className="pt-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-gray-500 text-sm">
            <Icon className="h-4 w-4" />
            {title}
          </div>
          {change !== undefined && (
            <div className={`flex items-center text-sm ${positive ? 'text-green-600' : 'text-red-600'}`}>
              {positive ? <ArrowUpRight className="h-4 w-4" /> : <ArrowDownRight className="h-4 w-4" />}
              {Math.abs(change)}%
            </div>
          )}
        </div>
        <p className="text-2xl font-bold mt-1">{formatCurrency(value)}</p>
      </CardContent>
    </Card>
  );

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Financial</h1>
        <p className="text-gray-500">Financial data from QuickBooks Online</p>
      </div>

      {/* Alert for demo mode */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start gap-3">
        <AlertCircle className="h-5 w-5 text-blue-500 mt-0.5" />
        <div>
          <p className="text-sm text-blue-700 font-medium">Demo Mode</p>
          <p className="text-sm text-blue-600">
            This page shows sample data. Connect your QuickBooks account in Data Sources to see real financial data.
          </p>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <MetricCard 
          title="Revenue (YTD)" 
          value={sampleMetrics.revenue} 
          change={sampleMetrics.revenueChange}
          icon={TrendingUp}
          positive={true}
        />
        <MetricCard 
          title="Expenses (YTD)" 
          value={sampleMetrics.expenses} 
          change={sampleMetrics.expenseChange}
          icon={TrendingDown}
          positive={false}
        />
        <MetricCard 
          title="Net Income" 
          value={sampleMetrics.netIncome} 
          change={sampleMetrics.netIncomeChange}
          icon={DollarSign}
          positive={true}
        />
        <MetricCard 
          title="Cash on Hand" 
          value={sampleMetrics.cashOnHand}
          icon={PiggyBank}
        />
        <MetricCard 
          title="Accounts Receivable" 
          value={sampleMetrics.accountsReceivable}
          icon={Receipt}
        />
        <MetricCard 
          title="Accounts Payable" 
          value={sampleMetrics.accountsPayable}
          icon={CreditCard}
        />
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="revenue">Revenue</TabsTrigger>
          <TabsTrigger value="expenses">Expenses</TabsTrigger>
          <TabsTrigger value="pl">P&L Statement</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Revenue vs Expenses</CardTitle>
                <CardDescription>Monthly comparison for current year</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64 flex items-end justify-between gap-1">
                  {sampleMonthlyRevenue.map((item, i) => (
                    <div key={i} className="flex-1 flex flex-col items-center gap-1">
                      <div className="w-full flex flex-col gap-0.5">
                        <div 
                          className="w-full bg-green-500 rounded-t"
                          style={{ height: `${(item.revenue / 350000) * 200}px` }}
                          title={`Revenue: ${formatCurrency(item.revenue)}`}
                        />
                        <div 
                          className="w-full bg-red-400 rounded-b"
                          style={{ height: `${(item.expenses / 350000) * 200}px` }}
                          title={`Expenses: ${formatCurrency(item.expenses)}`}
                        />
                      </div>
                      <span className="text-xs text-gray-500">{item.month}</span>
                    </div>
                  ))}
                </div>
                <div className="flex justify-center gap-6 mt-4">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-green-500 rounded" />
                    <span className="text-sm text-gray-600">Revenue</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-red-400 rounded" />
                    <span className="text-sm text-gray-600">Expenses</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Profit Margin Trend</CardTitle>
                <CardDescription>Net income as percentage of revenue</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64 flex items-end justify-between gap-2">
                  {sampleMonthlyRevenue.map((item, i) => {
                    const margin = ((item.revenue - item.expenses) / item.revenue) * 100;
                    return (
                      <div key={i} className="flex-1 flex flex-col items-center gap-1">
                        <div 
                          className="w-full bg-blue-500 rounded-t"
                          style={{ height: `${margin * 5}px` }}
                          title={`Margin: ${margin.toFixed(1)}%`}
                        />
                        <span className="text-xs text-gray-500">{item.month}</span>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="revenue">
          <Card>
            <CardHeader>
              <CardTitle>Revenue by Service Line</CardTitle>
              <CardDescription>Year-to-date revenue breakdown</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {sampleRevenueByService.map((item) => (
                  <div key={item.service} className="flex items-center gap-4">
                    <div className="w-40 text-sm font-medium">{item.service}</div>
                    <div className="flex-1 bg-gray-100 rounded-full h-6">
                      <div 
                        className="bg-green-500 h-6 rounded-full flex items-center justify-end pr-2"
                        style={{ width: `${item.percentage}%` }}
                      >
                        <span className="text-xs text-white font-medium">{item.percentage}%</span>
                      </div>
                    </div>
                    <div className="w-28 text-right font-medium">{formatCurrency(item.amount)}</div>
                  </div>
                ))}
              </div>
              <div className="mt-6 pt-4 border-t flex justify-between">
                <span className="font-bold">Total Revenue</span>
                <span className="font-bold">{formatCurrency(sampleMetrics.revenue)}</span>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="expenses">
          <Card>
            <CardHeader>
              <CardTitle>Expenses by Category</CardTitle>
              <CardDescription>Year-to-date expense breakdown</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {sampleExpenseCategories.map((item) => (
                  <div key={item.category} className="flex items-center gap-4">
                    <div className="w-32 text-sm font-medium">{item.category}</div>
                    <div className="flex-1 bg-gray-100 rounded-full h-6">
                      <div 
                        className="bg-red-400 h-6 rounded-full flex items-center justify-end pr-2"
                        style={{ width: `${item.percentage}%` }}
                      >
                        <span className="text-xs text-white font-medium">{item.percentage}%</span>
                      </div>
                    </div>
                    <div className="w-28 text-right font-medium">{formatCurrency(item.amount)}</div>
                  </div>
                ))}
              </div>
              <div className="mt-6 pt-4 border-t flex justify-between">
                <span className="font-bold">Total Expenses</span>
                <span className="font-bold">{formatCurrency(sampleMetrics.expenses)}</span>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="pl">
          <Card>
            <CardHeader>
              <CardTitle>Profit & Loss Statement</CardTitle>
              <CardDescription>Year-to-date summary</CardDescription>
            </CardHeader>
            <CardContent>
              <table className="w-full">
                <tbody>
                  <tr className="border-b">
                    <td className="py-3 font-bold text-lg" colSpan={2}>Revenue</td>
                  </tr>
                  {sampleRevenueByService.map((item) => (
                    <tr key={item.service} className="border-b border-gray-100">
                      <td className="py-2 pl-4">{item.service}</td>
                      <td className="py-2 text-right">{formatCurrency(item.amount)}</td>
                    </tr>
                  ))}
                  <tr className="border-b bg-gray-50">
                    <td className="py-2 font-bold">Total Revenue</td>
                    <td className="py-2 text-right font-bold">{formatCurrency(sampleMetrics.revenue)}</td>
                  </tr>
                  <tr>
                    <td className="py-3 font-bold text-lg" colSpan={2}>Expenses</td>
                  </tr>
                  {sampleExpenseCategories.map((item) => (
                    <tr key={item.category} className="border-b border-gray-100">
                      <td className="py-2 pl-4">{item.category}</td>
                      <td className="py-2 text-right text-red-600">({formatCurrency(item.amount)})</td>
                    </tr>
                  ))}
                  <tr className="border-b bg-gray-50">
                    <td className="py-2 font-bold">Total Expenses</td>
                    <td className="py-2 text-right font-bold text-red-600">({formatCurrency(sampleMetrics.expenses)})</td>
                  </tr>
                  <tr className="bg-green-50">
                    <td className="py-3 font-bold text-lg">Net Income</td>
                    <td className="py-3 text-right font-bold text-lg text-green-600">{formatCurrency(sampleMetrics.netIncome)}</td>
                  </tr>
                </tbody>
              </table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default VitalFinancial;
