import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { get, post } from '../lib/api'
import { useAuth } from '../hooks/useAuth'
import { Navigate } from 'react-router-dom'
import {
  Building2,
  Database,
  Server,
  Check,
  ChevronRight,
  AlertCircle,
  CheckCircle,
  Loader2,
  Plus,
  Zap,
  Settings,
  ArrowRight,
  RefreshCw
} from 'lucide-react'

// Wizard Steps
const STEPS = {
  WELCOME: 'welcome',
  ERP_TYPE: 'erp_type',
  DEALER_INFO: 'dealer_info',
  CONNECTION: 'connection',
  TEST: 'test',
  COMPLETE: 'complete'
}

// Supported ERP Systems
const ERP_SYSTEMS = [
  {
    id: 'softbase_evolution',
    name: 'Softbase Evolution',
    description: 'Material handling dealer ERP system',
    icon: Database,
    available: true
  },
  {
    id: 'dis_cai',
    name: 'DIS/CAI',
    description: 'Coming soon',
    icon: Server,
    available: false
  },
  {
    id: 'e_emphasys',
    name: 'e-Emphasys',
    description: 'Coming soon',
    icon: Server,
    available: false
  }
]

// Quick Setup Templates
const QUICK_SETUPS = [
  {
    id: 'bennett',
    name: 'Bennett Material Handling',
    description: 'Pre-configured Bennett setup with Softbase Evolution',
    endpoint: '/api/admin/setup-bennett'
  }
]

