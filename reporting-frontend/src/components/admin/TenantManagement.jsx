import React, { useState, useEffect } from 'react';
import { TenantList } from './TenantList';
import { TenantForm } from './TenantForm';
import { Button } from '@/components/ui/button';
import { adminApi } from '@/lib/api';

export const TenantManagement = () => {
  const [organizations, setOrganizations] = useState([]);
  const [selectedOrg, setSelectedOrg] = useState(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchOrganizations = async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await adminApi.getOrganizations();
      setOrganizations(data);
    } catch (err) {
      setError('Failed to fetch organizations: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchOrganizations();
  }, []);

  const handleCreate = () => {
    setSelectedOrg(null);
    setIsFormOpen(true);
  };

  const handleEdit = (org) => {
    setSelectedOrg(org);
    setIsFormOpen(true);
  };

  const handleCloseForm = () => {
    setIsFormOpen(false);
    setSelectedOrg(null);
    fetchOrganizations(); // Refresh list after form closes
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-lg">Loading organizations...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
        <Button onClick={fetchOrganizations} className="mt-4">
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Tenant Management</h1>
        {!isFormOpen && (
          <Button onClick={handleCreate} className="bg-blue-600 hover:bg-blue-700">
            + Create New Organization
          </Button>
        )}
      </div>
      
      {isFormOpen ? (
        <TenantForm organization={selectedOrg} onClose={handleCloseForm} />
      ) : (
        <TenantList organizations={organizations} onEdit={handleEdit} />
      )}
    </div>
  );
};