// Career aggregation for player pages: rows come from batting/bowling joined to matches.
import { FORMAT_ORDER } from './cricket';

export type BatRow = { match_id: string; fmt: string; gender: string; runs: number; balls: number; fours: number; sixes: number; out: number };
export type BowlRow = { match_id: string; fmt: string; gender: string; balls: number; runs: number; wkts: number; maidens: number; bpo: number };

const byFormat = <T extends { fmt: string }>(rows: T[]) => {
  const g = new Map<string, T[]>();
  for (const r of rows) g.set(r.fmt, [...(g.get(r.fmt) ?? []), r]);
  return [...g.entries()].sort((a, b) => FORMAT_ORDER.indexOf(a[0]) - FORMAT_ORDER.indexOf(b[0]));
};

export function batting(rows: BatRow[]) {
  return byFormat(rows).map(([fmt, rs]) => {
    const best = rs.reduce((a, r) => (r.runs > a.runs || (r.runs === a.runs && !r.out) ? r : a), rs[0]);
    const runs = rs.reduce((s, r) => s + r.runs, 0);
    return {
      fmt, matches: new Set(rs.map((r) => r.match_id)).size, inns: rs.length,
      notOut: rs.filter((r) => !r.out).length, runs, balls: rs.reduce((s, r) => s + r.balls, 0),
      outs: rs.filter((r) => r.out).length, hs: `${best.runs}${best.out ? '' : '*'}`, hsMatch: best.match_id,
      hundreds: rs.filter((r) => r.runs >= 100).length, fifties: rs.filter((r) => r.runs >= 50 && r.runs < 100).length,
      fours: rs.reduce((s, r) => s + r.fours, 0), sixes: rs.reduce((s, r) => s + r.sixes, 0),
    };
  });
}

export function bowling(rows: BowlRow[]) {
  return byFormat(rows).map(([fmt, rs]) => {
    const best = rs.reduce((a, r) => (r.wkts > a.wkts || (r.wkts === a.wkts && r.runs < a.runs) ? r : a), rs[0]);
    return {
      fmt, inns: rs.length, balls: rs.reduce((s, r) => s + r.balls, 0), runs: rs.reduce((s, r) => s + r.runs, 0),
      wkts: rs.reduce((s, r) => s + r.wkts, 0), maidens: rs.reduce((s, r) => s + r.maidens, 0),
      best: `${best.wkts}/${best.runs}`, bestMatch: best.match_id, fiveFors: rs.filter((r) => r.wkts >= 5).length, bpo: rs[0].bpo || 6,
    };
  });
}

export const cricinfoUrl = (name: string, key: string) =>
  `https://www.espncricinfo.com/cricketers/${name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')}-${key}`;
export const cricketArchiveUrl = (key: string) =>
  `https://cricketarchive.com/Archive/Players/${Math.floor(Number(key) / 1000)}/${key}/${key}.html`;
