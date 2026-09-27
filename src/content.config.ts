import { defineCollection, reference } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

// A piece lives at src/content/pieces/<section>/<slug>.mdx; its URL is /<section>/<slug>/.
const pieces = defineCollection({
  loader: glob({ base: './src/content/pieces', pattern: '**/*.{md,mdx}' }),
  schema: z.object({
    title: z.string(),
    dek: z.string(),
    author: reference('authors'),
    published: z.coerce.date(),
    updated: z.coerce.date().optional(),
    series: reference('series').optional(),
    seriesOrder: z.number().optional(),
    tags: z.array(z.string()).default([]),
    matches: z.array(z.string()).default([]),
    presentation: z.enum(['article', 'app']).default('article'),
    draft: z.boolean().default(false),
  }),
});

const series = defineCollection({
  loader: glob({ base: './src/content/series', pattern: '**/*.md' }),
  schema: z.object({
    title: z.string(),
    dek: z.string(),
    status: z.enum(['ongoing', 'complete']).default('ongoing'),
    started: z.coerce.date(),
    featured: z.boolean().default(false),
  }),
});

const authors = defineCollection({
  loader: glob({ base: './src/content/authors', pattern: '**/*.md' }),
  schema: z.object({
    name: z.string(),
    bio: z.string(),
  }),
});

export const collections = { pieces, series, authors };
