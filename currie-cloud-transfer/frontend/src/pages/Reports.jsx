import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../hooks/useAuth'
import { get } from '../lib/api'
import { FileBarChart, Download, Calendar, Loader2, AlertCircle, ChevronDown, ChevronRight } from 'lucide-react'

// Format currency
const formatCurrency = (value) => {
  if (value === null || value === undefined) return '$0.00'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value)
}

// Format percentage
const formatPercent = (value) => {
  if (value === null || value === undefined) return '0.0%'
  return `${(value * 100).toFixed(1)}%`
}

// Collapsible Section Component
function ReportSection({ title, children, defaultOpen = true }) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <div className="border border-gray-200 rounded-lg mb-4">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 rounded-t-lg"
      >
        <h3 className="font-semibold text-gray-900">{title}</h3>
        {isOpen ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
      </button>
      {isOpen && <div className="p-4">{children}</div>}
    </div>
  )
}

// Financial Table Row
function FinancialRow({ label, sales, cogs, grossProfit, isTotal = false, indent = 0 }) {
  const baseClass = isTotal ? 'font-semibold bg-gray-50' : ''
  const paddingClass = indent > 0 ? `pl-${indent * 4}` : ''

  return (
    <tr className={baseClass}>
      <td className={`py-2 px-3 ${paddingClass}`}>{label}</td>
      <td className="py-2 px-3 text-right">{formatCurrency(sales)}</td>
      <td className="py-2 px-3 text-right">{formatCurrency(cogs)}</td>
      <td className="py-2 px-3 text-right">{formatCurrency(grossProfit)}</td>
      <td className="py-2 px-3 text-right">
        {sales > 0 ? formatPercent(grossProfit / sales) : '0.0%'}
      </td>
    </tr>
  )
}