export default function AdminSetup() {
  const { isCurrieAdmin } = useAuth()
  const queryClient = useQueryClient()

  // Wizard State
  const [currentStep, setCurrentStep] = useState(STEPS.WELCOME)
  const [formData, setFormData] = useState({
    erp_type: '',
    name: '',
    code: '',
    contact_name: '',
    contact_email: '',
    server: '',
    database: '',
    username: '',
    password: '',
    schema: 'ben002',
    subscription_tier: 'professional'
  })
  const [testResult, setTestResult] = useState(null)
  const [setupResult, setSetupResult] = useState(null)

  // Fetch existing dealers
  const { data: dealersData, isLoading: loadingDealers } = useQuery({
    queryKey: ['admin-dealers'],
    queryFn: () => get('/api/admin/dealers'),
    enabled: isCurrieAdmin
  })

  // Fetch supported ERP types
  const { data: erpData } = useQuery({
    queryKey: ['erp-types'],
    queryFn: () => get('/api/admin/erp-types'),
    enabled: isCurrieAdmin
  })

  // Test connection mutation
  const testConnectionMutation = useMutation({
    mutationFn: (data) => post('/api/admin/test-connection', data),
    onSuccess: (result) => {
      setTestResult(result)
    },
    onError: (error) => {
      setTestResult({ success: false, message: error.message })
    }
  })

  // Setup dealer mutation
  const setupDealerMutation = useMutation({
    mutationFn: (data) => post('/api/admin/setup-dealer', data),
    onSuccess: (result) => {
      setSetupResult(result)
      queryClient.invalidateQueries(['admin-dealers'])
      queryClient.invalidateQueries(['dealers'])
      setCurrentStep(STEPS.COMPLETE)
    },
    onError: (error) => {
      setSetupResult({ error: error.message })
    }
  })

  // Quick setup mutation
  const quickSetupMutation = useMutation({
    mutationFn: (endpoint) => post(endpoint, {}),
    onSuccess: (result) => {
      setSetupResult(result)
      queryClient.invalidateQueries(['admin-dealers'])
      queryClient.invalidateQueries(['dealers'])
      setCurrentStep(STEPS.COMPLETE)
    },
    onError: (error) => {
      setSetupResult({ error: error.message })
    }
  })

  // Redirect non-admins
  if (!isCurrieAdmin) {
    return <Navigate to="/" replace />
  }

  const dealers = dealersData?.dealers || []

  const updateFormData = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleTestConnection = () => {
    testConnectionMutation.mutate({
      erp_type: formData.erp_type,
      server: formData.server,
      database: formData.database,
      username: formData.username,
      password: formData.password,
      schema: formData.schema
    })
  }

  const handleSetupDealer = () => {
    setupDealerMutation.mutate(formData)
  }

  const handleQuickSetup = (endpoint) => {
    quickSetupMutation.mutate(endpoint)
  }

  const resetWizard = () => {
    setCurrentStep(STEPS.WELCOME)
    setFormData({
      erp_type: '',
      name: '',
      code: '',
      contact_name: '',
      contact_email: '',
      server: '',
      database: '',
      username: '',
      password: '',
      schema: 'ben002',
      subscription_tier: 'professional'
    })
    setTestResult(null)
    setSetupResult(null)
  }

  // Progress indicator
  const stepOrder = [STEPS.WELCOME, STEPS.ERP_TYPE, STEPS.DEALER_INFO, STEPS.CONNECTION, STEPS.TEST, STEPS.COMPLETE]
  const currentStepIndex = stepOrder.indexOf(currentStep)

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Admin Setup</h1>
        <p className="mt-1 text-sm text-gray-500">
          Set up new dealers and ERP connections
        </p>
      </div>

      {/* Progress Bar */}
      {currentStep !== STEPS.WELCOME && currentStep !== STEPS.COMPLETE && (
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            {stepOrder.slice(1, -1).map((step, index) => (
              <div key={step} className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  index < currentStepIndex - 1
                    ? 'bg-currie-600 text-white'
                    : index === currentStepIndex - 1
                    ? 'bg-currie-600 text-white ring-4 ring-currie-100'
                    : 'bg-gray-200 text-gray-600'
                }`}>
                  {index < currentStepIndex - 1 ? <Check className="w-4 h-4" /> : index + 1}
                </div>
                {index < stepOrder.length - 3 && (
                  <div className={`w-20 h-1 mx-2 ${
                    index < currentStepIndex - 1 ? 'bg-currie-600' : 'bg-gray-200'
                  }`} />
                )}
              </div>
            ))}
          </div>
          <div className="flex justify-between text-xs text-gray-500">
            <span>ERP Type</span>
            <span>Dealer Info</span>
            <span>Connection</span>
            <span>Test</span>
          </div>
        </div>
      )}

      {/* Welcome Step */}
      {currentStep === STEPS.WELCOME && (
        <div className="space-y-6">
          {/* Existing Dealers */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Configured Dealers</h2>
            {loadingDealers ? (
              <div className="text-center py-4 text-gray-500">Loading...</div>
            ) : dealers.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Building2 className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>No dealers configured yet</p>
              </div>
            ) : (
              <div className="space-y-3">
                {dealers.map(dealer => (
                  <div key={dealer.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center">
                      <Building2 className="w-8 h-8 text-currie-600 mr-3" />
                      <div>
                        <div className="font-medium text-gray-900">{dealer.name}</div>
                        <div className="text-sm text-gray-500">{dealer.code} - {dealer.erp_system}</div>
                      </div>
                    </div>
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                      dealer.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {dealer.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Quick Setup Options */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Zap className="w-5 h-5 mr-2 text-yellow-500" />
              Quick Setup
            </h2>
            <div className="grid gap-4 md:grid-cols-2">
              {QUICK_SETUPS.map(setup => {
                const alreadyExists = dealers.some(d => d.code === setup.id.toUpperCase())
                return (
                  <div key={setup.id} className="border border-gray-200 rounded-lg p-4">
                    <h3 className="font-medium text-gray-900">{setup.name}</h3>
                    <p className="text-sm text-gray-500 mt-1">{setup.description}</p>
                    <button
                      onClick={() => handleQuickSetup(setup.endpoint)}
                      disabled={quickSetupMutation.isPending || alreadyExists}
                      className={`mt-3 w-full py-2 px-4 rounded-md text-sm font-medium ${
                        alreadyExists
                          ? 'bg-gray-100 text-gray-500 cursor-not-allowed'
                          : 'bg-currie-600 text-white hover:bg-currie-700 disabled:opacity-50'
                      }`}
                    >
                      {quickSetupMutation.isPending ? (
                        <span className="flex items-center justify-center">
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Setting up...
                        </span>
                      ) : alreadyExists ? (
                        <span className="flex items-center justify-center">
                          <CheckCircle className="w-4 h-4 mr-2" />
                          Already Configured
                        </span>
                      ) : (
                        <span className="flex items-center justify-center">
                          <Zap className="w-4 h-4 mr-2" />
                          Quick Setup
                        </span>
                      )}
                    </button>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Manual Setup Button */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Settings className="w-5 h-5 mr-2 text-gray-500" />
              Manual Setup
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              Set up a new dealer with custom ERP connection settings. This wizard will guide you through the process step by step.
            </p>
            <button
              onClick={() => setCurrentStep(STEPS.ERP_TYPE)}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-currie-600 hover:bg-currie-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add New Dealer
              <ArrowRight className="w-4 h-4 ml-2" />
            </button>
          </div>
        </div>
      )}

      {/* Step 1: ERP Type Selection */}
      {currentStep === STEPS.ERP_TYPE && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Select ERP/DMS System</h2>
          <p className="text-sm text-gray-500 mb-6">
            Choose the dealer's ERP or DMS system type
          </p>

          <div className="grid gap-4 md:grid-cols-3">
            {ERP_SYSTEMS.map(erp => (
              <button
                key={erp.id}
                onClick={() => {
                  if (erp.available) {
                    updateFormData('erp_type', erp.id)
                    setCurrentStep(STEPS.DEALER_INFO)
                  }
                }}
                disabled={!erp.available}
                className={`p-6 border-2 rounded-lg text-left transition-all ${
                  formData.erp_type === erp.id
                    ? 'border-currie-600 bg-currie-50'
                    : erp.available
                    ? 'border-gray-200 hover:border-currie-300 hover:bg-gray-50'
                    : 'border-gray-100 bg-gray-50 opacity-60 cursor-not-allowed'
                }`}
              >
                <erp.icon className={`w-8 h-8 mb-3 ${
                  formData.erp_type === erp.id ? 'text-currie-600' : 'text-gray-400'
                }`} />
                <h3 className="font-semibold text-gray-900">{erp.name}</h3>
                <p className="text-sm text-gray-500 mt-1">{erp.description}</p>
                {formData.erp_type === erp.id && (
                  <div className="mt-3 flex items-center text-currie-600 text-sm font-medium">
                    <Check className="w-4 h-4 mr-1" />
                    Selected
                  </div>
                )}
              </button>
            ))}
          </div>

          <div className="mt-6 flex justify-between">
            <button
              onClick={() => setCurrentStep(STEPS.WELCOME)}
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              Back
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Dealer Information */}
      {currentStep === STEPS.DEALER_INFO && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Dealer Information</h2>
          <p className="text-sm text-gray-500 mb-6">
            Enter the basic dealer information
          </p>

          <div className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Dealer Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => updateFormData('name', e.target.value)}
                  placeholder="Bennett Material Handling"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-currie-500 focus:border-currie-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Dealer Code *
                </label>
                <input
                  type="text"
                  value={formData.code}
                  onChange={(e) => updateFormData('code', e.target.value.toUpperCase())}
                  placeholder="BENNETT"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-currie-500 focus:border-currie-500 uppercase"
                />
                <p className="text-xs text-gray-500 mt-1">Unique identifier for this dealer</p>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Contact Name
                </label>
                <input
                  type="text"
                  value={formData.contact_name}
                  onChange={(e) => updateFormData('contact_name', e.target.value)}
                  placeholder="John Smith"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-currie-500 focus:border-currie-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Contact Email
                </label>
                <input
                  type="email"
                  value={formData.contact_email}
                  onChange={(e) => updateFormData('contact_email', e.target.value)}
                  placeholder="john@dealer.com"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-currie-500 focus:border-currie-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Subscription Tier
              </label>
              <select
                value={formData.subscription_tier}
                onChange={(e) => updateFormData('subscription_tier', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-currie-500 focus:border-currie-500"
              >
                <option value="basic">Basic</option>
                <option value="professional">Professional</option>
                <option value="enterprise">Enterprise</option>
              </select>
            </div>
          </div>

          <div className="mt-6 flex justify-between">
            <button
              onClick={() => setCurrentStep(STEPS.ERP_TYPE)}
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              Back
            </button>
            <button
              onClick={() => setCurrentStep(STEPS.CONNECTION)}
              disabled={!formData.name || !formData.code}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-currie-600 hover:bg-currie-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Continue
              <ChevronRight className="w-4 h-4 ml-1" />
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Connection Details */}
      {currentStep === STEPS.CONNECTION && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">ERP Connection Details</h2>
          <p className="text-sm text-gray-500 mb-6">
            Enter the database connection credentials for{' '}
            <span className="font-medium">{ERP_SYSTEMS.find(e => e.id === formData.erp_type)?.name}</span>
          </p>

          <div className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Server Address *
                </label>
                <input
                  type="text"
                  value={formData.server}
                  onChange={(e) => updateFormData('server', e.target.value)}
                  placeholder="server.database.windows.net"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-currie-500 focus:border-currie-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Database Name *
                </label>
                <input
                  type="text"
                  value={formData.database}
                  onChange={(e) => updateFormData('database', e.target.value)}
                  placeholder="evo"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-currie-500 focus:border-currie-500"
                />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Username *
                </label>
                <input
                  type="text"
                  value={formData.username}
                  onChange={(e) => updateFormData('username', e.target.value)}
                  placeholder="db_user"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-currie-500 focus:border-currie-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Password *
                </label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => updateFormData('password', e.target.value)}
                  placeholder="********"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-currie-500 focus:border-currie-500"
                />
              </div>
            </div>

            {formData.erp_type === 'softbase_evolution' && (
              <div className="md:w-1/2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Schema
                </label>
                <input
                  type="text"
                  value={formData.schema}
                  onChange={(e) => updateFormData('schema', e.target.value)}
                  placeholder="ben002"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-currie-500 focus:border-currie-500"
                />
                <p className="text-xs text-gray-500 mt-1">Softbase dealer schema (e.g., ben002)</p>
              </div>
            )}
          </div>

          <div className="mt-6 flex justify-between">
            <button
              onClick={() => setCurrentStep(STEPS.DEALER_INFO)}
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              Back
            </button>
            <button
              onClick={() => setCurrentStep(STEPS.TEST)}
              disabled={!formData.server || !formData.database || !formData.username || !formData.password}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-currie-600 hover:bg-currie-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Continue
              <ChevronRight className="w-4 h-4 ml-1" />
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Test Connection */}
      {currentStep === STEPS.TEST && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Test Connection</h2>
          <p className="text-sm text-gray-500 mb-6">
            Verify the connection before creating the dealer
          </p>

          {/* Summary */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <h3 className="text-sm font-medium text-gray-700 mb-3">Configuration Summary</h3>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
              <dt className="text-gray-500">Dealer:</dt>
              <dd className="font-medium text-gray-900">{formData.name} ({formData.code})</dd>
              <dt className="text-gray-500">ERP System:</dt>
              <dd className="font-medium text-gray-900">{ERP_SYSTEMS.find(e => e.id === formData.erp_type)?.name}</dd>
              <dt className="text-gray-500">Server:</dt>
              <dd className="font-medium text-gray-900">{formData.server}</dd>
              <dt className="text-gray-500">Database:</dt>
              <dd className="font-medium text-gray-900">{formData.database}</dd>
              {formData.schema && (
                <>
                  <dt className="text-gray-500">Schema:</dt>
                  <dd className="font-medium text-gray-900">{formData.schema}</dd>
                </>
              )}
            </dl>
          </div>

          {/* Test Result */}
          {testResult && (
            <div className={`p-4 rounded-lg mb-6 ${
              testResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
            }`}>
              <div className="flex items-center">
                {testResult.success ? (
                  <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
                )}
                <span className={`font-medium ${testResult.success ? 'text-green-800' : 'text-red-800'}`}>
                  {testResult.success ? 'Connection Successful!' : 'Connection Failed'}
                </span>
              </div>
              {testResult.message && (
                <p className={`mt-2 text-sm ${testResult.success ? 'text-green-700' : 'text-red-700'}`}>
                  {testResult.message}
                </p>
              )}
            </div>
          )}

          {/* Setup Result Error */}
          {setupResult?.error && (
            <div className="p-4 rounded-lg mb-6 bg-red-50 border border-red-200">
              <div className="flex items-center">
                <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
                <span className="font-medium text-red-800">Setup Failed</span>
              </div>
              <p className="mt-2 text-sm text-red-700">{setupResult.error}</p>
            </div>
          )}

          <div className="flex gap-3 mb-6">
            <button
              onClick={handleTestConnection}
              disabled={testConnectionMutation.isPending}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
            >
              {testConnectionMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Testing...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Test Connection
                </>
              )}
            </button>
          </div>

          <div className="mt-6 flex justify-between">
            <button
              onClick={() => setCurrentStep(STEPS.CONNECTION)}
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              Back
            </button>
            <button
              onClick={handleSetupDealer}
              disabled={setupDealerMutation.isPending}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-currie-600 hover:bg-currie-700 disabled:opacity-50"
            >
              {setupDealerMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creating Dealer...
                </>
              ) : (
                <>
                  <Check className="w-4 h-4 mr-2" />
                  Create Dealer
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Step 5: Complete */}
      {currentStep === STEPS.COMPLETE && (
        <div className="bg-white shadow rounded-lg p-8 text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-10 h-10 text-green-600" />
          </div>
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">
            Dealer Setup Complete!
          </h2>
          <p className="text-gray-500 mb-6">
            {setupResult?.dealer?.name || 'The dealer'} has been successfully configured.
          </p>

          {setupResult?.connection_test && (
            <div className={`inline-flex items-center px-4 py-2 rounded-full mb-6 ${
              setupResult.connection_test.success
                ? 'bg-green-100 text-green-800'
                : 'bg-yellow-100 text-yellow-800'
            }`}>
              {setupResult.connection_test.success ? (
                <>
                  <CheckCircle className="w-4 h-4 mr-2" />
                  ERP Connection Verified
                </>
              ) : (
                <>
                  <AlertCircle className="w-4 h-4 mr-2" />
                  Connection needs verification
                </>
              )}
            </div>
          )}

          <div className="space-y-3">
            <button
              onClick={resetWizard}
              className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-currie-600 hover:bg-currie-700"
            >
              <Plus className="w-5 h-5 mr-2" />
              Add Another Dealer
            </button>
            <div>
              <a
                href="/reports"
                className="text-currie-600 hover:text-currie-700 text-sm font-medium"
              >
                Go to Reports &rarr;
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
