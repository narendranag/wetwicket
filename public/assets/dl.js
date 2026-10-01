// Duckworth-Lewis Standard Edition (2002 table). A port of pipeline/rain_rules.py;
// scripts/test-dl.mjs checks it against the ICC's worked examples.
const DL = (() => {
  let SE = null; // SE[balls_left][wickets_lost], percent of a 50-over innings
  const load = async () => (SE = SE || await (await fetch("/data/dl-se.json")).json());
  const use = table => { SE = table; };

  const resource = (ballsLeft, wkts) => (wkts >= 10 || ballsLeft <= 0 ? 0 : SE[Math.min(ballsLeft, 300)][wkts]);

  // stoppages: [balls left at suspension, wickets lost, balls left at resumption]; a termination resumes with 0.
  const inningsResource = (startBalls, stoppages = []) =>
    resource(startBalls, 0) - stoppages.reduce((sum, [s, w, r]) => sum + (resource(s, w) - resource(r, w)), 0);

  // Revised target (ICC playing conditions, clause 5.6).
  const target = (S, R1, R2, G50 = 245) => {
    if (R2 < R1) return Math.floor(S * R2 / R1) + 1;
    if (R2 === R1) return S + 1;
    return Math.floor(S + (R2 - R1) * G50 / 100) + 1;
  };

  // "47.1" -> 283 balls. Returns NaN for anything that isn't overs.balls.
  const balls = text => {
    const m = /^(\d{1,2})(?:\.([0-5]))?$/.exec(String(text).trim());
    return m ? +m[1] * 6 + +(m[2] || 0) : NaN;
  };
  const overs = b => (b % 6 ? `${Math.floor(b / 6)}.${b % 6}` : `${b / 6}`);

  // An innings as a scorer sees it. stops: {bowled, wkts, length}, where length is the innings' new
  // length in balls once play resumes (equal to bowled if there was no more play).
  // Returns the D/L stoppages and the innings' final length.
  const stoppages = (startBalls, stops) => {
    let length = startBalls;
    const out = stops.map(({ bowled, wkts, length: next }) => {
      const s = [length - bowled, wkts, next - bowled];
      length = next;
      return s;
    });
    return { stoppages: out, length };
  };

  return { load, use, resource, inningsResource, target, balls, overs, stoppages };
})();
