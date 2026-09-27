(async () => {
const DATA = await (await fetch("/data/rain.json")).json();
const FMTS = ["Test", "ODI", "T20I", "T20 league", "One-day (other)", "First-class"];
const M = DATA.matches.map(r => ({
  date: r[0], fmt: r[1], gender: r[2], event: r[3], t1: r[4], t2: r[5], venue: r[6], country: r[7],
  outcome: r[8], conf: r[9], stage: r[10], reason: r[11], method: r[12], id: r[13], year: +r[0].slice(0, 4),
}));
const T = DATA.totals.map(([fmt, country, year, gender, n]) => ({ fmt, country, year, gender, n }));
const years = [...new Set(T.map(t => t.year))].sort((a, b) => a - b);
const minY = years[0], maxY = years[years.length - 1];
const DEFAULT = { fmt: new Set(FMTS), country: "", from: minY, to: maxY, gender: "all", conf: "all", q: "" };
let S = { ...DEFAULT, fmt: new Set(FMTS) };
let shown = 50;
const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const nf = new Intl.NumberFormat("en");

$("updated").textContent = `${nf.format(T.reduce((a, t) => a + t.n, 0))} matches to ${DATA.updated}`;

function chipGroup(el, opts, get, set) {
  el.innerHTML = opts.map(([v, label]) => `<button type="button" class="chip" data-v="${esc(v)}">${esc(label)}</button>`).join("");
  el.addEventListener("click", e => { const b = e.target.closest(".chip"); if (b) { set(b.dataset.v); shown = 50; render(); } });
  return () => el.querySelectorAll(".chip").forEach(b => b.setAttribute("aria-pressed", get(b.dataset.v)));
}
const syncFmt = chipGroup($("fmt"), FMTS.map(f => [f, f]), v => S.fmt.has(v), v => {
  // First click on a full set narrows to that one format; after that, chips toggle.
  if (S.fmt.size === FMTS.length) S.fmt = new Set([v]);
  else if (S.fmt.has(v) && S.fmt.size > 1) S.fmt.delete(v);
  else if (S.fmt.has(v)) S.fmt = new Set(FMTS);
  else S.fmt.add(v);
});
const syncGender = chipGroup($("gender"), [["all", "All"], ["male", "Men"], ["female", "Women"]], v => S.gender === v, v => S.gender = v);
const syncConf = chipGroup($("conf"), [["all", "All"], ["confirmed", "Confirmed"], ["likely", "Likely"]], v => S.conf === v, v => S.conf = v);

const yearOpts = years.map(y => `<option value="${y}">${y}</option>`).join("");
$("from").innerHTML = yearOpts; $("to").innerHTML = yearOpts;
$("from").onchange = e => { S.from = +e.target.value; if (S.from > S.to) S.to = S.from; shown = 50; render(); };
$("to").onchange = e => { S.to = +e.target.value; if (S.to < S.from) S.from = S.to; shown = 50; render(); };
$("country").onchange = e => { S.country = e.target.value; shown = 50; render(); };
$("q").oninput = e => { S.q = e.target.value.trim().toLowerCase(); shown = 50; render(); };
$("reset").onclick = () => { S = { ...DEFAULT, fmt: new Set(FMTS) }; $("q").value = ""; shown = 50; render(); };
$("more").onclick = () => { shown += 50; render(); };

const base = (x, skip = {}) => S.fmt.has(x.fmt) && (S.gender === "all" || x.gender === S.gender)
  && (skip.country || !S.country || x.country === S.country)
  && (skip.year || (x.year >= S.from && x.year <= S.to));
const matchOk = (m, skip) => base(m, skip) && (S.conf === "all" || m.conf === S.conf)
  && (!S.q || `${m.t1} ${m.t2} ${m.event}`.toLowerCase().includes(S.q));
// Denominators ignore the evidence and team filters, which have no equivalent for unaffected matches.
const played = skip => T.reduce((a, t) => a + (base(t, skip) ? t.n : 0), 0);
const pct = (a, b) => b ? (a / b * 100).toFixed(a / b < 0.1 ? 1 : 0) + "%" : "–";

function renderCountrySelect() {
  const counts = {};
  M.forEach(m => { if (matchOk(m, { country: true })) counts[m.country] = (counts[m.country] || 0) + 1; });
  if (S.country && !counts[S.country]) counts[S.country] = 0;
  const names = Object.keys(counts).sort((a, b) => a.localeCompare(b));
  $("country").innerHTML = `<option value="">All countries</option>` +
    names.map(c => `<option value="${esc(c)}">${esc(c)} (${counts[c]})</option>`).join("");
  $("country").value = S.country;
}

function renderStats(list) {
  const total = played();
  const conf = list.filter(m => m.conf === "confirmed").length;
  const method = list.filter(m => m.method).length;
  const washouts = list.filter(m => m.reason.startsWith("No result")).length;
  $("stats").innerHTML = [
    [nf.format(list.length), `rain-hit matches (${pct(list.length, total)} of ${nf.format(total)} played)`],
    [nf.format(conf), "confirmed by the scorecard"],
    [nf.format(method), "results decided by DLS or VJD"],
    [nf.format(washouts), "abandoned with no result"],
  ].map(([b, s]) => `<div class="stat"><b>${b}</b><span>${s}</span></div>`).join("");
}

function renderChart() {
  const by = {};
  years.forEach(y => by[y] = { c: 0, l: 0 });
  M.forEach(m => { if (matchOk(m, { year: true })) by[m.year][m.conf === "confirmed" ? "c" : "l"]++; });
  const W = 720, H = 240, L = 34, B = 26, Tp = 10, R = 6;
  const max = Math.max(1, ...years.map(y => by[y].c + by[y].l));
  const step = max <= 5 ? 1 : Math.pow(10, Math.floor(Math.log10(max / 4)));
  const tick = [1, 2, 5, 10].map(k => k * step).find(t => max / t <= 5) || step * 10;
  const top = Math.ceil(max / tick) * tick;
  const y = v => Tp + (H - Tp - B) * (1 - v / top);
  const bw = (W - L - R) / years.length;
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Rain-hit matches per year">`;
  for (let v = 0; v <= top; v += tick)
    s += `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" stroke="var(--line)"/><text x="${L - 6}" y="${y(v) + 4}" text-anchor="end">${v}</text>`;
  years.forEach((yr, i) => {
    const { c, l } = by[yr], x = L + i * bw + 1.5, w = Math.max(1, bw - 3);
    const on = yr >= S.from && yr <= S.to;
    s += `<g class="bar" tabindex="0" role="button" data-y="${yr}" opacity="${on ? 1 : 0.3}"><title>${yr}: ${c} confirmed, ${l} likely</title>`;
    s += `<rect x="${L + i * bw}" y="${Tp}" width="${bw}" height="${H - Tp - B}" fill="transparent"/>`;
    s += `<rect x="${x}" y="${y(c)}" width="${w}" height="${y(0) - y(c)}" fill="var(--accent)"/>`;
    s += `<rect x="${x}" y="${y(c + l)}" width="${w}" height="${y(c) - y(c + l)}" fill="var(--likely)"/></g>`;
    if (yr % 5 === 0 || years.length < 12) s += `<text x="${L + i * bw + bw / 2}" y="${H - 8}" text-anchor="middle">${yr}</text>`;
  });
  $("chart").innerHTML = s + "</svg>";
}
function pickYear(yr) {
  yr = +yr;
  if (S.from === yr && S.to === yr) { S.from = minY; S.to = maxY; } else { S.from = S.to = yr; }
  shown = 50; render();
}
$("chart").addEventListener("click", e => { const g = e.target.closest(".bar"); if (g) pickYear(g.dataset.y); });
$("chart").addEventListener("keydown", e => { const g = e.target.closest(".bar"); if (g && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); pickYear(g.dataset.y); } });

function renderCountries() {
  const hit = {}, tot = {};
  M.forEach(m => { if (matchOk(m, { country: true })) hit[m.country] = (hit[m.country] || 0) + 1; });
  T.forEach(t => { if (base(t, { country: true })) tot[t.country] = (tot[t.country] || 0) + t.n; });
  const rows = Object.keys(hit).sort((a, b) => hit[b] - hit[a]).slice(0, 14);
  if (S.country && !rows.includes(S.country) && hit[S.country]) rows.push(S.country);
  const max = Math.max(1, ...rows.map(c => hit[c]));
  $("clist").innerHTML = rows.length ? rows.map(c => `<button type="button" class="crow" data-c="${esc(c)}" aria-pressed="${S.country === c}">
      <span class="name">${esc(c)}<span class="track"><span class="fill" style="width:${hit[c] / max * 100}%"></span></span></span>
      <span class="n">${hit[c]}</span><span class="pct">${pct(hit[c], tot[c])}</span></button>`).join("")
    : `<p class="hint">No rain-hit matches for these filters.</p>`;
}
$("clist").addEventListener("click", e => {
  const b = e.target.closest(".crow"); if (!b) return;
  S.country = S.country === b.dataset.c ? "" : b.dataset.c; shown = 50; render();
});

function renderTable(list) {
  $("rows").innerHTML = list.length ? list.slice(0, shown).map(m => `<tr>
    <td class="date">${m.date}</td>
    <td><span class="teams">${esc(m.t1)} v ${esc(m.t2)}</span><span class="sub">${esc(m.event)}</span></td>
    <td>${esc(m.fmt)}<span class="sub">${m.gender === "female" ? "Women" : "Men"}</span></td>
    <td>${esc(m.country)}<span class="sub">${esc(m.venue)}</span></td>
    <td>${esc(m.outcome)}</td>
    <td><span class="pill ${m.conf}">${m.conf}</span><span class="sub">${esc(m.reason)}${m.stage ? ` · ${esc(m.stage)}` : ""}</span></td>
    <td><a href="https://cricsheet.org/matches/${m.id}/" target="_blank" rel="noopener">Scorecard</a></td>
  </tr>`).join("") : `<tr><td colspan="7" class="empty">No rain-hit matches for these filters. Try a wider year range or more formats.</td></tr>`;
  const left = list.length - shown;
  $("more").hidden = left <= 0;
  $("more").textContent = `Show ${Math.min(50, left)} more of ${nf.format(left)}`;
}

function render() {
  syncFmt(); syncGender(); syncConf();
  $("from").value = S.from; $("to").value = S.to;
  const list = M.filter(m => matchOk(m));
  renderCountrySelect(); renderStats(list); renderChart(); renderCountries(); renderTable(list);
}
render();
})();
