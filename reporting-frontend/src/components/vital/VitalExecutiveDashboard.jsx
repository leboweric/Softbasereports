import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts'
import {
  DollarSign,
  FileText,
  Users,
  Clock
} from 'lucide-react'

// VITAL Worklife Executive Dashboard with seeded data
const VitalExecutiveDashboard = ({ user, loading }) => {
  // Sample data for visualizations
  const caseVolumeData = [
    { month: 'Jan', cases: 45, resolved: 42 },
    { month: 'Feb', cases: 52, resolved: 48 },
    { month: 'Mar', cases: 48, resolved: 46 },
    { month: 'Apr', cases: 61, resolved: 58 },
    { month: 'May', cases: 55, resolved: 52 },
    { month: 'Jun', cases: 67, resolved: 64 },
  ];

  const conversionData = [
    { stage: 'Leads', value: 1200 },
    { stage: 'Prospects', value: 850 },
    { stage: 'Qualified', value: 620 },
    { stage: 'Closed', value: 380 },
  ];

  const openCases = [
    { id: 'CS-001', client: 'Acme Corp', status: 'In Progress', daysOpen: 12, priority: 'High' },
    { id: 'CS-002', client: 'TechStart Inc', status: 'Pending Review', daysOpen: 8, priority: 'Medium' },
    { id: 'CS-003', client: 'Global Solutions', status: 'In Progress', daysOpen: 5, priority: 'High' },
    { id: 'CS-004', client: 'Innovation Labs', status: 'Awaiting Client', daysOpen: 3, priority: 'Low' },
    { id: 'CS-005', client: 'Enterprise Group', status: 'In Progress', daysOpen: 15, priority: 'Critical' },
  ];

  const getPriorityColor = (priority) => {
    switch(priority) {
      case 'Critical': return 'text-red-600 bg-red-50';
      case 'High': return 'text-orange-600 bg-orange-50';
      case 'Medium': return 'text-yellow-600 bg-yellow-50';
      case 'Low': return 'text-green-600 bg-green-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const StatCard = ({ title, value, icon: Icon, color, trend }) => (
    <Card className="shadow-lg">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className={`h-4 w-4 text-${color}-500`} />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <p className="text-xs text-gray-500">{trend || '+20.1% from last month'}</p>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <div className="flex justify-center items-center h-full">
        <LoadingSpinner size={50} />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight">AI Operations Platform</h1>
        <p className="text-gray-600">Welcome back, {user?.first_name || 'User'}! Here's what's happening with your business.</p>
      </div>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard 
          title="Total Cases Closed" 
          value="1,250" 
          icon={FileText} 
          color="blue"
          trend="+8.2% from last month"
        />
        <StatCard 
          title="Avg. Resolution Time" 
          value="4.5 Days" 
          icon={Clock} 
          color="red"
          trend="↓ 12% improvement"
        />
        <StatCard 
          title="New Clients (HubSpot)" 
          value="+12" 
          icon={Users} 
          color="purple"
          trend="+5 from last month"
        />
        <StatCard 
          title="Monthly Revenue" 
          value="$150K" 
          icon={DollarSign} 
          color="green"
          trend="+15.3% from last month"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle>Case Volume Trend</CardTitle>
            <CardDescription>Monthly cases and resolutions</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={caseVolumeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="cases" fill="#3b82f6" name="Total Cases" radius={[4, 4, 0, 0]} />
                <Bar dataKey="resolved" fill="#10b981" name="Resolved" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle>Marketing Funnel Conversion</CardTitle>
            <CardDescription>Lead to close conversion rates</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={conversionData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="stage" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#8b5cf6" name="Count" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle>Top 5 Open Cases</CardTitle>
          <CardDescription>Active cases requiring attention</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 px-2">Case ID</th>
                  <th className="text-left py-2 px-2">Client</th>
                  <th className="text-left py-2 px-2">Status</th>
                  <th className="text-left py-2 px-2">Days Open</th>
                  <th className="text-left py-2 px-2">Priority</th>
                </tr>
              </thead>
              <tbody>
                {openCases.map((caseItem) => (
                  <tr key={caseItem.id} className="border-b hover:bg-gray-50">
                    <td className="font-medium py-2 px-2">{caseItem.id}</td>
                    <td className="py-2 px-2">{caseItem.client}</td>
                    <td className="py-2 px-2">{caseItem.status}</td>
                    <td className="py-2 px-2">{caseItem.daysOpen}</td>
                    <td className="py-2 px-2">
                      <Badge className={getPriorityColor(caseItem.priority)}>
                        {caseItem.priority}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default VitalExecutiveDashboard;
