// @ts-check
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://wetwicket.com',
  trailingSlash: 'always',
  integrations: [mdx(), sitemap()],
});
