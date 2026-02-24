import { describe, it, expect } from 'vitest';

import { ArticleSchema, CveDetailsSchema } from '../types';

describe('Zod Schemas', () => {
    describe('ArticleSchema', () => {
        it('should parse a valid article response', () => {
            const validArticle = {
                id: 1,
                title: 'Critical RCE in Important Service',
                source: 'Security Vendor X',
                link: 'https://example.com/advisory',
                summary: 'A new bug was found.',
                ai_summary: undefined,
                published_date: '2023-10-12T10:00:00Z',
                severity: 'Critical',
                threat_type: 'RCE',
            };

            const data = ArticleSchema.parse(validArticle);
            expect(data.title).toBe('Critical RCE in Important Service');
        });

        it('should handle optional properties gracefully', () => {
            const minimalArticle = {
                id: '99',
                title: 'Minimal Data Article',
                source: 'Twitter Researcher',
            };

            const data = ArticleSchema.parse(minimalArticle);
            expect(data.ai_summary).toBeUndefined();
        });

        it('should accept a valid iocs array', () => {
            const articleWithIocs = {
                id: 1,
                title: 'Bad Article',
                source: 'Bad Source',
                iocs: [
                    { id: '123', ioc_type: 'cve', value: 'CVE-2023-0001' }
                ]
            };

            const result = ArticleSchema.safeParse(articleWithIocs);
            expect(result.success).toBe(true);
        });
    });

    describe('CveDetailsSchema', () => {
        it('should parse a full CVE payload matching the backend serializer output', () => {
            // This shape comes from feeds/serializers.py CVEDetailSerializer
            // after _normalize_cve_data processes the cve.circl.lu JSON 5.1 response
            const fullCve = {
                id: 'CVE-2021-44228',
                summary: 'Apache Log4j2 JNDI features do not protect against attacker-controlled LDAP.',
                cvss: 0.0,
                cvss_v3: 10.0,
                cvss_vector: 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H',
                severity: 'CRITICAL',
                published: '2021-12-10T00:00:00.000Z',
                modified: '2025-10-21T23:25:23.121Z',
                last_modified: '2025-10-21T23:25:23.121Z',
                references: ['https://logging.apache.org/log4j/2.x/security.html'],
                vulnerable_products: ['Apache Software Foundation:Apache Log4j2'],
                cwe: 'CWE-502',
            };

            const data = CveDetailsSchema.parse(fullCve);
            expect(data.id).toBe('CVE-2021-44228');
            expect(data.cvss_v3).toBe(10.0);
            expect(data.severity).toBe('CRITICAL');
            expect(data.cwe).toBe('CWE-502');
            expect(data.references).toHaveLength(1);
            expect(data.vulnerable_products).toHaveLength(1);
        });

        it('should apply defaults for all fields when only id is present', () => {
            // _normalize_cve_data always initializes these fields with defaults;
            // Zod defaults act as a safety net if any are unexpectedly absent.
            const data = CveDetailsSchema.parse({ id: 'CVE-2023-0001' });
            expect(data.cvss_v3).toBe(0);
            expect(data.cvss).toBe(0);
            expect(data.cvss_vector).toBe('');
            expect(data.summary).toBe('');
            expect(data.severity).toBe('UNKNOWN');
            expect(data.references).toEqual([]);
            expect(data.vulnerable_products).toEqual([]);
        });

        it('should accept the optional internal tracking fields', () => {
            // These fields are added by cve_detail_view when the CVE exists in the IOC database
            const trackedCve = {
                id: 'CVE-2023-5678',
                seen_in_articles: [1, 2, 3],
                first_seen_in_feed: '2024-01-15T12:00:00Z',
                times_seen: 5,
            };

            const data = CveDetailsSchema.parse(trackedCve);
            expect(data.seen_in_articles).toEqual([1, 2, 3]);
            expect(data.times_seen).toBe(5);
            expect(data.first_seen_in_feed).toBe('2024-01-15T12:00:00Z');
        });

        it('should fail when id is missing', () => {
            const result = CveDetailsSchema.safeParse({ summary: 'No ID provided', cvss_v3: 7.5 });
            expect(result.success).toBe(false);
        });

        it('should strip stale fields from the old schema', () => {
            // The schema migrated from z.looseObject with assigner/description/cvsses[]
            // to z.object with the flat backend shape. Unknown keys are stripped.
            const cveWithOldFields = {
                id: 'CVE-2023-9999',
                assigner: 'cve@mitre.org',
                description: 'Old flat description field',
                cvsses: [{ baseScore: 9.8, vectorString: 'CVSS:3.1/AV:N' }],
            };

            const data = CveDetailsSchema.parse(cveWithOldFields);
            expect(data).not.toHaveProperty('assigner');
            expect(data).not.toHaveProperty('description');
            expect(data).not.toHaveProperty('cvsses');
        });
    });
});
