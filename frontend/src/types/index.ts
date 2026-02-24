import { z } from 'zod';

// Shared Schemas
export const IocSchema = z.looseObject({
    id: z.number().or(z.string()),
    ioc_type: z.string(),
    value: z.string(),
    // Add more fields if the backend provides them
});

export const ArticleSchema = z.looseObject({
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
});

// Matches feeds/serializers.py CVEDetailSerializer exactly.
// The backend normalizes cve.circl.lu JSON 5.1 into this flat shape via _normalize_cve_data.
export const CveDetailsSchema = z.object({
    id: z.string(),
    summary: z.string().default(''),
    cvss: z.number().default(0),
    cvss_v3: z.number().default(0),
    cvss_vector: z.string().default(''),
    severity: z.string().default('UNKNOWN'),
    published: z.string().nullish(),
    modified: z.string().nullish(),
    last_modified: z.string().nullish(),
    references: z.array(z.string()).default([]),
    vulnerable_products: z.array(z.string()).default([]),
    cwe: z.string().nullish(),
    // Present only when the CVE exists in the local IOC database
    seen_in_articles: z.array(z.number()).optional(),
    first_seen_in_feed: z.string().nullish(),
    times_seen: z.number().optional(),
});

// Exported Types
export type Ioc = z.infer<typeof IocSchema>;
export type Article = z.infer<typeof ArticleSchema>;
export type CveDetailsType = z.infer<typeof CveDetailsSchema>;

export type FilterParams = {
    search?: string;
    source?: string;
    severity?: string;
    [key: string]: string | undefined;
};

