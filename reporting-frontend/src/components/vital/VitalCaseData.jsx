import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { ClipboardList, Users, Clock, TrendingUp, AlertCircle, CheckCircle, BarChart3 } from 'lucide-react';

const VitalCaseData = ({ user }) => {
  const [activeTab, setActiveTab] = useState('overview');

  // Sample/placeholder data for demo
  const sampleMetrics = {
    totalCases: 1247,
    activeCases: 342,
    resolvedThisMonth: 156,
    avgResolutionTime: '4.2 days',
    clientSatisfaction: '94%',
    newCasesThisWeek: 47
  };

  const sampleCasesByType = [
    { type: 'Counseling', count: 423, percentage: 34 },
    { type: 'Coaching', count: 312, percentage: 25 },
    { type: 'Crisis Support', count: 187, percentage: 15 },
    { type: 'Work-Life Services', count: 156, percentage: 12 },
    { type: 'Legal/Financial', count: 112, percentage: 9 },
    { type: 'Other', count: 57, percentage: 5 },
  ];

  const sampleRecentCases = [
    { id: 'C-2024-1247', type: 'Counseling', status: 'Active', assignee: 'Dr. Smith', created: '2024-01-15' },
    { id: 'C-2024-1246', type: 'Coaching', status: 'In Progress', assignee: 'J. Williams', created: '2024-01-14' },
    { id: 'C-2024-1245', type: 'Crisis Support', status: 'Resolved', assignee: 'M. Johnson', created: '2024-01-14' },
    { id: 'C-2024-1244', type: 'Work-Life', status: 'Active', assignee: 'S. Davis', created: '2024-01-13' },
    { id: 'C-2024-1243', type: 'Legal/Financial', status: 'Pending', assignee: 'R. Brown', created: '2024-01-12' },
  ];

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Case Data</h1>
        <p className="text-gray-500">Case management analytics from BigQuery</p>
      </div>

      {/* Alert for demo mode */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start gap-3">
        <AlertCircle className="h-5 w-5 text-blue-500 mt-0.5" />
        <div>
          <p className="text-sm text-blue-700 font-medium">Demo Mode</p>
          <p className="text-sm text-blue-600">
            This page shows sample data. Connect your BigQuery data source in Data Sources to see real case data.
          </p>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-gray-500 text-sm">
              <ClipboardList className="h-4 w-4" />
              Total Cases
            </div>
            <p className="text-2xl font-bold mt-1">{sampleMetrics.totalCases.toLocaleString()}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-gray-500 text-sm">
              <Users className="h-4 w-4" />
              Active Cases
            </div>
            <p className="text-2xl font-bold mt-1 text-blue-600">{sampleMetrics.activeCases}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-gray-500 text-sm">
              <CheckCircle className="h-4 w-4" />
              Resolved (Month)
            </div>
            <p className="text-2xl font-bold mt-1 text-green-600">{sampleMetrics.resolvedThisMonth}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-gray-500 text-sm">
              <Clock className="h-4 w-4" />
              Avg Resolution
            </div>
            <p className="text-2xl font-bold mt-1">{sampleMetrics.avgResolutionTime}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-gray-500 text-sm">
              <TrendingUp className="h-4 w-4" />
              Satisfaction
            </div>
            <p className="text-2xl font-bold mt-1 text-green-600">{sampleMetrics.clientSatisfaction}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-gray-500 text-sm">
              <BarChart3 className="h-4 w-4" />
              New This Week
            </div>
            <p className="text-2xl font-bold mt-1">{sampleMetrics.newCasesThisWeek}</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="by-type">By Type</TabsTrigger>
          <TabsTrigger value="recent">Recent Cases</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Cases by Type</CardTitle>
                <CardDescription>Distribution of cases across service types</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {sampleCasesByType.map((item) => (
                    <div key={item.type} className="flex items-center gap-3">
                      <div className="w-24 text-sm text-gray-600">{item.type}</div>
                      <div className="flex-1 bg-gray-100 rounded-full h-4">
                        <div 
                          className="bg-blue-500 h-4 rounded-full"
                          style={{ width: `${item.percentage}%` }}
                        />
                      </div>
                      <div className="w-16 text-right text-sm font-medium">{item.count}</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Case Volume Trend</CardTitle>
                <CardDescription>Monthly case volume over time</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-48 flex items-end justify-between gap-2">
                  {[65, 78, 82, 71, 89, 95, 88, 92, 85, 91, 97, 103].map((value, i) => (
                    <div key={i} className="flex-1 flex flex-col items-center gap-1">
                      <div 
                        className="w-full bg-blue-500 rounded-t"
                        style={{ height: `${(value / 110) * 100}%` }}
                      />
                      <span className="text-xs text-gray-500">
                        {['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'][i]}
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="by-type">
          <Card>
            <CardHeader>
              <CardTitle>Detailed Case Type Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">Case Type</th>
                    <th className="text-right py-2">Total</th>
                    <th className="text-right py-2">Active</th>
                    <th className="text-right py-2">Resolved</th>
                    <th className="text-right py-2">Avg Time</th>
                  </tr>
                </thead>
                <tbody>
                  {sampleCasesByType.map((item) => (
                    <tr key={item.type} className="border-b">
                      <td className="py-2">{item.type}</td>
                      <td className="text-right py-2">{item.count}</td>
                      <td className="text-right py-2 text-blue-600">{Math.round(item.count * 0.27)}</td>
                      <td className="text-right py-2 text-green-600">{Math.round(item.count * 0.73)}</td>
                      <td className="text-right py-2">{(3 + Math.random() * 3).toFixed(1)} days</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="recent">
          <Card>
            <CardHeader>
              <CardTitle>Recent Cases</CardTitle>
              <CardDescription>Latest case activity</CardDescription>
            </CardHeader>
            <CardContent>
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">Case ID</th>
                    <th className="text-left py-2">Type</th>
                    <th className="text-left py-2">Status</th>
                    <th className="text-left py-2">Assignee</th>
                    <th className="text-left py-2">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {sampleRecentCases.map((caseItem) => (
                    <tr key={caseItem.id} className="border-b hover:bg-gray-50">
                      <td className="py-2 font-mono text-sm">{caseItem.id}</td>
                      <td className="py-2">{caseItem.type}</td>
                      <td className="py-2">
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          caseItem.status === 'Resolved' ? 'bg-green-100 text-green-700' :
                          caseItem.status === 'Active' ? 'bg-blue-100 text-blue-700' :
                          caseItem.status === 'In Progress' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {caseItem.status}
                        </span>
                      </td>
                      <td className="py-2">{caseItem.assignee}</td>
                      <td className="py-2 text-gray-500">{caseItem.created}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trends">
          <Card>
            <CardHeader>
              <CardTitle>Case Trends & Analytics</CardTitle>
              <CardDescription>Historical trends and forecasting</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12 text-gray-500">
                <BarChart3 className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>Connect your BigQuery data source to view detailed trends and analytics</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default VitalCaseData;
