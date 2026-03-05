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
  Globe
} from 'lucide-react'

const SAP_SYSTEM_TYPES = [
  { value: 's4hana', label: 'SAP S/4HANA' },
  { value: 'business_one', label: 'SAP Business One' },
  { value: 'ecc', label: 'SAP ECC' },
  { value: 'bydesign', label: 'SAP Business ByDesign' },
]

const CONNECTION_METHODS = {
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

const AlohaDataSources = ({ user }) => {
  const [dataSources, setDataSources] = useState({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState({})
  const [testing, setTesting] = useState({})
  const [message, setMessage] = useState(null)
  const [showSecrets, setShowSecrets] = useState({})
  const [activeTab, setActiveTab] = useState('sap_sandia_plastics')

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
        if (data.sources) {
          setDataSources(data.sources)
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
        setMessage({ type: 'success', text: `${dataSources[sourceId]?.name || sourceId} configuration saved.` })
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

  const sourceIds = ['sap_sandia_plastics', 'sap_kauai_exclusive', 'sap_hawaii_care']
  const subsidiaryLabels = {
    'sap_sandia_plastics': 'Sandia Plastics',
    'sap_kauai_exclusive': 'Kauai Exclusive',
    'sap_hawaii_care': 'Hawaii Care & Cleaning',
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Database className="h-7 w-7 text-teal-600" />
          SAP Data Sources
        </h1>
        <p className="text-gray-500 mt-1">
          Configure connections to each subsidiary's SAP ERP system
        </p>
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

      {/* Tabs for each subsidiary */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid grid-cols-3 w-full max-w-lg">
          {sourceIds.map((id, idx) => (
            <TabsTrigger key={id} value={id} className="flex items-center gap-1.5">
              <Building2 className="h-3.5 w-3.5" />
              {dataSources[id]?.name || subsidiaryLabels[id] || `Subsidiary ${idx + 1}`}
              {dataSources[id]?.connected ? (
                <CheckCircle className="h-3 w-3 text-green-500" />
              ) : (
                <XCircle className="h-3 w-3 text-gray-300" />
              )}
            </TabsTrigger>
          ))}
        </TabsList>

        {sourceIds.map((sourceId, idx) => (
          <TabsContent key={sourceId} value={sourceId}>
            <SAPConnectionForm
              sourceId={sourceId}
              index={idx}
              config={dataSources[sourceId] || {}}
              onUpdate={(field, value) => updateField(sourceId, field, value)}
              onSave={() => saveDataSource(sourceId)}
              onTest={() => testConnection(sourceId)}
              saving={saving[sourceId]}
              testing={testing[sourceId]}
              showSecrets={showSecrets}
              onToggleSecret={(field) => setShowSecrets(prev => ({ ...prev, [`${sourceId}_${field}`]: !prev[`${sourceId}_${field}`] }))}
            />
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}

const SAPConnectionForm = ({ sourceId, index, config, onUpdate, onSave, onTest, saving, testing, showSecrets, onToggleSecret }) => {
  const systemType = config.system_type || ''
  const connectionMethods = systemType ? (CONNECTION_METHODS[systemType] || []) : []

  return (
    <div className="space-y-4">
      {/* Subsidiary Name */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Building2 className="h-5 w-5 text-teal-600" />
            Subsidiary {index + 1} — General Info
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <Label>Company Name</Label>
            <Input
              value={config.name || ''}
              onChange={(e) => onUpdate('name', e.target.value)}
              placeholder={`Enter subsidiary ${index + 1} company name`}
            />
          </div>
        </CardContent>
      </Card>

      {/* SAP System Type */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Server className="h-5 w-5 text-blue-600" />
            SAP System Configuration
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
                onUpdate('connection_method', '')  // Reset connection method
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

      {/* Connection Details */}
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
                  placeholder={config.connection_method === 'service_layer' ? '50000' : config.connection_method === 'odata' ? '443' : '30015'}
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
                  placeholder="SAP username"
                />
              </div>
              <div>
                <Label>Password</Label>
                <div className="relative">
                  <Input
                    type={showSecrets[`${sourceId}_password`] ? 'text' : 'password'}
                    value={config.password || ''}
                    onChange={(e) => onUpdate('password', e.target.value)}
                    placeholder="SAP password"
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

      {/* Actions */}
      <div className="flex gap-3">
        <Button onClick={onSave} disabled={saving} className="bg-teal-600 hover:bg-teal-700">
          {saving ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
          Save Configuration
        </Button>
        <Button variant="outline" onClick={onTest} disabled={testing || !config.host}>
          {testing ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <TestTube className="h-4 w-4 mr-2" />}
          Test Connection
        </Button>
      </div>
    </div>
  )
}

export default AlohaDataSources
