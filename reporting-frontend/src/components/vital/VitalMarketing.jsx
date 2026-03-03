import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { TrendingUp, Users, Mail, MousePointer, Target, Calendar, AlertCircle, ArrowUpRight, ArrowDownRight } from 'lucide-react';

const VitalMarketing = ({ user }) => {
  const [activeTab, setActiveTab] = useState('overview');

  // Sample/placeholder data for demo
  const sampleMetrics = {
    totalContacts: 12847,
    contactsChange: 8.3,
    newLeads: 342,
    leadsChange: 15.2,
    emailsSent: 45600,
    openRate: 24.7,
    clickRate: 3.8,
    websiteVisits: 28450,
    visitsChange: 12.1,
    conversionRate: 2.4,
  };

  const sampleLeadsBySource = [
    { source: 'Website', count: 145, percentage: 42 },
    { source: 'Email Campaign', count: 78, percentage: 23 },
    { source: 'Referral', count: 52, percentage: 15 },
    { source: 'LinkedIn', count: 38, percentage: 11 },
    { source: 'Events', count: 29, percentage: 9 },
  ];

  const sampleCampaigns = [
    { name: 'Q1 Wellness Initiative', status: 'Active', sent: 12500, opened: 3125, clicked: 475, leads: 28 },
    { name: 'EAP Awareness Month', status: 'Active', sent: 8200, opened: 2132, clicked: 328, leads: 19 },
    { name: 'Mental Health Resources', status: 'Completed', sent: 15000, opened: 3900, clicked: 570, leads: 34 },
    { name: 'Leadership Coaching Promo', status: 'Scheduled', sent: 0, opened: 0, clicked: 0, leads: 0 },
    { name: 'Year-End Review', status: 'Draft', sent: 0, opened: 0, clicked: 0, leads: 0 },
  ];

  const sampleContactsByStage = [
    { stage: 'Subscriber', count: 8450, color: 'bg-gray-400' },
    { stage: 'Lead', count: 2847, color: 'bg-blue-400' },
    { stage: 'MQL', count: 892, color: 'bg-yellow-400' },
    { stage: 'SQL', count: 423, color: 'bg-orange-400' },
    { stage: 'Opportunity', count: 187, color: 'bg-green-400' },
    { stage: 'Customer', count: 48, color: 'bg-green-600' },
  ];

  const sampleMonthlyLeads = [
    { month: 'Jan', leads: 28 },
    { month: 'Feb', leads: 32 },
    { month: 'Mar', leads: 45 },
    { month: 'Apr', leads: 38 },
    { month: 'May', leads: 52 },
    { month: 'Jun', leads: 48 },
    { month: 'Jul', leads: 41 },
    { month: 'Aug', leads: 35 },
    { month: 'Sep', leads: 58 },
    { month: 'Oct', leads: 62 },
    { month: 'Nov', leads: 71 },
    { month: 'Dec', leads: 45 },
  ];

  const MetricCard = ({ title, value, change, icon: Icon, suffix = '', positive }) => (
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
        <p className="text-2xl font-bold mt-1">
          {typeof value === 'number' ? value.toLocaleString() : value}{suffix}
        </p>
      </CardContent>
    </Card>
  );

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Marketing</h1>
        <p className="text-gray-500">Marketing and CRM data from HubSpot</p>
      </div>

      {/* Alert for demo mode */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start gap-3">
        <AlertCircle className="h-5 w-5 text-blue-500 mt-0.5" />
        <div>
          <p className="text-sm text-blue-700 font-medium">Demo Mode</p>
          <p className="text-sm text-blue-600">
            This page shows sample data. Connect your HubSpot account in Data Sources to see real marketing data.
          </p>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <MetricCard 
          title="Total Contacts" 
          value={sampleMetrics.totalContacts} 
          change={sampleMetrics.contactsChange}
          icon={Users}
          positive={true}
        />
        <MetricCard 
          title="New Leads (Month)" 
          value={sampleMetrics.newLeads} 
          change={sampleMetrics.leadsChange}
          icon={Target}
          positive={true}
        />
        <MetricCard 
          title="Email Open Rate" 
          value={sampleMetrics.openRate}
          suffix="%"
          icon={Mail}
        />
        <MetricCard 
          title="Click Rate" 
          value={sampleMetrics.clickRate}
          suffix="%"
          icon={MousePointer}
        />
        <MetricCard 
          title="Website Visits" 
          value={sampleMetrics.websiteVisits} 
          change={sampleMetrics.visitsChange}
          icon={TrendingUp}
          positive={true}
        />
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="campaigns">Campaigns</TabsTrigger>
          <TabsTrigger value="leads">Leads</TabsTrigger>
          <TabsTrigger value="funnel">Funnel</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Lead Generation Trend</CardTitle>
                <CardDescription>Monthly new leads over time</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-48 flex items-end justify-between gap-2">
                  {sampleMonthlyLeads.map((item, i) => (
                    <div key={i} className="flex-1 flex flex-col items-center gap-1">
                      <div 
                        className="w-full bg-blue-500 rounded-t"
                        style={{ height: `${(item.leads / 80) * 100}%` }}
                        title={`${item.leads} leads`}
                      />
                      <span className="text-xs text-gray-500">{item.month}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Leads by Source</CardTitle>
                <CardDescription>Where your leads are coming from</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {sampleLeadsBySource.map((item) => (
                    <div key={item.source} className="flex items-center gap-3">
                      <div className="w-28 text-sm text-gray-600">{item.source}</div>
                      <div className="flex-1 bg-gray-100 rounded-full h-4">
                        <div 
                          className="bg-orange-500 h-4 rounded-full"
                          style={{ width: `${item.percentage}%` }}
                        />
                      </div>
                      <div className="w-12 text-right text-sm font-medium">{item.count}</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="campaigns">
          <Card>
            <CardHeader>
              <CardTitle>Email Campaigns</CardTitle>
              <CardDescription>Campaign performance metrics</CardDescription>
            </CardHeader>
            <CardContent>
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">Campaign</th>
                    <th className="text-left py-2">Status</th>
                    <th className="text-right py-2">Sent</th>
                    <th className="text-right py-2">Opened</th>
                    <th className="text-right py-2">Clicked</th>
                    <th className="text-right py-2">Leads</th>
                  </tr>
                </thead>
                <tbody>
                  {sampleCampaigns.map((campaign) => (
                    <tr key={campaign.name} className="border-b hover:bg-gray-50">
                      <td className="py-2 font-medium">{campaign.name}</td>
                      <td className="py-2">
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          campaign.status === 'Active' ? 'bg-green-100 text-green-700' :
                          campaign.status === 'Completed' ? 'bg-blue-100 text-blue-700' :
                          campaign.status === 'Scheduled' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {campaign.status}
                        </span>
                      </td>
                      <td className="py-2 text-right">{campaign.sent.toLocaleString()}</td>
                      <td className="py-2 text-right">
                        {campaign.opened.toLocaleString()}
                        {campaign.sent > 0 && (
                          <span className="text-gray-400 text-sm ml-1">
                            ({((campaign.opened / campaign.sent) * 100).toFixed(1)}%)
                          </span>
                        )}
                      </td>
                      <td className="py-2 text-right">
                        {campaign.clicked.toLocaleString()}
                        {campaign.sent > 0 && (
                          <span className="text-gray-400 text-sm ml-1">
                            ({((campaign.clicked / campaign.sent) * 100).toFixed(1)}%)
                          </span>
                        )}
                      </td>
                      <td className="py-2 text-right font-medium text-green-600">{campaign.leads}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="leads">
          <Card>
            <CardHeader>
              <CardTitle>Recent Leads</CardTitle>
              <CardDescription>Latest lead activity</CardDescription>
            </CardHeader>
            <CardContent>
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">Contact</th>
                    <th className="text-left py-2">Company</th>
                    <th className="text-left py-2">Source</th>
                    <th className="text-left py-2">Stage</th>
                    <th className="text-left py-2">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { name: 'Sarah Johnson', company: 'Acme Corp', source: 'Website', stage: 'MQL', created: '2024-01-15' },
                    { name: 'Michael Chen', company: 'TechStart Inc', source: 'LinkedIn', stage: 'SQL', created: '2024-01-14' },
                    { name: 'Emily Davis', company: 'Healthcare Plus', source: 'Referral', stage: 'Lead', created: '2024-01-14' },
                    { name: 'James Wilson', company: 'Finance Group', source: 'Email', stage: 'MQL', created: '2024-01-13' },
                    { name: 'Lisa Anderson', company: 'Retail Solutions', source: 'Event', stage: 'Lead', created: '2024-01-12' },
                  ].map((lead) => (
                    <tr key={lead.name} className="border-b hover:bg-gray-50">
                      <td className="py-2 font-medium">{lead.name}</td>
                      <td className="py-2">{lead.company}</td>
                      <td className="py-2">{lead.source}</td>
                      <td className="py-2">
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          lead.stage === 'SQL' ? 'bg-orange-100 text-orange-700' :
                          lead.stage === 'MQL' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-blue-100 text-blue-700'
                        }`}>
                          {lead.stage}
                        </span>
                      </td>
                      <td className="py-2 text-gray-500">{lead.created}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="funnel">
          <Card>
            <CardHeader>
              <CardTitle>Sales Funnel</CardTitle>
              <CardDescription>Contact lifecycle stages</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="max-w-2xl mx-auto space-y-2">
                {sampleContactsByStage.map((stage, index) => {
                  const width = 100 - (index * 12);
                  return (
                    <div key={stage.stage} className="flex items-center gap-4">
                      <div className="w-24 text-right text-sm font-medium">{stage.stage}</div>
                      <div 
                        className={`${stage.color} h-10 rounded flex items-center justify-center text-white font-bold transition-all`}
                        style={{ width: `${width}%` }}
                      >
                        {stage.count.toLocaleString()}
                      </div>
                    </div>
                  );
                })}
              </div>
              <div className="mt-8 text-center">
                <p className="text-sm text-gray-500">
                  Overall Conversion Rate: <span className="font-bold text-green-600">{sampleMetrics.conversionRate}%</span>
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default VitalMarketing;
