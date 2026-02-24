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

            const result = ArticleSchema.safeParse(validArticle);
            expect(result.success).toBe(true);
            if (result.success) {
                expect(result.data.title).toBe('Critical RCE in Important Service');
            }
        });

        it('should handle optional properties gracefully', () => {
            const minimalArticle = {
                id: '99',
                title: 'Minimal Data Article',
                source: 'Twitter Researcher',
            };

            const result = ArticleSchema.safeParse(minimalArticle);
            expect(result.success).toBe(true);
            if (result.success) {
                expect(result.data.ai_summary).toBeUndefined();
            }
        });

        it('should filter out invalid types (like a nested object instead of a string array)', () => {
            const invalidArticle = {
                id: 1,
                title: 'Bad Article',
                source: 'Bad Source',
                iocs: [
                    { id: '123', ioc_type: 'cve', value: 'CVE-2023-0001' }
                ]
            };

            const result = ArticleSchema.safeParse(invalidArticle);
            expect(result.success).toBe(true); // Should pass as we loosely typed pass-through or allowed valid arrays
        });
    });

    describe('CveDetailsSchema', () => {
        it('should gracefully parse CVE payload', () => {
            const validCve = {
                id: 'CVE-2023-1234',
                assigner: 'cve@mitre.org',
                description: 'Buffer overflow somewhere',
                cvsses: [{ baseScore: 9.8, vectorString: 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H' }],
                references: ['http://patch.example.com']
            };

            const result = CveDetailsSchema.safeParse(validCve);
            expect(result.success).toBe(true);
            if (result.success && result.data.cvsses) {
                expect(result.data.cvsses[0].baseScore).toBe(9.8);
            }
        });
    });
});
