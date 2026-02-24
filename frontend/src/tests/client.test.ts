import { describe, it, expect, vi, beforeEach } from 'vitest';
import apiClient, { articlesAPI, iocAPI } from '../api/client';
import { Article, CveDetailsType } from '../types';

// Mock axios methods
vi.mock('axios', () => {
    return {
        default: {
            create: vi.fn(() => ({
                get: vi.fn(),
                post: vi.fn(),
            })),
        },
    };
});

describe('API Client Validations', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('articlesAPI', () => {
        it('should fetch and rigidly parse all articles', async () => {
            const mockPayload = [
                { id: 101, title: 'Valid Alert', source: 'CISA', severity: 'High' }
            ];

            // @ts-ignore - vitest mock typing
            apiClient.get.mockResolvedValueOnce({ data: mockPayload });

            const result = await articlesAPI.getAll();
            expect(apiClient.get).toHaveBeenCalledWith('/articles/', { params: {} });
            expect(result.data).toHaveLength(1);
            expect(result.data[0].title).toBe('Valid Alert');
        });

        it('should throw ZodError if backend returns fatally malformed data', async () => {
            // id is missing completely, breaking the schema if it were strictly required (we loosely typed it)
            // let's test a case where we assert Zod behaves. In our current schema, almost everything is nullish.
            // Let's pass array instead of object to getById
            const malformedPayload = [{ id: 1, title: "I am array but should be object" }];

            // @ts-ignore
            apiClient.get.mockResolvedValueOnce({ data: malformedPayload });

            await expect(articlesAPI.getById(1)).rejects.toThrow();
        });
    });

    describe('iocAPI', () => {
        it('should fetch CVE details correctly', async () => {
            const mockCve: CveDetailsType = {
                id: 'CVE-2022-1234',
                assigner: 'test@mitre.org',
                description: 'Buffer overflow',
            };

            // @ts-ignore
            apiClient.get.mockResolvedValueOnce({ data: mockCve });

            const result = await iocAPI.getCveDetails('CVE-2022-1234');
            expect(apiClient.get).toHaveBeenCalledWith('/articles/cves/CVE-2022-1234/');
            expect(result.data.id).toBe('CVE-2022-1234');
        });
    });
});
