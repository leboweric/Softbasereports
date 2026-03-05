import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { apiUrl } from '@/lib/api'
import {
  Database,
  Building2,
  CheckCircle,
  XCircle,
  Loader2,
  Eye,
  EyeOff,
  Save,
  TestTube,
  RefreshCw,
  Server,
  Globe,
  Cloud
} from 'lucide-react'

const SAP_SYSTEM_TYPES = [
  { value: 's4hana', label: 'SAP S/4HANA' },
  { value: 'business_one', label: 'SAP Business One' },
  { value: 'ecc', label: 'SAP ECC' },
  { value: 'bydesign', label: 'SAP Business ByDesign' },
]

const SAP_CONNECTION_METHODS = {
  s4hana: [
    { value: 'odata', label: 'OData API' },
    { value: 'rfc', label: 'RFC (Remote Function Call)' },
    { value: 'db_direct', label: 'Direct HANA DB Connection' },
  ],
  business_one: [
    { value: 'service_layer', label: 'Service Layer API' },
    { value: 'db_direct', label: 'Direct DB Connection (SQL Server/HANA)' },
  ],
  ecc: [
    { value: 'odata', label: 'OData Gateway' },
    { value: 'rfc', label: 'RFC (Remote Function Call)' },
  ],
  bydesign: [
    { value: 'odata', label: 'OData API' },
    { value: 'api', label: 'Custom API' },
  ],
}

const NS_CONNECTION_METHODS = [
  { value: 'token_based_auth', label: 'Token-Based Authentication (TBA)' },
  { value: 'oauth2', label: 'OAuth 2.0' },
  { value: 'suitetalk', label: 'SuiteTalk (SOAP)' },
  { value: 'restlet', label: 'RESTlet' },
]

const SAP_SOURCES = [
  { id: 'sap_sandia', name: 'Sandia' },
  { id: 'sap_mercury', name: 'Mercury' },
  { id: 'sap_ultimate_solutions', name: 'Ultimate Solutions' },
  { id: 'sap_avalon', name: 'Avalon' },
  { id: 'sap_orbot', name: 'Orbot' },
]

const NS_SOURCES = [
  { id: 'ns_hawaii_care', name: 'Hawaii Care and Cleaning' },
  { id: 'ns_kauai_exclusive', name: 'Kauai Exclusive' },
  { id: 'ns_heavenly_vacations', name: 'Heavenly Vacations' },
]

