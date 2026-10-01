// Worked examples 1-6 from the ICC D-L Standard Edition playing conditions, run against the browser
// port in public/assets/dl.js. The Python originals are in pipeline/test_rain_rules.py.
//   node scripts/test-dl.mjs
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const root = new URL('..', import.meta.url);
const DL = vm.runInNewContext(readFileSync(new URL('public/assets/dl.js', root), 'utf8') + '; DL');
DL.use(JSON.parse(readFileSync(new URL('public/data/dl-se.json', root), 'utf8')));
const r1 = (v) => Math.round(v * 10) / 10;
const res = DL.inningsResource;

const tests = {
  example1_team1_interrupted_uplift() {
    const R1 = res(300, [[180, 3, 120]]), R2 = res(240);
    assert.equal(r1(R1), 87.5); assert.equal(R2, 89.3);
    assert.equal(DL.target(180, R1, R2), 185);
  },
  example2_team2_delayed() {
    assert.equal(DL.target(212, res(270), res(210)), 185);
  },
  example3_team2_interrupted() {
    const R2 = res(300, [[228, 1, 168]]);
    assert.equal(r1(R2), 86.8);
    assert.equal(DL.target(250, 100, R2), 218);
  },
  example4_abandoned_par() {
    const R2 = res(300, [[228, 1, 168], [108, 3, 96], [7 * 6 + 4, 6, 0]]);
    assert.equal(r1(R2), 63.8);
    assert.equal(DL.target(250, 100, R2) - 1, 159);
  },
  example5_team1_terminated_midover() {
    const R1 = res(300, [[17, 8, 0]]);
    assert.equal(r1(R1), 93.1);
    assert.equal(DL.target(226, R1, res(198)), 194);
  },
  example6() {
    const R1 = res(300, [[17, 8, 0]]), R2 = res(198, [[48, 2, 18]]);
    assert.equal(r1(R2), 64.7);
    assert.equal(DL.target(226, R1, R2), 158);
  },
  scorer_inputs_become_stoppages() {
    // Example 4 as a scorer would enter it: stopped after 12 overs (cut to 40), after 22 (cut to 38),
    // and for good after 30.2.
    const b = DL.balls;
    const { stoppages, length } = DL.stoppages(300, [
      { bowled: b('12'), wkts: 1, length: b('40') },
      { bowled: b('22'), wkts: 3, length: b('38') },
      { bowled: b('30.2'), wkts: 6, length: b('30.2') },
    ]);
    assert.deepEqual(JSON.parse(JSON.stringify(stoppages)), [[228, 1, 168], [108, 3, 96], [46, 6, 0]]);
    assert.equal(DL.overs(length), '30.2');
    assert.ok(Number.isNaN(DL.balls('30.6')));
  },
  durban_2003() {
    // Sri Lanka 268; South Africa 229/6 when rain ended play after 45 overs. Par 229: a tie.
    assert.equal(DL.target(268, 100, res(300, [[30, 6, 0]])) - 1, 229);
  },
};

for (const [name, fn] of Object.entries(tests)) {
  fn();
  console.log('ok', name);
}
