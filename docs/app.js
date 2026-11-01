/* app.js — 静态站 UI。辨证逻辑在 tcm-engine.js（与 Python 版逐行对照）。 */
'use strict';

const E = window.TCMEngine;
let DATA = null;

const $ = (sel) => document.querySelector(sel);

function esc(s) {
  return String(s).replace(/[&<>"']/g, c => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function formulasFor(id) {
  return (DATA.formulas || []).filter(f => (f['证型'] || []).includes(id));
}

const LEVEL_CLASS = { '较高': 'lv-high', '中等': 'lv-mid', '较低': 'lv-low', '无': 'lv-none' };

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
  const others = results.slice(1, 4);
  const words = { '较高': '最可能', '中等': '可能是', '较低': '暂偏向' }[a.level] || '可能是';

  let html = `
    <div class="card main">
      <div class="verdict-head">
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
    html += `<div class="card"><h3>参考方剂<span class="sub2">只给组成，不给剂量——剂量错一点就是事故</span></h3>`;
    for (const f of fs) {
      html += `<div class="formula">
        <div class="f-head"><b>${esc(f['名'])}</b><span class="f-src">${esc(f['出处'] || '')}</span></div>
        <div class="f-row"><span>组成</span>${esc(f['组成'] || '')}</div>
        <div class="f-row"><span>功用</span>${esc(f['功用'] || '')}</div>
        <div class="f-row"><span>主治</span>${esc(f['主治'] || '')}</div>
        ${f['注意'] ? `<div class="f-warn">⚠️ ${esc(f['注意'])}</div>` : ''}
      </div>`;
    }
    html += `</div>`;
  }

  if (others.length) {
    html += `<div class="card"><h3>也可能是</h3><ul class="others">`;
    for (const o of others) {
      html += `<li><b>${esc(o.id)}</b> <span class="o-score">${o.score} 分</span>
        <span class="o-cat">${esc(o.category)}</span></li>`;
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

/* 进场动效：卡片错峰、进度条从 0 展开、分数滚动 */
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

/* 鼠标跟随的柔光（仅精确指针设备，触屏跳过） */
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

async function boot() {
  const res = await fetch('data.json');
  DATA = await res.json();
  E.setData(DATA);

  renderChips();
  initPointerGlow();

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
}

boot().catch(err => {
  $('#result').hidden = false;
  $('#result').innerHTML = `<div class="card empty"><h2>数据没加载出来</h2>
    <p>${esc(err.message)}</p><p class="hint">本地双击打开 html 会被浏览器拦截 fetch；用本地服务器或线上地址打开即可。</p></div>`;
});
