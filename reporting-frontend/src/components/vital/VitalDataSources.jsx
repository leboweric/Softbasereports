import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Alert, AlertDescription } from '../ui/alert';
import { Database, Cloud, DollarSign, TrendingUp, CheckCircle, XCircle, Loader2, Eye, EyeOff } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const VitalDataSources = ({ user }) => {
  const [dataSources, setDataSources] = useState({
    bigquery: {
      connected: false,
      project_id: '',
      dataset: '',
      credentials_type: 'service_account', // 'service_account' or 'oauth'
      service_account_json: '',
    },
    quickbooks: {
      connected: false,
      company_id: '',
      auth_type: 'oauth', // QuickBooks Online requires OAuth
      access_token: '',
      refresh_token: '',
    },
    hubspot: {
      connected: false,
      auth_type: 'api_key', // 'api_key' or 'oauth'
      api_key: '',
      access_token: '',
    }
  });
  
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState({});
  const [testing, setTesting] = useState({});
  const [message, setMessage] = useState(null);
  const [showSecrets, setShowSecrets] = useState({});

  useEffect(() => {
    loadDataSources();
  }, []);

  const loadDataSources = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/vital/data-sources`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        if (data.sources) {
          setDataSources(prev => ({
            ...prev,
            ...data.sources
          }));
        }
      }
    } catch (error) {
      console.error('Error loading data sources:', error);
    }
    setLoading(false);
  };

  const saveDataSource = async (sourceType) => {
    setSaving(prev => ({ ...prev, [sourceType]: true }));
    setMessage(null);
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/vital/data-sources/${sourceType}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(dataSources[sourceType])
      });
      
      const data = await response.json();
      if (response.ok) {
        setMessage({ type: 'success', text: `${sourceType} configuration saved successfully` });
      } else {
        setMessage({ type: 'error', text: data.message || 'Failed to save configuration' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error saving configuration' });
    }
    
    setSaving(prev => ({ ...prev, [sourceType]: false }));
  };

  const testConnection = async (sourceType) => {
    setTesting(prev => ({ ...prev, [sourceType]: true }));
    setMessage(null);
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/vital/data-sources/${sourceType}/test`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(dataSources[sourceType])
      });
      
      const data = await response.json();
      if (response.ok && data.success) {
        setMessage({ type: 'success', text: `${sourceType} connection successful!` });
        setDataSources(prev => ({
          ...prev,
          [sourceType]: { ...prev[sourceType], connected: true }
        }));
      } else {
        setMessage({ type: 'error', text: data.message || 'Connection test failed' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error testing connection' });
    }
    
    setTesting(prev => ({ ...prev, [sourceType]: false }));
  };

  const updateField = (sourceType, field, value) => {
    setDataSources(prev => ({
      ...prev,
      [sourceType]: { ...prev[sourceType], [field]: value }
    }));
  };

  const toggleShowSecret = (field) => {
    setShowSecrets(prev => ({ ...prev, [field]: !prev[field] }));
  };

  const ConnectionStatus = ({ connected }) => (
    <div className={`flex items-center gap-2 ${connected ? 'text-green-600' : 'text-gray-400'}`}>
      {connected ? <CheckCircle className="h-5 w-5" /> : <XCircle className="h-5 w-5" />}
      <span>{connected ? 'Connected' : 'Not Connected'}</span>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Data Sources</h1>
        <p className="text-gray-500">Configure connections to your data sources</p>
      </div>

      {message && (
        <Alert className={message.type === 'success' ? 'border-green-500 bg-green-50' : 'border-red-500 bg-red-50'}>
          <AlertDescription className={message.type === 'success' ? 'text-green-700' : 'text-red-700'}>
            {message.text}
          </AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="bigquery" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="bigquery" className="flex items-center gap-2">
            <Cloud className="h-4 w-4" />
            BigQuery
          </TabsTrigger>
          <TabsTrigger value="quickbooks" className="flex items-center gap-2">
            <DollarSign className="h-4 w-4" />
            QuickBooks
          </TabsTrigger>
          <TabsTrigger value="hubspot" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            HubSpot
          </TabsTrigger>
        </TabsList>

        {/* BigQuery Configuration */}
        <TabsContent value="bigquery">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Cloud className="h-5 w-5" />
                    Google BigQuery
                  </CardTitle>
                  <CardDescription>Connect to your case management data in BigQuery</CardDescription>
                </div>
                <ConnectionStatus connected={dataSources.bigquery.connected} />
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="bq-project">Project ID</Label>
                  <Input
                    id="bq-project"
                    placeholder="your-gcp-project-id"
                    value={dataSources.bigquery.project_id}
                    onChange={(e) => updateField('bigquery', 'project_id', e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="bq-dataset">Dataset</Label>
                  <Input
                    id="bq-dataset"
                    placeholder="your_dataset_name"
                    value={dataSources.bigquery.dataset}
                    onChange={(e) => updateField('bigquery', 'dataset', e.target.value)}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Authentication Method</Label>
                <div className="flex gap-4">
                  <label className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="bq-auth"
                      checked={dataSources.bigquery.credentials_type === 'service_account'}
                      onChange={() => updateField('bigquery', 'credentials_type', 'service_account')}
                    />
                    Service Account JSON
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="bq-auth"
                      checked={dataSources.bigquery.credentials_type === 'oauth'}
                      onChange={() => updateField('bigquery', 'credentials_type', 'oauth')}
                    />
                    OAuth (User Authentication)
                  </label>
                </div>
              </div>

              {dataSources.bigquery.credentials_type === 'service_account' && (
                <div className="space-y-2">
                  <Label htmlFor="bq-credentials">Service Account JSON</Label>
                  <div className="relative">
                    <textarea
                      id="bq-credentials"
                      className="w-full h-32 p-2 border rounded-md font-mono text-sm"
                      placeholder='{"type": "service_account", "project_id": "...", ...}'
                      value={dataSources.bigquery.service_account_json}
                      onChange={(e) => updateField('bigquery', 'service_account_json', e.target.value)}
                    />
                  </div>
                  <p className="text-sm text-gray-500">
                    Paste your service account JSON key file contents here
                  </p>
                </div>
              )}

              {dataSources.bigquery.credentials_type === 'oauth' && (
                <div className="p-4 bg-blue-50 rounded-md">
                  <p className="text-sm text-blue-700">
                    OAuth authentication will redirect you to Google to authorize access.
                    Click "Connect with Google" to begin the authentication flow.
                  </p>
                  <Button className="mt-2" variant="outline">
                    Connect with Google
                  </Button>
                </div>
              )}

              <div className="flex gap-2 pt-4">
                <Button 
                  onClick={() => testConnection('bigquery')}
                  variant="outline"
                  disabled={testing.bigquery}
                >
                  {testing.bigquery ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                  Test Connection
                </Button>
                <Button 
                  onClick={() => saveDataSource('bigquery')}
                  disabled={saving.bigquery}
                >
                  {saving.bigquery ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                  Save Configuration
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* QuickBooks Configuration */}
        <TabsContent value="quickbooks">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <DollarSign className="h-5 w-5" />
                    QuickBooks Online
                  </CardTitle>
                  <CardDescription>Connect to your financial data in QuickBooks</CardDescription>
                </div>
                <ConnectionStatus connected={dataSources.quickbooks.connected} />
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 bg-blue-50 rounded-md">
                <p className="text-sm text-blue-700 mb-2">
                  QuickBooks Online requires OAuth authentication. Click the button below to connect your QuickBooks account.
                </p>
                <Button variant="outline" className="bg-white">
                  <img src="https://quickbooks.intuit.com/etc.clientlibs/qbo/clientlibs/clientlib-site/resources/images/qb-logo.svg" alt="QuickBooks" className="h-5 mr-2" />
                  Connect to QuickBooks
                </Button>
              </div>

              {dataSources.quickbooks.connected && (
                <div className="space-y-2">
                  <Label>Company ID</Label>
                  <Input
                    value={dataSources.quickbooks.company_id}
                    disabled
                    className="bg-gray-50"
                  />
                  <p className="text-sm text-green-600">
                    Connected to QuickBooks. Your financial data will sync automatically.
                  </p>
                </div>
              )}

              <div className="flex gap-2 pt-4">
                <Button 
                  onClick={() => testConnection('quickbooks')}
                  variant="outline"
                  disabled={testing.quickbooks || !dataSources.quickbooks.connected}
                >
                  {testing.quickbooks ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                  Test Connection
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* HubSpot Configuration */}
        <TabsContent value="hubspot">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5" />
                    HubSpot
                  </CardTitle>
                  <CardDescription>Connect to your marketing and CRM data in HubSpot</CardDescription>
                </div>
                <ConnectionStatus connected={dataSources.hubspot.connected} />
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Authentication Method</Label>
                <div className="flex gap-4">
                  <label className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="hs-auth"
                      checked={dataSources.hubspot.auth_type === 'api_key'}
                      onChange={() => updateField('hubspot', 'auth_type', 'api_key')}
                    />
                    Private App Access Token
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="hs-auth"
                      checked={dataSources.hubspot.auth_type === 'oauth'}
                      onChange={() => updateField('hubspot', 'auth_type', 'oauth')}
                    />
                    OAuth
                  </label>
                </div>
              </div>

              {dataSources.hubspot.auth_type === 'api_key' && (
                <div className="space-y-2">
                  <Label htmlFor="hs-api-key">Private App Access Token</Label>
                  <div className="relative">
                    <Input
                      id="hs-api-key"
                      type={showSecrets['hs-api-key'] ? 'text' : 'password'}
                      placeholder="pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                      value={dataSources.hubspot.api_key}
                      onChange={(e) => updateField('hubspot', 'api_key', e.target.value)}
                    />
                    <button
                      type="button"
                      className="absolute right-2 top-1/2 -translate-y-1/2"
                      onClick={() => toggleShowSecret('hs-api-key')}
                    >
                      {showSecrets['hs-api-key'] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                  <p className="text-sm text-gray-500">
                    Create a Private App in HubSpot Settings → Integrations → Private Apps
                  </p>
                </div>
              )}

              {dataSources.hubspot.auth_type === 'oauth' && (
                <div className="p-4 bg-orange-50 rounded-md">
                  <p className="text-sm text-orange-700 mb-2">
                    OAuth authentication will redirect you to HubSpot to authorize access.
                  </p>
                  <Button variant="outline" className="bg-white">
                    Connect to HubSpot
                  </Button>
                </div>
              )}

              <div className="flex gap-2 pt-4">
                <Button 
                  onClick={() => testConnection('hubspot')}
                  variant="outline"
                  disabled={testing.hubspot}
                >
                  {testing.hubspot ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                  Test Connection
                </Button>
                <Button 
                  onClick={() => saveDataSource('hubspot')}
                  disabled={saving.hubspot}
                >
                  {saving.hubspot ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                  Save Configuration
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default VitalDataSources;
