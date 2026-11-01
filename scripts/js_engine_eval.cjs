/* js_engine_eval.cjs — 用 Node 跑 JS 引擎，输出每条用例的 Top1，供与 Python 版对拍。 */
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const E = require(path.join(ROOT, 'docs', 'tcm-engine.js'));
const data = JSON.parse(fs.readFileSync(path.join(ROOT, 'docs', 'data.json'), 'utf8'));
const cases = JSON.parse(fs.readFileSync(path.join(ROOT, 'eval', 'cases_oral.json'), 'utf8'));

E.setData(data);

const out = cases.cases.map(c => {
  const r = E.diagnose(c.input).results;
  return {
    id: c.id,
    input: c.input,
    top: r.length ? r[0].id : null,
    score: r.length ? r[0].score : 0,
    level: r.length ? E.assess(r).level : '无',
  };
});

fs.writeFileSync(path.join(ROOT, 'docs', '_js_eval.json'), JSON.stringify(out, null, 1), 'utf8');
console.log(`JS 引擎跑完 ${out.length} 条 -> docs/_js_eval.json`);
