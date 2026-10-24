import { defineMiddleware } from 'astro:middleware';
import { env } from 'cloudflare:workers';

/**
 * Edge cache for the on-demand (D1) pages. A Worker's responses are not cached by the CDN, so
 * the Cache-Control that `cacheFor` sets (src/lib/db.ts) only reached browsers. Here a GET that
 * answers 200 with a public Cache-Control is kept in this data centre's cache for its s-maxage.
 * The key carries the deployed version's id, so every deploy (the nightly one included) starts
 * with an empty cache and never serves pages from before a D1 update.
 */
export const onRequest = defineMiddleware(async (context, next) => {
  if (context.isPrerendered || context.request.method !== 'GET' || typeof caches === 'undefined') return next();

  const version = (env as { CF_VERSION_METADATA?: { id: string } }).CF_VERSION_METADATA?.id ?? 'dev';
  const keyUrl = new URL(context.request.url);
  keyUrl.searchParams.set('__v', version);
  const key = new Request(keyUrl.toString());
  const cache = caches.default;

  const hit = await cache.match(key);
  if (hit) {
    const response = new Response(hit.body, hit);
    response.headers.set('X-Edge-Cache', 'HIT');
    return response;
  }

  const response = await next();
  const cc = response.headers.get('Cache-Control') ?? '';
  if (response.status === 200 && /\bpublic\b/.test(cc) && !response.headers.has('Set-Cookie')) {
    context.locals.cfContext?.waitUntil(cache.put(key, response.clone()));
    response.headers.set('X-Edge-Cache', 'MISS');
  }
  return response;
});