export default function Reports() {
  const { dealer, isCurrieAdmin } = useAuth()
  const [dateRange, setDateRange] = useState({
    start: '',
    end: ''
  })
  const [selectedDealer, setSelectedDealer] = useState(null)
  const [showReport, setShowReport] = useState(false)

  // Fetch dealers for Currie admin
  const { data: dealersData } = useQuery({
    queryKey: ['dealers'],
    queryFn: () => get('/api/dealers'),
    enabled: isCurrieAdmin
  })

  const dealers = dealersData?.dealers || []

  // Fetch report data
  const {
    data: reportData,
    isLoading: reportLoading,
    error: reportError,
    refetch: fetchReport
  } = useQuery({
    queryKey: ['currie-financial-model', dateRange.start, dateRange.end, selectedDealer],
    queryFn: () => {
      const params = new URLSearchParams({
        start_date: dateRange.start,
        end_date: dateRange.end
      })
      if (selectedDealer) {
        params.append('dealer_id', selectedDealer)
      }
      return get(`/api/reports/currie-financial-model?${params}`)
    },
    enabled: false // Only fetch when button is clicked
  })

  const handleGenerateReport = () => {
    setShowReport(true)
    fetchReport()
  }

  const report = reportData?.report

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
        <p className="mt-1 text-sm text-gray-500">
          Generate and download financial reports
        </p>
      </div>

      {/* Report Selection */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Currie Financial Model */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center mb-4">
            <FileBarChart className="w-8 h-8 text-blue-600 mr-3" />
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                Currie Financial Model
              </h2>
              <p className="text-sm text-gray-500">
                Complete P&amp;L breakdown by department
              </p>
            </div>
          </div>

          <div className="space-y-4">
            {/* Dealer Selection for Currie Admin */}
            {isCurrieAdmin && dealers.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Select Dealer
                </label>
                <select
                  value={selectedDealer || ''}
                  onChange={(e) => setSelectedDealer(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select a dealer...</option>
                  {dealers.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name} ({d.code})
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Start Date
                </label>
                <input
                  type="date"
                  value={dateRange.start}
                  onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  End Date
                </label>
                <input
                  type="date"
                  value={dateRange.end}
                  onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            <button
              onClick={handleGenerateReport}
              disabled={!dateRange.start || !dateRange.end || (isCurrieAdmin && !selectedDealer)}
              className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {reportLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <FileBarChart className="w-4 h-4 mr-2" />
                  Generate Report
                </>
              )}
            </button>
          </div>
        </div>

        {/* Benchmark Report */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center mb-4">
            <FileBarChart className="w-8 h-8 text-green-600 mr-3" />
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                Industry Benchmarks
              </h2>
              <p className="text-sm text-gray-500">
                Compare your performance to industry averages
              </p>
            </div>
          </div>

          <div className="p-4 bg-gray-50 rounded-md text-center">
            <p className="text-sm text-gray-600">
              Benchmarking requires Professional or Enterprise subscription.
            </p>
            <button className="mt-3 text-sm text-blue-600 hover:text-blue-800 font-medium">
              Upgrade Subscription
            </button>
          </div>
        </div>
      </div>

      {/* Report Display */}
      {showReport && (
        <div className="mt-8">
          {reportLoading && (
            <div className="bg-white shadow rounded-lg p-8 text-center">
              <Loader2 className="w-12 h-12 mx-auto mb-4 text-blue-600 animate-spin" />
              <p className="text-gray-600">Generating Currie Financial Model...</p>
              <p className="text-sm text-gray-500 mt-1">
                Pulling live data from Softbase Evolution
              </p>
            </div>
          )}

          {reportError && (
            <div className="bg-white shadow rounded-lg p-8">
              <div className="flex items-center justify-center text-red-600 mb-4">
                <AlertCircle className="w-8 h-8 mr-2" />
                <span className="font-semibold">Error Generating Report</span>
              </div>
              <p className="text-center text-gray-600">
                {reportError.message || 'Failed to generate report. Please check that the dealer has an active ERP connection.'}
              </p>
            </div>
          )}

          {report && !reportLoading && (
            <div className="bg-white shadow rounded-lg overflow-hidden">
              {/* Report Header */}
              <div className="bg-blue-600 text-white p-6">
                <h2 className="text-xl font-bold">Currie Financial Model</h2>
                <p className="text-blue-100 mt-1">
                  {report.dealership_info?.name} | {report.dealership_info?.start_date} to {report.dealership_info?.end_date}
                </p>
                <p className="text-blue-100 text-sm">
                  {report.dealership_info?.num_months} month(s) | Generated: {reportData.generated_at}
                </p>
              </div>

              <div className="p-6 space-y-6">
                {/* Sales/COGS/GP Section */}
                <ReportSection title="Sales, Cost of Goods Sold &amp; Gross Profit">
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-100">
                        <tr>
                          <th className="py-2 px-3 text-left">Department</th>
                          <th className="py-2 px-3 text-right">Sales</th>
                          <th className="py-2 px-3 text-right">COGS</th>
                          <th className="py-2 px-3 text-right">Gross Profit</th>
                          <th className="py-2 px-3 text-right">GP %</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {/* New Equipment */}
                        <tr className="bg-blue-50">
                          <td colSpan={5} className="py-2 px-3 font-semibold text-blue-800">
                            NEW EQUIPMENT
                          </td>
                        </tr>
                        {report.new_equipment && Object.entries(report.new_equipment).map(([key, data]) => (
                          <FinancialRow
                            key={key}
                            label={key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            sales={data.sales}
                            cogs={data.cogs}
                            grossProfit={data.gross_profit}
                            indent={1}
                          />
                        ))}
                        <FinancialRow
                          label="TOTAL SALES DEPT"
                          sales={report.totals?.total_sales_dept?.sales}
                          cogs={report.totals?.total_sales_dept?.cogs}
                          grossProfit={report.totals?.total_sales_dept?.gross_profit}
                          isTotal
                        />

                        {/* Rental */}
                        <tr className="bg-green-50">
                          <td colSpan={5} className="py-2 px-3 font-semibold text-green-800">
                            RENTAL
                          </td>
                        </tr>
                        <FinancialRow
                          label="Rental Revenue"
                          sales={report.rental?.sales}
                          cogs={report.rental?.cogs}
                          grossProfit={report.rental?.gross_profit}
                          indent={1}
                        />
                        <FinancialRow
                          label="TOTAL RENTAL"
                          sales={report.totals?.total_rental?.sales}
                          cogs={report.totals?.total_rental?.cogs}
                          grossProfit={report.totals?.total_rental?.gross_profit}
                          isTotal
                        />

                        {/* Service */}
                        <tr className="bg-orange-50">
                          <td colSpan={5} className="py-2 px-3 font-semibold text-orange-800">
                            SERVICE
                          </td>
                        </tr>
                        {report.service && Object.entries(report.service).map(([key, data]) => (
                          <FinancialRow
                            key={key}
                            label={key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            sales={data.sales}
                            cogs={data.cogs}
                            grossProfit={data.gross_profit}
                            indent={1}
                          />
                        ))}
                        <FinancialRow
                          label="TOTAL SERVICE"
                          sales={report.totals?.total_service?.sales}
                          cogs={report.totals?.total_service?.cogs}
                          grossProfit={report.totals?.total_service?.gross_profit}
                          isTotal
                        />

                        {/* Parts */}
                        <tr className="bg-purple-50">
                          <td colSpan={5} className="py-2 px-3 font-semibold text-purple-800">
                            PARTS
                          </td>
                        </tr>
                        {report.parts && Object.entries(report.parts).map(([key, data]) => (
                          <FinancialRow
                            key={key}
                            label={key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            sales={data.sales}
                            cogs={data.cogs}
                            grossProfit={data.gross_profit}
                            indent={1}
                          />
                        ))}
                        <FinancialRow
                          label="TOTAL PARTS"
                          sales={report.totals?.total_parts?.sales}
                          cogs={report.totals?.total_parts?.cogs}
                          grossProfit={report.totals?.total_parts?.gross_profit}
                          isTotal
                        />

                        {/* Trucking */}
                        <tr className="bg-gray-100">
                          <td colSpan={5} className="py-2 px-3 font-semibold text-gray-800">
                            TRUCKING
                          </td>
                        </tr>
                        <FinancialRow
                          label="Trucking/Delivery"
                          sales={report.trucking?.sales}
                          cogs={report.trucking?.cogs}
                          grossProfit={report.trucking?.gross_profit}
                          indent={1}
                        />

                        {/* Grand Total */}
                        <tr className="bg-blue-100 font-bold">
                          <td className="py-3 px-3">TOTAL COMPANY</td>
                          <td className="py-3 px-3 text-right">{formatCurrency(report.totals?.total_company?.sales)}</td>
                          <td className="py-3 px-3 text-right">{formatCurrency(report.totals?.total_company?.cogs)}</td>
                          <td className="py-3 px-3 text-right">{formatCurrency(report.totals?.total_company?.gross_profit)}</td>
                          <td className="py-3 px-3 text-right">
                            {report.totals?.total_company?.sales > 0
                              ? formatPercent(report.totals.total_company.gross_profit / report.totals.total_company.sales)
                              : '0.0%'}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </ReportSection>

                {/* Expenses Section */}
                <ReportSection title="Expenses">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h4 className="font-semibold text-gray-700 mb-2">Personnel</h4>
                      <p className="text-2xl font-bold text-gray-900">
                        {formatCurrency(report.expenses?.personnel?.total)}
                      </p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h4 className="font-semibold text-gray-700 mb-2">Operating</h4>
                      <p className="text-2xl font-bold text-gray-900">
                        {formatCurrency(report.expenses?.operating?.total)}
                      </p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h4 className="font-semibold text-gray-700 mb-2">Occupancy</h4>
                      <p className="text-2xl font-bold text-gray-900">
                        {formatCurrency(report.expenses?.occupancy?.total)}
                      </p>
                    </div>
                  </div>
                  <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                    <div className="flex justify-between items-center">
                      <span className="font-semibold text-blue-800">Total Expenses</span>
                      <span className="text-2xl font-bold text-blue-900">
                        {formatCurrency(report.expenses?.grand_total)}
                      </span>
                    </div>
                  </div>
                </ReportSection>

                {/* Summary Section */}
                <ReportSection title="Bottom Line Summary">
                  <div className="space-y-3">
                    <div className="flex justify-between p-3 bg-gray-50 rounded">
                      <span>Total Gross Profit</span>
                      <span className="font-semibold">{formatCurrency(report.totals?.total_company?.gross_profit)}</span>
                    </div>
                    <div className="flex justify-between p-3 bg-gray-50 rounded">
                      <span>Less: Total Expenses</span>
                      <span className="font-semibold text-red-600">({formatCurrency(report.expenses?.grand_total)})</span>
                    </div>
                    <div className="flex justify-between p-3 bg-gray-50 rounded">
                      <span>Other Income</span>
                      <span className="font-semibold">{formatCurrency(report.other_income)}</span>
                    </div>
                    <div className="flex justify-between p-3 bg-gray-50 rounded">
                      <span>Interest Expense</span>
                      <span className="font-semibold">{formatCurrency(report.interest_expense)}</span>
                    </div>
                    <div className="flex justify-between p-4 bg-green-100 rounded-lg">
                      <span className="font-bold text-green-800">Operating Profit</span>
                      <span className="text-xl font-bold text-green-900">{formatCurrency(report.total_operating_profit)}</span>
                    </div>
                    <div className="flex justify-between p-3 bg-gray-50 rounded">
                      <span>F&amp;I Income</span>
                      <span className="font-semibold">{formatCurrency(report.fi_income)}</span>
                    </div>
                    <div className="flex justify-between p-4 bg-blue-100 rounded-lg">
                      <span className="font-bold text-blue-800">Pre-Tax Income</span>
                      <span className="text-xl font-bold text-blue-900">{formatCurrency(report.pre_tax_income)}</span>
                    </div>
                  </div>
                </ReportSection>

                {/* AR Aging Section */}
                {report.ar_aging && (
                  <ReportSection title="Accounts Receivable Aging" defaultOpen={false}>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                      <div className="bg-green-50 p-4 rounded-lg">
                        <h4 className="text-sm text-green-700">Current</h4>
                        <p className="text-lg font-bold text-green-900">{formatCurrency(report.ar_aging.current)}</p>
                      </div>
                      <div className="bg-yellow-50 p-4 rounded-lg">
                        <h4 className="text-sm text-yellow-700">31-60 Days</h4>
                        <p className="text-lg font-bold text-yellow-900">{formatCurrency(report.ar_aging.days_31_60)}</p>
                      </div>
                      <div className="bg-orange-50 p-4 rounded-lg">
                        <h4 className="text-sm text-orange-700">61-90 Days</h4>
                        <p className="text-lg font-bold text-orange-900">{formatCurrency(report.ar_aging.days_61_90)}</p>
                      </div>
                      <div className="bg-red-50 p-4 rounded-lg">
                        <h4 className="text-sm text-red-700">91+ Days</h4>
                        <p className="text-lg font-bold text-red-900">{formatCurrency(report.ar_aging.days_91_plus)}</p>
                      </div>
                      <div className="bg-gray-100 p-4 rounded-lg">
                        <h4 className="text-sm text-gray-700">Total AR</h4>
                        <p className="text-lg font-bold text-gray-900">{formatCurrency(report.ar_aging.total)}</p>
                      </div>
                    </div>
                  </ReportSection>
                )}

                {/* Balance Sheet Section */}
                {report.balance_sheet && Object.keys(report.balance_sheet).length > 0 && (
                  <ReportSection title="Balance Sheet Summary" defaultOpen={false}>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h4 className="font-semibold text-gray-700 mb-3">Assets</h4>
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span>Cash</span>
                            <span>{formatCurrency(report.balance_sheet.cash)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Accounts Receivable</span>
                            <span>{formatCurrency(report.balance_sheet.accounts_receivable)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Inventory</span>
                            <span>{formatCurrency(report.balance_sheet.inventory)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Fixed Assets</span>
                            <span>{formatCurrency(report.balance_sheet.fixed_assets)}</span>
                          </div>
                        </div>
                      </div>
                      <div>
                        <h4 className="font-semibold text-gray-700 mb-3">Liabilities &amp; Equity</h4>
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span>Accounts Payable</span>
                            <span>{formatCurrency(report.balance_sheet.accounts_payable)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Other Current Liabilities</span>
                            <span>{formatCurrency(report.balance_sheet.other_current_liabilities)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Long Term Debt</span>
                            <span>{formatCurrency(report.balance_sheet.long_term_debt)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Equity</span>
                            <span>{formatCurrency(report.balance_sheet.equity)}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </ReportSection>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Recent Reports - when no report is shown */}
      {!showReport && (
        <div className="mt-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Recent Reports
          </h2>
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="p-8 text-center text-gray-500">
              <Calendar className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>No reports generated yet</p>
              <p className="text-sm mt-1">
                Generate your first report using the options above
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
