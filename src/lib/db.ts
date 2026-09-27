import { env } from 'cloudflare:workers';

/** Run a read query against D1 and return all rows. */
export async function all<T = Record<string, any>>(sql: string, ...params: unknown[]): Promise<T[]> {
  const { results } = await env.DB.prepare(sql).bind(...params).all<T>();
  return results;
}

export async function one<T = Record<string, any>>(sql: string, ...params: unknown[]): Promise<T | null> {
  return env.DB.prepare(sql).bind(...params).first<T>();
}

/** Data pages change at most once a day; let browsers and the edge reuse them for an hour. */
export function cacheFor(response: { headers: Headers }, seconds = 3600) {
  response.headers.set('Cache-Control', `public, max-age=${seconds}, s-maxage=${seconds * 6}`);
}
