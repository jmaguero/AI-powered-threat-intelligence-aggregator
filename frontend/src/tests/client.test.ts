import { describe, it, expect, vi, beforeEach } from 'vitest';

import apiClient, { articlesAPI, iocAPI } from '../api/client';
import type { Article } from '../types';

vi.mock('axios', () => {
    return {
        default: {
            create: vi.fn(() => ({
                get: vi.fn(),
                post: vi.fn(),
            })),
            isAxiosError: vi.fn(() => false),
            isCancel: vi.fn(() => false),
        },
    };
});

describe('API Client Validations', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('articlesAPI', () => {
        it('should fetch and parse all articles', async () => {
            const mockPayload: Article[] = [
                { id: 101, title: 'Valid Alert', source: 'CISA', severity: 'High' }
            ];

            vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockPayload });

            const result = await articlesAPI.getAll();
            expect(apiClient.get).toHaveBeenCalledWith('/articles/', { params: {} });
            expect(result.data).toHaveLength(1);
            expect(result.data[0]?.title).toBe('Valid Alert');
        });

        it('should throw a ZodError when getById receives an array instead of an object', async () => {
            const malformedPayload = [{ id: 1, title: 'I am array but should be object' }];

            vi.mocked(apiClient.get).mockResolvedValueOnce({ data: malformedPayload });

            await expect(articlesAPI.getById(1)).rejects.toThrow();
        });
    });

    describe('iocAPI', () => {
        it('should fetch and parse CVE details', async () => {
            // Matches the shape of feeds/serializers.py CVEDetailSerializer
            const mockPayload = {
                id: 'CVE-2022-1234',
                summary: 'Buffer overflow in libfoo allows RCE',
                cvss: 0,
                cvss_v3: 9.8,
                cvss_vector: 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H',
                severity: 'CRITICAL',
                published: '2022-03-01T00:00:00Z',
                modified: '2022-04-01T00:00:00Z',
                last_modified: '2022-04-01T00:00:00Z',
                references: ['https://example.com/advisory'],
                vulnerable_products: ['vendor:libfoo'],
                cwe: 'CWE-120',
            };

            vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockPayload });

            const result = await iocAPI.getCveDetails('CVE-2022-1234');
            expect(apiClient.get).toHaveBeenCalledWith(
                '/articles/cves/CVE-2022-1234/',
                { signal: undefined }
            );
            expect(result.data.id).toBe('CVE-2022-1234');
            expect(result.data.cvss_v3).toBe(9.8);
            expect(result.data.severity).toBe('CRITICAL');
        });

        it('should forward an AbortSignal to axios', async () => {
            vi.mocked(apiClient.get).mockResolvedValueOnce({ data: { id: 'CVE-2023-0001' } });

            const controller = new AbortController();
            await iocAPI.getCveDetails('CVE-2023-0001', controller.signal);

            expect(apiClient.get).toHaveBeenCalledWith(
                '/articles/cves/CVE-2023-0001/',
                { signal: controller.signal }
            );
        });

        it('should throw a ZodError when backend returns a CVE without an id', async () => {
            vi.mocked(apiClient.get).mockResolvedValueOnce({ data: { summary: 'Missing ID', cvss_v3: 7.5 } });

            await expect(iocAPI.getCveDetails('CVE-2023-BAD')).rejects.toThrow();
        });
    });
});
