(async () => {
const D = await (await fetch("/data/par-game.json")).json();
const CHASES = D.chases.map(r => Object.fromEntries(D.fields.map((f, i) => [f, r[i]])));
// [largest miss, runs]: a miss beyond the last band is a wicket.
const BANDS = {
  ODI: [[2, 6], [5, 4], [9, 3], [14, 2], [20, 1], [30, 0]],
  T20I: [[1, 6], [3, 4], [5, 3], [8, 2], [11, 1], [16, 0]],
};
const CALL = { 6: "Six!", 4: "Four", 3: "Three", 2: "Two", 1: "A single", 0: "Dot ball", W: "Out!" };
const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const day = d => new Date(d + "T00:00:00Z").toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
const plural = (n, word) => `${n} ${word}${n === 1 ? "" : "s"}`;

let over = [], balls = [], best = null;
try { best = JSON.parse(localStorage.getItem("btp-best")); } catch (e) {}

const shot = (c, guess) => {
  const miss = Math.abs(guess - c.par);
  const band = BANDS[c.fmt].find(([max]) => miss <= max);
  return band ? band[1] : "W";
};
const tally = () => ({ runs: balls.reduce((a, b) => a + (b === "W" ? 0 : b), 0), wkts: balls.filter(b => b === "W").length });
const scoreText = t => `${t.runs}/${t.wkts}`;

function board() {
  $("balls").innerHTML = Array.from({ length: 6 }, (_, i) => {
    const b = balls[i];
    const cls = b === undefined ? (i === balls.length ? "next" : "") : b === "W" ? "w" : b >= 4 ? "b" : "r";
    return `<li class="${cls}">${b === undefined ? "" : b === 0 ? "•" : b}</li>`;
  }).join("");
  $("total").textContent = scoreText(tally());
  $("best").textContent = best ? scoreText(best) : "–";
}

function newOver() {
  const pool = [...CHASES];
  over = Array.from({ length: 6 }, () => pool.splice(Math.floor(Math.random() * pool.length), 1)[0]);
  balls = [];
  face();
}

const scene = c => `
  <div class="meta">${c.gender === "female" ? "Women's " : ""}${c.fmt} · ${day(c.date)}</div>
  <div class="scores">
    <div><span class="team"><i class="swatch t1"></i>${esc(c.team1)}</span><b>${c.S}</b><span class="ov">${c.N} overs</span></div>
    <div><span class="team"><i class="swatch t2"></i>${esc(c.team2)}</span><b>${c.runs}/${c.wkts}</b><span class="ov">after ${c.k} overs · rain</span></div>
  </div>`;

function face() {
  board();
  const c = over[balls.length];
  const start = Math.round(c.S / 2);
  $("card").innerHTML = `
    <div class="eyebrow">Ball ${balls.length + 1} of 6</div>
    ${scene(c)}
    <p class="ask">${esc(c.team1)} made ${c.S}. ${esc(c.team2)} are ${c.runs} for ${c.wkts} after ${c.k} of their ${c.N} overs, and the rain has ended the match. <b>What is the D/L par score?</b></p>
    <form class="guess" id="guess">
      <input type="range" id="slide" min="0" max="${c.S}" value="${start}" aria-label="Your guess at the par score">
      <div class="entry">
        <button type="button" class="step" data-d="-1" aria-label="One fewer">−</button>
        <input type="number" id="num" min="0" max="${c.S}" value="${start}" inputmode="numeric" aria-label="Your guess at the par score">
        <button type="button" class="step" data-d="1" aria-label="One more">+</button>
        <button type="submit" class="go">Play the shot</button>
      </div>
    </form>`;
  const slide = $("slide"), num = $("num");
  const clamp = v => Math.max(0, Math.min(c.S, Math.round(v) || 0));
  slide.addEventListener("input", () => { num.value = slide.value; });
  num.addEventListener("input", () => { slide.value = clamp(+num.value); });
  $("guess").addEventListener("click", e => {
    const d = +e.target.dataset?.d;
    if (d) { num.value = slide.value = clamp(+num.value + d); }
  });
  $("guess").addEventListener("submit", e => { e.preventDefault(); reveal(c, clamp(+num.value)); });
}

function reveal(c, guess) {
  const runs = shot(c, guess);
  balls.push(runs);
  board();
  const miss = Math.abs(guess - c.par), lead = c.runs - c.par;
  const dl = lead > 0 ? `${esc(c.team2)} were ${plural(lead, "run")} ahead of par and would have won.`
    : lead < 0 ? `${esc(c.team2)} were ${plural(-lead, "run")} short of par, so ${esc(c.team1)} would have won.`
      : `${esc(c.team2)} were exactly on par. A tie.`;
  const pct = v => (100 * v / c.S).toFixed(1) + "%";
  const last = balls.length === 6;
  $("card").innerHTML = `
    <div class="eyebrow">Ball ${balls.length} of 6</div>
    ${scene(c)}
    <div class="call ${runs === "W" ? "w" : runs >= 4 ? "b" : ""}">${CALL[runs]}</div>
    <p class="ask">The par was <b>${c.par}</b>. You said ${guess}: ${miss === 0 ? "spot on" : `out by ${miss}`}.</p>
    <div class="line" role="img" aria-label="Your guess ${guess}, par ${c.par}, actual score ${c.runs}, on a scale from 0 to ${c.S}">
      <i class="pin score" style="left:${pct(Math.min(c.runs, c.S))}"><span>${c.runs}</span></i>
      <i class="pin par" style="left:${pct(c.par)}"><span>Par ${c.par}</span></i>
      <i class="pin you" style="left:${pct(guess)}"><span>You</span></i>
    </div>
    <ul class="after">
      <li><b>D/L says:</b> ${dl}</li>
      <li><b>Run rate alone</b> would have said ${c.arr}. D/L also weighs what they had left: ${plural(c.N - c.k, "over")} and ${plural(10 - c.wkts, "wicket")}.</li>
      <li><b>What really happened:</b> it didn't rain. ${esc(c.outcome)}. <a href="/matches/${esc(c.id)}/">Scorecard</a></li>
    </ul>
    <button type="button" class="go" id="next">${last ? "See the over" : "Next ball"}</button>`;
  $("next").addEventListener("click", last ? summary : face);
  $("next").focus();
}

function summary() {
  const t = tally();
  const beaten = !best || t.runs > best.runs || (t.runs === best.runs && t.wkts < best.wkts);
  if (beaten) {
    best = t;
    try { localStorage.setItem("btp-best", JSON.stringify(best)); } catch (e) {}
  }
  board();
  const line = t.wkts >= 3 ? "The par sheet wins this one." : t.runs >= 24 ? "Frank and Tony would have you on the committee."
    : t.runs >= 15 ? "A tidy over. You read the wickets well." : t.runs >= 8 ? "Ones and twos. Wickets in hand count for more than you think."
      : "Tough over. Remember: every wicket down pushes the par up.";
  const share = `Beat the Par: ${balls.map(b => (b === 0 ? "•" : b)).join(" ")} (${scoreText(t)})\nhttps://wetwicket.com/nets/beat-the-par/`;
  $("card").innerHTML = `
    <div class="eyebrow">End of the over${beaten ? " · your best yet" : ""}</div>
    <div class="call">${t.runs} for ${t.wkts}</div>
    <p class="ask">${line}</p>
    <div class="entry">
      <button type="button" class="go" id="again">Another over</button>
      <button type="button" class="step wide" id="copy">Copy your over</button>
    </div>`;
  $("again").addEventListener("click", newOver);
  $("copy").addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(share); $("copy").textContent = "Copied"; } catch (e) { $("copy").textContent = "Couldn't copy"; }
  });
  $("again").focus();
}

const upTo = (bands, i) => (i === 0 ? `0–${bands[0][0]}` : `${bands[i - 1][0] + 1}–${bands[i][0]}`);
$("bands").innerHTML = BANDS.ODI.map(([, runs], i) =>
  `<tr><td>${upTo(BANDS.ODI, i)} runs</td><td>${upTo(BANDS.T20I, i)}</td><td>${runs === 0 ? "a dot ball" : runs}</td></tr>`).join("")
  + `<tr><td>more than ${BANDS.ODI[5][0]}</td><td>more than ${BANDS.T20I[5][0]}</td><td>a wicket</td></tr>`;

newOver();
})();
