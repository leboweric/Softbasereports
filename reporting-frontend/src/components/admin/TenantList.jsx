import React from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export const TenantList = ({ organizations, onEdit }) => {
  const getStatusBadge = (isActive) => {
    return isActive ? (
      <Badge variant="default" className="bg-green-100 text-green-800">
        Active
      </Badge>
    ) : (
      <Badge variant="secondary" className="bg-red-100 text-red-800">
        Inactive
      </Badge>
    );
  };

  const getTierBadge = (tier) => {
    const colors = {
      basic: "bg-gray-100 text-gray-800",
      professional: "bg-blue-100 text-blue-800", 
      enterprise: "bg-purple-100 text-purple-800"
    };
    
    return (
      <Badge variant="secondary" className={colors[tier] || "bg-gray-100 text-gray-800"}>
        {tier ? tier.charAt(0).toUpperCase() + tier.slice(1) : 'Unknown'}
      </Badge>
    );
  };

  if (!organizations || organizations.length === 0) {
    return (
      <div className="bg-white rounded-lg border p-8 text-center">
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Organizations Found</h3>
        <p className="text-gray-500">Get started by creating your first organization.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border shadow-sm">
      <Table>
        <TableHeader>
          <TableRow className="border-b">
            <TableHead className="font-semibold">Organization Name</TableHead>
            <TableHead className="font-semibold">Platform Type</TableHead>
            <TableHead className="font-semibold">Subscription Tier</TableHead>
            <TableHead className="font-semibold">Users</TableHead>
            <TableHead className="font-semibold">Status</TableHead>
            <TableHead className="font-semibold">Database</TableHead>
            <TableHead className="font-semibold text-center">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {organizations.map((org) => (
            <TableRow key={org.id} className="hover:bg-gray-50">
              <TableCell className="font-medium">{org.name}</TableCell>
              <TableCell>
                <code className="bg-gray-100 px-2 py-1 rounded text-sm">
                  {org.platform_type}
                </code>
              </TableCell>
              <TableCell>{getTierBadge(org.subscription_tier)}</TableCell>
              <TableCell>
                <span className="text-sm">
                  {org.user_count || 0} / {org.max_users}
                </span>
              </TableCell>
              <TableCell>{getStatusBadge(org.is_active)}</TableCell>
              <TableCell>
                <div className="text-sm text-gray-600">
                  <div>{org.db_server}</div>
                  <div className="text-xs text-gray-400">{org.db_name}</div>
                </div>
              </TableCell>
              <TableCell className="text-center">
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => onEdit(org)}
                  className="hover:bg-blue-50 hover:border-blue-300"
                >
                  Edit
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};