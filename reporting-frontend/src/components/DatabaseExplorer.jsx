import React, { useState, useEffect } from 'react';
import { Search, Database, Table, Key, Clock, Package, ChevronRight, ChevronDown, RefreshCw, Download } from 'lucide-react';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { apiUrl } from '@/lib/api';

const DatabaseExplorer = ({ user }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [databaseInfo, setDatabaseInfo] = useState(null);
  const [expandedTables, setExpandedTables] = useState(new Set());
  const [searchTerm, setSearchTerm] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  const fetchDatabaseInfo = async () => {
    try {
      setError(null);
      const token = localStorage.getItem('token');
      // Use the full schema endpoint for comprehensive data
      const response = await fetch(apiUrl('/api/database/full-schema'), {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch database info');
      }

      const data = await response.json();
      console.log('Database Explorer API Response:', data);
      
      // Transform the full-schema response to match expected format
      const tables = [];
      if (data.schema) {
        for (const [tableName, tableInfo] of Object.entries(data.schema)) {
          if (!tableInfo.error) {
            tables.push({
              table_name: tableName,
              row_count: tableInfo.row_count || 0,
              columns: tableInfo.columns || [],
              primary_keys: tableInfo.primary_keys || [],
              relationships: tableInfo.foreign_keys || []
            });
          }
        }
      }
      
      setDatabaseInfo({
        database: data.database,
        total_tables: data.total_tables,
        tables: tables,
        summary: {
          total_tables: data.total_tables,
          total_rows: tables.reduce((sum, t) => sum + (t.row_count || 0), 0),
          total_relationships: data.relationships ? data.relationships.length : 0
        },
        export_date: new Date().toISOString()
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDatabaseInfo();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchDatabaseInfo();
  };

  const handleDownload = async () => {
    try {
      setRefreshing(true);
      
      // Fetch full export data
      const token = localStorage.getItem('token');
      const response = await fetch(apiUrl('/api/reports/database-explorer?full_export=true'), {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch full export data');
      }

      const fullData = await response.json();
      
      // Create a comprehensive export object
      const exportData = {
        export_date: new Date().toISOString(),
        export_version: '1.0',
        database: 'Tenant ERP Database',
        schema: 'ben002',
        summary: fullData.summary,
        tables: fullData.tables?.map(table => ({
          table_name: table.table_name,
          row_count: table.row_count,
          columns: table.columns,
          primary_keys: table.primary_keys,
          relationships: table.relationships,
          sample_data: table.sample_data?.slice(0, 3) // Include only 3 sample rows
        }))
      };
      
      // Convert to JSON with pretty formatting
      const jsonStr = JSON.stringify(exportData, null, 2);
      
      // Create blob and download
      const blob = new Blob([jsonStr], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `erp_database_schema_${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading database schema:', error);
      alert('Failed to download database schema. Please try again.');
    } finally {
      setRefreshing(false);
    }
  };

  const toggleTable = (tableName) => {
    const newExpanded = new Set(expandedTables);
    if (newExpanded.has(tableName)) {
      newExpanded.delete(tableName);
    } else {
      newExpanded.add(tableName);
    }
    setExpandedTables(newExpanded);
  };

  const formatDataType = (dataType, maxLength) => {
    if (maxLength && dataType.toLowerCase().includes('char')) {
      return `${dataType}(${maxLength})`;
    }
    return dataType;
  };

  const formatNumber = (num) => {
    return num?.toLocaleString() || '0';
  };

  const filterTables = (tables) => {
    if (!searchTerm) return tables;
    
    const term = searchTerm.toLowerCase();
    return tables.filter(table => 
      table.table_name.toLowerCase().includes(term) ||
      table.columns?.some(col => col.column_name.toLowerCase().includes(term))
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow">
          <h2 className="text-xl font-semibold text-red-600 mb-2">Error</h2>
          <p className="text-gray-600">{error}</p>
          <button
            onClick={handleRefresh}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const filteredTables = filterTables(databaseInfo?.tables || []);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <Database className="h-8 w-8 text-blue-600 mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Database Explorer</h1>
                <p className="text-gray-600">Browse ERP database structure and sample data</p>
              </div>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={handleDownload}
                disabled={loading || !databaseInfo}
                className="flex items-center px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400"
              >
                <Download className="h-4 w-4 mr-2" />
                Export JSON
              </button>
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-400"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
          </div>

          {/* Summary Stats */}
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-gray-50 p-4 rounded">
              <div className="flex items-center">
                <Table className="h-5 w-5 text-gray-600 mr-2" />
                <div>
                  <p className="text-sm text-gray-600">Total Tables</p>
                  <p className="text-2xl font-semibold">{databaseInfo?.summary?.total_tables || 0}</p>
                </div>
              </div>
            </div>
            <div className="bg-gray-50 p-4 rounded">
              <div className="flex items-center">
                <Package className="h-5 w-5 text-gray-600 mr-2" />
                <div>
                  <p className="text-sm text-gray-600">Total Rows</p>
                  <p className="text-2xl font-semibold">{formatNumber(databaseInfo?.summary?.total_rows)}</p>
                </div>
              </div>
            </div>
            <div className="bg-gray-50 p-4 rounded">
              <div className="flex items-center">
                <Key className="h-5 w-5 text-gray-600 mr-2" />
                <div>
                  <p className="text-sm text-gray-600">Relationships</p>
                  <p className="text-2xl font-semibold">{databaseInfo?.summary?.total_relationships || 0}</p>
                </div>
              </div>
            </div>
            <div className="bg-gray-50 p-4 rounded">
              <div className="flex items-center">
                <Clock className="h-5 w-5 text-gray-600 mr-2" />
                <div>
                  <p className="text-sm text-gray-600">Export Date</p>
                  <p className="text-sm font-semibold">{new Date(databaseInfo?.export_date).toLocaleDateString()}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Search */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search tables or columns..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Tables List */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">
              Tables ({filteredTables.length} of {databaseInfo?.tables?.length || 0})
            </h2>
          </div>
          
          <div className="divide-y divide-gray-200">
            {filteredTables.map((table) => (
              <div key={table.table_name} className="p-6">
                <div 
                  className="flex items-center justify-between cursor-pointer"
                  onClick={() => toggleTable(table.table_name)}
                >
                  <div className="flex items-center">
                    {expandedTables.has(table.table_name) ? 
                      <ChevronDown className="h-5 w-5 text-gray-400 mr-2" /> : 
                      <ChevronRight className="h-5 w-5 text-gray-400 mr-2" />
                    }
                    <Table className="h-5 w-5 text-gray-600 mr-2" />
                    <h3 className="text-lg font-medium text-gray-900">{table.table_name}</h3>
                    <span className="ml-2 text-sm text-gray-500">
                      ({formatNumber(table.row_count)} rows, {table.columns?.length || 0} columns)
                    </span>
                  </div>
                  {table.primary_keys?.length > 0 && (
                    <div className="flex items-center text-sm text-gray-500">
                      <Key className="h-4 w-4 mr-1" />
                      {table.primary_keys.join(', ')}
                    </div>
                  )}
                </div>

                {expandedTables.has(table.table_name) && (
                  <div className="mt-4 space-y-4">
                    {/* Columns */}
                    <div>
                      <h4 className="text-sm font-semibold text-gray-700 mb-2">Columns</h4>
                      <div className="bg-gray-50 rounded overflow-hidden">
                        <table className="min-w-full">
                          <thead>
                            <tr className="border-b border-gray-200">
                              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Nullable</th>
                              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Default</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-200">
                            {table.columns?.map((column) => (
                              <tr key={column.column_name}>
                                <td className="px-4 py-2 text-sm text-gray-900">
                                  {column.column_name}
                                  {table.primary_keys?.includes(column.column_name) && (
                                    <Key className="inline-block h-3 w-3 ml-1 text-yellow-600" />
                                  )}
                                </td>
                                <td className="px-4 py-2 text-sm text-gray-600">
                                  {formatDataType(column.data_type, column.character_maximum_length)}
                                </td>
                                <td className="px-4 py-2 text-sm text-gray-600">
                                  {column.is_nullable === 'YES' ? 'Yes' : 'No'}
                                </td>
                                <td className="px-4 py-2 text-sm text-gray-600">
                                  {column.column_default || '-'}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {/* Sample Data */}
                    {table.sample_data?.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-700 mb-2">Sample Data (First 5 rows)</h4>
                        <div className="bg-gray-50 rounded overflow-x-auto">
                          <table className="min-w-full">
                            <thead>
                              <tr className="border-b border-gray-200">
                                {Object.keys(table.sample_data[0]).map(key => (
                                  <th key={key} className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase whitespace-nowrap">
                                    {key}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                              {table.sample_data.map((row, idx) => (
                                <tr key={idx}>
                                  {Object.values(row).map((value, cellIdx) => (
                                    <td key={cellIdx} className="px-4 py-2 text-sm text-gray-900 whitespace-nowrap">
                                      {value !== null ? String(value).substring(0, 50) : 'NULL'}
                                      {value && String(value).length > 50 && '...'}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    {/* Relationships */}
                    {table.relationships?.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-700 mb-2">Relationships</h4>
                        <div className="space-y-1">
                          {table.relationships.map((rel, idx) => (
                            <div key={idx} className="text-sm text-gray-600">
                              {rel.type === 'foreign_key' ? (
                                <span>
                                  <Key className="inline-block h-3 w-3 mr-1 text-blue-600" />
                                  {rel.column} → {rel.referenced_table}.{rel.referenced_column}
                                </span>
                              ) : (
                                <span>
                                  <Key className="inline-block h-3 w-3 mr-1 text-green-600" />
                                  {rel.referenced_table}.{rel.referenced_column} → {rel.column}
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default DatabaseExplorer;