// @ts-check
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import cloudflare from '@astrojs/cloudflare';

// Editorial pages are prerendered; data pages (matches, players, competitions, grounds) opt out
// with `export const prerender = false` and read from D1 at request time.
export default defineConfig({
  site: 'https://wetwicket.com',
  trailingSlash: 'always',
  adapter: cloudflare(),
  integrations: [
    mdx(),
    // The Archive's sitemaps are served from D1 by src/pages/archive-[kind].xml.ts.
    sitemap({ customSitemaps: ['matches', 'players', 'places'].map((k) => `https://wetwicket.com/archive-${k}.xml`) }),
  ],
});
