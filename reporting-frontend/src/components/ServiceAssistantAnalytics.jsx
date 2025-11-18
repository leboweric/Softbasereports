import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { BarChart3, TrendingUp, AlertTriangle, Users } from 'lucide-react';
import axios from 'axios';

const ServiceAssistantAnalytics = () => {
  const [summary, setSummary] = useState(null);
  const [topQuestions, setTopQuestions] = useState([]);
  const [equipment, setEquipment] = useState([]);
  const [knowledgeGaps, setKnowledgeGaps] = useState([]);
  const [trendingTopics, setTrendingTopics] = useState([]);
  const [loading, setLoading] = useState(true);

  // Helper function to format UTC date to local date string
  const formatLocalDate = (utcDateString) => {
    if (!utcDateString) return 'N/A';
    // Parse the UTC timestamp and convert to local time
    const date = new Date(utcDateString);
    // Format in local timezone
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
    });
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const [summaryRes, questionsRes, equipmentRes, gapsRes, topicsRes] = await Promise.all([
        axios.get(`${import.meta.env.VITE_API_URL}/api/service-assistant/analytics/summary`, { headers }),
        axios.get(`${import.meta.env.VITE_API_URL}/api/service-assistant/analytics/top-questions`, { headers }),
        axios.get(`${import.meta.env.VITE_API_URL}/api/service-assistant/analytics/equipment-breakdown`, { headers }),
        axios.get(`${import.meta.env.VITE_API_URL}/api/service-assistant/analytics/knowledge-gaps`, { headers }),
        axios.get(`${import.meta.env.VITE_API_URL}/api/service-assistant/analytics/trending-topics`, { headers })
      ]);

      setSummary(summaryRes.data);
      setTopQuestions(questionsRes.data.questions || []);
      setEquipment(equipmentRes.data.equipment || []);
      setKnowledgeGaps(gapsRes.data.gaps || []);
      setTrendingTopics(topicsRes.data.topics || []);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-500">Loading analytics...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total Queries</p>
                <p className="text-2xl font-bold">{summary?.totalQueries || 0}</p>
              </div>
              <BarChart3 className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Last 7 Days</p>
                <p className="text-2xl font-bold">{summary?.queriesLastWeek || 0}</p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Last 30 Days</p>
                <p className="text-2xl font-bold">{summary?.queriesLastMonth || 0}</p>
              </div>
              <Users className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Avg KB Results</p>
                <p className="text-2xl font-bold">
                  {summary?.averageResults?.kbArticles?.toFixed(1) || '0.0'}
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Top Questions */}
      <Card>
        <CardHeader>
          <CardTitle>Most Frequently Asked Questions</CardTitle>
          <p className="text-sm text-gray-500">
            Questions asked most often - potential training opportunities
          </p>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {topQuestions.slice(0, 10).map((q, idx) => (
              <div
                key={idx}
                className="flex items-start justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-blue-600">#{idx + 1}</span>
                    <p className="text-sm text-gray-900">{q.question}</p>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Last asked: {formatLocalDate(q.lastAsked)}
                  </p>
                </div>
                <div className="flex flex-col items-end ml-4">
                  <span className="text-lg font-bold text-gray-900">{q.frequency}</span>
                  <span className="text-xs text-gray-500">times</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Equipment Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Questions by Equipment Make</CardTitle>
          <p className="text-sm text-gray-500">
            Which equipment brands generate the most questions
          </p>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {equipment.map((eq, idx) => (
              <div key={idx} className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium">{eq.make}</span>
                    <span className="text-sm text-gray-600">{eq.queryCount} queries</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{
                        width: `${(eq.queryCount / equipment[0]?.queryCount) * 100}%`
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Knowledge Gaps */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-orange-500" />
            Knowledge Gaps - Training Opportunities
          </CardTitle>
          <p className="text-sm text-gray-500">
            Frequently asked questions with limited internal documentation
          </p>
        </CardHeader>
        <CardContent>
          {knowledgeGaps.length === 0 ? (
            <p className="text-gray-500 text-center py-4">
              No significant knowledge gaps identified. Great job!
            </p>
          ) : (
            <div className="space-y-4">
              {knowledgeGaps.map((gap, idx) => (
                <div
                  key={idx}
                  className="p-4 border border-orange-200 bg-orange-50 rounded-lg"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{gap.question}</p>
                      {gap.make && (
                        <p className="text-sm text-gray-600 mt-1">
                          Equipment: {gap.make} {gap.model || ''}
                        </p>
                      )}
                      <div className="flex gap-4 mt-2 text-xs text-gray-600">
                        <span>KB Articles: {gap.kbResults}</span>
                        <span>Work Orders: {gap.woResults}</span>
                        <span>Asked {gap.frequency} times</span>
                      </div>
                    </div>
                    <div className="ml-4">
                      <span className="inline-block px-3 py-1 bg-orange-100 text-orange-800 text-xs font-medium rounded-full">
                        Create KB Article
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Trending Topics */}
      <Card>
        <CardHeader>
          <CardTitle>Trending Topics (Last 30 Days)</CardTitle>
          <p className="text-sm text-gray-500">
            Most common keywords in recent queries
          </p>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {trendingTopics.slice(0, 20).map((topic, idx) => (
              <span
                key={idx}
                className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
              >
                {topic.keyword}
                <span className="text-xs text-blue-600 font-semibold">
                  {topic.frequency}
                </span>
              </span>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ServiceAssistantAnalytics;
