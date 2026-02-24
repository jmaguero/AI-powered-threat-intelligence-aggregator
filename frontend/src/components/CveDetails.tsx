import { isAxiosError, isCancel } from 'axios';
import { useState, useEffect } from 'react';

import { iocAPI } from '../api/client';
import type { CveDetailsType } from '../types';

import './CveDetails.css';

type Props = {
    cveId: string;
};

const getSeverityClass = (severity: string | null | undefined): string => {
    if (!severity) return 'severity-unknown';
    const lower = severity.toLowerCase();
    if (lower.includes('critical')) return 'severity-critical';
    if (lower.includes('high')) return 'severity-high';
    if (lower.includes('medium')) return 'severity-medium';
    if (lower.includes('low')) return 'severity-low';
    return 'severity-unknown';
};

function CveDetails({ cveId }: Props) {
    const [cveData, setCveData] = useState<CveDetailsType | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [expanded, setExpanded] = useState(false);

    useEffect(() => {
        const controller = new AbortController();

        const fetchCve = async () => {
            setLoading(true);
            setError(null);
            try {
                const response = await iocAPI.getCveDetails(cveId, controller.signal);
                setCveData(response.data);
            } catch (err: unknown) {
                if (isCancel(err)) return;
                if (isAxiosError(err) && err.response?.status === 404) {
                    setError('CVE not found in database');
                } else {
                    setError('Failed to load CVE details');
                }
            } finally {
                setLoading(false);
            }
        };

        void fetchCve();
        return () => controller.abort();
    }, [cveId]);

    if (loading) {
        return <div className="cve-card loading-pulse">Loading {cveId} data...</div>;
    }

    if (error) {
        return (
            <div className="cve-card error">
                <strong>{cveId}</strong>: {error}
            </div>
        );
    }

    if (!cveData) return null;

    const hasExtraDetails =
        cveData.summary ||
        cveData.vulnerable_products.length > 0 ||
        cveData.cwe;

    return (
        <div className={`cve-card ${getSeverityClass(cveData.severity)}`}>
            <div className="cve-header">
                <div className="cve-title-area">
                    <h3>{cveData.id}</h3>
                    <span className={`cve-badge ${getSeverityClass(cveData.severity)}`}>
                        {cveData.severity}
                    </span>
                    {cveData.cvss_v3 > 0 && (
                        <span className="cvss-score" title={cveData.cvss_vector}>
                            CVSS {cveData.cvss_v3}
                        </span>
                    )}
                </div>

                {hasExtraDetails && (
                    <button
                        className="cve-expand-btn"
                        aria-label="Toggle details"
                        aria-expanded={expanded}
                        onClick={() => setExpanded(!expanded)}
                    >
                        {expanded ? '▲' : '▼'}
                    </button>
                )}
            </div>

            {expanded && hasExtraDetails && (
                <div className="cve-body">
                    {cveData.summary && <p className="cve-summary">{cveData.summary}</p>}

                    <div className="cve-meta-grid">
                        {cveData.cwe && (
                            <div className="cve-meta-item">
                                <strong>Weakness:</strong> {cveData.cwe}
                            </div>
                        )}
                        {cveData.published && (
                            <div className="cve-meta-item">
                                <strong>Published:</strong> {new Date(cveData.published).toLocaleDateString()}
                            </div>
                        )}
                        {cveData.last_modified && (
                            <div className="cve-meta-item">
                                <strong>Updated:</strong> {new Date(cveData.last_modified).toLocaleDateString()}
                            </div>
                        )}
                    </div>

                    {cveData.vulnerable_products.length > 0 && (
                        <div className="cve-products">
                            <strong>Affected Products:</strong>
                            <ul>
                                {cveData.vulnerable_products.slice(0, 5).map((prod) => (
                                    <li key={prod}>{prod}</li>
                                ))}
                                {cveData.vulnerable_products.length > 5 && (
                                    <li className="more-items">...and {cveData.vulnerable_products.length - 5} more</li>
                                )}
                            </ul>
                        </div>
                    )}

                    {cveData.references.length > 0 && (
                        <div className="cve-references">
                            <a href={cveData.references[0]} target="_blank" rel="noopener noreferrer">
                                Primary Reference ↗
                            </a>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default CveDetails;
