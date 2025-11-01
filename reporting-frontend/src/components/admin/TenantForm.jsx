import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { adminApi } from '@/lib/api';
import { ConnectionTest } from './ConnectionTest';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';

export const TenantForm = ({ organization, onClose }) => {
  const [formData, setFormData] = useState({
    name: '',
    platform_type: 'evolution',
    db_server: '',
    db_name: '',
    db_username: '',
    db_password: '',
    subscription_tier: 'basic',
    max_users: 5,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (organization) {
      setFormData({
        name: organization.name || '',
        platform_type: organization.platform_type || 'evolution',
        db_server: organization.db_server || '',
        db_name: organization.db_name || '',
        db_username: organization.db_username || '',
        db_password: '', // Always empty for security
        subscription_tier: organization.subscription_tier || 'basic',
        max_users: organization.max_users || 5,
      });
    }
  }, [organization]);

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({ 
      ...prev, 
      [name]: type === 'number' ? parseInt(value) || 0 : value 
    }));
  };

  const handleSelectChange = (name, value) => {
    setFormData((prev) => ({ ...prev, [name]: value }));
    
    // Update max_users based on subscription tier
    if (name === 'subscription_tier') {
      const defaultMaxUsers = {
        basic: 5,
        professional: 25,
        enterprise: 100
      };
      setFormData((prev) => ({ 
        ...prev, 
        max_users: defaultMaxUsers[value] || 5 
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setSuccess('');

    try {
      // Filter out empty password for updates
      const submitData = { ...formData };
      if (organization && !submitData.db_password) {
        delete submitData.db_password;
      }

      if (organization) {
        await adminApi.updateOrganization(organization.id, submitData);
        setSuccess('Organization updated successfully!');
      } else {
        await adminApi.createOrganization(submitData);
        setSuccess('Organization created successfully!');
      }
      
      // Auto-close after 2 seconds on success
      setTimeout(() => {
        onClose();
      }, 2000);
    } catch (err) {
      setError(err.message || 'Failed to save organization.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle className="text-2xl">
          {organization ? 'Edit Organization' : 'Create New Organization'}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <Label htmlFor="name" className="text-sm font-medium">
                Organization Name *
              </Label>
              <Input 
                id="name"
                name="name" 
                value={formData.name} 
                onChange={handleChange} 
                required 
                placeholder="Enter organization name"
              />
            </div>
            <div>
              <Label htmlFor="platform_type" className="text-sm font-medium">
                Platform Type
              </Label>
              <Select 
                value={formData.platform_type} 
                onValueChange={(value) => handleSelectChange('platform_type', value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="evolution">Softbase Evolution</SelectItem>
                  <SelectItem value="minitrac">Minitrac</SelectItem>
                  <SelectItem value="custom">Custom SQL Server</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Database Configuration */}
          <div className="border-t pt-6">
            <h3 className="text-lg font-medium mb-4">Database Configuration</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <Label htmlFor="db_server" className="text-sm font-medium">
                  Database Server *
                </Label>
                <Input 
                  id="db_server"
                  name="db_server" 
                  value={formData.db_server} 
                  onChange={handleChange} 
                  required 
                  placeholder="server.database.windows.net"
                />
              </div>
              <div>
                <Label htmlFor="db_name" className="text-sm font-medium">
                  Database Name *
                </Label>
                <Input 
                  id="db_name"
                  name="db_name" 
                  value={formData.db_name} 
                  onChange={handleChange} 
                  required 
                  placeholder="database_name"
                />
              </div>
              <div>
                <Label htmlFor="db_username" className="text-sm font-medium">
                  Database Username *
                </Label>
                <Input 
                  id="db_username"
                  name="db_username" 
                  value={formData.db_username} 
                  onChange={handleChange} 
                  required 
                  placeholder="username"
                />
              </div>
              <div>
                <Label htmlFor="db_password" className="text-sm font-medium">
                  Database Password {organization ? '' : '*'}
                </Label>
                <Input 
                  id="db_password"
                  name="db_password" 
                  type="password"
                  value={formData.db_password} 
                  onChange={handleChange} 
                  required={!organization}
                  placeholder={organization ? "Leave blank to keep current password" : "Enter password"}
                />
              </div>
            </div>
          </div>

          {/* Subscription Settings */}
          <div className="border-t pt-6">
            <h3 className="text-lg font-medium mb-4">Subscription Settings</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <Label htmlFor="subscription_tier" className="text-sm font-medium">
                  Subscription Tier
                </Label>
                <Select 
                  value={formData.subscription_tier} 
                  onValueChange={(value) => handleSelectChange('subscription_tier', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="basic">Basic (5 users, 100 reports/month)</SelectItem>
                    <SelectItem value="professional">Professional (25 users, 1000 reports/month)</SelectItem>
                    <SelectItem value="enterprise">Enterprise (Unlimited)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="max_users" className="text-sm font-medium">
                  Maximum Users
                </Label>
                <Input 
                  id="max_users"
                  name="max_users" 
                  type="number"
                  value={formData.max_users} 
                  onChange={handleChange} 
                  min="1"
                  max="1000"
                />
              </div>
            </div>
          </div>

          {/* Alerts */}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          
          {success && (
            <Alert className="border-green-200 bg-green-50">
              <AlertDescription className="text-green-800">{success}</AlertDescription>
            </Alert>
          )}

          {/* Actions */}
          <div className="flex justify-between items-center pt-6 border-t">
            <div>
              {organization && (
                <ConnectionTest orgId={organization.id} />
              )}
            </div>
            <div className="flex space-x-3">
              <Button type="button" variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button 
                type="submit" 
                disabled={isLoading}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {isLoading ? 'Saving...' : organization ? 'Update Organization' : 'Create Organization'}
              </Button>
            </div>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};