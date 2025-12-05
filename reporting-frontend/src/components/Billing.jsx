import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { CheckCircle, CreditCard, Calendar, ExternalLink, AlertTriangle, Loader2 } from 'lucide-react'
import { apiUrl } from '@/lib/api'

const Billing = ({ user, organization }) => {
  const [billingStatus, setBillingStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState(null)
  const [successMessage, setSuccessMessage] = useState(null)

  // Debug log on mount
  useEffect(() => {
    console.log('Billing component mounted', { user, organization })
  }, [])

  // Check URL params for success/canceled messages
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search)
    if (urlParams.get('billing') === 'success') {
      setSuccessMessage('Subscription activated successfully! Thank you for subscribing.')
      // Clear URL params
      window.history.replaceState({}, document.title, window.location.pathname)
      // Refresh billing status
      fetchBillingStatus()
    }
    if (urlParams.get('billing') === 'canceled') {
      setError('Checkout was canceled. You can try again when ready.')
      window.history.replaceState({}, document.title, window.location.pathname)
    }
  }, [])

  useEffect(() => {
    fetchBillingStatus()
  }, [])

  const fetchBillingStatus = async () => {
    try {
      setLoading(true)
      setError(null)
      const token = localStorage.getItem('token')
      console.log('Fetching billing status...', { apiUrl: apiUrl('/api/billing/status') })

      const response = await fetch(apiUrl('/api/billing/status'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      console.log('Billing status response:', response.status)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `Failed to fetch billing status (${response.status})`)
      }

      const data = await response.json()
      console.log('Billing status data:', data)
      setBillingStatus(data)
    } catch (err) {
      console.error('Billing status error:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSubscribe = async () => {
    try {
      setActionLoading(true)
      setError(null)
      const token = localStorage.getItem('token')

      const response = await fetch(apiUrl('/api/billing/create-checkout-session'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.error || 'Failed to create checkout session')
      }

      const { checkout_url } = await response.json()

      // Redirect to Stripe Checkout
      window.location.href = checkout_url
    } catch (err) {
      setError(err.message)
      setActionLoading(false)
    }
  }

  const handleManageBilling = async () => {
    try {
      setActionLoading(true)
      setError(null)
      const token = localStorage.getItem('token')

      const response = await fetch(apiUrl('/api/billing/create-portal-session'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.error || 'Failed to open billing portal')
      }

      const { portal_url } = await response.json()

      // Redirect to Stripe Customer Portal
      window.location.href = portal_url
    } catch (err) {
      setError(err.message)
      setActionLoading(false)
    }
  }

  const getStatusBadge = (status) => {
    const statusConfig = {
      active: { variant: 'default', className: 'bg-green-500', label: 'Active' },
      trialing: { variant: 'secondary', label: 'Not Subscribed' },
      past_due: { variant: 'destructive', label: 'Past Due' },
      canceled: { variant: 'secondary', label: 'Canceled' },
      unpaid: { variant: 'destructive', label: 'Unpaid' }
    }

    const config = statusConfig[status] || { variant: 'secondary', label: 'Not Subscribed' }

    return (
      <Badge variant={config.variant} className={config.className}>
        {config.label}
      </Badge>
    )
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  if (loading) {
    return (
      <div className="p-8">
        <Card>
          <CardContent className="flex items-center justify-center h-64">
            <LoadingSpinner />
          </CardContent>
        </Card>
      </div>
    )
  }

  // User has a paid/active subscription only if they have a Stripe customer AND active status
  const hasStripeCustomer = billingStatus?.stripe_customer_id
  const hasPaidSubscription = hasStripeCustomer && billingStatus?.subscription_status === 'active'

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Billing & Subscription</h1>
        <p className="text-muted-foreground mt-1">Manage your subscription and billing details</p>
      </div>

      {successMessage && (
        <Alert className="bg-green-50 border-green-200">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">
            {successMessage}
          </AlertDescription>
        </Alert>
      )}

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Current Plan Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            Current Plan
          </CardTitle>
          <CardDescription>Your current subscription status</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b">
              <div>
                <p className="font-medium">Softbase Reports</p>
                <p className="text-sm text-muted-foreground">Full access to all features</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold">$700</p>
                <p className="text-sm text-muted-foreground">per month</p>
              </div>
            </div>

            <div className="flex items-center justify-between py-2">
              <span className="text-muted-foreground">Status</span>
              {getStatusBadge(billingStatus?.subscription_status)}
            </div>

            {billingStatus?.subscription_ends_at && (
              <div className="flex items-center justify-between py-2">
                <span className="text-muted-foreground flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  {billingStatus?.subscription_status === 'canceled' ? 'Access Until' : 'Next Billing Date'}
                </span>
                <span className="font-medium">{formatDate(billingStatus.subscription_ends_at)}</span>
              </div>
            )}

          </div>
        </CardContent>
      </Card>

      {/* Actions Card */}
      <Card>
        <CardHeader>
          <CardTitle>Manage Subscription</CardTitle>
          <CardDescription>
            {hasPaidSubscription
              ? 'Update payment method, view invoices, or cancel subscription'
              : 'Subscribe to get full access to Softbase Reports'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {hasPaidSubscription ? (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-green-600 mb-4">
                <CheckCircle className="h-5 w-5" />
                <span className="font-medium">Your subscription is active</span>
              </div>

              <Button
                onClick={handleManageBilling}
                disabled={actionLoading || !hasStripeCustomer}
                className="w-full sm:w-auto"
              >
                {actionLoading ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <ExternalLink className="h-4 w-4 mr-2" />
                )}
                Manage Billing
              </Button>
              <p className="text-sm text-muted-foreground">
                Update payment method, view invoices, or cancel your subscription through Stripe's secure portal.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-amber-600 mb-4">
                <AlertTriangle className="h-5 w-5" />
                <span className="font-medium">
                  {billingStatus?.subscription_status === 'canceled'
                    ? 'Your subscription has been canceled'
                    : billingStatus?.subscription_status === 'past_due'
                    ? 'Payment is past due - please update your payment method'
                    : 'Subscribe to get started with Softbase Reports'}
                </span>
              </div>

              <Button
                onClick={handleSubscribe}
                disabled={actionLoading}
                size="lg"
                className="w-full sm:w-auto"
              >
                {actionLoading ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <CreditCard className="h-4 w-4 mr-2" />
                )}
                {billingStatus?.subscription_status === 'canceled' || billingStatus?.subscription_status === 'past_due'
                  ? 'Resubscribe'
                  : 'Subscribe Now'}
              </Button>

              {hasStripeCustomer && (
                <Button
                  variant="outline"
                  onClick={handleManageBilling}
                  disabled={actionLoading}
                  className="w-full sm:w-auto ml-0 sm:ml-2"
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  View Past Invoices
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Features Card */}
      <Card>
        <CardHeader>
          <CardTitle>What's Included</CardTitle>
          <CardDescription>Full access to all Softbase Reports features</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              'Department Dashboards (Parts, Service, Rental, Accounting)',
              'Real-time Data Sync from Softbase',
              'PM Route Planning & Scheduling',
              'Work Order Management & Tracking',
              'Customer Billing Reports',
              'Equipment Analytics',
              'Financial Reports & P&L',
              'AI-Powered Query Assistant',
              'Excel & PDF Exports',
              'Knowledge Base',
              'Quarterly Business Reviews',
              'Unlimited Users'
            ].map((feature, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-500 flex-shrink-0" />
                <span className="text-sm">{feature}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Support Card */}
      <Card>
        <CardHeader>
          <CardTitle>Need Help?</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            If you have any questions about billing or need assistance with your subscription,
            please contact us at <a href="mailto:support@pbnllc.com" className="text-blue-600 hover:underline">support@pbnllc.com</a>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

export default Billing
