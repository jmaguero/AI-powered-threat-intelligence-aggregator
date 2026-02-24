import { z } from 'zod';

// Shared Schemas
export const IocSchema = z.object({
    id: z.number().or(z.string()),
    ioc_type: z.string(),
    value: z.string(),
    // Add more fields if the backend provides them
}).passthrough();

export const ArticleSchema = z.object({
    id: z.number().or(z.string()),
    title: z.string(),
    source: z.string(),
    link: z.string().url().nullish(),
    summary: z.string().nullish(),
    ai_summary: z.string().nullish(),
    published_date: z.string().nullish(),
    enriched_at: z.string().nullish(),
    severity: z.string().nullish(),
    threat_type: z.string().nullish(),
    affected_tech: z.string().nullish(),
    iocs: z.array(IocSchema).optional().nullable(),
}).passthrough();

export const CveDetailsSchema = z.object({
    id: z.string(),
    assigner: z.string().nullish(),
    description: z.string().nullish(),
    cvsses: z.array(
        z.object({
            baseScore: z.number().nullish(),
            vectorString: z.string().nullish(),
        }).passthrough()
    ).optional().nullable(),
    references: z.array(z.string()).optional().nullable(),
}).passthrough();

// Exported Types
export type Ioc = z.infer<typeof IocSchema>;
export type Article = z.infer<typeof ArticleSchema>;
export type CveDetailsType = z.infer<typeof CveDetailsSchema>;

export type FilterParams = {
    search?: string;
    source?: string;
    severity?: string;
    [key: string]: any;
};