const AlohaDataSources = ({ user }) => {
  const [dataSources, setDataSources] = useState({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState({})
  const [testing, setTesting] = useState({})
  const [message, setMessage] = useState(null)
  const [showSecrets, setShowSecrets] = useState({})
  const [activeTab, setActiveTab] = useState('sap_sandia')
  const [activeGroup, setActiveGroup] = useState('sap')

  useEffect(() => {
    loadDataSources()
  }, [])

  const loadDataSources = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/aloha/data-sources'), {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        if (data.all_sources) {
          setDataSources(data.all_sources)
        }
      }
    } catch (error) {
      console.error('Error loading data sources:', error)
    }
    setLoading(false)
  }

  const saveDataSource = async (sourceId) => {
    setSaving(prev => ({ ...prev, [sourceId]: true }))
    setMessage(null)

    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl(`/api/aloha/data-sources/${sourceId}`), {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(dataSources[sourceId])
      })

      const data = await response.json()
      if (response.ok) {
        setMessage({ type: 'success', text: data.message || 'Configuration saved.' })
      } else {
        setMessage({ type: 'error', text: data.error || 'Failed to save' })
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Network error saving configuration' })
    }
    setSaving(prev => ({ ...prev, [sourceId]: false }))
  }

  const testConnection = async (sourceId) => {
    setTesting(prev => ({ ...prev, [sourceId]: true }))
    setMessage(null)

    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl(`/api/aloha/data-sources/${sourceId}/test`), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(dataSources[sourceId])
      })

      const data = await response.json()
      if (data.success) {
        setMessage({ type: 'success', text: data.message })
      } else {
        setMessage({ type: 'error', text: data.message || 'Connection test failed' })
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Network error testing connection' })
    }
    setTesting(prev => ({ ...prev, [sourceId]: false }))
  }

  const updateField = (sourceId, field, value) => {
    setDataSources(prev => ({
      ...prev,
      [sourceId]: {
        ...prev[sourceId],
        [field]: value
      }
    }))
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-teal-500" />
        <span className="ml-3 text-gray-600">Loading data sources...</span>
      </div>
    )
  }

  const currentSources = activeGroup === 'sap' ? SAP_SOURCES : NS_SOURCES

  // Count connected sources per group
  const sapConnected = SAP_SOURCES.filter(s => dataSources[s.id]?.connected).length
  const nsConnected = NS_SOURCES.filter(s => dataSources[s.id]?.connected).length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Database className="h-7 w-7 text-teal-600" />
          ERP Data Sources
        </h1>
        <p className="text-gray-500 mt-1">
          Configure connections to each subsidiary's ERP system — 5 SAP + 3 NetSuite
        </p>
      </div>

      {/* Status overview */}
      <div className="grid grid-cols-2 gap-4">
        <Card
          className={`cursor-pointer transition-all ${activeGroup === 'sap' ? 'ring-2 ring-teal-500 bg-teal-50' : 'hover:bg-gray-50'}`}
          onClick={() => { setActiveGroup('sap'); setActiveTab(SAP_SOURCES[0].id) }}
        >
          <CardContent className="p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Server className="h-8 w-8 text-blue-600" />
              <div>
                <p className="font-semibold text-gray-900">SAP Systems</p>
                <p className="text-sm text-gray-500">5 subsidiaries</p>
              </div>
            </div>
            <Badge variant={sapConnected > 0 ? 'default' : 'secondary'}>
              {sapConnected}/5 connected
            </Badge>
          </CardContent>
        </Card>
        <Card
          className={`cursor-pointer transition-all ${activeGroup === 'netsuite' ? 'ring-2 ring-teal-500 bg-teal-50' : 'hover:bg-gray-50'}`}
          onClick={() => { setActiveGroup('netsuite'); setActiveTab(NS_SOURCES[0].id) }}
        >
          <CardContent className="p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Cloud className="h-8 w-8 text-orange-600" />
              <div>
                <p className="font-semibold text-gray-900">NetSuite Systems</p>
                <p className="text-sm text-gray-500">3 subsidiaries</p>
              </div>
            </div>
            <Badge variant={nsConnected > 0 ? 'default' : 'secondary'}>
              {nsConnected}/3 connected
            </Badge>
          </CardContent>
        </Card>
      </div>

      {/* Status message */}
      {message && (
        <Alert variant={message.type === 'error' ? 'destructive' : 'default'}
               className={message.type === 'success' ? 'border-green-200 bg-green-50' : ''}>
          <AlertDescription className={message.type === 'success' ? 'text-green-800' : ''}>
            {message.type === 'success' && <CheckCircle className="h-4 w-4 inline mr-2" />}
            {message.text}
          </AlertDescription>
        </Alert>
      )}

      {/* Tabs for subsidiaries in the active group */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className={`grid w-full ${activeGroup === 'sap' ? 'grid-cols-5' : 'grid-cols-3'} max-w-2xl`}>
          {currentSources.map((source) => (
            <TabsTrigger key={source.id} value={source.id} className="flex items-center gap-1 text-xs">
              <Building2 className="h-3 w-3" />
              <span className="truncate">{source.name}</span>
              {dataSources[source.id]?.connected ? (
                <CheckCircle className="h-3 w-3 text-green-500 shrink-0" />
              ) : (
                <XCircle className="h-3 w-3 text-gray-300 shrink-0" />
              )}
            </TabsTrigger>
          ))}
        </TabsList>

        {currentSources.map((source, idx) => (
          <TabsContent key={source.id} value={source.id}>
            {activeGroup === 'sap' ? (
              <SAPConnectionForm
                sourceId={source.id}
                sourceName={source.name}
                index={idx}
                config={dataSources[source.id] || {}}
                onUpdate={(field, value) => updateField(source.id, field, value)}
                onSave={() => saveDataSource(source.id)}
                onTest={() => testConnection(source.id)}
                saving={saving[source.id]}
                testing={testing[source.id]}
                showSecrets={showSecrets}
                onToggleSecret={(field) => setShowSecrets(prev => ({ ...prev, [`${source.id}_${field}`]: !prev[`${source.id}_${field}`] }))}
              />
            ) : (
              <NetSuiteConnectionForm
                sourceId={source.id}
                sourceName={source.name}
                index={idx}
                config={dataSources[source.id] || {}}
                onUpdate={(field, value) => updateField(source.id, field, value)}
                onSave={() => saveDataSource(source.id)}
                onTest={() => testConnection(source.id)}
                saving={saving[source.id]}
                testing={testing[source.id]}
                showSecrets={showSecrets}
                onToggleSecret={(field) => setShowSecrets(prev => ({ ...prev, [`${source.id}_${field}`]: !prev[`${source.id}_${field}`] }))}
              />
            )}
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}

const SAPConnectionForm = ({ sourceId, sourceName, index, config, onUpdate, onSave, onTest, saving, testing, showSecrets, onToggleSecret }) => {
  const systemType = config.system_type || ''
  const connectionMethods = systemType ? (SAP_CONNECTION_METHODS[systemType] || []) : []

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Server className="h-5 w-5 text-blue-600" />
            {sourceName} — SAP Configuration
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <Label>SAP System Type</Label>
            <select
              className="w-full mt-1 rounded-md border border-gray-300 px-3 py-2 text-sm"
              value={systemType}
              onChange={(e) => {
                onUpdate('system_type', e.target.value)
                onUpdate('connection_method', '')
              }}
            >
              <option value="">Select SAP system type...</option>
              {SAP_SYSTEM_TYPES.map(type => (
                <option key={type.value} value={type.value}>{type.label}</option>
              ))}
            </select>
          </div>

          {systemType && (
            <div>
              <Label>Connection Method</Label>
              <select
                className="w-full mt-1 rounded-md border border-gray-300 px-3 py-2 text-sm"
                value={config.connection_method || ''}
                onChange={(e) => onUpdate('connection_method', e.target.value)}
              >
                <option value="">Select connection method...</option>
                {connectionMethods.map(method => (
                  <option key={method.value} value={method.value}>{method.label}</option>
                ))}
              </select>
            </div>
          )}
        </CardContent>
      </Card>

      {systemType && config.connection_method && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Globe className="h-5 w-5 text-green-600" />
              Connection Details
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Host / Server Address</Label>
                <Input
                  value={config.host || ''}
                  onChange={(e) => onUpdate('host', e.target.value)}
                  placeholder="e.g., sap.company.com"
                />
              </div>
              <div>
                <Label>Port</Label>
                <Input
                  value={config.port || ''}
                  onChange={(e) => onUpdate('port', e.target.value)}
                  placeholder={systemType === 'business_one' ? '50000' : '443'}
                />
              </div>
            </div>

            {(systemType === 's4hana' || systemType === 'ecc') && (
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label>SAP Client</Label>
                  <Input
                    value={config.client || ''}
                    onChange={(e) => onUpdate('client', e.target.value)}
                    placeholder="e.g., 100"
                  />
                </div>
                <div>
                  <Label>System Number</Label>
                  <Input
                    value={config.system_number || ''}
                    onChange={(e) => onUpdate('system_number', e.target.value)}
                    placeholder="e.g., 00"
                  />
                </div>
              </div>
            )}

            {systemType === 'business_one' && (
              <div>
                <Label>Company Database</Label>
                <Input
                  value={config.company_db || ''}
                  onChange={(e) => onUpdate('company_db', e.target.value)}
                  placeholder="e.g., SBODemoUS"
                />
              </div>
            )}

            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Username</Label>
                <Input
                  value={config.username || ''}
                  onChange={(e) => onUpdate('username', e.target.value)}
                  placeholder="SAP service account username"
                />
              </div>
              <div>
                <Label>Password</Label>
                <div className="relative">
                  <Input
                    type={showSecrets[`${sourceId}_password`] ? 'text' : 'password'}
                    value={config.password || ''}
                    onChange={(e) => onUpdate('password', e.target.value)}
                    placeholder="••••••••"
                  />
                  <button
                    type="button"
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    onClick={() => onToggleSecret('password')}
                  >
                    {showSecrets[`${sourceId}_password`] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Action buttons */}
      <div className="flex gap-3">
        <Button onClick={onSave} disabled={saving} className="bg-teal-600 hover:bg-teal-700">
          {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
          Save Configuration
        </Button>
        <Button variant="outline" onClick={onTest} disabled={testing}>
          {testing ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <TestTube className="h-4 w-4 mr-2" />}
          Test Connection
        </Button>
      </div>
    </div>
  )
}

const NetSuiteConnectionForm = ({ sourceId, sourceName, index, config, onUpdate, onSave, onTest, saving, testing, showSecrets, onToggleSecret }) => {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Cloud className="h-5 w-5 text-orange-600" />
            {sourceName} — NetSuite Configuration
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <Label>Connection Method</Label>
            <select
              className="w-full mt-1 rounded-md border border-gray-300 px-3 py-2 text-sm"
              value={config.connection_method || ''}
              onChange={(e) => onUpdate('connection_method', e.target.value)}
            >
              <option value="">Select connection method...</option>
              {NS_CONNECTION_METHODS.map(method => (
                <option key={method.value} value={method.value}>{method.label}</option>
              ))}
            </select>
          </div>

          <div>
            <Label>NetSuite Account ID</Label>
            <Input
              value={config.account_id || ''}
              onChange={(e) => onUpdate('account_id', e.target.value)}
              placeholder="e.g., 1234567 or TSTDRV1234567"
            />
          </div>

          <div>
            <Label>Realm (Account ID for auth)</Label>
            <Input
              value={config.realm || ''}
              onChange={(e) => onUpdate('realm', e.target.value)}
              placeholder="Usually same as Account ID"
            />
          </div>
        </CardContent>
      </Card>

      {(config.connection_method === 'token_based_auth' || config.connection_method === 'oauth2') && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Globe className="h-5 w-5 text-green-600" />
              Authentication Credentials
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Consumer Key</Label>
                <div className="relative">
                  <Input
                    type={showSecrets[`${sourceId}_consumer_key`] ? 'text' : 'password'}
                    value={config.consumer_key || ''}
                    onChange={(e) => onUpdate('consumer_key', e.target.value)}
                    placeholder="Integration consumer key"
                  />
                  <button
                    type="button"
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    onClick={() => onToggleSecret('consumer_key')}
                  >
                    {showSecrets[`${sourceId}_consumer_key`] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              <div>
                <Label>Consumer Secret</Label>
                <div className="relative">
                  <Input
                    type={showSecrets[`${sourceId}_consumer_secret`] ? 'text' : 'password'}
                    value={config.consumer_secret || ''}
                    onChange={(e) => onUpdate('consumer_secret', e.target.value)}
                    placeholder="Integration consumer secret"
                  />
                  <button
                    type="button"
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    onClick={() => onToggleSecret('consumer_secret')}
                  >
                    {showSecrets[`${sourceId}_consumer_secret`] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Token ID</Label>
                <div className="relative">
                  <Input
                    type={showSecrets[`${sourceId}_token_id`] ? 'text' : 'password'}
                    value={config.token_id || ''}
                    onChange={(e) => onUpdate('token_id', e.target.value)}
                    placeholder="Access token ID"
                  />
                  <button
                    type="button"
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    onClick={() => onToggleSecret('token_id')}
                  >
                    {showSecrets[`${sourceId}_token_id`] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              <div>
                <Label>Token Secret</Label>
                <div className="relative">
                  <Input
                    type={showSecrets[`${sourceId}_token_secret`] ? 'text' : 'password'}
                    value={config.token_secret || ''}
                    onChange={(e) => onUpdate('token_secret', e.target.value)}
                    placeholder="Access token secret"
                  />
                  <button
                    type="button"
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    onClick={() => onToggleSecret('token_secret')}
                  >
                    {showSecrets[`${sourceId}_token_secret`] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Action buttons */}
      <div className="flex gap-3">
        <Button onClick={onSave} disabled={saving} className="bg-teal-600 hover:bg-teal-700">
          {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
          Save Configuration
        </Button>
        <Button variant="outline" onClick={onTest} disabled={testing}>
          {testing ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <TestTube className="h-4 w-4 mr-2" />}
          Test Connection
        </Button>
      </div>
    </div>
  )
}

export default AlohaDataSources
