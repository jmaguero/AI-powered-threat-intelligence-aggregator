import { format } from 'date-fns';
import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';

import { articlesAPI } from '../api/client';
import type { Article } from '../types';

import CveDetails from './CveDetails';
import './ArticleDetail.css';

function ArticleDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [article, setArticle] = useState<Article | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchArticle = async () => {
      try {
        setLoading(true);
        setError(null);
        if (!id) return;
        const response = await articlesAPI.getById(id);
        setArticle(response.data);
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Failed to fetch article';
        setError(message);
        console.error('Error fetching article:', err);
      } finally {
        setLoading(false);
      }
    };

    void fetchArticle();
  }, [id]);

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return 'N/A';
    try {
      return format(new Date(dateString), 'MMMM d, yyyy HH:mm');
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

  if (loading) {
    return (
      <div className="container">
        <button onClick={() => { void navigate(-1); }} className="back-btn">
          ← Back
        </button>
        <div className="loading">Loading article...</div>
      </div>
    );
  }

  if (error || !article) {
    return (
      <div className="container">
        <button onClick={() => { void navigate(-1); }} className="back-btn">
          ← Back
        </button>
        <div className="error">
          <strong>Error:</strong> {error || 'Article not found'}
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <button onClick={() => { void navigate(-1); }} className="back-btn">
        ← Back
      </button>

      <article className="article-detail">
        <div className="article-detail-header">
          <div className="header-top">
            <span className="source-badge">{article.source}</span>
            {article.severity && (
              <span className={`severity-badge ${getSeverityClass(article.severity)}`}>
                {article.severity}
              </span>
            )}
          </div>

          <h1>{article.title}</h1>

          <div className="article-meta-info">
            <span className="meta-item">
              <strong>Published:</strong> {formatDate(article.published_date)}
            </span>
            {article.enriched_at && (
              <span className="meta-item">
                <strong>AI Enriched:</strong> {formatDate(article.enriched_at)}
              </span>
            )}
          </div>

          <a
            href={article.link}
            target="_blank"
            rel="noopener noreferrer"
            className="original-link"
          >
            View Original Article ↗
          </a>
        </div>

        {article.ai_summary && (
          <section className="section ai-section">
            <h2>AI Summary</h2>
            <p className="ai-summary">{article.ai_summary}</p>
          </section>
        )}

        {article.summary && (
          <section className="section">
            <h2>Original Summary</h2>
            <p>{article.summary}</p>
          </section>
        )}

        <section className="section metadata-section">
          <h2>Threat Intelligence Metadata</h2>
          <div className="metadata-grid">
            {article.threat_type && (
              <div className="metadata-item">
                <strong>Threat Type:</strong>
                <span className="threat-type-tag">{article.threat_type}</span>
              </div>
            )}

            {article.affected_tech && (
              <div className="metadata-item">
                <strong>Affected Technology:</strong>
                <span>{article.affected_tech}</span>
              </div>
            )}
          </div>
        </section>

        {/* Indicators of Compromise Section */}
        <section className="section ioc-section">
          <h2>Indicators of Compromise (IOCs)</h2>

          {article.iocs && article.iocs.length > 0 ? (
            <div className="ioc-list">
              {article.iocs.map((ioc) => {
                if (ioc.ioc_type === 'cve') {
                  return <CveDetails key={ioc.id} cveId={ioc.value} />;
                }

                // Fallback for other IOC types (IP, Domain, etc - Phase 5)
                return (
                  <div key={ioc.id} className="ioc-item generic-ioc">
                    <span className="ioc-type">{ioc.ioc_type.toUpperCase()}</span>
                    <span className="ioc-value">{ioc.value}</span>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="no-iocs">No Indicators of Compromise automatically extracted for this article.</p>
          )}
        </section>
      </article>
    </div>
  );
}

export default ArticleDetail;
