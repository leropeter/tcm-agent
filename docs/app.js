/* app.js 鈥?闈欐€佺珯 UI銆傝鲸璇侀€昏緫鍦?tcm-engine.js锛堜笌 Python 鐗堥€愯瀵圭収锛夈€?*/
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
  return (DATA.formulas || []).filter(f => (f['璇佸瀷'] || []).includes(id));
}

function syndromeById(id) {
  return (DATA.syndromes || []).find(s => s.id === id);
}

const LEVEL_CLASS = { '杈冮珮': 'lv-high', '涓瓑': 'lv-mid', '杈冧綆': 'lv-low', '鏃?: 'lv-none' };

/* ---------------- 鍓傚瀷 鈫?閫氱敤鍒朵綔娴佺▼锛堜笉娑夊強鍓傞噺锛?---------------- */

function prepMethod(name) {
  if (/涓?.test(name)) {
    return {
      kind: '涓稿墏',
      steps: [
        '鑽潗鎸夋柟鐮斾负缁嗘湯锛屾贩鍖€銆?,
        '鎸夊尰鍢变互铚溿€佹按鎴栫背绯婁负璧嬪舰鍓傚埗涓革紙鏈柟鍘熸硶瑙佸嚭澶勶級銆?,
        '鎸夊尰鍢辩敤閲忥紝娓╂按閫佹湇锛涜ˉ鐩婄被澶氶キ鍓嶏紝娑堝绫诲楗悗銆?,
      ],
      tip: '涓稿墏璧锋晥缂擄紝閫傚悎涔呮湇璋冨吇锛涙€ョ棁涓€鑸笉鐢ㄤ父銆?,
    };
  }
  if (/鏁?.test(name)) {
    return {
      kind: '鏁ｅ墏',
      steps: [
        '鑽潗鐮斾负缁嗘湯锛岃繃绛涙贩鍖€锛屽瘑灏侀槻娼€?,
        '鎸夊尰鍢辩敤閲忥紝娓╂按銆佸姹ゆ垨绫虫堡閫佹湇銆?,
        '鐜板鍙鍏ヨ兌鍥婃垨鍐叉湇锛岄鍛宠緝鏄撴帴鍙椼€?,
      ],
      tip: '鏁ｅ墏鐪佽嵂鏉愩€佽捣鏁堝揩锛屼絾鎸ュ彂鎬ц嵂鏉愶紙濡傝杽鑽凤級涓嶅疁涔呭瓨銆?,
    };
  }
  return {
    kind: '姹ゅ墏',
    steps: [
      '鑽潗鍐锋按娴告场 30 鍒嗛挓锛屾按闈㈡病杩囪嵂鏉愮害 2鈥? 鍘樼背銆?,
      '姝︾伀鐓哺鍚庤浆鏂囩伀锛屽ご鐓?25鈥?0 鍒嗛挓锛屾护鍑鸿嵂娑层€?,
      '鍘熻嵂娓ｅ啀鍔犳按锛屼簩鐓?20 鍒嗛挓锛屾护鍑恒€?,
      '涓ゆ鑽恫鍚堝苟锛屽垎鏃╂櫄涓ゆ娓╂湇銆?,
    ],
    tip: '瑙ｈ〃鑽疁姝︾伀蹇厧锛?5 鍒嗛挓宸﹀彸锛夛紝婊嬭ˉ鑽疁鏂囩伀涔呯厧锛?0 鍒嗛挓浠ヤ笂锛夛紱鍚檮瀛愩€佷箤澶寸被蹇呴』鍏堢厧銆?,
  };
}

/* ---------------- 寮瑰眰 ---------------- */

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
  const src = SOURCES[f['鍚?]] || [];
  const prep = prepMethod(f['鍚?]);

  let html = `
    <div class="md-head">
      <h2>${esc(f['鍚?])}</h2>
      <div class="md-src">${esc(f['鍑哄'] || '鍑哄鏈浇')}</div>
    </div>`;

  if (f['鍔熺敤']) html += `<p class="md-row"><b>鍔熺敤</b>${esc(f['鍔熺敤'])}</p>`;
  if (f['涓绘不']) html += `<p class="md-row"><b>涓绘不</b>${esc(f['涓绘不'])}</p>`;
  if (f['缁勬垚']) html += `<p class="md-row"><b>缁勬垚</b>${esc(f['缁勬垚'])}</p>`;

  html += `<div class="md-block">
      <h3>鎬庝箞鍋氾紙${prep.kind}閫氱敤娉曪級</h3>
      <ol class="md-steps">${prep.steps.map(s => `<li>${esc(s)}</li>`).join('')}</ol>
      <p class="md-tip">馃挕 ${esc(prep.tip)}</p>
    </div>`;

  if (src.length) {
    html += `<div class="md-block">
      <h3>鍏哥睄鍘熸枃</h3>
      ${src.map(s => `<div class="md-quote"><div class="q-book">銆?{esc(s.book.replace('.md', ''))}銆?/div>
        <p>${esc(s.text)}</p></div>`).join('')}
      <p class="md-tip">浠ヤ笂涓烘绱㈠懡涓殑鍙ょ睄娈佃惤鍘熸枃锛屽彲鑳藉寘鍚浉閭绘潯鏂囷紱鍙ゅ埗璁￠噺鍗曚綅锛堜袱銆佸崌銆佹灇锛変笌浠婁笉鍚岋紝<b>涓嶅彲鐩存帴鐓ф惉</b>銆?/p>
    </div>`;
  }

  if (f['娉ㄦ剰']) {
    html += `<div class="md-block md-warn"><h3>娉ㄦ剰</h3><p>${esc(f['娉ㄦ剰'])}</p></div>`;
  }

  html += `<p class="md-foot">鏈〉鍙粰缁勬垚涓庨€氱敤鍒舵硶锛?b>涓嶇粰鍓傞噺</b>鈥斺€斿墏閲忛敊涓€鐐瑰氨鏄簨鏁咃紝璇风敱鍖诲笀鎸変綘鐨勪綋璐ㄥ拰鐥呮儏瀹氥€?/p>`;
  return html;
}

function syndromeDetailHTML(id) {
  const s = syndromeById(id);
  if (!s) return '<p>娌℃湁杩欎釜璇佸瀷</p>';
  const fs = formulasFor(id);
  const adv = s.advice || {};

  let html = `
    <div class="md-head">
      <h2>${esc(s.id)}</h2>
      <div class="md-src">${esc(s.category)}</div>
    </div>
    <p class="md-row"><b>杈ㄨ瘉渚濇嵁</b>${esc(s.evidence)}</p>`;

  html += `<div class="md-block"><h3>鎬庝箞璋?/h3><dl class="md-advice">`;
  for (const [k, v] of Object.entries(adv)) {
    html += `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`;
  }
  html += `</dl></div>`;

  if (fs.length) {
    html += `<div class="md-block"><h3>鍙傝€冩柟鍓?/h3><div class="md-formula-list">`;
    for (const f of fs) {
      html += `<button class="md-formula-btn" data-fname="${esc(f['鍚?])}">
        <b>${esc(f['鍚?])}</b><span>${esc(f['鍔熺敤'] || '')}</span>
      </button>`;
    }
    html += `</div><p class="md-tip">鐐规柟鍚嶇湅缁勬垚銆佹€庝箞鍋氥€佸吀绫嶅師鏂囥€?/p></div>`;
  }
  return html;
}

/* ---------------- 缁撴灉娓叉煋 ---------------- */

function renderChips() {
  const box = $('#chips');
  const picks = ['澶辩湢', '澶氭ⅵ', '涔忓姏', '鎬曞喎', '鍙ｅ共', '鍙ｈ嫤', '澶存檿', '鑰抽福',
    '椋熸涓嶆尟', '澶т究涓嶆垚褰?, '鑵伴吀', '蹇冪儲', '鍜冲椊', '鐥伴粍', '鎵嬭剼鍐板噳', '瀹规槗鎰熷啋'];
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
        <h2>鏆傛椂鐪嬩笉鍑鸿瘉鍨?/h2>
        <p>浣犵粰鐨勪俊鎭繕涓嶈冻浠ヤ笅缁撹銆傚彲浠ヨˉ涓€鍙ワ細<b>鏄€曞喎杩樻槸鎬曠儹銆佹湁娌℃湁姹椼€佸ぇ渚垮共杩樻槸绋€銆佺潯寰楀ソ涓嶅ソ銆佸彛骞蹭笉骞?/b>銆?/p>
        <p class="hint">杩欏彴宸ュ叿鐨勫師鍒欐槸锛氳瘉鎹笉瓒虫椂瀹佸彲涓嶇粰璇佸瀷锛屼篃涓嶇‖濂椾竴涓€?/p>
      </div>`;
    box.scrollIntoView({ behavior: 'smooth', block: 'start' });
    return;
  }

  const a = E.assess(results);
  const top = results[0];
  const src = top.src || {};
  const others = results.slice(1, 5);
  const words = { '杈冮珮': '鏈€鍙兘', '涓瓑': '鍙兘鏄?, '杈冧綆': '鏆傚亸鍚? }[a.level] || '鍙兘鏄?;

  let html = `
    <div class="card main">
      <div class="verdict-head">
        <span class="sx-icon" aria-hidden="true">${esc(src.image || '馃尶')}</span>
        <span class="badge ${LEVEL_CLASS[a.level]}">鎶婃彙${a.level}</span>
        <h2>${words} <span class="sx">${esc(top.id)}</span></h2>
        <span class="cat">${esc(top.category)}</span>
      </div>
      <div class="meter"><i style="width:${Math.min(100, top.score * 7)}%"></i><span data-score="${top.score}">0 鍒?/span></div>
      <p class="note">${esc(a.note)}</p>
      ${a.conflict ? `<p class="conflict">鈿狅笍 ${esc(a.conflict)}</p>` : ''}
      <div class="hits">
        <span class="hits-label">鍛戒腑浣犵殑鍘熻瘽锛?/span>
        ${top.hits.map(h => `<span class="tag">${esc(h)}</span>`).join('')}
      </div>
      <p class="evidence"><b>杈ㄨ瘉渚濇嵁锛?/b>${esc(src.evidence || '')}</p>
    </div>`;

  const adv = src.advice || {};
  if (Object.keys(adv).length) {
    html += `<div class="card"><h3>鎬庝箞璋?/h3><dl class="advice">`;
    for (const [k, v] of Object.entries(adv)) {
      html += `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`;
    }
    html += `</dl></div>`;
  }

  const fs = formulasFor(top.id);
  if (fs.length) {
    html += `<div class="card"><h3>鍙傝€冩柟鍓?span class="sub2">鐐瑰紑鐪嬬粍鎴愩€佸仛娉曘€佸吀绫嶅師鏂?/span></h3>`;
    for (const f of fs) {
      html += `<button class="formula" data-fname="${esc(f['鍚?])}">
        <div class="f-head"><b>${esc(f['鍚?])}</b><span class="f-src">${esc(f['鍑哄'] || '')}</span>
          <span class="f-go">鐐瑰嚮灞曞紑 鈥?/span></div>
        <div class="f-row"><span>鍔熺敤</span>${esc(f['鍔熺敤'] || '')}</div>
        <div class="f-row"><span>缁勬垚</span>${esc(f['缁勬垚'] || '')}</div>
      </button>`;
    }
    html += `</div>`;
  }

  if (others.length) {
    html += `<div class="card"><h3>涔熷彲鑳芥槸<span class="sub2">鐐瑰紑鐪嬭繖涓瘉鍨嬫€庝箞璋?/span></h3><ul class="others">`;
    for (const o of others) {
      html += `<li><button class="other-btn" data-sid="${esc(o.id)}">
        <b>${esc(o.id)}</b>
        <span class="o-score">${o.score} 鍒?/span>
        <span class="o-cat">${esc(o.category)}</span>
        <span class="o-go">鈥?/span>
      </button></li>`;
    }
    html += `</ul></div>`;
  }

  html += `<div class="card warn-card">
      <p><b>杩欎笉鏄瘖鏂€?/b>缁撴灉鏄寜鐥囩姸璇嶅姞鏉冨尮閰嶅嚭鏉ョ殑鍊惧悜锛岀湡瀹炰复搴婅鐪嬬梾绋嬨€佷綋璐ㄣ€佽垖鑴夊拰鏃㈠線娌荤枟鍙嶅簲銆?      濡傛灉鐥囩姸鎸佺画銆佸姞閲嶏紝鎴栬€呭嚭鐜拌兏鐥涖€侀粦渚裤€佸墽鐑堝ご鐥涖€佽偄浣撻夯鏈紝璇风洿鎺ュ氨鍖汇€?/p>
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
    el.textContent = Math.round(to * eased) + ' 鍒?;
    if (p < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

/* 榧犳爣璺熼殢鐨勬煍鍏夛紙浠呯簿纭寚閽堣澶囷級 */
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

/* 鍏ㄥ眬鐐瑰嚮锛氭柟鍓?/ 鍏朵粬璇佸瀷 / 鍏抽棴寮瑰眰 */
function initDelegates() {
  document.addEventListener('click', (e) => {
    const fBtn = e.target.closest('[data-fname]');
    if (fBtn) {
      const name = fBtn.dataset.fname;
      const f = (DATA.formulas || []).find(x => x['鍚?] === name);
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

async function boot() {
  const res = await fetch('data.json?v=5');
  DATA = await res.json();
  E.setData(DATA);

  try {
    const s = await fetch('formula_sources_v2.json?v=1');
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

/* 娣遍摼锛?f=鍥涘悰瀛愭堡 鐩存帴鎵撳紑鏂瑰墏锛?#s=鑴炬皵铏?鐩存帴鎵撳紑璇佸瀷锛堟柟渚垮垎浜級 */
function openFromHash() {
  const raw = decodeURIComponent(location.hash.slice(1));
  if (!raw) return;
  if (raw.startsWith('f=')) {
    const f = (DATA.formulas || []).find(x => x['鍚?] === raw.slice(2));
    if (f) openModal(formulaDetailHTML(f));
  } else if (raw.startsWith('s=')) {
    openModal(syndromeDetailHTML(raw.slice(2)));
  }
}

boot().catch(err => {
  $('#result').hidden = false;
  $('#result').innerHTML = `<div class="card empty"><h2>鏁版嵁娌″姞杞藉嚭鏉?/h2>
    <p>${esc(err.message)}</p><p class="hint">鏈湴鍙屽嚮鎵撳紑 html 浼氳娴忚鍣ㄦ嫤鎴?fetch锛涚敤鏈湴鏈嶅姟鍣ㄦ垨绾夸笂鍦板潃鎵撳紑鍗冲彲銆?/p></div>`;
});
