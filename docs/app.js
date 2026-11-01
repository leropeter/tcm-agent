/* app.js — 静态站 UI。辨证逻辑在 tcm-engine.js（与 Python 版逐行对照）。 */
'use strict';

const E = window.TCMEngine;
let DATA = null;
let SOURCES = {};

const $ = (sel) => document.querySelector(sel);

function esc(s) {
  return String(s).replace(/[&<>"']/g, c => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function formulasFor(id) {
  return (DATA.formulas || []).filter(f => (f['证型'] || []).includes(id));
}

function syndromeById(id) {
  return (DATA.syndromes || []).find(s => s.id === id);
}

const LEVEL_CLASS = { '较高': 'lv-high', '中等': 'lv-mid', '较低': 'lv-low', '无': 'lv-none' };

/* ---------------- 剂型 → 通用制作流程（不涉及剂量） ---------------- */

function prepMethod(name) {
  if (/丸/.test(name)) {
    return {
      kind: '丸剂',
      steps: [
        '药材按方研为细末，混匀。',
        '按医嘱以蜜、水或米糊为赋形剂制丸（本方原法见出处）。',
        '按医嘱用量，温水送服；补益类多饭前，消导类多饭后。',
      ],
      tip: '丸剂起效缓，适合久服调养；急症一般不用丸。',
    };
  }
  if (/散/.test(name)) {
    return {
      kind: '散剂',
      steps: [
        '药材研为细末，过筛混匀，密封防潮。',
        '按医嘱用量，温水、姜汤或米汤送服。',
        '现多可装入胶囊或冲服，风味较易接受。',
      ],
      tip: '散剂省药材、起效快，但挥发性药材（如薄荷）不宜久存。',
    };
  }
  return {
    kind: '汤剂',
    steps: [
      '药材冷水浸泡 30 分钟，水面没过药材约 2–3 厘米。',
      '武火煮沸后转文火，头煎 25–30 分钟，滤出药液。',
      '原药渣再加水，二煎 20 分钟，滤出。',
      '两次药液合并，分早晚两次温服。',
    ],
    tip: '解表药宜武火快煎（15 分钟左右），滋补药宜文火久煎（40 分钟以上）；含附子、乌头类必须先煎。',
  };
}

/* ---------------- 弹层 ---------------- */

function openModal(html) {
  $('#modal-content').innerHTML = html;
  const m = $('#modal');
  m.hidden = false;
  requestAnimationFrame(() => m.classList.add('on'));
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  const m = $('#modal');
  m.classList.remove('on');
  document.body.style.overflow = '';
  setTimeout(() => { m.hidden = true; }, 220);
}

function formulaDetailHTML(f) {
  const src = SOURCES[f['名']] || [];
  const prep = prepMethod(f['名']);

  let html = `
    <div class="md-head">
      <h2>${esc(f['名'])}</h2>
      <div class="md-src">${esc(f['出处'] || '出处未载')}</div>
    </div>`;

  if (f['功用']) html += `<p class="md-row"><b>功用</b>${esc(f['功用'])}</p>`;
  if (f['主治']) html += `<p class="md-row"><b>主治</b>${esc(f['主治'])}</p>`;
  if (f['组成']) html += `<p class="md-row"><b>组成</b>${esc(f['组成'])}</p>`;

  html += `<div class="md-block">
      <h3>怎么做（${prep.kind}通用法）</h3>
      <ol class="md-steps">${prep.steps.map(s => `<li>${esc(s)}</li>`).join('')}</ol>
      <p class="md-tip">💡 ${esc(prep.tip)}</p>
    </div>`;

  if (src.length) {
    html += `<div class="md-block">
      <h3>典籍原文</h3>
      ${src.map(s => `<div class="md-quote"><div class="q-book">《${esc(s.book.replace('.md', ''))}》</div>
        <p>${esc(s.text)}</p></div>`).join('')}
      <p class="md-tip">以上为检索命中的古籍段落原文，可能包含相邻条文；古制计量单位（两、升、枚）与今不同，<b>不可直接照搬</b>。</p>
    </div>`;
  }

  if (f['注意']) {
    html += `<div class="md-block md-warn"><h3>注意</h3><p>${esc(f['注意'])}</p></div>`;
  }

  html += `<p class="md-foot">本页只给组成与通用制法，<b>不给剂量</b>——剂量错一点就是事故，请由医师按你的体质和病情定。</p>`;
  return html;
}

function syndromeDetailHTML(id) {
  const s = syndromeById(id);
  if (!s) return '<p>没有这个证型</p>';
  const fs = formulasFor(id);
  const adv = s.advice || {};

  let html = `
    <div class="md-head">
      <h2>${esc(s.id)}</h2>
      <div class="md-src">${esc(s.category)}</div>
    </div>
    <p class="md-row"><b>辨证依据</b>${esc(s.evidence)}</p>`;

  html += `<div class="md-block"><h3>怎么调</h3><dl class="md-advice">`;
  for (const [k, v] of Object.entries(adv)) {
    html += `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`;
  }
  html += `</dl></div>`;

  if (fs.length) {
    html += `<div class="md-block"><h3>参考方剂</h3><div class="md-formula-list">`;
    for (const f of fs) {
      html += `<button class="md-formula-btn" data-fname="${esc(f['名'])}">
        <b>${esc(f['名'])}</b><span>${esc(f['功用'] || '')}</span>
      </button>`;
    }
    html += `</div><p class="md-tip">点方名看组成、怎么做、典籍原文。</p></div>`;
  }
  return html;
}

/* ---------------- 结果渲染 ---------------- */

function renderChips() {
  const box = $('#chips');
  const picks = ['失眠', '多梦', '乏力', '怕冷', '口干', '口苦', '头晕', '耳鸣',
    '食欲不振', '大便不成形', '腰酸', '心烦', '咳嗽', '痰黄', '手脚冰凉', '容易感冒'];
  box.innerHTML = '';
  for (const t of picks) {
    const b = document.createElement('button');
    b.className = 'chip';
    b.textContent = t;
    b.onclick = () => {
      const ta = $('#symptoms');
      const cur = ta.value.trim();
      ta.value = cur ? cur + ' ' + t : t;
      ta.focus();
    };
    box.appendChild(b);
  }
}

function render(analysis) {
  const { results } = analysis;
  const box = $('#result');
  box.hidden = false;

  if (!results.length) {
    box.innerHTML = `
      <div class="card empty">
        <h2>暂时看不出证型</h2>
        <p>你给的信息还不足以下结论。可以补一句：<b>是怕冷还是怕热、有没有汗、大便干还是稀、睡得好不好、口干不干</b>。</p>
        <p class="hint">这台工具的原则是：证据不足时宁可不给证型，也不硬套一个。</p>
      </div>`;
    box.scrollIntoView({ behavior: 'smooth', block: 'start' });
    return;
  }

  const a = E.assess(results);
  const top = results[0];
  const src = top.src || {};
  const others = results.slice(1, 5);
  const words = { '较高': '最可能', '中等': '可能是', '较低': '暂偏向' }[a.level] || '可能是';

  let html = `
    <div class="card main">
      <div class="verdict-head">
        <span class="sx-icon" aria-hidden="true">${esc(src.image || '🌿')}</span>
        <span class="badge ${LEVEL_CLASS[a.level]}">把握${a.level}</span>
        <h2>${words} <span class="sx">${esc(top.id)}</span></h2>
        <span class="cat">${esc(top.category)}</span>
      </div>
      <div class="meter"><i style="width:${Math.min(100, top.score * 7)}%"></i><span data-score="${top.score}">0 分</span></div>
      <p class="note">${esc(a.note)}</p>
      ${a.conflict ? `<p class="conflict">⚠️ ${esc(a.conflict)}</p>` : ''}
      <div class="hits">
        <span class="hits-label">命中你的原话：</span>
        ${top.hits.map(h => `<span class="tag">${esc(h)}</span>`).join('')}
      </div>
      <p class="evidence"><b>辨证依据：</b>${esc(src.evidence || '')}</p>
    </div>`;

  const adv = src.advice || {};
  if (Object.keys(adv).length) {
    html += `<div class="card"><h3>怎么调</h3><dl class="advice">`;
    for (const [k, v] of Object.entries(adv)) {
      html += `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`;
    }
    html += `</dl></div>`;
  }

  const fs = formulasFor(top.id);
  if (fs.length) {
    html += `<div class="card"><h3>参考方剂<span class="sub2">点开看组成、做法、典籍原文</span></h3>`;
    for (const f of fs) {
      html += `<button class="formula" data-fname="${esc(f['名'])}">
        <div class="f-head"><b>${esc(f['名'])}</b><span class="f-src">${esc(f['出处'] || '')}</span>
          <span class="f-go">点击展开 ›</span></div>
        <div class="f-row"><span>功用</span>${esc(f['功用'] || '')}</div>
        <div class="f-row"><span>组成</span>${esc(f['组成'] || '')}</div>
      </button>`;
    }
    html += `</div>`;
  }

  if (others.length) {
    html += `<div class="card"><h3>也可能是<span class="sub2">点开看这个证型怎么调</span></h3><ul class="others">`;
    for (const o of others) {
      html += `<li><button class="other-btn" data-sid="${esc(o.id)}">
        <b>${esc(o.id)}</b>
        <span class="o-score">${o.score} 分</span>
        <span class="o-cat">${esc(o.category)}</span>
        <span class="o-go">›</span>
      </button></li>`;
    }
    html += `</ul></div>`;
  }

  html += `<div class="card warn-card">
      <p><b>这不是诊断。</b>结果是按症状词加权匹配出来的倾向，真实临床要看病程、体质、舌脉和既往治疗反应。
      如果症状持续、加重，或者出现胸痛、黑便、剧烈头痛、肢体麻木，请直接就医。</p>
    </div>`;

  box.innerHTML = html;
  playAnimations(box);
  box.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function playAnimations(box) {
  const cards = box.querySelectorAll('.card');
  cards.forEach((el, i) => { el.style.animationDelay = (i * 75) + 'ms'; });

  const bar = box.querySelector('.meter i');
  if (bar) {
    const target = bar.style.width;
    bar.style.width = '0';
    requestAnimationFrame(() => requestAnimationFrame(() => { bar.style.width = target; }));
  }

  const scoreEl = box.querySelector('.meter span[data-score]');
  if (scoreEl) countUp(scoreEl, Number(scoreEl.dataset.score), 850);
}

function countUp(el, to, dur) {
  const t0 = performance.now();
  const tick = (now) => {
    const p = Math.min(1, (now - t0) / dur);
    const eased = 1 - Math.pow(1 - p, 3);
    el.textContent = Math.round(to * eased) + ' 分';
    if (p < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

/* 鼠标跟随的柔光（仅精确指针设备） */
function initPointerGlow() {
  if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;
  document.addEventListener('mousemove', (e) => {
    const main = e.target.closest && e.target.closest('.card.main');
    if (main) {
      const r = main.getBoundingClientRect();
      main.style.setProperty('--mx', ((e.clientX - r.left) / r.width * 100) + '%');
      main.style.setProperty('--my', ((e.clientY - r.top) / r.height * 100) + '%');
    }
    const ic = e.target.closest && e.target.closest('.input-card');
    if (ic) {
      const r = ic.getBoundingClientRect();
      ic.style.setProperty('--spot-x', ((e.clientX - r.left) / r.width * 100) + '%');
      ic.style.setProperty('--spot-y', ((e.clientY - r.top) / r.height * 100) + '%');
    }
  }, { passive: true });
}

/* 全局点击：方剂 / 其他证型 / 关闭弹层 */
function initDelegates() {
  document.addEventListener('click', (e) => {
    const fBtn = e.target.closest('[data-fname]');
    if (fBtn) {
      const name = fBtn.dataset.fname;
      const f = (DATA.formulas || []).find(x => x['名'] === name);
      if (f) openModal(formulaDetailHTML(f));
      return;
    }
    const sBtn = e.target.closest('[data-sid]');
    if (sBtn) {
      openModal(syndromeDetailHTML(sBtn.dataset.sid));
      return;
    }
    if (e.target.closest('[data-close]') || e.target.closest('#modal-x')) closeModal();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
  });
}

/* 深链：#f=四君子汤 直接打开方剂， #s=脾气虚 直接打开证型（方便分享） */
function openFromHash() {
  const raw = decodeURIComponent(location.hash.slice(1));
  if (!raw) return;
  if (raw.startsWith('f=')) {
    const f = (DATA.formulas || []).find(x => x['名'] === raw.slice(2));
    if (f) openModal(formulaDetailHTML(f));
  } else if (raw.startsWith('s=')) {
    openModal(syndromeDetailHTML(raw.slice(2)));
  }
}

async function boot() {
  const res = await fetch('data.json?v=6');
  DATA = await res.json();
  E.setData(DATA);

  try {
    const s = await fetch('formula_sources_v2.json?v=2');
    SOURCES = await s.json();
  } catch (_) { SOURCES = {}; }

  renderChips();
  initPointerGlow();
  initDelegates();

  $('#go').onclick = () => {
    const text = $('#symptoms').value.trim();
    if (!text) {
      const ta = $('#symptoms');
      ta.classList.remove('shake');
      void ta.offsetWidth;
      ta.classList.add('shake');
      setTimeout(() => ta.classList.remove('shake'), 500);
      ta.focus();
      return;
    }
    render(E.diagnose(text));
  };

  document.querySelectorAll('.ex').forEach(b => {
    b.onclick = () => {
      $('#symptoms').value = b.dataset.text;
      render(E.diagnose(b.dataset.text));
    };
  });

  $('#symptoms').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) $('#go').click();
  });

  openFromHash();
  window.addEventListener('hashchange', openFromHash);
}

boot().catch(err => {
  $('#result').hidden = false;
  $('#result').innerHTML = `<div class="card empty"><h2>数据没加载出来</h2>
    <p>${esc(err.message)}</p><p class="hint">本地双击打开 html 会被浏览器拦截 fetch；用本地服务器或线上地址打开即可。</p></div>`;
});
