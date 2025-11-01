import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { adminApi } from '@/lib/api';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';

export const ConnectionTest = ({ orgId }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleTest = async () => {
    if (!orgId) {
      setResult({ 
        success: false, 
        message: 'Organization ID is required for connection testing.' 
      });
      return;
    }

    setIsLoading(true);
    setResult(null);
    
    try {
      const data = await adminApi.testConnection(orgId);
      setResult(data);
    } catch (err) {
      setResult({ 
        success: false, 
        message: 'Failed to run connection test.', 
        error: err.message 
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getResultIcon = () => {
    if (isLoading) return <Loader2 className="h-4 w-4 animate-spin" />;
    if (result?.success) return <CheckCircle className="h-4 w-4 text-green-600" />;
    if (result && !result.success) return <XCircle className="h-4 w-4 text-red-600" />;
    return null;
  };

  const getResultVariant = () => {
    if (result?.success) return "default";
    return "destructive";
  };

  return (
    <div className="space-y-3">
      <Button 
        type="button" 
        variant="secondary" 
        onClick={handleTest} 
        disabled={isLoading || !orgId}
        className="flex items-center gap-2"
      >
        {getResultIcon()}
        {isLoading ? 'Testing Connection...' : 'Test Database Connection'}
      </Button>
      
      {result && (
        <Alert variant={getResultVariant()} className="max-w-md">
          <AlertDescription className="text-sm">
            <div className="flex items-start gap-2">
              {result.success ? (
                <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
              ) : (
                <XCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
              )}
              <div>
                <p className="font-medium">
                  {result.success ? 'Connection Successful' : 'Connection Failed'}
                </p>
                <p className="mt-1">{result.message}</p>
                {result.error && (
                  <p className="mt-1 text-xs opacity-75">
                    Error: {result.error}
                  </p>
                )}
                {result.connection_time && (
                  <p className="mt-1 text-xs opacity-75">
                    Response time: {result.connection_time}ms
                  </p>
                )}
              </div>
            </div>
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
};