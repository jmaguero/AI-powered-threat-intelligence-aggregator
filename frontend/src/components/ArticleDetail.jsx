import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import { articlesAPI } from '../api/client';
import './ArticleDetail.css';

function ArticleDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchArticle = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await articlesAPI.getById(id);
        setArticle(response.data);
      } catch (err) {
        setError(err.message || 'Failed to fetch article');
        console.error('Error fetching article:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchArticle();
  }, [id]);

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return format(new Date(dateString), 'MMMM d, yyyy HH:mm');
    } catch {
      return dateString;
    }
  };

  const getSeverityClass = (severity) => {
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
        <button onClick={() => navigate(-1)} className="back-btn">
          ← Back
        </button>
        <div className="loading">Loading article...</div>
      </div>
    );
  }

  if (error || !article) {
    return (
      <div className="container">
        <button onClick={() => navigate(-1)} className="back-btn">
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
      <button onClick={() => navigate(-1)} className="back-btn">
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

        {/* IOC Section - Placeholder for Phase 5 */}
        <section className="section ioc-section">
          <h2>Indicators of Compromise (IOCs)</h2>
          <div className="placeholder">
            <p>IOC extraction will be available after Phase 5 implementation.</p>
            <p className="placeholder-note">
              Features coming soon:
            </p>
            <ul>
              <li>IP addresses</li>
              <li>Domain names</li>
              <li>File hashes (MD5, SHA1, SHA256)</li>
              <li>CVE IDs with enriched data from local cve-search</li>
            </ul>
          </div>
        </section>
      </article>
    </div>
  );
}

export default ArticleDetail;
