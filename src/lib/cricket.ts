// Formatting helpers shared by the data pages.

export const oversFrom = (balls: number, bpo = 6) =>
  balls % bpo ? `${Math.floor(balls / bpo)}.${balls % bpo}` : `${balls / bpo}`;

export const score = (runs: number, wkts: number, declared = 0) =>
  `${runs}${wkts >= 10 ? '' : `/${wkts}`}${declared ? 'd' : ''}`;

export const avg = (runs: number, outs: number) => (outs ? (runs / outs).toFixed(2) : '–');
export const rate = (num: number, den: number, mult = 1, dp = 2) => (den ? ((num / den) * mult).toFixed(dp) : '–');

export const fmtDay = (iso: string) =>
  new Date(iso + 'T00:00:00Z').toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });

export const FORMAT_ORDER = ['Test', 'ODI', 'T20I', 'First-class', 'One-day (other)', 'T20 league', 'The Hundred'];
export const genderLabel = (g: string) => (g === 'female' ? "Women's" : "Men's");

export type Summary = { team: string; runs: number; wkts: number; balls: number; declared: number; super_over: number };

/** Seasons like "2023/24" appear in URLs as "2023-24". */
export const seasonSlug = (s: string) => String(s).replace('/', '-');
export const seasonFromSlug = (s: string) => s.replace(/^(\d{4})-(\d{2})$/, '$1/$2');
