import React, { useState } from 'react';
import { apiUrl } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Loader2, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

export default function QueryVariationTester() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [selectedGroup, setSelectedGroup] = useState(null);

  const testVariations = async (groupName = null) => {
    setLoading(true);
    setError(null);
    setResults(null);
    setSelectedGroup(groupName);

    try {
      const response = await fetch(apiUrl('/api/ai-test/test-variations'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ group: groupName })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (data.success) {
        setResults(data.results);
      } else {
        throw new Error(data.error || 'Test failed');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'passed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
    }
  };

  const getConsistencyColor = (score) => {
    const percentage = parseFloat(score);
    if (percentage >= 90) return 'text-green-600';
    if (percentage >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Query Variation Tester</CardTitle>
          <p className="text-sm text-gray-600">
            Test multiple variations of the same query to ensure consistent SQL generation
          </p>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex gap-2 flex-wrap">
              <Button
                onClick={() => testVariations()}
                disabled={loading}
              >
                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Test All Groups
              </Button>
              <Button
                variant="outline"
                onClick={() => testVariations('forklift_rentals')}
                disabled={loading}
              >
                Test Forklift Rentals
              </Button>
              <Button
                variant="outline"
                onClick={() => testVariations('parts_reorder')}
                disabled={loading}
              >
                Test Parts Reorder
              </Button>
              <Button
                variant="outline"
                onClick={() => testVariations('active_rentals')}
                disabled={loading}
              >
                Test Active Rentals
              </Button>
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {results && (
              <div className="space-y-6">
                {Object.entries(results).map(([groupName, groupData]) => (
                  <Card key={groupName}>
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <div>
                          <CardTitle className="text-lg">{groupName}</CardTitle>
                          <p className="text-sm text-gray-600">{groupData.description}</p>
                        </div>
                        <div className="text-right">
                          <p className={`text-2xl font-bold ${getConsistencyColor(groupData.summary.consistency_score)}`}>
                            {groupData.summary.consistency_score}
                          </p>
                          <p className="text-xs text-gray-500">Consistency</p>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {/* Summary Stats */}
                        <div className="grid grid-cols-3 gap-4 text-sm">
                          <div>
                            <p className="text-gray-600">Total Variations</p>
                            <p className="font-semibold">{groupData.summary.total_variations}</p>
                          </div>
                          <div>
                            <p className="text-gray-600">Unique SQL Queries</p>
                            <p className="font-semibold">{groupData.summary.unique_sql_queries}</p>
                          </div>
                          <div>
                            <p className="text-gray-600">Expected Action</p>
                            <p className="font-semibold">{groupData.expected.action}</p>
                          </div>
                        </div>

                        {/* SQL Groups */}
                        {groupData.summary.sql_groups.length > 1 && (
                          <div className="border-t pt-4">
                            <p className="text-sm font-semibold mb-2">SQL Query Groups:</p>
                            {groupData.summary.sql_groups.map((group, idx) => (
                              <div key={idx} className="mb-3 p-3 bg-gray-50 rounded">
                                <p className="text-xs font-mono mb-2">{group.sql}</p>
                                <p className="text-xs text-gray-600">
                                  Queries ({group.queries.length}): {group.queries.join(', ')}
                                </p>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Variation Details */}
                        <details className="border-t pt-4">
                          <summary className="cursor-pointer text-sm font-semibold">
                            Variation Details
                          </summary>
                          <div className="mt-4 space-y-2">
                            {groupData.variations.map((variation, idx) => (
                              <div key={idx} className="flex items-start gap-2 text-sm">
                                {getStatusIcon(variation.status)}
                                <div className="flex-1">
                                  <p className="font-medium">{variation.query}</p>
                                  {variation.ai_analysis && (
                                    <div className="mt-1 flex gap-2 flex-wrap">
                                      {variation.ai_analysis.query_action && (
                                        <Badge variant="outline" className="text-xs">
                                          action: {variation.ai_analysis.query_action}
                                        </Badge>
                                      )}
                                      {variation.ai_analysis.entity_subtype && (
                                        <Badge variant="outline" className="text-xs">
                                          type: {variation.ai_analysis.entity_subtype}
                                        </Badge>
                                      )}
                                      {variation.ai_analysis.filters?.status && (
                                        <Badge variant="outline" className="text-xs">
                                          status: {variation.ai_analysis.filters.status}
                                        </Badge>
                                      )}
                                    </div>
                                  )}
                                  {variation.error && (
                                    <p className="text-xs text-red-600 mt-1">{variation.error}</p>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </details>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}