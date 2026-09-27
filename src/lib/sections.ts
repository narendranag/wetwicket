import { getCollection, type CollectionEntry } from 'astro:content';

export const SECTIONS = [
  { id: 'numbers', name: 'The Numbers', plain: 'Data', blurb: 'Data explorations: what the scorecards say when you read all of them at once.' },
  { id: 'classics', name: 'Classics', plain: 'Great matches', blurb: 'Epic matches, broken down through the moments that decided them.' },
  { id: 'nets', name: 'The Nets', plain: 'Games', blurb: 'Simple browser games for when you have an over or two to spare.' },
  { id: 'long-room', name: 'The Long Room', plain: 'Essays', blurb: 'Long-form writing on the game, its laws and its history.' },
  { id: 'scorebook', name: 'Scorebook', plain: 'Tools', blurb: 'Things to use rather than read: explorers and calculators.' },
] as const;

export type SectionId = (typeof SECTIONS)[number]['id'];
export const SECTION_IDS = SECTIONS.map((s) => s.id) as [SectionId, ...SectionId[]];
export const sectionById = (id: string) => SECTIONS.find((s) => s.id === id)!;

export type Piece = CollectionEntry<'pieces'>;

/** "numbers/who-wins-when-it-rains" -> section and slug. */
export const sectionOf = (p: Piece) => p.id.split('/')[0] as SectionId;
export const slugOf = (p: Piece) => p.id.split('/').slice(1).join('/');
export const urlOf = (p: Piece) => `/${sectionOf(p)}/${slugOf(p)}/`;

export async function allPieces() {
  const pieces = await getCollection('pieces', (p) => import.meta.env.DEV || !p.data.draft);
  return pieces.sort((a, b) => b.data.published.valueOf() - a.data.published.valueOf());
}

export async function seriesPieces(seriesId: string) {
  return (await allPieces())
    .filter((p) => p.data.series?.id === seriesId)
    .sort((a, b) => (a.data.seriesOrder ?? 99) - (b.data.seriesOrder ?? 99));
}

export const fmtDate = (d: Date) =>
  d.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });
