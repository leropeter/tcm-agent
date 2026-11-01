/* tcm-engine.js — 辨证引擎（纯逻辑，无 DOM 依赖）
 *
 * 逐行对照 Python 版 src/agent.py + src/normalize.py。
 * 浏览器里挂到 window.TCMEngine，Node 里可 require。
 * 提供 selfTest(cases) 用于与 Python 版对拍。
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.TCMEngine = factory();
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  let DATA = null;

  const DELIM = /[,，、;\s；]+/;

  const STOPWORDS = [
    '有点儿', '有点', '特别', '非常', '比较', '稍微', '超级', '最近', '一直',
    '老是', '总是', '经常', '偶尔', '有时', '感觉', '觉得', '好像',
    '浑身', '全身上下',
    '也', '很', '太', '挺', '还', '都', '就', '又', '再', '总', '有些',
  ].sort((a, b) => b.length - a.length);
  const STOP_RE = new RegExp(STOPWORDS.map(escapeRe).join('|'), 'g');

  function escapeRe(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

  function setData(data) {
    DATA = data;
    DATA._synKeys = Object.keys(data.synonyms).sort((a, b) => b.length - a.length);
    DATA._kwSet = new Set(data.keywords);
    return DATA;
  }

  function getData() { return DATA; }

  function parseSymptoms(text) {
    const parts = String(text).trim().split(DELIM);
    const seen = new Set();
    const out = [];
    for (const p of parts) {
      if (p && !seen.has(p)) { seen.add(p); out.push(p); }
    }
    return out;
  }

  function clean(t) {
    const s = t.replace(STOP_RE, '');
    return s || t;
  }

  function expandSymptoms(tokens) {
    const out = new Set();
    const trace = {};
    const add = (kw, src) => {
      if (!DATA._kwSet.has(kw)) return;
      out.add(kw);
      if (!trace[kw]) trace[kw] = [];
      if (!trace[kw].includes(src)) trace[kw].push(src);
    };

    for (const t of tokens) {
      if (!t) continue;
      const cands = [t];
      const tc = clean(t);
      if (tc !== t) cands.push(tc);
      for (const c of cands) {
        if (!c) continue;
        add(c, t);
        for (const slang of DATA._synKeys) {
          if (c.includes(slang)) {
            for (const std of DATA.synonyms[slang]) add(std, t);
          }
        }
        if (c.length >= 2) {
          for (const kw of DATA.keywords) {
            if (kw.length >= 2 && kw !== c && c.includes(kw)) add(kw, t);
          }
        }
      }
    }
    return { out, trace };
  }

  function match(symptoms, syndrome, trace) {
    let score = 0;
    const hits = [];
    const table = syndrome.symptoms;
    const others = Object.keys(table);

    for (const kw of others) {
      const w = table[kw];
      if (!symptoms.has(kw)) continue;
      let superseded = false;
      for (const src of (trace[kw] || [])) {
        for (const other of others) {
          if (other === kw || other.length <= kw.length || !other.includes(kw)) continue;
          if (symptoms.has(other) && (trace[other] || []).includes(src)) {
            superseded = true; break;
          }
        }
        if (superseded) break;
      }
      if (superseded) continue;
      score += w;
      hits.push(kw);
    }
    return { score, hits };
  }

  const COLD = ['寒', '阳虚', '外感', '表证'];
  const HOT = ['热', '火', '阴虚', '燥'];
  function nature(s) {
    if (COLD.some(k => s.includes(k))) return '寒';
    if (HOT.some(k => s.includes(k))) return '热';
    return null;
  }

  function diagnose(text) {
    const tokens = parseSymptoms(text);
    const { out, trace } = expandSymptoms(tokens);

    const results = [];
    for (const s of DATA.syndromes) {
      const { score, hits } = match(out, s, trace);
      if (score > 0 && hits.length) {
        results.push({ id: s.id, category: s.category, score, hits, trace, src: s });
      }
    }
    results.sort((a, b) => b.score - a.score);
    return { results, tokens, expanded: Array.from(out).sort() };
  }

  function assess(results) {
    if (!results.length) {
      return { level: '无', lead: 0, signals: 0, conflict: null, note: '没有足够的证型匹配信号。' };
    }
    const top = results[0];
    const score = top.score;
    const second = results[1] ? results[1].score : 0;
    const lead = score - second;

    const srcs = new Set();
    for (const kw of top.hits) {
      for (const s of (top.trace[kw] || [kw])) srcs.add(s);
    }
    let n = srcs.size;
    const longSrc = Array.from(srcs).some(s => s.length >= 6);
    if (n <= 1 && longSrc && top.hits.length >= 2) n = 2;

    let conflict = null;
    if (results[1]) {
      const n1 = nature(top.id + top.category);
      const n2 = nature(results[1].id + results[1].category);
      if (n1 && n2 && n1 !== n2 && lead <= 2) {
        conflict = `「${top.id}」（偏${n1}）与「${results[1].id}」（偏${n2}）方向相反且分数接近（${score} vs ${results[1].score}），需鉴别后再调养。`;
      }
    }

    let level, note;
    if (score >= 8 && lead >= 2 && n >= 2) {
      level = '较高'; note = `命中 ${n} 个独立症状、领先第二名 ${lead} 分。`;
    } else if (score >= 6 && lead >= 2) {
      level = '中等'; note = `方向较清楚（${score} 分，领先 ${lead} 分）。`;
    } else if (score >= 4 && lead >= 1) {
      level = '较低'; note = `只有 ${score} 分、领先 ${lead} 分，只能算倾向。`;
    } else if (n <= 1) {
      level = '较低'; note = '只有 1 个症状线索，不足以确定证型。';
    } else {
      level = '较低'; note = `证据分散（${score} 分，领先 ${lead} 分），多个证型都像。`;
    }
    if (n <= 1 && level === '较高') { level = '中等'; note += '（但仅 1 个症状线索，暂不给最高把握）'; }

    return { level, lead, signals: n, conflict, note };
  }

  return {
    setData, getData, parseSymptoms, clean, expandSymptoms, match, diagnose, assess,
  };
}));
