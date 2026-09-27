(async () => {
const D = await (await fetch("/data/replay.json")).json();
const RULES = [
  { id: "DL-SE", name: "D/L Standard Edition", short: "D/L 2002", color: "var(--r-se)" },
  { id: "ARR", name: "Average Run Rate", short: "ARR", color: "var(--r-arr)" },
  { id: "DL-refit", name: "D/L modern refit", short: "Refit", color: "var(--r-refit)" },
  { id: "MPO", name: "Most Productive Overs", short: "MPO", color: "var(--r-mpo)" },
  { id: "DL-Pro", name: "D/L Pro, ICC average", short: "Pro (ICC)", color: "var(--r-pro)" },
  { id: "DL-Pro-avg", name: "D/L Pro, real average", short: "Pro (real)", color: "var(--r-proavg)" },
];
const MID = { "50-over": 30, T20: 12 };
let fam = "50-over";
try { fam = localStorage.getItem("wwir-fam") || fam; } catch (e) {}
const $ = id => document.getElementById(id);
const nf = new Intl.NumberFormat("en");
const pc = (v, d = 0) => (v * 100).toFixed(d) + "%";
const sg = (v, d = 1) => (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v).toFixed(d);
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

$("nmatch").textContent = nf.format(D.matches["50-over"] + D.matches.T20);
$("nm50").textContent = nf.format(D.matches["50-over"]);
$("nm20").textContent = nf.format(D.matches.T20);
$("nstates").textContent = nf.format(D.states);
$("nfit").textContent = nf.format(D.fit_matches);

const stageRows = (f, rule) => D.by_stage.filter(r => r.family === f && r.rule === rule).sort((a, b) => a.k - b.k);
const midRow = (f, rule) => D.by_stage.find(r => r.family === f && r.rule === rule && r.k === MID[f]);

// Tooltip for any element carrying data-tip.
const tip = $("tip");
document.addEventListener("pointermove", e => {
  const t = e.target.closest && e.target.closest("[data-tip]");
  if (!t) { tip.hidden = true; return; }
  tip.innerHTML = t.dataset.tip; tip.hidden = false;
  const x = Math.min(e.clientX + 14, innerWidth - tip.offsetWidth - 8);
  tip.style.left = x + "px"; tip.style.top = (e.clientY + 16) + "px";
});

function renderFindings() {
  const txt = {
    "DL-SE": r => [Math.abs(r.p_at_par - 0.5) < 0.04 ? "Close to fair" : r.p_at_par > 0.5 ? "Slightly against chasers" : "Slightly for chasers",
      `On-par chasers won ${pc(r.p_at_par)}. It named the real winner ${pc(r.agree)} of the time, against a best possible ${pc(midRow(fam, "Best possible").agree)}.`],
    ARR: r => ["Against chasers", `On-par chasers won ${pc(r.p_at_par)}. By ignoring wickets it took the win from ${pc(r.to_defender)} of chasers who went on to win.`],
    "DL-refit": r => [Math.abs(r.p_at_par - 0.5) < 0.04 ? "Close to fair" : r.p_at_par < 0.5 ? "Slightly for chasers" : "Slightly against chasers",
      `On-par chasers won ${pc(r.p_at_par)}. Fitted to 2015–2026 scoring, it named the real winner ${pc(r.agree)} of the time.`],
    "DL-Pro": r => [r.p_at_par > 0.54 ? "Against chasers" : "Close to fair",
      `On-par chasers won ${pc(r.p_at_par)}. Judged against the ICC's fixed average of 245, most modern totals count as high, which pushes pars up.`],
    "DL-Pro-avg": r => [Math.abs(r.p_at_par - 0.5) < 0.04 ? "Closest to fair" : r.p_at_par > 0.5 ? "Slightly against chasers" : "Slightly for chasers",
      `On-par chasers won ${pc(r.p_at_par)}. It named the real winner ${pc(r.agree)} of the time, the best of any rule we tested.`],
    MPO: r => ["Heavily against chasers", `On-par chasers won ${pc(r.p_at_par)}. It took the win from ${pc(r.to_defender)} of chasers who went on to win.`],
  };
  $("findings").innerHTML = RULES.map(R => {
    const r = midRow(fam, R.id), [v, p] = txt[R.id](r);
    return `<div class="finding"><div class="rule"><span class="swatch" style="background:${R.color}"></span>${R.name}</div>
      <div class="verdict">${v}</div><p>${p}</p></div>`;
  }).join("");
}

function axisTicks(lo, hi, n) {
  const step = [1, 2, 5, 10, 20, 25, 50].find(s => (hi - lo) / s <= n) || 100;
  const out = []; for (let v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) out.push(v); return out;
}

function lineChart(el, { series, xDomain, yDomain, xTicks, yTicks, xLabel, yFmt, ref, H = 300, labelRight = true, labelAt = "end" }) {
  const W = 760, L = 44, R = labelRight ? 108 : 16, T = 12, B = 40;
  const x = v => L + (v - xDomain[0]) / (xDomain[1] - xDomain[0]) * (W - L - R);
  const y = v => T + (1 - (v - yDomain[0]) / (yDomain[1] - yDomain[0])) * (H - T - B);
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img">`;
  yTicks.forEach(v => s += `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" stroke="var(--grid)"/><text x="${L - 8}" y="${y(v) + 4}" text-anchor="end">${yFmt(v)}</text>`);
  xTicks.forEach(v => s += `<text x="${x(v)}" y="${H - B + 18}" text-anchor="middle">${v}</text>`);
  s += `<line x1="${L}" x2="${W - R}" y1="${y(yDomain[0])}" y2="${y(yDomain[0])}" stroke="var(--line)"/>`;
  s += `<text x="${(L + W - R) / 2}" y="${H - 4}" text-anchor="middle">${xLabel}</text>`;
  if (ref != null) s += `<line x1="${L}" x2="${W - R}" y1="${y(ref)}" y2="${y(ref)}" stroke="var(--muted)" stroke-dasharray="3 4"/><text x="${W - R + 6}" y="${y(ref) + 4}">fair</text>`;
  const labels = [];
  series.forEach(se => {
    const d = se.points.map((p, i) => `${i ? "L" : "M"}${x(p[0]).toFixed(1)},${y(p[1]).toFixed(1)}`).join("");
    s += `<path d="${d}" fill="none" stroke="${se.color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"${se.dash ? ' stroke-dasharray="6 4"' : ""}/>`;
    if (se.dots) se.points.forEach(p => s += `<circle cx="${x(p[0])}" cy="${y(p[1])}" r="4" fill="${se.color}" stroke="var(--surface)" stroke-width="2"/>`);
    se.points.forEach((p, i) => { if (se.tips) s += `<circle class="hit" cx="${x(p[0])}" cy="${y(p[1])}" r="11" fill="transparent" data-tip="${esc(se.tips[i])}"/>`; });
    if (se.label) { const p = labelAt === "start" ? se.points[0] : se.points[se.points.length - 1];
      labels.push({ y: labelAt === "start" ? y(p[1]) - 10 : y(p[1]), x: labelAt === "start" ? x(p[0]) - 4 : x(p[0]), text: se.label }); }
  });
  labels.sort((a, b) => a.y - b.y);
  for (let i = 1; i < labels.length; i++) if (labels[i].y - labels[i - 1].y < 14) labels[i].y = labels[i - 1].y + 14;
  labels.forEach(l => s += `<text class="lbl" x="${l.x + 10}" y="${l.y + 4}">${esc(l.text)}</text>`);
  el.innerHTML = s + "</svg>";
}

function renderResources() {
  const N = fam === "50-over" ? 50 : 20;
  const refit = D.refit[String(N)], se = D.se[String(N)];
  const overs = refit.overs_left;
  const series = [];
  [0, 2, 4, 6, 8].forEach(w => {
    const color = `var(--w${w})`;
    series.push({ color, points: overs.map((u, i) => [u, se["w" + w][i]]), label: `${w} down`,
      tips: overs.map((u, i) => `${u} overs left, ${w} down<br>2002 table: ${se["w" + w][i]}% · refit: ${refit["w" + w][i]}%`) });
    series.push({ color, dash: true, points: overs.map((u, i) => [u, refit["w" + w][i]]) });
  });
  lineChart($("c-res"), { series, xDomain: [N, 0], yDomain: [0, 100], xTicks: axisTicks(0, N, 10).reverse(), yTicks: [0, 25, 50, 75, 100],
    xLabel: "overs left", yFmt: v => v + "%", H: 320, labelRight: false, labelAt: "start" });
}

function renderPar() {
  const N = fam === "50-over" ? 50 : 20;
  const series = RULES.map(R => {
    const rows = stageRows(fam, R.id);
    return { color: R.color, dots: true, label: R.short, points: rows.map(r => [r.k, r.p_at_par * 100]),
      tips: rows.map(r => `${R.name}, stopped after ${r.k} overs<br>On-par chasers won ${pc(r.p_at_par, 1)}<br>${nf.format(r.n)} chases`) };
  });
  const ks = stageRows(fam, "DL-SE").map(r => r.k);
  lineChart($("c-par"), { series, xDomain: [ks[0] - 1, ks[ks.length - 1] + 1], yDomain: [0, 100], xTicks: ks, yTicks: [0, 25, 50, 75, 100],
    xLabel: `overs faced by the chaser when rain stops play (of ${N})`, yFmt: v => v + "%", ref: 50 });
  $("lg-par").innerHTML = RULES.map(R => `<span><i class="swatch" style="background:${R.color}"></i>${R.name}</span>`).join("");
  $("t-par").innerHTML = `<table><thead><tr><th>Overs faced</th>${RULES.map(R => `<th class="r">${R.short}</th>`).join("")}<th class="r">Chases</th></tr></thead><tbody>` +
    ks.map(k => `<tr><td>${k}</td>${RULES.map(R => `<td class="r">${pc(D.by_stage.find(r => r.family === fam && r.rule === R.id && r.k === k).p_at_par, 1)}</td>`).join("")}
      <td class="r">${nf.format(D.by_stage.find(r => r.family === fam && r.rule === "DL-SE" && r.k === k).n)}</td></tr>`).join("") + "</tbody></table>";
}

function divergingBars(el, rows, { fmt, domain, unit }) {
  const W = 480, L = 120, R = 56, rowH = 34, T = 8, B = 26, H = T + rows.length * rowH + B;
  const x = v => L + (v - domain[0]) / (domain[1] - domain[0]) * (W - L - R);
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img">`;
  axisTicks(domain[0], domain[1], 6).forEach(v => s += `<line x1="${x(v)}" x2="${x(v)}" y1="${T}" y2="${H - B}" stroke="var(--grid)"/><text x="${x(v)}" y="${H - 8}" text-anchor="middle">${sg(v, 0)}</text>`);
  s += `<line x1="${x(0)}" x2="${x(0)}" y1="${T}" y2="${H - B}" stroke="var(--muted)"/>`;
  rows.forEach((r, i) => {
    const y0 = T + i * rowH + 7, h = rowH - 14, v = Math.max(domain[0], Math.min(domain[1], r.v));
    const xa = Math.min(x(0), x(v)), w = Math.max(1, Math.abs(x(v) - x(0)));
    const color = r.color || (r.v >= 0 ? "var(--pos)" : "var(--neg)");
    s += `<text class="lbl" x="${L - 10}" y="${y0 + h / 2 + 4}" text-anchor="end">${esc(r.label)}</text>`;
    s += `<rect x="${xa}" y="${y0}" width="${w}" height="${h}" rx="3" fill="${color}"/>`;
    // Long bars carry their value inside, in dark ink that reads on every bar fill.
    const inside = w > 90;
    const tx = inside ? (r.v >= 0 ? x(v) - 6 : x(v) + 6) : (r.v >= 0 ? x(v) + 6 : x(v) - 6);
    const anchor = (r.v >= 0) !== inside ? "start" : "end";
    s += `<text x="${tx}" y="${y0 + h / 2 + 4}" text-anchor="${anchor}" style="fill:${inside ? "#0b0b0b" : "var(--ink)"}">${fmt(r.v)}</text>`;
    s += `<rect class="hit" x="${L}" y="${y0 - 5}" width="${W - L - R}" height="${h + 10}" fill="transparent" data-tip="${esc(r.tip)}"/>`;
  });
  el.innerHTML = s + "</svg>";
}

function renderFlips() {
  const rows = RULES.map(R => { const r = midRow(fam, R.id); return { label: R.short, v: (r.to_chaser - r.to_defender) * 100, color: R.color,
    tip: `${R.name}<br>Win handed to a chaser who lost: ${pc(r.to_chaser, 1)}<br>Win taken from a chaser who won: ${pc(r.to_defender, 1)}` }; });
  divergingBars($("c-flip"), rows, { fmt: v => sg(v) + " pts", domain: [-50, 10] });
  const ks = stageRows(fam, "DL-SE").map(r => r.k);
  const cols = [...RULES.map(R => [R.id, R.short]), ["Best possible", "Best possible"]];
  $("t-agree").innerHTML = `<table><thead><tr><th>Overs faced</th>${cols.map(c => `<th class="r">${c[1]}</th>`).join("")}</tr></thead><tbody>` +
    ks.map(k => `<tr><td>${k}</td>${cols.map(c => `<td class="r">${pc(D.by_stage.find(r => r.family === fam && r.rule === c[0] && r.k === k).agree)}</td>`).join("")}</tr>`).join("") + "</tbody></table>";
}

function renderSE() {
  // The 2002 table next to the 2004 fix (real average), one bar each per band.
  const shown = RULES.filter(R => R.id === "DL-SE" || R.id === "DL-Pro-avg");
  const mk = (src, label) => src.filter(r => r.family === fam && shown.some(R => R.id === r.rule))
    .map(r => { const R = shown.find(x => x.id === r.rule); return { label: r.rule === "DL-SE" ? label(r.band) : "", v: r.fair_shift, color: R.color,
      tip: `${R.name}, ${label(r.band)}<br>On-par chasers won ${pc(r.p_at_par, 1)}<br>Par should move ${sg(r.fair_shift)} runs<br>${nf.format(r.n)} stopping points` }; });
  $("lg-se").innerHTML = shown.map(R => `<span><i class="swatch" style="background:${R.color}"></i>${R.name}</span>`).join("");
  const score = mk(D.by_score, b => `${b} runs`), wk = mk(D.by_wickets, b => `${b} down`);
  const lim = Math.ceil(Math.max(10, ...[...score, ...wk].map(r => Math.abs(r.v))) / 5) * 5;
  divergingBars($("c-score"), score, { fmt: v => sg(v) + " runs", domain: [-lim, lim] });
  divergingBars($("c-wkts"), wk, { fmt: v => sg(v) + " runs", domain: [-lim, lim] });
}

function renderExamples() {
  const rows = D.examples.map(e => {
    const chaseWon = e.winner === e.team2;
    const cell = id => { const p = e.pars[id], says = e.runs > p, flip = e.runs !== p && says !== chaseWon;
      return `<td class="r ${flip ? "flip" : "ok"}">${p}</td>`; };
    return `<tr><td class="num">${e.date}</td><td><b>${esc(e.team2)}</b> chasing ${e.S + 1} v ${esc(e.team1)}</td>
      <td class="r num">${e.runs}/${e.wkts}</td>${RULES.map(R => cell(R.id)).join("")}
      <td>${esc(e.winner)} won <span class="muted">(${esc(e.team2)} ${e.final})</span></td>
      <td><a href="/matches/${e.match_id}/">Scorecard</a></td></tr>`;
  }).join("");
  $("t-ex").innerHTML = `<table><thead><tr><th>Date</th><th>Chase</th><th class="r">After 30</th>${RULES.map(R => `<th class="r">${R.short} par</th>`).join("")}<th>Real result</th><th></th></tr></thead><tbody>${rows}</tbody></table>`;
}

function render() {
  document.querySelectorAll("#fam button").forEach(b => b.setAttribute("aria-pressed", b.dataset.v === fam));
  renderFindings(); renderResources(); renderPar(); renderFlips(); renderSE();
}
$("fam").addEventListener("click", e => {
  const b = e.target.closest("button"); if (!b) return;
  fam = b.dataset.v; try { localStorage.setItem("wwir-fam", fam); } catch (err) {}
  render();
});
render(); renderExamples();
})();
