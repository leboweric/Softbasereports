import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { apiUrl } from '@/lib/api';
import { Search, Filter, Plus, Edit, Trash2, Eye, Book, Wrench, AlertCircle, CheckCircle, Paperclip, FileText, MessageSquare, Bot, Send } from 'lucide-react';
import FileUploadDropzone from './FileUploadDropzone';
import SearchableSelect from './SearchableSelect';
import ServiceAssistantAnalytics from './ServiceAssistantAnalytics';

const KnowledgeBase = () => {
  const [articles, setArticles] = useState([]);
  const [filteredArticles, setFilteredArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedMake, setSelectedMake] = useState('');
  const [categories, setCategories] = useState([]);
  const [makes, setMakes] = useState([]);
  const [models, setModels] = useState([]);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [showArticleModal, setShowArticleModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingArticle, setEditingArticle] = useState(null);
  const [isAdmin, setIsAdmin] = useState(false);
  
  // Work Order History state
  const [workOrders, setWorkOrders] = useState([]);
  const [woLoading, setWoLoading] = useState(false);
  const [woSearchTerm, setWoSearchTerm] = useState('');
  const [woMakeFilter, setWoMakeFilter] = useState('');
  const [woCustomerFilter, setWoCustomerFilter] = useState('');

  // Service Assistant state
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [selectedWorkOrder, setSelectedWorkOrder] = useState(null);
  const [showWoModal, setShowWoModal] = useState(false);

  useEffect(() => {
    fetchArticles();
    fetchCategories();
    fetchMakes();
    checkAdminStatus();
  }, []);

  useEffect(() => {
    filterArticles();
  }, [articles, searchTerm, selectedCategory, selectedMake]);

  const checkAdminStatus = () => {
    // RBAC disabled - allow all authenticated users
    setIsAdmin(true);
  };

  const fetchArticles = async () => {
    try {
      setLoading(true);
      const response = await fetch(apiUrl('/api/knowledge-base/articles'), {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) throw new Error('Failed to fetch articles');

      const data = await response.json();
      setArticles(data.articles);
      setFilteredArticles(data.articles);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await fetch(apiUrl('/api/knowledge-base/categories'), {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setCategories(data.categories);
      }
    } catch (err) {
      console.error('Failed to fetch categories:', err);
    }
  };

  const fetchMakes = async () => {
    try {
      const response = await fetch(apiUrl('/api/knowledge-base/equipment-makes'), {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setMakes(data.makes);
      }
    } catch (err) {
      console.error('Failed to fetch makes:', err);
    }
  };

  const fetchModels = async (make = '') => {
    try {
      const url = make 
        ? apiUrl(`/api/knowledge-base/equipment-models?make=${encodeURIComponent(make)}`)
        : apiUrl('/api/knowledge-base/equipment-models');
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setModels(data.models);
      }
    } catch (err) {
      console.error('Failed to fetch models:', err);
    }
  };

  const filterArticles = () => {
    let filtered = articles;

    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(article =>
        article.title.toLowerCase().includes(term) ||
        article.symptoms.toLowerCase().includes(term) ||
        article.rootCause.toLowerCase().includes(term) ||
        article.solution.toLowerCase().includes(term) ||
        article.equipmentMake.toLowerCase().includes(term) ||
        article.equipmentModel.toLowerCase().includes(term)
      );
    }

    if (selectedCategory) {
      filtered = filtered.filter(article => article.issueCategory === selectedCategory);
    }

    if (selectedMake) {
      filtered = filtered.filter(article => article.equipmentMake === selectedMake);
    }

    setFilteredArticles(filtered);
  };

  const searchWorkOrders = async () => {
    try {
      setWoLoading(true);
      
      const params = new URLSearchParams();
      if (woSearchTerm) params.append('search', woSearchTerm);
      if (woMakeFilter) params.append('equipment_make', woMakeFilter);
      if (woCustomerFilter) params.append('customer', woCustomerFilter);
      params.append('limit', '100');
      
      const response = await fetch(apiUrl(`/api/knowledge-base/work-orders/search?${params.toString()}`), {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) throw new Error('Failed to search work orders');

      const data = await response.json();
      setWorkOrders(data.workOrders || []);
    } catch (err) {
      console.error('Failed to search work orders:', err);
      setWorkOrders([]);
    } finally {
      setWoLoading(false);
    }
  };

  const viewArticle = async (articleId) => {
    try {
      const response = await fetch(apiUrl(`/api/knowledge-base/articles/${articleId}`), {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSelectedArticle(data.article);
        setShowArticleModal(true);
      }
    } catch (err) {
      console.error('Failed to fetch article:', err);
    }
  };

  const createArticle = () => {
    setEditingArticle({
      title: '',
      equipmentMake: '',
      equipmentModel: '',
      issueCategory: '',
      symptoms: '',
      rootCause: '',
      solution: '',
      relatedWONumbers: '',
      imageUrls: []
    });
    setShowEditModal(true);
  };

  const editArticle = (article) => {
    setEditingArticle(article);
    // If article has a make, fetch models for that make
    if (article.equipmentMake) {
      fetchModels(article.equipmentMake);
    }
    setShowEditModal(true);
  };

  const convertToArticle = (wo) => {
    // Combine all comment fields into symptoms
    const allComments = [
      wo.comments,
      wo.privateComments,
      wo.shopComments
    ].filter(Boolean).join('\n\n');

    // Auto-generate title from make, model, and first line of comments
    const firstCommentLine = wo.comments?.split('\n')[0] || 'Work Order';
    const title = `${wo.make || 'Equipment'} ${wo.model || ''} - ${firstCommentLine}`.trim();

    setEditingArticle({
      title: title.substring(0, 200), // Limit title length
      equipmentMake: wo.make || '',
      equipmentModel: wo.model || '',
      issueCategory: '', // User will select
      symptoms: allComments,
      rootCause: '', // User will fill in
      solution: wo.workDescription || '', // Labor/parts performed
      relatedWONumbers: wo.woNumber.toString(),
      imageUrls: []
    });

    // If WO has a make, fetch models for that make
    if (wo.make) {
      fetchModels(wo.make);
    }

    setShowEditModal(true);
  };

  const saveArticle = async () => {
    try {
      const url = editingArticle.id
        ? apiUrl(`/api/knowledge-base/articles/${editingArticle.id}`)
        : apiUrl('/api/knowledge-base/articles');

      const method = editingArticle.id ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(editingArticle)
      });

      if (response.ok) {
        setShowEditModal(false);
        setEditingArticle(null);
        fetchArticles();
        fetchCategories();
        fetchMakes();
      } else {
        const error = await response.json();
        alert(`Failed to save article: ${error.error}`);
      }
    } catch (err) {
      alert(`Error saving article: ${err.message}`);
    }
  };

  const deleteArticle = async (articleId) => {
    if (!confirm('Are you sure you want to delete this article?')) return;

    try {
      const response = await fetch(apiUrl(`/api/knowledge-base/articles/${articleId}`), {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        fetchArticles();
      } else {
        alert('Failed to delete article');
      }
    } catch (err) {
      alert(`Error deleting article: ${err.message}`);
    }
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'Hydraulic': return '🔧';
      case 'Engine': return '⚙️';
      case 'Electrical': return '⚡';
      case 'Transmission': return '🔩';
      case 'Brake': return '🛑';
      case 'Cooling': return '❄️';
      case 'Fuel': return '⛽';
      default: return '🔨';
    }
  };

  const handleSendMessage = async (messageOverride = null) => {
    const message = messageOverride || chatInput.trim();
    if (!message || chatLoading) return;

    // Add user message to chat
    const userMessage = { role: 'user', content: message };
    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');
    setChatLoading(true);

    try {
      const response = await fetch(apiUrl('/api/service-assistant/chat'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message })
      });

      if (!response.ok) throw new Error('Failed to get response from assistant');

      const data = await response.json();
      const assistantMessage = { role: 'assistant', content: data.response };
      setChatMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Chat error:', err);
      const errorMessage = { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error. Please try again.' 
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setChatLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading Knowledge Base...</div>
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-red-500">Error: {error}</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Book className="h-8 w-8 text-blue-600" />
            Service Knowledge Base
          </h1>
          <p className="text-gray-600 mt-1">
            Technical troubleshooting articles and solutions for field technicians
          </p>
        </div>
        {isAdmin && (
          <button
            onClick={createArticle}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" />
            New Article
          </button>
        )}
      </div>

      {/* Tabs */}
      <Tabs defaultValue="articles" className="w-full">
        <TabsList className="grid w-full max-w-4xl grid-cols-4">
          <TabsTrigger value="articles">
            Knowledge Articles
          </TabsTrigger>
          <TabsTrigger value="work-orders">
            Work Order History
          </TabsTrigger>
          <TabsTrigger value="assistant">
            Service Assistant
          </TabsTrigger>
          <TabsTrigger value="analytics">
            Analytics
          </TabsTrigger>
        </TabsList>

        <TabsContent value="articles" className="space-y-6 mt-6">
          {/* Search and Filters */}
          <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search articles..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border rounded-md"
              />
            </div>

            {/* Category Filter */}
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border rounded-md appearance-none"
              >
                <option value="">All Categories</option>
                {categories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>

            {/* Equipment Make Filter */}
            <div>
              <SearchableSelect
                value={selectedMake}
                onChange={setSelectedMake}
                options={makes}
                placeholder="All Equipment Makes"
              />
            </div>
          </div>

          {/* Results Count */}
          <div className="mt-4 text-sm text-gray-600">
            Showing {filteredArticles.length} of {articles.length} articles
          </div>
        </CardContent>
      </Card>

      {/* Articles List */}
      <div className="grid grid-cols-1 gap-4">
        {filteredArticles.map(article => (
          <Card key={article.id} className="hover:shadow-lg transition-shadow">
            <CardContent className="p-6">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-2xl">{getCategoryIcon(article.issueCategory)}</span>
                    <div>
                      <h3 className="text-xl font-semibold">{article.title}</h3>
                      <div className="flex items-center gap-2 text-sm text-gray-600 mt-1">
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">
                          {article.issueCategory}
                        </span>
                        {article.equipmentMake && (
                          <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded">
                            {article.equipmentMake} {article.equipmentModel}
                          </span>
                        )}
                        <span className="flex items-center gap-1">
                          <Eye className="h-3 w-3" />
                          {article.viewCount} views
                        </span>
                        {article.attachmentCount > 0 && (
                          <span className="flex items-center gap-1 text-gray-600">
                            <Paperclip className="h-3 w-3" />
                            {article.attachmentCount}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="mt-3 space-y-2">
                    <div>
                      <span className="font-semibold text-sm flex items-center gap-1">
                        <AlertCircle className="h-4 w-4 text-orange-600" />
                        Symptoms:
                      </span>
                      <p className="text-gray-700 text-sm mt-1 line-clamp-2">
                        {article.symptoms}
                      </p>
                    </div>
                  </div>

                  <div className="mt-4 flex items-center gap-4 text-xs text-gray-500">
                    <span>Created by {article.createdBy}</span>
                    {article.updatedDate && (
                      <span>Updated {new Date(article.updatedDate).toLocaleDateString()}</span>
                    )}
                  </div>
                </div>

                <div className="flex gap-2 ml-4">
                  <button
                    onClick={() => viewArticle(article.id)}
                    className="p-2 text-blue-600 hover:bg-blue-50 rounded"
                    title="View Article"
                  >
                    <Eye className="h-5 w-5" />
                  </button>
                  {isAdmin && (
                    <>
                      <button
                        onClick={() => editArticle(article)}
                        className="p-2 text-green-600 hover:bg-green-50 rounded"
                        title="Edit Article"
                      >
                        <Edit className="h-5 w-5" />
                      </button>
                      <button
                        onClick={() => deleteArticle(article.id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded"
                        title="Delete Article"
                      >
                        <Trash2 className="h-5 w-5" />
                      </button>
                    </>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}

        {filteredArticles.length === 0 && (
          <Card>
            <CardContent className="p-12 text-center text-gray-500">
              <Book className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p className="text-lg">No articles found</p>
              <p className="text-sm mt-2">Try adjusting your search or filters</p>
            </CardContent>
          </Card>
        )}
      </div>
        </TabsContent>

        <TabsContent value="work-orders" className="space-y-6 mt-6">
          {/* Work Order Search */}
          <Card>
            <CardContent className="p-4">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {/* Keyword Search */}
                <div className="md:col-span-2">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <input
                        type="text"
                        placeholder="Search work order notes and descriptions..."
                        value={woSearchTerm}
                        onChange={(e) => setWoSearchTerm(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && searchWorkOrders()}
                      className="w-full pl-10 pr-4 py-2 border rounded-md"
                    />
                  </div>
                </div>

                {/* Equipment Make Filter */}
                <div>
                  <SearchableSelect
                    value={woMakeFilter}
                    onChange={setWoMakeFilter}
                    options={makes}
                    placeholder="All Makes"
                  />
                </div>

                {/* Search Button */}
                <div>
                  <button
                    onClick={searchWorkOrders}
                    disabled={woLoading}
                    className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 flex items-center justify-center gap-2"
                  >
                    <Search className="h-4 w-4" />
                    {woLoading ? 'Searching...' : 'Search'}
                  </button>
                </div>
              </div>

              {/* Results Count */}
              {workOrders.length > 0 && (
                <div className="mt-4 text-sm text-gray-600">
                  Found {workOrders.length} work order{workOrders.length !== 1 ? 's' : ''}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Work Orders List */}
          <div className="grid grid-cols-1 gap-4">
            {workOrders.map(wo => (
              <Card key={wo.woNumber} className="hover:shadow-lg transition-shadow">
                <CardContent className="p-6">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <Wrench className="h-5 w-5 text-blue-600" />
                        <div>
                          <h3 className="text-lg font-semibold">WO #{wo.woNumber}</h3>
                          <div className="flex items-center gap-2 text-sm text-gray-600 mt-1">
                            <span className="text-gray-600">
                              Bill To: {wo.billTo}
                            </span>
                            {wo.make && (
                              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">
                                {wo.make} {wo.model}
                              </span>
                            )}
                            {wo.unitNumber && (
                              <span className="text-gray-500">Unit: {wo.unitNumber}</span>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="mt-3 space-y-3">
                        {wo.comments && (
                          <div>
                            <span className="font-semibold text-sm flex items-center gap-1 text-blue-600">
                              <MessageSquare className="h-4 w-4" />
                              Comments
                            </span>
                            <p className="text-gray-700 text-sm mt-1 whitespace-pre-wrap">
                              {wo.comments}
                            </p>
                          </div>
                        )}
                        {wo.privateComments && (
                          <div>
                            <span className="font-semibold text-sm flex items-center gap-1 text-purple-600">
                              <MessageSquare className="h-4 w-4" />
                              Private Comments
                            </span>
                            <p className="text-gray-700 text-sm mt-1 whitespace-pre-wrap">
                              {wo.privateComments}
                            </p>
                          </div>
                        )}
                        {wo.shopComments && (
                          <div>
                            <span className="font-semibold text-sm flex items-center gap-1 text-orange-600">
                              <MessageSquare className="h-4 w-4" />
                              Shop Comments
                            </span>
                            <p className="text-gray-700 text-sm mt-1 whitespace-pre-wrap">
                              {wo.shopComments}
                            </p>
                          </div>
                        )}
                        {wo.workDescription && (
                          <div>
                            <span className="font-semibold text-sm flex items-center gap-1 text-gray-600">
                              <MessageSquare className="h-4 w-4" />
                              Labor/Parts Items
                            </span>
                            <p className="text-gray-700 text-sm mt-1 whitespace-pre-wrap">
                              {wo.workDescription}
                            </p>
                          </div>
                        )}
                      </div>

                      <div className="mt-4 flex items-center gap-4 text-xs text-gray-500">
                        {wo.type && <span>Type: {wo.type}</span>}
                        {wo.dateClosed && (
                          <span>Closed: {new Date(wo.dateClosed).toLocaleDateString()}</span>
                        )}
                        {wo.serialNumber && <span>S/N: {wo.serialNumber}</span>}
                      </div>

                      {/* Convert to KB Article Button */}
                      {isAdmin && (
                        <div className="mt-4 pt-4 border-t">
                          <button
                            onClick={() => convertToArticle(wo)}
                            className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 flex items-center justify-center gap-2 text-sm font-medium"
                          >
                            <Book className="h-4 w-4" />
                            Convert to Knowledge Base Article
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}

            {workOrders.length === 0 && !woLoading && (
              <Card>
                <CardContent className="p-12 text-center text-gray-500">
                  <FileText className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p className="text-lg">No work orders found</p>
                  <p className="text-sm mt-2">Enter keywords to search past work orders</p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="assistant" className="space-y-6 mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bot className="h-5 w-5 text-blue-600" />
                Service Assistant
              </CardTitle>
              <p className="text-sm text-gray-600">Ask questions about equipment issues, troubleshooting, or search our knowledge base and work order history.</p>
            </CardHeader>
            <CardContent className="p-6">
              {/* Suggested Questions */}
              {chatMessages.length === 0 && (
                <div className="mb-6">
                  <p className="text-sm font-semibold text-gray-700 mb-3">Try asking:</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {[
                      "How do I troubleshoot hydraulic pressure loss on a Linde forklift?",
                      "What are common causes of engine overheating?",
                      "Show me recent work orders for Toyota forklifts",
                      "How do I replace the mast on a Crown forklift?"
                    ].map((question, idx) => (
                      <button
                        key={idx}
                        onClick={() => {
                          setChatInput(question);
                          handleSendMessage(question);
                        }}
                        className="text-left p-3 text-sm bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors text-blue-900"
                      >
                        {question}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Chat Messages */}
              <div className="space-y-4 mb-4 max-h-[500px] overflow-y-auto">
                {chatMessages.map((msg, idx) => (
                  <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] rounded-lg p-4 ${
                      msg.role === 'user' 
                        ? 'bg-blue-600 text-white' 
                        : 'bg-gray-100 text-gray-900'
                    }`}>
                      {msg.role === 'assistant' && (
                        <div className="flex items-center gap-2 mb-2">
                          <Bot className="h-4 w-4" />
                          <span className="font-semibold text-sm">Service Assistant</span>
                        </div>
                      )}
                      <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
                    </div>
                  </div>
                ))}
                {chatLoading && (
                  <div className="flex justify-start">
                    <div className="max-w-[80%] rounded-lg p-4 bg-gray-100 text-gray-900">
                      <div className="flex items-center gap-2">
                        <Bot className="h-4 w-4 animate-pulse" />
                        <span className="text-sm">Thinking...</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Input Area */}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                  placeholder="Ask about equipment issues, troubleshooting, or search work orders..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={chatLoading}
                />
                <button
                  onClick={() => handleSendMessage()}
                  disabled={chatLoading || !chatInput.trim()}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  <Send className="h-4 w-4" />
                  Send
                </button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6 mt-6">
          <ServiceAssistantAnalytics />
        </TabsContent>
      </Tabs>

      {/* View Article Modal */}
      {showArticleModal && selectedArticle && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h2 className="text-2xl font-bold">{selectedArticle.title}</h2>
                  <div className="flex items-center gap-2 mt-2">
                    <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded">
                      {selectedArticle.issueCategory}
                    </span>
                    {selectedArticle.equipmentMake && (
                      <span className="px-3 py-1 bg-gray-100 text-gray-800 rounded">
                        {selectedArticle.equipmentMake} {selectedArticle.equipmentModel}
                      </span>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => setShowArticleModal(false)}
                  className="text-gray-500 hover:text-gray-700 text-2xl"
                >
                  ×
                </button>
              </div>

              <div className="space-y-6">
                <div>
                  <h3 className="font-semibold text-lg flex items-center gap-2 text-orange-600">
                    <AlertCircle className="h-5 w-5" />
                    Symptoms
                  </h3>
                  <p className="mt-2 text-gray-700 whitespace-pre-wrap">{selectedArticle.symptoms}</p>
                </div>

                <div>
                  <h3 className="font-semibold text-lg flex items-center gap-2 text-red-600">
                    <AlertCircle className="h-5 w-5" />
                    Root Cause
                  </h3>
                  <p className="mt-2 text-gray-700 whitespace-pre-wrap">{selectedArticle.rootCause}</p>
                </div>

                <div>
                  <h3 className="font-semibold text-lg flex items-center gap-2 text-green-600">
                    <CheckCircle className="h-5 w-5" />
                    Solution
                  </h3>
                  <div className="mt-2 text-gray-700 whitespace-pre-wrap">{selectedArticle.solution}</div>
                </div>

                {selectedArticle.relatedWONumbers && (
                  <div>
                    <h3 className="font-semibold text-sm text-gray-600">Related Work Orders</h3>
                    <p className="mt-1 text-sm text-gray-700">{selectedArticle.relatedWONumbers}</p>
                  </div>
                )}

                {/* Attachments */}
                <div>
                  <h3 className="font-semibold text-sm text-gray-600 mb-2">Attachments</h3>
                  <FileUploadDropzone 
                    articleId={selectedArticle.id} 
                    onUploadComplete={() => {
                      // Refresh article if needed
                    }}
                  />
                </div>

                <div className="text-xs text-gray-500 pt-4 border-t">
                  <p>Created by {selectedArticle.createdBy} on {new Date(selectedArticle.createdDate).toLocaleDateString()}</p>
                  {selectedArticle.updatedDate && (
                    <p>Last updated by {selectedArticle.updatedBy} on {new Date(selectedArticle.updatedDate).toLocaleDateString()}</p>
                  )}
                  <p className="mt-1">Views: {selectedArticle.viewCount}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Article Modal */}
      {showEditModal && editingArticle && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-bold">
                  {editingArticle.id ? 'Edit Article' : 'New Article'}
                </h2>
                <button
                  onClick={() => setShowEditModal(false)}
                  className="text-gray-500 hover:text-gray-700 text-2xl"
                >
                  ×
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Title *</label>
                  <input
                    type="text"
                    value={editingArticle.title}
                    onChange={(e) => setEditingArticle({...editingArticle, title: e.target.value})}
                    className="w-full px-3 py-2 border rounded-md"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Equipment Make</label>
                    <SearchableSelect
                      value={editingArticle.equipmentMake}
                      onChange={(newMake) => {
                        setEditingArticle({...editingArticle, equipmentMake: newMake, equipmentModel: ''});
                        if (newMake) {
                          fetchModels(newMake);
                        } else {
                          setModels([]);
                        }
                      }}
                      options={makes}
                      placeholder="Select Make"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Equipment Model</label>
                    <SearchableSelect
                      value={editingArticle.equipmentModel}
                      onChange={(newModel) => setEditingArticle({...editingArticle, equipmentModel: newModel})}
                      options={models}
                      placeholder="Select Model"
                      disabled={!editingArticle.equipmentMake}
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Issue Category *</label>
                  <select
                    value={editingArticle.issueCategory}
                    onChange={(e) => setEditingArticle({...editingArticle, issueCategory: e.target.value})}
                    className="w-full px-3 py-2 border rounded-md"
                    required
                  >
                    <option value="">Select Category</option>
                    <option value="Hydraulic">Hydraulic</option>
                    <option value="Engine">Engine</option>
                    <option value="Electrical">Electrical</option>
                    <option value="Transmission">Transmission</option>
                    <option value="Brake">Brake</option>
                    <option value="Cooling">Cooling</option>
                    <option value="Fuel">Fuel</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Symptoms *</label>
                  <textarea
                    value={editingArticle.symptoms}
                    onChange={(e) => setEditingArticle({...editingArticle, symptoms: e.target.value})}
                    className="w-full px-3 py-2 border rounded-md"
                    rows="3"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Root Cause *</label>
                  <textarea
                    value={editingArticle.rootCause}
                    onChange={(e) => setEditingArticle({...editingArticle, rootCause: e.target.value})}
                    className="w-full px-3 py-2 border rounded-md"
                    rows="3"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Solution *</label>
                  <textarea
                    value={editingArticle.solution}
                    onChange={(e) => setEditingArticle({...editingArticle, solution: e.target.value})}
                    className="w-full px-3 py-2 border rounded-md"
                    rows="6"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Related Work Order Numbers</label>
                  <input
                    type="text"
                    value={editingArticle.relatedWONumbers}
                    onChange={(e) => setEditingArticle({...editingArticle, relatedWONumbers: e.target.value})}
                    className="w-full px-3 py-2 border rounded-md"
                    placeholder="e.g., WO-12345, WO-12389"
                  />
                </div>

                {/* File Attachments */}
                <div>
                  <label className="block text-sm font-medium mb-2">Attachments</label>
                  <FileUploadDropzone 
                    articleId={editingArticle.id} 
                    onUploadComplete={() => {
                      // Optionally refresh article data
                    }}
                  />
                </div>

                <div className="flex justify-end gap-2 pt-4">
                  <button
                    onClick={() => setShowEditModal(false)}
                    className="px-4 py-2 border rounded-md hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={saveArticle}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Save Article
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeBase;
