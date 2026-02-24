import { format } from 'date-fns';
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

import { articlesAPI } from '../api/client';
import type { Article, FilterParams } from '../types';

import FilterBar from './FilterBar';
import './ArticleList.css';

function ArticleList() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<FilterParams>({});

  const fetchArticles = async (filterParams: FilterParams = {}) => {
    try {
      setLoading(true);
      setError(null);

      // Remove empty filter values
      const cleanFilters = Object.fromEntries(
        Object.entries(filterParams).filter(([_, v]) => v !== '')
      );

      const response = await articlesAPI.getAll(cleanFilters);
      setArticles(response.data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to fetch articles';
      setError(message);
      console.error('Error fetching articles:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchArticles(filters);
  }, [filters]);

  const handleFilterChange = (newFilters: FilterParams) => {
    setFilters(newFilters);
  };

  const handleSearch = (query: string) => {
    // For now, just trigger a re-fetch with filters
    // You could add a search endpoint to Django later
    void fetchArticles({ ...filters, search: query });
  };

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return 'N/A';
    try {
      return format(new Date(dateString), 'MMM d, yyyy HH:mm');
    } catch {
      return dateString;
    }
  };

  const getSeverityClass = (severity: string | null | undefined) => {
    if (!severity) return '';
    const lower = severity.toLowerCase();
    if (lower.includes('critical')) return 'severity-critical';
    if (lower.includes('high')) return 'severity-high';
    if (lower.includes('medium')) return 'severity-medium';
    if (lower.includes('low')) return 'severity-low';
    return '';
  };

  if (loading && articles.length === 0) {
    return (
      <div className="container">
        <h1>Threat Intelligence Feed</h1>
        <FilterBar onFilterChange={handleFilterChange} onSearch={handleSearch} />
        <div className="loading">Loading articles...</div>
      </div>
    );
  }

  return (
    <div className="container">
      <h1>Threat Intelligence Feed</h1>

      <FilterBar onFilterChange={handleFilterChange} onSearch={handleSearch} />

      {error && (
        <div className="error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {articles.length === 0 && !loading ? (
        <div className="no-results">
          No articles found. Try adjusting your filters or fetch new feeds.
        </div>
      ) : (
        <div className="articles-grid">
          {articles.map((article) => (
            <Link
              key={article.id}
              to={`/article/${article.id}`}
              className="article-card"
            >
              <div className="article-header">
                <span className="article-source">{article.source}</span>
                {article.severity && (
                  <span className={`severity-badge ${getSeverityClass(article.severity)}`}>
                    {article.severity}
                  </span>
                )}
              </div>

              <h2 className="article-title">{article.title}</h2>

              {article.ai_summary && (
                <p className="article-summary">{article.ai_summary}</p>
              )}

              <div className="article-meta">
                <span className="article-date">
                  {formatDate(article.published_date)}
                </span>
                {article.threat_type && (
                  <span className="threat-type">{article.threat_type}</span>
                )}
              </div>

              {article.affected_tech && (
                <div className="affected-tech">
                  <strong>Affected:</strong> {article.affected_tech}
                </div>
              )}
            </Link>
          ))}
        </div>
      )}

      {loading && articles.length > 0 && (
        <div className="loading-overlay">Updating...</div>
      )}
    </div>
  );
}

export default ArticleList;
