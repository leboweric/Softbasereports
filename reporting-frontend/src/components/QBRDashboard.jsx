import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command';
import { apiUrl } from '@/lib/api';
import { cn } from '@/lib/utils';
import {
  Download,
  Save,
  RefreshCw,
  FileBarChart,
  Truck,
  Wrench,
  DollarSign,
  AlertTriangle,
  CheckCircle,
  Clock,
  Package,
  TrendingUp,
  Lightbulb,
  ClipboardList,
  Building,
  ChevronsUpDown,
  Check
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';

const QBRDashboard = () => {
  // Customer and Quarter selection
  const [customers, setCustomers] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState('');
  const [selectedQuarter, setSelectedQuarter] = useState('Q4-2025');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [customerSearchOpen, setCustomerSearchOpen] = useState(false);

  // QBR Data
  const [qbrData, setQbrData] = useState(null);

  // Manual inputs (Phase 3)
  const [businessPriorities, setBusinessPriorities] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [actionItems, setActionItems] = useState([]);

  // Export state
  const [exporting, setExporting] = useState(false);
  const [saving, setSaving] = useState(false);

  // Fetch customers on mount
  useEffect(() => {
    fetchCustomers();
  }, []);

  // Fetch QBR data when customer or quarter changes
  useEffect(() => {
    if (selectedCustomer && selectedQuarter) {
      fetchQBRData();
    }
  }, [selectedCustomer, selectedQuarter]);

  const fetchCustomers = async () => {
    try {
      const response = await fetch(apiUrl('/api/qbr/customers'), {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) throw new Error('Failed to fetch customers');

      const data = await response.json();
      setCustomers(data.customers || []);
    } catch (err) {
      console.error('Error fetching customers:', err);
      setError(err.message);
    }
  };

  const fetchQBRData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        apiUrl(`/api/qbr/${selectedCustomer}/data?quarter=${selectedQuarter}`),
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      if (!response.ok) throw new Error('Failed to fetch QBR data');

      const data = await response.json();
      setQbrData(data.data);

      // Set auto-generated recommendations
      if (data.data?.recommendations) {
        setRecommendations(data.data.recommendations);
      }
    } catch (err) {
      console.error('Error fetching QBR data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveQBR = async () => {
    try {
      setSaving(true);

      const response = await fetch(apiUrl(`/api/qbr/${selectedCustomer}/save`), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          quarter: selectedQuarter.replace('-', ' '),
          business_priorities: businessPriorities,
          custom_recommendations: recommendations,
          action_items: actionItems
        })
      });

      if (!response.ok) throw new Error('Failed to save QBR');

      const data = await response.json();
      alert(`QBR saved successfully! ID: ${data.qbr_id}`);
    } catch (err) {
      console.error('Error saving QBR:', err);
      alert(`Error saving QBR: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleExportPowerPoint = async () => {
    if (!qbrData) return;

    try {
      setExporting(true);

      const qbrId = `QBR-${selectedQuarter}-${selectedCustomer}`;

      const response = await fetch(apiUrl(`/api/qbr/${qbrId}/export`), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...qbrData,
          business_priorities: businessPriorities,
          recommendations: recommendations,
          action_items: actionItems
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to export PowerPoint');
      }

      // Check if we got a file or JSON response
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/vnd.openxmlformats')) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${qbrId}.pptx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
      } else {
        const data = await response.json();
        alert(data.message || 'Export initiated');
      }
    } catch (err) {
      console.error('Error exporting PowerPoint:', err);
      alert(`Error exporting: ${err.message}`);
    } finally {
      setExporting(false);
    }
  };

  // Generate quarter options
  const quarterOptions = [
    'Q1-2025', 'Q2-2025', 'Q3-2025', 'Q4-2025',
    'Q1-2024', 'Q2-2024', 'Q3-2024', 'Q4-2024'
  ];

  // Colors for charts
  const COLORS = ['#22c55e', '#f59e0b', '#ef4444', '#6366f1', '#8b5cf6'];
  const HEALTH_COLORS = {
    good: '#22c55e',
    monitor: '#f59e0b',
    replace: '#ef4444'
  };

  // Format currency
  const formatCurrency = (value) => {
    if (value === null || value === undefined) return '$0';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  // Format percentage
  const formatPercent = (value) => {
    if (value === null || value === undefined) return '0%';
    return `${(value * 100).toFixed(1)}%`;
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <FileBarChart className="h-7 w-7" />
            Quarterly Business Review
          </h1>
          <p className="text-gray-500">Generate QBR presentations for customers</p>
        </div>

        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={fetchQBRData}
            disabled={!selectedCustomer || loading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button
            variant="outline"
            onClick={handleSaveQBR}
            disabled={!qbrData || saving}
          >
            <Save className="h-4 w-4 mr-2" />
            {saving ? 'Saving...' : 'Save'}
          </Button>
          <Button
            onClick={handleExportPowerPoint}
            disabled={!qbrData || exporting}
          >
            <Download className="h-4 w-4 mr-2" />
            {exporting ? 'Exporting...' : 'Export PowerPoint'}
          </Button>
        </div>
      </div>

      {/* Customer and Quarter Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building className="h-5 w-5" />
            Select Customer & Quarter
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium mb-2">Customer</label>
              <Popover open={customerSearchOpen} onOpenChange={setCustomerSearchOpen}>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    role="combobox"
                    aria-expanded={customerSearchOpen}
                    className="w-full justify-between font-normal"
                  >
                    {selectedCustomer
                      ? customers.find((c) => c.customer_number === selectedCustomer)?.customer_name
                      : "Search for a customer..."}
                    <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-[400px] p-0" align="start">
                  <Command>
                    <CommandInput placeholder="Type to search customers..." />
                    <CommandList>
                      <CommandEmpty>No customer found.</CommandEmpty>
                      <CommandGroup>
                        {customers.map((customer) => (
                          <CommandItem
                            key={customer.customer_number}
                            value={customer.customer_name}
                            onSelect={() => {
                              setSelectedCustomer(customer.customer_number);
                              setCustomerSearchOpen(false);
                            }}
                          >
                            <Check
                              className={cn(
                                "mr-2 h-4 w-4",
                                selectedCustomer === customer.customer_number ? "opacity-100" : "opacity-0"
                              )}
                            />
                            {customer.customer_name}
                          </CommandItem>
                        ))}
                      </CommandGroup>
                    </CommandList>
                  </Command>
                </PopoverContent>
              </Popover>
            </div>
            <div className="w-48">
              <label className="block text-sm font-medium mb-2">Quarter</label>
              <Select value={selectedQuarter} onValueChange={setSelectedQuarter}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {quarterOptions.map((q) => (
                    <SelectItem key={q} value={q}>{q.replace('-', ' ')}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error State */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-red-700">
              <AlertTriangle className="h-5 w-5" />
              <span>{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center p-12">
          <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
          <span className="ml-2 text-gray-500">Loading QBR data...</span>
        </div>
      )}

      {/* QBR Content */}
      {qbrData && !loading && (
        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList>
            <TabsTrigger value="overview">Fleet Overview</TabsTrigger>
            <TabsTrigger value="health">Fleet Health</TabsTrigger>
            <TabsTrigger value="service">Service Performance</TabsTrigger>
            <TabsTrigger value="costs">Costs & Value</TabsTrigger>
            <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
          </TabsList>

          {/* Fleet Overview Tab */}
          <TabsContent value="overview" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">Total Units</p>
                      <p className="text-2xl font-bold">{qbrData.fleet_overview?.total_units || 0}</p>
                    </div>
                    <Truck className="h-8 w-8 text-blue-500" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">Under Contract</p>
                      <p className="text-2xl font-bold">{qbrData.fleet_overview?.under_contract || 0}</p>
                    </div>
                    <CheckCircle className="h-8 w-8 text-green-500" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">Avg Fleet Age</p>
                      <p className="text-2xl font-bold">{qbrData.fleet_overview?.avg_age?.toFixed(1) || 0} yrs</p>
                    </div>
                    <Clock className="h-8 w-8 text-amber-500" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">Service Calls</p>
                      <p className="text-2xl font-bold">{qbrData.fleet_overview?.service_calls || 0}</p>
                    </div>
                    <Wrench className="h-8 w-8 text-purple-500" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Equipment by Type Chart */}
            {qbrData.fleet_overview?.equipment_by_type && (
              <Card>
                <CardHeader>
                  <CardTitle>Equipment by Type</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={qbrData.fleet_overview.equipment_by_type}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="equipment_type" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Fleet Health Tab */}
          <TabsContent value="health" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card className="border-green-200">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">Good Condition</p>
                      <p className="text-2xl font-bold text-green-600">
                        {qbrData.fleet_health?.good || 0}
                      </p>
                    </div>
                    <CheckCircle className="h-8 w-8 text-green-500" />
                  </div>
                </CardContent>
              </Card>

              <Card className="border-amber-200">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">Monitor</p>
                      <p className="text-2xl font-bold text-amber-600">
                        {qbrData.fleet_health?.monitor || 0}
                      </p>
                    </div>
                    <AlertTriangle className="h-8 w-8 text-amber-500" />
                  </div>
                </CardContent>
              </Card>

              <Card className="border-red-200">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">Replace</p>
                      <p className="text-2xl font-bold text-red-600">
                        {qbrData.fleet_health?.replace || 0}
                      </p>
                    </div>
                    <AlertTriangle className="h-8 w-8 text-red-500" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Health Distribution Pie Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Fleet Health Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={[
                          { name: 'Good', value: qbrData.fleet_health?.good || 0 },
                          { name: 'Monitor', value: qbrData.fleet_health?.monitor || 0 },
                          { name: 'Replace', value: qbrData.fleet_health?.replace || 0 }
                        ]}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        paddingAngle={5}
                        dataKey="value"
                        label
                      >
                        <Cell fill={HEALTH_COLORS.good} />
                        <Cell fill={HEALTH_COLORS.monitor} />
                        <Cell fill={HEALTH_COLORS.replace} />
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Units Needing Attention */}
            {qbrData.fleet_health?.units_needing_attention?.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5 text-amber-500" />
                    Units Requiring Attention
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left p-2">Unit</th>
                          <th className="text-left p-2">Make/Model</th>
                          <th className="text-left p-2">Age</th>
                          <th className="text-left p-2">Annual Cost</th>
                          <th className="text-left p-2">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {qbrData.fleet_health.units_needing_attention.map((unit, idx) => (
                          <tr key={idx} className="border-b">
                            <td className="p-2">{unit.unit_no}</td>
                            <td className="p-2">{unit.make} {unit.model}</td>
                            <td className="p-2">{unit.age_years?.toFixed(1)} yrs</td>
                            <td className="p-2">{formatCurrency(unit.annual_cost)}</td>
                            <td className="p-2">
                              <span className={`px-2 py-1 rounded text-xs ${
                                unit.status === 'replace'
                                  ? 'bg-red-100 text-red-700'
                                  : 'bg-amber-100 text-amber-700'
                              }`}>
                                {unit.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Service Performance Tab */}
          <TabsContent value="service" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">Total Work Orders</p>
                      <p className="text-2xl font-bold">{qbrData.service_performance?.total_work_orders || 0}</p>
                    </div>
                    <ClipboardList className="h-8 w-8 text-blue-500" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">PM Compliance</p>
                      <p className="text-2xl font-bold text-green-600">
                        {formatPercent(qbrData.service_performance?.pm_compliance)}
                      </p>
                    </div>
                    <CheckCircle className="h-8 w-8 text-green-500" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">Avg Response Time</p>
                      <p className="text-2xl font-bold">
                        {qbrData.service_performance?.avg_response_time?.toFixed(1) || 0} hrs
                      </p>
                    </div>
                    <Clock className="h-8 w-8 text-amber-500" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">First-Time Fix Rate</p>
                      <p className="text-2xl font-bold">
                        {formatPercent(qbrData.service_performance?.first_time_fix_rate)}
                      </p>
                    </div>
                    <Wrench className="h-8 w-8 text-purple-500" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Work Orders by Type */}
            {qbrData.service_performance?.by_type && (
              <Card>
                <CardHeader>
                  <CardTitle>Work Orders by Type</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={qbrData.service_performance.by_type}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="type" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Costs & Value Tab */}
          <TabsContent value="costs" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Service Costs */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <DollarSign className="h-5 w-5" />
                    Service Costs
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-500">Total Service Cost</span>
                      <span className="text-xl font-bold">
                        {formatCurrency(qbrData.service_costs?.total_service_cost)}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-500">Labor</span>
                      <span>{formatCurrency(qbrData.service_costs?.labor_cost)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-500">Parts</span>
                      <span>{formatCurrency(qbrData.service_costs?.parts_cost)}</span>
                    </div>
                    <div className="flex justify-between items-center border-t pt-2">
                      <span className="text-gray-500">Cost Per Unit</span>
                      <span>{formatCurrency(qbrData.service_costs?.cost_per_unit)}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Parts & Rentals */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Package className="h-5 w-5" />
                    Parts & Rentals
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-500">Parts Purchases</span>
                      <span className="text-xl font-bold">
                        {formatCurrency(qbrData.parts_rentals?.parts_total)}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-500">Rental Revenue</span>
                      <span>{formatCurrency(qbrData.parts_rentals?.rental_revenue)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-500">Rental Days</span>
                      <span>{qbrData.parts_rentals?.rental_days || 0}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Value Delivered */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-green-500" />
                  Value Delivered
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <p className="text-sm text-gray-500">PM Savings</p>
                    <p className="text-2xl font-bold text-green-600">
                      {formatCurrency(qbrData.value_delivered?.pm_savings)}
                    </p>
                    <p className="text-xs text-gray-400">vs. reactive maintenance</p>
                  </div>
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <p className="text-sm text-gray-500">Uptime Value</p>
                    <p className="text-2xl font-bold text-blue-600">
                      {formatCurrency(qbrData.value_delivered?.uptime_value)}
                    </p>
                    <p className="text-xs text-gray-400">avoided downtime costs</p>
                  </div>
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <p className="text-sm text-gray-500">Total ROI</p>
                    <p className="text-2xl font-bold text-purple-600">
                      {formatCurrency(qbrData.value_delivered?.total_value)}
                    </p>
                    <p className="text-xs text-gray-400">partnership value</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Recommendations Tab */}
          <TabsContent value="recommendations" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lightbulb className="h-5 w-5 text-amber-500" />
                  Recommendations
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recommendations.length > 0 ? (
                    recommendations.map((rec, idx) => (
                      <div key={idx} className="p-4 border rounded-lg">
                        <div className="flex items-start gap-3">
                          <div className={`p-2 rounded ${
                            rec.category === 'equipment_refresh' ? 'bg-red-100' :
                            rec.category === 'safety_training' ? 'bg-amber-100' :
                            'bg-blue-100'
                          }`}>
                            {rec.category === 'equipment_refresh' ? (
                              <AlertTriangle className="h-5 w-5 text-red-600" />
                            ) : rec.category === 'safety_training' ? (
                              <AlertTriangle className="h-5 w-5 text-amber-600" />
                            ) : (
                              <TrendingUp className="h-5 w-5 text-blue-600" />
                            )}
                          </div>
                          <div className="flex-1">
                            <h4 className="font-medium">{rec.title}</h4>
                            <p className="text-sm text-gray-500 mt-1">{rec.description}</p>
                            {rec.estimated_impact && (
                              <p className="text-sm text-green-600 mt-2">
                                Estimated Impact: {rec.estimated_impact}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-gray-500 text-center py-8">
                      No recommendations generated. Select a customer to see recommendations.
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}

      {/* Empty State */}
      {!qbrData && !loading && !error && (
        <Card>
          <CardContent className="p-12 text-center">
            <FileBarChart className="h-16 w-16 mx-auto text-gray-300 mb-4" />
            <h3 className="text-lg font-medium text-gray-700">Select a Customer</h3>
            <p className="text-gray-500 mt-2">
              Choose a customer and quarter above to generate the QBR dashboard
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default QBRDashboard;
