import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Alert, AlertDescription } from './ui/alert';
import { 
  Lightbulb, 
  Play, 
  Save, 
  Download, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  Sparkles,
  FileText,
  Database
} from 'lucide-react';

const ReportCreator = () => {
  const [description, setDescription] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [reportResult, setReportResult] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [examples, setExamples] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [validation, setValidation] = useState(null);
  const [activeTab, setActiveTab] = useState('create');

  useEffect(() => {
    fetchExamples();
    fetchTemplates();
  }, []);

  useEffect(() => {
    if (description.length > 3) {
      fetchSuggestions();
      validateDescription();
    } else {
      setSuggestions([]);
      setValidation(null);
    }
  }, [description]);

  const fetchExamples = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/custom-reports/examples', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      if (data.success) {
        setExamples(data.examples);
      }
    } catch (error) {
      console.error('Failed to fetch examples:', error);
    }
  };

  const fetchTemplates = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/custom-reports/templates', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      if (data.success) {
        setTemplates(data.templates);
      }
    } catch (error) {
      console.error('Failed to fetch templates:', error);
    }
  };

  const fetchSuggestions = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/custom-reports/suggestions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ description })
      });
      const data = await response.json();
      if (data.success) {
        setSuggestions(data.suggestions);
      }
    } catch (error) {
      console.error('Failed to fetch suggestions:', error);
    }
  };

  const validateDescription = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/custom-reports/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ description })
      });
      const data = await response.json();
      if (data.success) {
        setValidation(data.validation);
      }
    } catch (error) {
      console.error('Failed to validate description:', error);
    }
  };

  const createReport = async (saveTemplate = false) => {
    if (!description.trim()) return;

    setIsCreating(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/custom-reports/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ 
          description,
          save_template: saveTemplate
        })
      });
      
      const data = await response.json();
      setReportResult(data);
      
      if (data.success && saveTemplate) {
        fetchTemplates(); // Refresh templates list
      }
    } catch (error) {
      setReportResult({
        success: false,
        error: 'Failed to create report'
      });
    } finally {
      setIsCreating(false);
    }
  };

  const runTemplate = async (templateId) => {
    setIsCreating(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/custom-reports/templates/${templateId}/run`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      const data = await response.json();
      setReportResult(data);
      setActiveTab('create'); // Switch to results tab
    } catch (error) {
      setReportResult({
        success: false,
        error: 'Failed to run template'
      });
    } finally {
      setIsCreating(false);
    }
  };

  const exportReport = (format) => {
    if (!reportResult?.data) return;
    
    const data = reportResult.data;
    const filename = `${reportResult.metadata?.title || 'custom_report'}_${new Date().toISOString().split('T')[0]}`;
    
    if (format === 'csv') {
      const csv = convertToCSV(data);
      downloadFile(csv, `${filename}.csv`, 'text/csv');
    } else if (format === 'json') {
      const json = JSON.stringify(data, null, 2);
      downloadFile(json, `${filename}.json`, 'application/json');
    }
  };

  const convertToCSV = (data) => {
    if (!data.length) return '';
    
    const headers = Object.keys(data[0]);
    const csvContent = [
      headers.join(','),
      ...data.map(row => headers.map(header => `"${row[header] || ''}"`).join(','))
    ].join('\n');
    
    return csvContent;
  };

  const downloadFile = (content, filename, contentType) => {
    const blob = new Blob([content], { type: contentType });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  const useSuggestion = (suggestion) => {
    setDescription(suggestion);
  };

  const useExample = (example) => {
    setDescription(example);
    setActiveTab('create');
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-2">
        <Sparkles className="h-6 w-6 text-blue-600" />
        <h2 className="text-2xl font-bold">AI Report Creator</h2>
        <Badge variant="secondary">Natural Language</Badge>
      </div>
      
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="create">Create Report</TabsTrigger>
          <TabsTrigger value="templates">Saved Templates</TabsTrigger>
          <TabsTrigger value="examples">Examples</TabsTrigger>
        </TabsList>
        
        <TabsContent value="create" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <FileText className="h-5 w-5" />
                <span>Describe Your Report</span>
              </CardTitle>
              <CardDescription>
                Tell us what report you need in plain English. Be specific about what data you want to see.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Textarea
                  placeholder="Example: Show me all work orders that are complete but haven't been invoiced"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="min-h-[100px]"
                />
                
                {validation && (
                  <Alert className={validation.is_valid ? "border-green-200" : "border-yellow-200"}>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <span>Confidence: </span>
                          <Badge variant={validation.confidence === 'high' ? 'default' : 'secondary'}>
                            {validation.confidence}
                          </Badge>
                        </div>
                        {validation.warnings.map((warning, index) => (
                          <div key={index} className="text-yellow-600">⚠️ {warning}</div>
                        ))}
                        {validation.suggestions.map((suggestion, index) => (
                          <div key={index} className="text-blue-600">💡 {suggestion}</div>
                        ))}
                      </div>
                    </AlertDescription>
                  </Alert>
                )}
              </div>
              
              {suggestions.length > 0 && (
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <Lightbulb className="h-4 w-4 text-yellow-500" />
                    <span className="text-sm font-medium">Suggestions:</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {suggestions.map((suggestion, index) => (
                      <Button
                        key={index}
                        variant="outline"
                        size="sm"
                        onClick={() => useSuggestion(suggestion)}
                        className="text-left h-auto p-2 whitespace-normal"
                      >
                        {suggestion}
                      </Button>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="flex space-x-2">
                <Button 
                  onClick={() => createReport(false)}
                  disabled={!description.trim() || isCreating}
                  className="flex items-center space-x-2"
                >
                  <Play className="h-4 w-4" />
                  <span>{isCreating ? 'Creating...' : 'Create Report'}</span>
                </Button>
                
                <Button 
                  variant="outline"
                  onClick={() => createReport(true)}
                  disabled={!description.trim() || isCreating}
                  className="flex items-center space-x-2"
                >
                  <Save className="h-4 w-4" />
                  <span>Create & Save Template</span>
                </Button>
              </div>
            </CardContent>
          </Card>
          
          {reportResult && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Database className="h-5 w-5" />
                  <span>Report Results</span>
                  {reportResult.success ? (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-red-500" />
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {reportResult.success ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center">
                        <div className="text-2xl font-bold">{reportResult.metadata?.data_count || 0}</div>
                        <div className="text-sm text-gray-500">Records Found</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold">{reportResult.metadata?.columns?.length || 0}</div>
                        <div className="text-sm text-gray-500">Columns</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold">{reportResult.metadata?.title}</div>
                        <div className="text-sm text-gray-500">Report Title</div>
                      </div>
                      <div className="text-center">
                        <div className="flex justify-center space-x-2">
                          <Button size="sm" onClick={() => exportReport('csv')}>
                            <Download className="h-4 w-4 mr-1" />
                            CSV
                          </Button>
                          <Button size="sm" variant="outline" onClick={() => exportReport('json')}>
                            <Download className="h-4 w-4 mr-1" />
                            JSON
                          </Button>
                        </div>
                        <div className="text-sm text-gray-500">Export</div>
                      </div>
                    </div>
                    
                    {reportResult.data && reportResult.data.length > 0 && (
                      <div className="overflow-x-auto">
                        <table className="w-full border-collapse border border-gray-300">
                          <thead>
                            <tr className="bg-gray-50">
                              {Object.keys(reportResult.data[0]).map((column) => (
                                <th key={column} className="border border-gray-300 px-4 py-2 text-left">
                                  {column.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {reportResult.data.slice(0, 10).map((row, index) => (
                              <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                                {Object.values(row).map((value, cellIndex) => (
                                  <td key={cellIndex} className="border border-gray-300 px-4 py-2">
                                    {value !== null && value !== undefined ? String(value) : '-'}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {reportResult.data.length > 10 && (
                          <div className="text-center text-sm text-gray-500 mt-2">
                            Showing first 10 of {reportResult.data.length} records. Export for full data.
                          </div>
                        )}
                      </div>
                    )}
                    
                    {reportResult.template_saved && (
                      <Alert className="border-green-200">
                        <CheckCircle className="h-4 w-4" />
                        <AlertDescription>
                          Report template saved successfully! You can find it in the "Saved Templates" tab.
                        </AlertDescription>
                      </Alert>
                    )}
                  </div>
                ) : (
                  <Alert className="border-red-200">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      {reportResult.error || 'Failed to create report'}
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>
        
        <TabsContent value="templates" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Saved Report Templates</CardTitle>
              <CardDescription>
                Quickly run reports you've created and saved before
              </CardDescription>
            </CardHeader>
            <CardContent>
              {templates.length > 0 ? (
                <div className="space-y-3">
                  {templates.map((template) => (
                    <div key={template.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex-1">
                        <h4 className="font-medium">{template.name}</h4>
                        <p className="text-sm text-gray-500 mt-1">{template.description}</p>
                        <div className="flex items-center space-x-4 mt-2 text-xs text-gray-400">
                          <span className="flex items-center space-x-1">
                            <Clock className="h-3 w-3" />
                            <span>Created {new Date(template.created_at).toLocaleDateString()}</span>
                          </span>
                          <span>Used {template.usage_count} times</span>
                        </div>
                      </div>
                      <Button 
                        onClick={() => runTemplate(template.id)}
                        disabled={isCreating}
                        className="ml-4"
                      >
                        <Play className="h-4 w-4 mr-1" />
                        Run
                      </Button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No saved templates yet</p>
                  <p className="text-sm">Create a report and save it as a template to see it here</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="examples" className="space-y-4">
          {examples.map((category) => (
            <Card key={category.category}>
              <CardHeader>
                <CardTitle>{category.category}</CardTitle>
                <CardDescription>
                  Click any example to use it as a starting point
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {category.examples.map((example, index) => (
                    <Button
                      key={index}
                      variant="outline"
                      onClick={() => useExample(example)}
                      className="w-full text-left justify-start h-auto p-3 whitespace-normal"
                    >
                      {example}
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ReportCreator;

