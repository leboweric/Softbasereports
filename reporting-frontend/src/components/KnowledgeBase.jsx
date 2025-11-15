import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { apiUrl } from '@/lib/api';
import { Search, Filter, Plus, Edit, Trash2, Eye, Book, Wrench, AlertCircle, CheckCircle, Paperclip } from 'lucide-react';
import FileUploadDropzone from './FileUploadDropzone';
import SearchableSelect from './SearchableSelect';

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
            <div className="relative">
              <Wrench className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <select
                value={selectedMake}
                onChange={(e) => setSelectedMake(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border rounded-md appearance-none"
              >
                <option value="">All Equipment Makes</option>
                {makes.map(make => (
                  <option key={make} value={make}>{make}</option>
                ))}
              </select>
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
