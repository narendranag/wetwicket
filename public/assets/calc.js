(async () => {
await DL.load();
const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const p1 = v => v.toFixed(1);

// Stoppages are entered as overs.balls strings, as a scorer writes them.
const EXAMPLES = [
  { name: "Durban 2003", n: 50, g50: 245, s: 268, stops1: [], n2: "", s2: 229,
    stops2: [{ bowled: "45", wkts: 6, ended: true }] },
  { name: "Rain in the first innings", n: 50, g50: 245, s: 180, n2: "40", s2: "",
    stops1: [{ bowled: "20", wkts: 3, length: "40" }], stops2: [] },
  { name: "A delayed chase", n: 45, g50: 245, s: 212, stops1: [], n2: "35", s2: "", stops2: [] },
  { name: "Rain mid-chase", n: 50, g50: 245, s: 250, stops1: [], n2: "", s2: "",
    stops2: [{ bowled: "12", wkts: 1, length: "40" }] },
  { name: "Three stoppages, then abandoned", n: 50, g50: 245, s: 250, stops1: [], n2: "", s2: 160,
    stops2: [{ bowled: "12", wkts: 1, length: "40" }, { bowled: "22", wkts: 3, length: "38" }, { bowled: "30.2", wkts: 6, ended: true }] },
];

let g50 = 245;
const syncG50 = () => $("g50").querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", +b.dataset.v === g50));

function addStop(team, stop = {}) {
  const row = $("stop-row").content.firstElementChild.cloneNode(true);
  for (const el of row.querySelectorAll("[data-k]")) {
    const v = stop[el.dataset.k];
    if (el.type === "checkbox") el.checked = !!v;
    else if (v !== undefined) el.value = v;
  }
  $("stops" + team).append(row);
  syncRow(row);
}
const syncRow = row => { row.querySelector('[data-k="length"]').disabled = row.querySelector('[data-k="ended"]').checked; };

function load(ex) {
  $("n").value = ex.n; $("s").value = ex.s; $("n2").value = ex.n2; $("s2").value = ex.s2;
  g50 = ex.g50;
  for (const team of [1, 2]) {
    $("stops" + team).innerHTML = "";
    ex["stops" + team].forEach(s => addStop(team, s));
  }
  render();
}

// Read one innings' stoppage rows. Throws a message for the scorer if they don't add up.
function readStops(team, startBalls) {
  let length = startBalls, last = 0;
  return [...$("stops" + team).children].map((row, i) => {
    const get = k => row.querySelector(`[data-k="${k}"]`);
    const where = `Team ${team}, stoppage ${i + 1}`;
    const bowled = DL.balls(get("bowled").value);
    const wkts = +get("wkts").value;
    const ended = get("ended").checked;
    if (Number.isNaN(bowled)) throw `${where}: enter the overs bowled when play stopped, such as 20 or 30.2.`;
    if (bowled > length) throw `${where}: play stopped after ${DL.overs(bowled)} overs, but the innings was only ${DL.overs(length)} overs long.`;
    if (bowled < last) throw `${where}: stoppages go in the order they happened.`;
    if (!(wkts >= 0 && wkts <= 9)) throw `${where}: wickets down must be between 0 and 9.`;
    const next = ended ? bowled : DL.balls(get("length").value);
    if (Number.isNaN(next)) throw `${where}: enter the innings' new length in overs, or tick "No more play".`;
    if (next < bowled || next > length) throw `${where}: the new length must be between ${DL.overs(bowled)} and ${DL.overs(length)} overs.`;
    if (i < $("stops" + team).children.length - 1 && ended) throw `${where}: only the last stoppage can end the innings.`;
    length = next; last = bowled;
    return { bowled, wkts, length: next, ended };
  });
}

function compute() {
  const N = +$("n").value, S = +$("s").value;
  if (!(N >= 1 && N <= 50) || !Number.isInteger(N)) throw "Overs a side must be a whole number from 1 to 50.";
  if (!(S >= 0) || $("s").value === "") throw "Enter Team 1's score.";
  const stops1 = readStops(1, N * 6);
  const i1 = DL.stoppages(N * 6, stops1);
  const R1 = DL.inningsResource(N * 6, i1.stoppages);

  const auto = Math.floor(i1.length / 6) * 6;
  $("n2").placeholder = DL.overs(auto);
  const start2 = $("n2").value.trim() === "" ? auto : DL.balls($("n2").value);
  if (Number.isNaN(start2) || start2 < 1 || start2 > N * 6) throw `Team 2's overs must be between 1 and ${N}.`;
  const stops2 = readStops(2, start2);
  const i2 = DL.stoppages(start2, stops2);
  const R2 = DL.inningsResource(start2, i2.stoppages);

  // The par sheet describes the chase as it stood before any final abandonment.
  const end = stops2.length && stops2[stops2.length - 1].ended ? stops2[stops2.length - 1] : null;
  const live = DL.stoppages(start2, end ? stops2.slice(0, -1) : stops2);
  const Rlive = DL.inningsResource(start2, live.stoppages);
  const from = Math.ceil((end ? stops2[stops2.length - 2]?.bowled ?? 0 : stops2[stops2.length - 1]?.bowled ?? 0) / 6);
  const sheet = [];
  for (let k = Math.max(from, 1); k * 6 <= live.length; k++) {
    sheet.push([k, ...Array.from({ length: 10 }, (_, w) => DL.target(S, R1, Rlive - DL.resource(live.length - k * 6, w), g50) - 1)]);
  }
  return { N, S, R1, R2, start2, length2: i2.length, target: DL.target(S, R1, R2, g50), end, sheet };
}

function render() {
  syncG50();
  let c;
  try { c = compute(); } catch (msg) {
    if (typeof msg !== "string") throw msg;
    $("verdict").innerHTML = `<p class="error">${esc(msg)}</p>`;
    $("resources").innerHTML = $("working").innerHTML = "";
    $("sheet-sec").hidden = true;
    return;
  }
  const { S, R1, R2, target, end } = c;
  const s2 = $("s2").value === "" ? null : +$("s2").value;
  if (end) {
    const par = target - 1;
    const d = s2 === null ? null : s2 - par;
    const out = d === null ? "" : d > 0 ? `Team 2 win by ${d} run${d === 1 ? "" : "s"}` : d < 0 ? `Team 1 win by ${-d} run${d === -1 ? "" : "s"}` : "Match tied";
    $("verdict").innerHTML = `<span class="eyebrow">Par score after ${DL.overs(end.bowled)} overs, ${end.wkts} down</span><b class="big">${par}</b>`
      + (out ? `<p class="out">${out} <span class="muted">(D/L method)</span></p>` : `<p class="muted">Enter Team 2's score to see the result. They needed ${target} to be ahead.</p>`);
  } else {
    $("verdict").innerHTML = `<span class="eyebrow">Team 2's target</span><b class="big">${target}</b>`
      + `<p class="out">to win from ${DL.overs(c.length2)} overs <span class="muted">· ${target - 1} ties</span></p>`;
  }
  $("resources").innerHTML = [["t1", "Team 1", R1], ["t2", "Team 2", R2]].map(([cls, name, r]) =>
    `<div><span class="eyebrow"><i class="swatch ${cls}"></i>${name} resources</span><b>${p1(r)}%</b><span class="track"><i class="${cls}" style="width:${Math.min(r, 100)}%"></i></span></div>`).join("");
  $("working").innerHTML = R2 < R1
    ? `Team 2 have fewer resources, so Team 1's score is scaled down: <code>${S} × ${p1(R2)} ÷ ${p1(R1)} = ${(S * R2 / R1).toFixed(2)}</code>. Round down for the par score, and add one for the target.`
    : R2 === R1
      ? `Both sides have the same resources, so Team 2 simply need one more than Team 1's ${S}.`
      : `Team 2 have more resources, so runs are added to Team 1's score: <code>${S} + ${p1(R2 - R1)}% × ${g50} = ${(S + (R2 - R1) * g50 / 100).toFixed(2)}</code>. Round down for the par score, and add one for the target.`;

  $("sheet-sec").hidden = !c.sheet.length;
  $("sheet-note").textContent = `If rain ends the chase for good after a completed over, this is the score Team 2 must be past to win, by wickets lost. Level with it is a tie.`
    + (end && end.bowled % 6 ? ` Play ended mid-over, after ${DL.overs(end.bowled)}; the sheet shows completed overs only.` : "");
  $("sheet").innerHTML = `<thead><tr><th>Overs</th>${Array.from({ length: 10 }, (_, w) => `<th class="r">${w} down</th>`).join("")}</tr></thead><tbody>`
    + c.sheet.map(([k, ...pars]) => `<tr><th>${k}</th>${pars.map((p, w) =>
      `<td class="r${end && end.bowled === k * 6 && end.wkts === w ? " hit" : ""}">${p}</td>`).join("")}</tr>`).join("") + "</tbody>";
}

$("examples").innerHTML = EXAMPLES.map((e, i) => `<button type="button" class="chip" data-i="${i}">${esc(e.name)}</button>`).join("");
$("examples").addEventListener("click", e => { const b = e.target.closest(".chip"); if (b) load(EXAMPLES[b.dataset.i]); });
$("g50").addEventListener("click", e => { const b = e.target.closest("button"); if (b) { g50 = +b.dataset.v; render(); } });
$("form").addEventListener("input", e => { const row = e.target.closest(".stop"); if (row) syncRow(row); render(); });
$("form").addEventListener("click", e => {
  if (e.target.dataset.add) { addStop(e.target.dataset.add); render(); }
  if (e.target.classList.contains("remove")) { e.target.closest(".stop").remove(); render(); }
});
$("form").addEventListener("submit", e => e.preventDefault());

load(EXAMPLES[0]);
})();
