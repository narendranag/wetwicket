import rss from '@astrojs/rss';
import { allPieces, urlOf } from '../lib/sections';

export async function GET(context) {
  const pieces = await allPieces();
  return rss({
    title: 'Wet Wicket',
    description: 'A loving exploration of cricket, by a cricket lover for cricket lovers.',
    site: context.site,
    items: pieces.map((p) => ({ title: p.data.title, description: p.data.dek, pubDate: p.data.published, link: urlOf(p) })),
  });
}
