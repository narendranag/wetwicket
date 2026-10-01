// Sitemaps for the Archive, built from D1 on request: /archive-matches.xml, /archive-players.xml
// and /archive-places.xml (competitions, seasons and grounds). Listed in sitemap-index.xml by
// astro.config.mjs. Editorial pages are covered by @astrojs/sitemap.
import type { APIRoute } from 'astro';
import { all, cacheFor } from '../lib/db';
import { seasonSlug } from '../lib/cricket';

export const prerender = false;

const KINDS: Record<string, () => Promise<{ path: string; lastmod?: string }[]>> = {
  matches: async () =>
    (await all('SELECT id, COALESCE(end_date, date) AS d FROM matches ORDER BY date DESC')).map((m) => ({ path: `/matches/${m.id}/`, lastmod: m.d })),
  players: async () =>
    (await all('SELECT DISTINCT player_id FROM match_players')).map((p) => ({ path: `/players/${p.player_id}/` })),
  places: async () => {
    const [comps, seasons, venues] = await Promise.all([
      all('SELECT id FROM competitions'),
      all('SELECT DISTINCT competition_id, season FROM matches WHERE competition_id IS NOT NULL AND season IS NOT NULL'),
      all('SELECT id FROM venues'),
    ]);
    return [
      ...['/matches/', '/players/', '/competitions/', '/grounds/'].map((path) => ({ path })),
      ...comps.map((c) => ({ path: `/competitions/${c.id}/` })),
      ...seasons.map((s) => ({ path: `/competitions/${s.competition_id}/${seasonSlug(s.season)}/` })),
      ...venues.map((v) => ({ path: `/grounds/${v.id}/` })),
    ];
  },
};

export const GET: APIRoute = async ({ params, site }) => {
  const rows = await KINDS[params.kind ?? '']?.();
  if (!rows) return new Response(null, { status: 404 });
  const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const body = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    + rows.map((r) => `<url><loc>${esc(new URL(encodeURI(r.path), site).href)}</loc>${r.lastmod ? `<lastmod>${r.lastmod}</lastmod>` : ''}</url>`).join('')
    + '</urlset>';
  const response = new Response(body, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
  cacheFor(response);
  return response;
};
