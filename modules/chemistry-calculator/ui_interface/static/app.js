/* CHEMCALC FX-17 — page logic (split out of index.html) */
/* ════════════════════════════════════════════════════════
   Safe storage — localStorage can be blocked (private windows)
════════════════════════════════════════════════════════ */
const store = {
  get(key, fallback) {
    try { const v = localStorage.getItem(key); return v === null ? fallback : v; }
    catch (e) { return fallback; }
  },
  set(key, value) {
    try { localStorage.setItem(key, value); } catch (e) { /* not saved */ }
  },
};

/* ════════════════════════════════════════════════════════
   Theme + Accent persistence
════════════════════════════════════════════════════════ */
function loadPreferences() {
  // Theme
  const savedTheme = store.get('ccTheme', 'dark');
  document.documentElement.setAttribute('data-theme', savedTheme);
  document.getElementById('themeBtn').textContent = savedTheme === 'dark' ? '☀ Light' : '☽ Dark';

  // Accent
  const savedAccent = store.get('ccAccent', null);
  const savedHover  = store.get('ccAccentHover', null);
  if (savedAccent) {
    applyAccent(savedAccent, savedHover || savedAccent);
    document.querySelectorAll('.accent-dot').forEach(d => {
      d.classList.toggle('active', d.dataset.accent === savedAccent);
    });
  } else {
    const first = document.querySelector('.accent-dot');
    if (first) first.classList.add('active');
  }

  // Output mode — must run after DOM is ready so the button exists
  const savedMode = store.get('outputMode', 'detailed');
  document.getElementById('outputModeBtn').textContent =
    savedMode === 'compact' ? '◼ Compact' : '≡ Detail';

  // Significant figures
  document.getElementById('sfSelect').value = getSigFigs();
}

function toggleTheme() {
  const html  = document.documentElement;
  const isNowDark = html.getAttribute('data-theme') !== 'dark';
  const theme = isNowDark ? 'dark' : 'light';
  html.setAttribute('data-theme', theme);
  document.getElementById('themeBtn').textContent = theme === 'dark' ? '☀ Light' : '☽ Dark';
  store.set('ccTheme', theme);
}

function applyAccent(color, hover) {
  const root = document.documentElement.style;
  root.setProperty('--accent', color);
  root.setProperty('--accent-hover', hover);
  // Parse RGB for the subtle tint
  const r = parseInt(color.slice(1,3), 16);
  const g = parseInt(color.slice(3,5), 16);
  const b = parseInt(color.slice(5,7), 16);
  root.setProperty('--accent-subtle', `rgba(${r},${g},${b},0.13)`);
}

function setAccent(btn) {
  const color = btn.dataset.accent;
  const hover = btn.dataset.hover;
  applyAccent(color, hover);
  store.set('ccAccent', color);
  store.set('ccAccentHover', hover);
  document.querySelectorAll('.accent-dot').forEach(d => d.classList.remove('active'));
  btn.classList.add('active');
}

// Apply saved preferences before first render
loadPreferences();
window.addEventListener('DOMContentLoaded', renderHistory);

/* ════════════════════════════════════════════════════════
   Output detail mode
════════════════════════════════════════════════════════ */
function getOutputMode() {
  return store.get('outputMode', 'detailed');
}

function applyOutputMode(mode) {
  document.getElementById('outputModeBtn').textContent =
    mode === 'compact' ? '◼ Compact' : '≡ Detail';
}

function toggleOutputMode() {
  const next = getOutputMode() === 'detailed' ? 'compact' : 'detailed';
  store.set('outputMode', next);
  applyOutputMode(next);
  if (lastResult) render(lastResult, { record: false });
}

/* ════════════════════════════════════════════════════════
   Significant figures + result rendering
════════════════════════════════════════════════════════ */
function getSigFigs() {
  const v = store.get('ccSigFigs', 'auto');
  return v === 'auto' ? 'auto' : Math.min(6, Math.max(2, parseInt(v, 10) || 4));
}
function setSigFigs(v) {
  store.set('ccSigFigs', v);
  if (lastResult) render(lastResult, { record: false });
  if (currentMod === 4 && lastResult) showChainToYield(lastResult);
}

const SUP = { '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹', '-': '⁻' };
function sci(v, n) {
  const [m, ex] = v.toExponential(n - 1).split('e');
  return `${m} × 10${String(parseInt(ex, 10)).split('').map(c => SUP[c] || c).join('')}`;
}
/* Format a number to the chosen significant figures.
   'auto' = 4 s.f. without trailing zeros; very large/small values use × 10ⁿ,
   and so does any value whose trailing zeros would be ambiguous. */
function fmtVal(v, sf) {
  if (typeof v !== 'number' || !isFinite(v)) return String(v);
  const n = sf === 'auto' ? 4 : sf;
  if (v === 0) return sf === 'auto' ? '0' : (0).toPrecision(n);
  const e = Math.floor(Math.log10(Math.abs(v)));
  if (e >= 6 || e <= -4 || (sf !== 'auto' && e >= n)) {
    let out = sci(v, n);
    if (sf === 'auto') out = out.replace(/(\.\d*?)0+ ×/, '$1 ×').replace(/\. ×/, ' ×');
    return out;
  }
  let t = v.toPrecision(n);
  if (t.includes('e')) return sci(v, n);          // rounding pushed it up a power (999.7 → 1.00e+3)
  if (sf === 'auto' && t.includes('.')) t = t.replace(/0+$/, '').replace(/\.$/, '');
  return t;
}
function answerLines(d, sf) {
  return (Array.isArray(d.answers) ? d.answers : []).map(a =>
    `${a.label} = ${fmtVal(a.value, sf)}${a.unit ? (a.unit === '%' ? '%' : ' ' + a.unit) : ''}`);
}

let lastResult = null;
/* Show a server response: headline + answers rounded to the chosen s.f.,
   or the full worked steps in Detail mode. */
function render(d, opts = {}) {
  const sf = getSigFigs();
  const lines = answerLines(d, sf);
  let compact = d.compact || '';
  if (sf !== 'auto' && lines.length) compact = [d.headline, ...lines].filter(Boolean).join('\n');
  const detailed = Array.isArray(d.detailed) ? d.detailed.slice() : [];
  if (sf !== 'auto' && lines.length && detailed.length) {
    detailed.push(`Answer to ${sf} s.f.: ${lines.join(';  ')}`);
  }
  showOutput(compact, detailed, d.warnings || []);
  lastResult = d;
  if (opts.record !== false) addHistory(compact, detailed, d.warnings || []);
}

/* ════════════════════════════════════════════════════════
   Copy answer
════════════════════════════════════════════════════════ */
async function copyOutput() {
  const out = document.getElementById('screenOut').innerText;
  const warn = document.getElementById('screenWarnings');
  const text = out + (warn.style.display !== 'none' && warn.innerText ? '\n' + warn.innerText : '');
  let copied = false;
  try {
    await navigator.clipboard.writeText(text);
    copied = true;
  } catch (e) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try { copied = document.execCommand('copy'); } catch (e2) { copied = false; }
    ta.remove();
  }
  const btn = document.getElementById('copyBtn');
  btn.textContent = copied ? '✓ Copied' : '✗ Copy failed';
  setTimeout(() => { btn.textContent = '⧉ Copy'; }, 1500);
}

/* ════════════════════════════════════════════════════════
   Recent calculations (kept in this browser only)
════════════════════════════════════════════════════════ */
const TYPE_SELECTS = ['moleType', 'volType', 'yieldType', 'gasType', 'abType', 'thermoType', 'iceType', 'ecType', 'kinType'];
function subtypeLabel() {
  for (const id of TYPE_SELECTS) {
    const el = document.getElementById(id);
    if (el && el.selectedIndex >= 0) return ' · ' + el.options[el.selectedIndex].text;
  }
  return '';
}
function loadHistory() {
  try { const h = JSON.parse(store.get('ccHistory', '[]')); return Array.isArray(h) ? h : []; }
  catch (e) { return []; }
}
function addHistory(compact, detailed, warnings) {
  if (!currentMod) return;
  const h = loadHistory();
  h.unshift({ mod: currentMod, title: MOD_NAMES[currentMod] + subtypeLabel(),
              compact, detailed, warnings, t: Date.now() });
  store.set('ccHistory', JSON.stringify(h.slice(0, 20)));
  renderHistory();
}
function clearHistory() {
  store.set('ccHistory', '[]');
  renderHistory();
}
function esc(t) {
  return String(t).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
function renderHistory() {
  const h = loadHistory();
  document.getElementById('historyBtn').textContent = `⟲ Recent${h.length ? ' (' + h.length + ')' : ''}`;
  const list = document.getElementById('historyList');
  if (!h.length) { list.innerHTML = '<div class="history-empty">No calculations yet.</div>'; return; }
  list.innerHTML = h.map((e, i) => {
    const time = new Date(e.t).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    return `<button class="history-item" onclick="showHistory(${i})">
      <div class="h-title">${esc(time)} · ${esc(e.title)}</div>
      <div class="h-answer">${esc(String(e.compact).split('\n').slice(0, 3).join('\n'))}</div></button>`;
  }).join('');
}
function toggleHistory() {
  renderHistory();
  document.getElementById('historyPanel').classList.toggle('hidden');
}
function showHistory(i) {
  const e = loadHistory()[i];
  if (!e) return;
  if (currentMod !== e.mod) selectMod(e.mod);
  showOutput(e.compact, e.detailed, e.warnings || []);
  showPrompt(`Showing a saved result from ${new Date(e.t).toLocaleTimeString()}.`);
  lastResult = null;
}

/* ════════════════════════════════════════════════════════
   Limiting reactant → % yield
════════════════════════════════════════════════════════ */
function hideChain() {
  const bar = document.getElementById('chainBar');
  bar.classList.add('hidden');
  bar.innerHTML = '';
}
function showChainToYield(d) {
  const bar = document.getElementById('chainBar');
  const prods = Object.entries(d.yields_g || {}).filter(([, g]) => typeof g === 'number');
  if (!prods.length) {
    bar.innerHTML = '<span>Tip: enter amounts in grams to send the theoretical yield to % Yield.</span>';
  } else {
    const sf = getSigFigs();
    bar.innerHTML = `<span>Use theoretical yield of</span>
      <select id="chainProd">${prods.map(([n, g]) =>
        `<option value="${g}">${esc(n)} (${fmtVal(g, sf)} g)</option>`).join('')}</select>
      <button class="mini-btn" onclick="chainToYield()">→ % Yield</button>`;
  }
  bar.classList.remove('hidden');
}
function chainToYield() {
  const sel = document.getElementById('chainProd');
  if (!sel) return;
  const grams = Number(sel.value);
  const name = sel.options[sel.selectedIndex].text.split(' (')[0];
  selectMod(10);
  setField('yieldType', 'percent');
  setField('yB', String(Number(grams.toPrecision(6))));
  const actual = document.getElementById('yA');
  if (actual) actual.focus();
  showPrompt(`Theoretical yield of ${name} filled in from Limiting Reactant — enter the actual yield.`);
}

/* ════════════════════════════════════════════════════════
   Worked examples
════════════════════════════════════════════════════════ */
function setField(id, value) {
  const el = document.getElementById(id);
  if (!el) return false;
  if (el.type === 'checkbox') el.checked = !!value;
  else el.value = value;
  el.dispatchEvent(new Event(el.tagName === 'SELECT' ? 'change' : 'input', { bubbles: true }));
  return true;
}
function fillRows(containerId, addFn, values) {
  const box = document.getElementById(containerId);
  if (!box) return;
  while (box.querySelectorAll('.dyn-row').length < values.length) addFn();
  const rows = Array.from(box.querySelectorAll('.dyn-row'));
  rows.slice(values.length).forEach(r => r.remove());
  rows.slice(0, values.length).forEach((r, i) => {
    r.querySelectorAll('input').forEach((inp, j) => {
      if (values[i][j] !== undefined) {
        inp.value = values[i][j];
        inp.dispatchEvent(new Event('input', { bubbles: true }));
      }
    });
  });
}
function setRadio(name, value) {
  const r = document.querySelector(`input[name="${name}"][value="${value}"]`);
  if (r) { r.checked = true; r.dispatchEvent(new Event('change', { bubbles: true })); }
}
const rowsOf = (id, add, values) => ({ rows: id, add, values });
const EXAMPLES = {
  '1:mass_to_moles':      [['mA', '10.0'], ['mB', 'CaCO3']],
  '1:moles_to_mass':      [['mA', '0.250'], ['mB', 'NaCl']],
  '1:moles_to_particles': [['mA', '0.250']],
  '1:particles_to_moles': [['mA', '3.01e23']],
  '1:moles_to_volume':    [['mA', '0.500']],
  '1:volume_to_moles':    [['mA', '4.54']],
  '2': [rowsOf('empRows', addEmpRow, [['C', '40.0'], ['H', '6.7'], ['O', '53.3']])],
  '3': [['eqInput', 'MnO4^- + Fe^2+ -> Mn^2+ + Fe^3+'], ['eqMedium', 'acidic']],
  '4': [['limUnit', 'g'], rowsOf('limRRows', addLimR, [['H2', '', '4.0'], ['O2', '', '16.0']]),
        rowsOf('limPRows', addLimP, [['H2O', '']])],
  '5': [['pctFormula', 'CuSO4.5H2O']],
  '6:mass_to_volume': [['vA', '50.0'], ['vB', '0.789']],
  '6:volume_to_mass': [['vA', '25.0'], ['vB', '13.6']],
  '6:density':        [['vA', '27.0'], ['vB', '10.0']],
  '7': [['oxFormula', 'K2Cr2O7'], ['oxCharge', '0'], ['oxPeroxide', false]],
  '8': [rowsOf('aeRRows', addAER, [['C6H12O6', '1']]), ['aeDesiredFormula', 'C2H5OH'], ['aeDesiredCoeff', '2']],
  '9:classify': [['ion1', 'Na'], ['ion2', 'Cl']],
  '9:formula':  [['ionCat', 'Al'], ['ionCatChg', '3'], ['ionAni', 'SO4'], ['ionAniChg', '-2']],
  '10:percent':     [['yA', '7.50'], ['yB', '10.0']],
  '10:actual':      [['yA', '85.0'], ['yB', '12.0']],
  '10:theoretical': [['yA', '6.20'], ['yB', '80.0']],
  '11': [{ radio: 'perType', value: 'symbol' }, ['perQuery', 'Fe']],
  '12:ideal':    [['gasPU', 'kPa'], ['gasVU', 'cm3'], ['gasTU', 'C'], ['gasIdealSolve', 'P'],
                  ['gasN', '0.0100'], ['gasV', '250'], ['gasT', '25.0'], ['gasP', '']],
  '12:combined': [['gasPU', 'kPa'], ['gasVU', 'dm3'], ['gasTU', 'C'], ['gasCombSolve', 'V2'],
                  ['gasP1', '100'], ['gasV1', '2.00'], ['gasT1', '27'], ['gasP2', '150'], ['gasV2', ''], ['gasT2', '127']],
  '12:graham':   [['gasM1', '2.016'], ['gasM2', '32.00']],
  '12:dalton':   [['gasPU', 'kPa'], rowsOf('daltonRows', addDaltonRow, [['N2', '79.0'], ['O2', '21.0']])],
  '12:mixing':   [['gasPU', 'kPa'], ['gasVU', 'dm3'], ['gasTU', 'C'], ['mixSolve', 'Pf'],
                  ['mixP1', '100'], ['mixV1', '1.0'], ['mixT1', '25'], ['mixP2', '200'], ['mixV2', '2.0'],
                  ['mixT2', '25'], ['mixVf', '3.0'], ['mixTf', '25']],
  '13:ph_convert':  [['abConvInput', 'pH'], ['abVal', '3.50']],
  '13:strong_acid': [['abConc', '0.0100']],
  '13:strong_base': [['abConc', '0.0500']],
  '13:weak_acid':   [['abKa', '1.74e-5'], ['abConc', '0.100']],
  '13:weak_base':   [['abKb', '1.78e-5'], ['abConc', '0.100']],
  '13:buffer':      [['abKa', '1.74e-5'], ['abAcid', '0.100'], ['abBase', '0.200']],
  '13:titration':   [['tiSolve', 'analyte_conc'], ['tiRa', '1'], ['tiRt', '2'], ['tiCt', '0.100'],
                     ['tiVt', '20.0'], ['tiVa', '25.0'], ['tiAcid', 'strong'], ['tiBase', 'strong']],
  '13:identify':    [['abFormula', 'CH3COOH']],
  '14:calorimetry':  [['calSolve', 'q'], ['calQ', ''], ['calM', '50.0'], ['calC', '4.18'], ['calDT', '12.0']],
  '14:hess':         [rowsOf('hessRows', addHessRow, [['-393.5', '1'], ['-283.0', '-1']])],
  '14:bond':         [rowsOf('bondBrRows', () => addBondRow('bondBrRows'), [['C-H', '4', ''], ['O=O', '2', '']]),
                      rowsOf('bondFmRows', () => addBondRow('bondFmRows'), [['C=O', '2', ''], ['O-H', '4', '']])],
  '14:std_enthalpy': [rowsOf('hfRRows', () => addHfRow('hfRRows'), [['CH4', '1', '-74.0'], ['O2', '2', '0']]),
                      rowsOf('hfPRows', () => addHfRow('hfPRows'), [['CO2', '1', '-393.5'], ['H2O', '2', '-285.8']])],
  '14:gibbs':        [['gibbsDH', '-92.2'], ['gibbsDS', '-199'], ['gibbsT', '298']],
  '14:gibbs_k':      [['gkSolve', 'dG'], ['gkK', '1.00e3'], ['gkDG', ''], ['gkT', '298']],
  '14:spontaneity':  [['spDH', '178'], ['spDS', '161']],
  '15:table':        [rowsOf('iceRRows', addIceR, [['H2', '1', '1.00'], ['I2', '1', '1.00']]),
                      rowsOf('icePRows', addIceP, [['HI', '2', '0']]), ['iceKc', '50']],
  '15:q_vs_k':       [rowsOf('iceRRows', addIceR, [['H2', '1', '0.20'], ['I2', '1', '0.20']]),
                      rowsOf('icePRows', addIceP, [['HI', '2', '1.0']]), ['iceKc', '50']],
  '15:le_chatelier': [['lcDist', 'pressure'], ['lcChange', 'increase'], ['lcDn', '-2']],
  '15:kc_kp':        [['kpSolve', 'Kp'], ['kpK', '0.500'], ['kpT', '500'], ['kpDn', '-2']],
  '16:cell_pick':    [{ wait: () => loadHalfCells() }, ['ecH1', 'MnO4-/Mn2+'], ['ecH2', 'Fe3+/Fe2+']],
  '16:cell':         [['ecCat', '0.34'], ['ecAno', '-0.76'], ['ecN', '2']],
  '16:faraday':      [['farSolve', 'mass'], ['farMass', ''], ['farI', '2.00'], ['farT', '1930'], ['farM', '63.55'], ['farN', '2']],
  '16:nernst':       [['nernstE0', '1.10'], ['nernstN', '2'], ['nernstQ', '10'], ['nernstT', '298.15']],
  '17:order':        [['kinC1', '0.10'], ['kinR1', '1.0e-3'], ['kinC2', '0.20'], ['kinR2', '4.0e-3']],
  '17:arrhenius':    [['arrSolve', 'Ea'], ['arrK1', '1.0e-3'], ['arrT1', '300'], ['arrK2', '4.0e-3'], ['arrT2', '320'], ['arrEa', '']],
  '17:halflife':     [['hlSolve', 't_half'], ['hlK', '0.0231'], ['hlT', '']],
  '17:integrated':   [['irOrder', '1'], ['irSolve', 'At'], ['irA0', '0.800'], ['irK', '0.0231'], ['irT', '60'], ['irAt', '']],
  '17:kunits':       [['kinOrder', '2']],
};
function exampleKey() {
  const radio = document.querySelector('#panelBody input[name="ionicAction"]:checked');
  let sub = radio ? radio.value : null;
  for (const id of TYPE_SELECTS) {
    const el = document.getElementById(id);
    if (el) { sub = el.value; break; }
  }
  const key = sub !== null ? `${currentMod}:${sub}` : `${currentMod}`;
  return EXAMPLES[key] ? key : (EXAMPLES[`${currentMod}`] ? `${currentMod}` : null);
}
async function applyExample() {
  const key = exampleKey();
  if (!key) { showPrompt('No example for this option yet.'); return; }
  for (const step of EXAMPLES[key]) {
    if (Array.isArray(step)) setField(step[0], step[1]);
    else if (step.rows) fillRows(step.rows, step.add, step.values);
    else if (step.radio) setRadio(step.radio, step.value);
    else if (step.wait) { try { await step.wait(); } catch (e) { /* shown by the form */ } await new Promise(r => setTimeout(r, 0)); }
  }
  checkButtonState();
  showPrompt('Example filled in — press = Calculate (or Enter).');
}

/* Show result using compact string or detailed steps array based on current mode.
   compact  : string  — one-line answer with units
   detailed : array   — each entry is one step of the working
   warnings : array   — edge case notices shown in amber below the result */
function showOutput(compact, detailed, warnings) {
  const mode = getOutputMode();
  if (mode === 'compact' || !Array.isArray(detailed) || detailed.length === 0) {
    showResult(compact);
  } else {
    const numbered = detailed.map((line, i) => `${i + 1}. ${line}`).join('\n');
    showResult(numbered);
  }
  const w = document.getElementById('screenWarnings');
  if (Array.isArray(warnings) && warnings.length > 0) {
    w.textContent = warnings.map(s => `⚠ ${s}`).join('\n');
    w.style.display = 'block';
  } else {
    w.textContent = ''; w.style.display = 'none';
  }
}

/* ════════════════════════════════════════════════════════
   Calculate button state
════════════════════════════════════════════════════════ */
const _btn = () => document.querySelector('.calc-btn');

function checkButtonState() {
  if (!currentMod) { _setReady(false); return; }
  // Check all text/number inputs inside .field-row (primary required inputs).
  // Selects always have a value. Dynamic rows (.dyn-row) are not required.
  const primary = document.querySelectorAll('#panelBody .field-row input[type="text"], #panelBody .field-row input[type="number"], #panelBody .field-row input:not([type])');
  // "—" placeholders mark solve-for / optional fields, data-optional marks
  // fields with a default (e.g. T = 298.15); the server reports anything missing.
  const required = Array.from(primary).filter(el =>
    !el.hasAttribute('data-optional') && !(el.placeholder || '').startsWith('—'));
  const allFilled = required.every(el => el.value.trim() !== '');
  _setReady(allFilled);
}

function _setReady(yes) {
  const b = _btn();
  if (b.classList.contains('loading')) return; // don't override loading state
  b.classList.toggle('ready', yes);
  b.textContent = '= Calculate';
}

function setButtonLoading() {
  const b = _btn();
  b.classList.remove('ready');
  b.classList.add('loading');
  b.textContent = 'Calculating…';
}

function setButtonDone() {
  const b = _btn();
  b.classList.remove('loading');
  b.textContent = '= Calculate';
  checkButtonState();
}

// Delegate input events from the whole panel so dynamic rows are also covered
document.getElementById('inputPanel').addEventListener('input', checkButtonState);
document.getElementById('inputPanel').addEventListener('change', checkButtonState);
// Enter in any field calculates
document.getElementById('inputPanel').addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey && e.target.matches('input, select')) {
    e.preventDefault();
    calculate();
  }
});

/* ════════════════════════════════════════════════════════
   Screen output helpers
════════════════════════════════════════════════════════ */
function showResult(text) {
  const el = document.getElementById('screenOut');
  el.textContent = text;
  el.className = 'screen-content';
  document.getElementById('screenPrompt').textContent = '';
  const w = document.getElementById('screenWarnings');
  w.style.display = 'none'; w.textContent = '';
}
function showError(text) {
  hideChain();
  const el = document.getElementById('screenOut');
  el.textContent = 'ERROR: ' + text;
  el.className = 'screen-content error';
  document.getElementById('screenPrompt').textContent = '';
  const w = document.getElementById('screenWarnings');
  w.style.display = 'none'; w.textContent = '';
}
function showPrompt(text) {
  document.getElementById('screenPrompt').textContent = text;
}

/* ════════════════════════════════════════════════════════
   Module selector
════════════════════════════════════════════════════════ */
let currentMod = 0;
const MOD_NAMES = {
  1:  'Mole Conversions',
  2:  'Empirical Formula',
  3:  'Equation Balancer',
  4:  'Limiting Reactant',
  5:  'Percent Composition',
  6:  'Volume / Mass',
  7:  'Oxidation Numbers',
  8:  'Atom Economy',
  9:  'Ionic Bonding',
  10: 'Percentage Yield',
  11: 'Periodic Table',
  12: 'Gas Laws',
  13: 'Acid-Base',
  14: 'Thermodynamics',
  15: 'ICE Solver',
  16: 'Electrochemistry',
  17: 'Kinetics',
};

function selectMod(n) {
  currentMod = n;
  lastResult = null;
  hideChain();
  document.getElementById('exampleBtn').classList.remove('hidden');
  document.querySelectorAll('.mod-btn').forEach(b => {
    b.classList.toggle('active', parseInt(b.dataset.mod) === n);
  });
  document.getElementById('panelTitle').textContent = MOD_NAMES[n];
  renderPanel(n);
  showResult(MOD_NAMES[n]);
  showPrompt('Enter values and press = Calculate');
  checkButtonState();
}

/* ════════════════════════════════════════════════════════
   Panel renderers
════════════════════════════════════════════════════════ */
function renderPanel(n) {
  const body = document.getElementById('panelBody');
  body.innerHTML = '';
  const fn = PANELS[n];
  if (fn) fn(body);
}

const PANELS = {
  /* ── 1. Mole Conversions ─────────────────────────── */
  1(body) {
    body.innerHTML = `
      <div class="field-row">
        <label>Conversion</label>
        <select id="moleType" onchange="updateMoleFields()">
          <option value="mass_to_moles">Mass → Moles</option>
          <option value="moles_to_mass">Moles → Mass</option>
          <option value="moles_to_particles">Moles → Particles</option>
          <option value="particles_to_moles">Particles → Moles</option>
          <option value="moles_to_volume">Moles → Volume (STP)</option>
          <option value="volume_to_moles">Volume → Moles (STP)</option>
        </select>
      </div>
      <div id="moleFields"></div>`;
    updateMoleFields();
  },

  /* ── 2. Empirical Formula ────────────────────────── */
  2(body) {
    body.innerHTML = `
      <div class="panel-title" style="margin-bottom:4px">Elements &amp; Masses (g)</div>
      <div class="dynamic-rows" id="empRows"></div>
      <button class="add-row-btn" onclick="addEmpRow()">+ Add Element</button>`;
    addEmpRow(); addEmpRow();
  },

  /* ── 3. Equation Balancer ────────────────────────── */
  3(body) {
    body.innerHTML = `
      <div class="field-row">
        <label>Equation</label>
        <input id="eqInput" type="text" placeholder="H2 + O2 -> H2O" />
      </div>
      <div class="field-row">
        <label>Solution</label>
        <select id="eqMedium">
          <option value="">None (as written)</option>
          <option value="acidic">Acidic (add H⁺ / H₂O)</option>
          <option value="basic">Basic (add OH⁻ / H₂O)</option>
        </select>
      </div>
      <div style="font-size:9px;color:var(--label-fg);margin-top:2px">
        Use -> between sides and " + " between species. Charges: Fe^3+, MnO4^-, SO4^2-; electrons: e-.<br>
        Example: MnO4^- + Fe^2+ -> Mn^2+ + Fe^3+ (acidic)
      </div>`;
  },

  /* ── 4. Limiting Reactant ────────────────────────── */
  4(body) {
    body.innerHTML = `
      <div class="field-row">
        <label>Amounts in</label>
        <select id="limUnit" onchange="document.querySelectorAll('.lim-unit').forEach(s => s.textContent = this.value)">
          <option value="mol">mol</option>
          <option value="g">g</option>
        </select>
      </div>
      <div style="font-size:9px;color:var(--label-fg);margin-bottom:4px">Reactants (formula, coefficient, amount) — leave all coefficients blank to auto-balance</div>
      <div class="dynamic-rows" id="limRRows"></div>
      <button class="add-row-btn" onclick="addLimR()">+ Reactant</button>
      <hr class="sep">
      <div style="font-size:9px;color:var(--label-fg);margin-bottom:4px">Products (name, coefficient)</div>
      <div class="dynamic-rows" id="limPRows"></div>
      <button class="add-row-btn" onclick="addLimP()">+ Product</button>`;
    addLimR(); addLimR();
    addLimP();
  },

  /* ── 5. Percent Composition ──────────────────────── */
  5(body) {
    body.innerHTML = `
      <div class="field-row">
        <label>Formula</label>
        <input id="pctFormula" type="text" placeholder="H2O, CuSO4, Fe2O3..." />
      </div>`;
  },

  /* ── 6. Volume / Mass ────────────────────────────── */
  6(body) {
    body.innerHTML = `
      <div class="field-row">
        <label>Conversion</label>
        <select id="volType" onchange="updateVolFields()">
          <option value="mass_to_volume">Mass → Volume</option>
          <option value="volume_to_mass">Volume → Mass</option>
          <option value="density">Density (from m &amp; V)</option>
        </select>
      </div>
      <div id="volFields"></div>`;
    updateVolFields();
  },

  /* ── 7. Oxidation Numbers ────────────────────────── */
  7(body) {
    body.innerHTML = `
      <div class="field-row">
        <label>Formula</label>
        <input id="oxFormula" type="text" placeholder="KMnO4, H2SO4..." />
      </div>
      <div class="field-row">
        <label>Ion charge</label>
        <input id="oxCharge" type="number" value="0" style="width:60px;flex:none" />
        <span style="font-size:9px;color:var(--label-fg)">(0 = neutral)</span>
      </div>
      <div class="field-row">
        <label style="min-width:auto">
          <input type="checkbox" id="oxPeroxide" style="width:auto;flex:none" />
          &nbsp;Peroxide compound
        </label>
      </div>`;
  },

  /* ── 8. Atom Economy ─────────────────────────────── */
  8(body) {
    body.innerHTML = `
      <div style="font-size:9px;color:var(--label-fg);margin-bottom:4px">Reactants (formula, coefficient)</div>
      <div class="dynamic-rows" id="aeRRows"></div>
      <button class="add-row-btn" onclick="addAER()">+ Reactant</button>
      <hr class="sep">
      <div style="font-size:9px;color:var(--label-fg);margin-bottom:4px">Desired product</div>
      <div class="dyn-row">
        <input class="w-lg" id="aeDesiredFormula" placeholder="formula" />
        <span class="dyn-label">coeff</span>
        <input class="w-sm" id="aeDesiredCoeff" value="1" />
      </div>`;
    addAER(); addAER();
  },

  /* ── 9. Ionic Bonding ────────────────────────────── */
  9(body) {
    body.innerHTML = `
      <div class="radio-row">
        <label><input type="radio" name="ionicAction" value="classify" checked onchange="updateIonicFields()"> Classify bond</label>
        <label><input type="radio" name="ionicAction" value="formula" onchange="updateIonicFields()"> Write formula</label>
      </div>
      <div id="ionicFields"></div>`;
    updateIonicFields();
  },

  /* ── 10. Percentage Yield ────────────────────────── */
  10(body) {
    body.innerHTML = `
      <div class="field-row">
        <label>Find</label>
        <select id="yieldType" onchange="updateYieldFields()">
          <option value="percent">% Yield (actual &amp; theoretical known)</option>
          <option value="actual">Actual yield (% &amp; theoretical known)</option>
          <option value="theoretical">Theoretical yield (actual &amp; % known)</option>
        </select>
      </div>
      <div id="yieldFields"></div>`;
    updateYieldFields();
  },

  /* ── 11. Periodic Table ──────────────────────────── */
  11(body) {
    body.innerHTML = `
      <div class="radio-row">
        <label><input type="radio" name="perType" value="symbol" checked> Symbol</label>
        <label><input type="radio" name="perType" value="name"> Name</label>
        <label><input type="radio" name="perType" value="number"> Atomic #</label>
      </div>
      <div class="field-row">
        <label>Search</label>
        <input id="perQuery" type="text" placeholder="e.g. Fe / Iron / 26" />
      </div>`;
  },

  /* ── 12. Gas Laws ────────────────────────────────── */
  12(body) {
    body.innerHTML = `
      <div class="field-row">
        <label>Law</label>
        <select id="gasType" onchange="updateGasFields()">
          <option value="ideal">Ideal Gas Law (PV=nRT)</option>
          <option value="combined">Combined Gas Law</option>
          <option value="graham">Graham's Effusion</option>
          <option value="dalton">Dalton's Partial Pressure</option>
          <option value="mixing">Gas Mixing (combine 2 samples)</option>
        </select>
      </div>
      <div class="field-row" id="gasUnitRow"><label>Units</label>
        <select id="gasPU" onchange="refreshGasUnits()" title="Pressure unit">
          <option value="atm">atm</option><option value="kPa">kPa</option><option value="Pa">Pa</option>
          <option value="bar">bar</option><option value="mmHg">mmHg</option>
        </select>
        <select id="gasVU" onchange="refreshGasUnits()" title="Volume unit">
          <option value="L">L</option><option value="dm3">dm³</option><option value="mL">mL</option>
          <option value="cm3">cm³</option><option value="m3">m³</option>
        </select>
        <select id="gasTU" onchange="refreshGasUnits()" title="Temperature unit">
          <option value="K">K</option><option value="C">°C</option>
        </select>
      </div>
      <div id="gasFields"></div>`;
    updateGasFields();
  },

  /* ── 13. Acid-Base ───────────────────────────────── */
  13(body) {
    body.innerHTML = `
      <div class="field-row">
        <label>Type</label>
        <select id="abType" onchange="updateABFields()">
          <option value="ph_convert">pH / [H⁺] / [OH⁻] Converter</option>
          <option value="strong_acid">Strong Acid → pH</option>
          <option value="strong_base">Strong Base → pH</option>
          <option value="weak_acid">Weak Acid → pH</option>
          <option value="weak_base">Weak Base → pH</option>
          <option value="buffer">Buffer pH (Henderson-Hasselbalch)</option>
          <option value="titration">Titration (c or V at equivalence)</option>
          <option value="identify">Identify Acid/Base</option>
        </select>
      </div>
      <div id="abFields"></div>`;
    updateABFields();
  },

  /* ── 14. Thermodynamics ──────────────────────────── */
  14(body) {
    body.innerHTML = `
      <div class="field-row">
        <label>Type</label>
        <select id="thermoType" onchange="updateThermoFields()">
          <option value="calorimetry">Calorimetry (q = mcΔT)</option>
          <option value="hess">Hess's Law</option>
          <option value="bond">Bond Enthalpy</option>
          <option value="std_enthalpy">ΔH°rxn from ΔH°f values</option>
          <option value="gibbs">Gibbs Free Energy (ΔG = ΔH − TΔS)</option>
          <option value="gibbs_k">ΔG° ↔ K (ΔG° = −RT ln K)</option>
          <option value="spontaneity">Spontaneity from signs of ΔH &amp; ΔS</option>
        </select>
      </div>
      <div id="thermoFields"></div>`;
    updateThermoFields();
  },

  /* ── 15. ICE Solver ──────────────────────────────── */
  15(body) {
    body.innerHTML = `
      <div class="field-row">
        <label>Tool</label>
        <select id="iceType" onchange="updateIceFields()">
          <option value="table">ICE table (equilibrium concentrations)</option>
          <option value="q_vs_k">Q vs K (which way it shifts)</option>
          <option value="le_chatelier">Le Chatelier's principle</option>
          <option value="kc_kp">Kc ↔ Kp</option>
        </select>
      </div>
      <div id="iceFields"></div>`;
    updateIceFields();
  },

  /* ── 16. Electrochemistry ────────────────────────── */
  16(body) {
    body.innerHTML = `
      <div class="field-row">
        <label>Type</label>
        <select id="ecType" onchange="updateECFields()">
          <option value="cell_pick">Cell from two half-cells (table)</option>
          <option value="cell">Cell Potential &amp; ΔG (enter E° values)</option>
          <option value="faraday">Faraday's Law</option>
          <option value="nernst">Nernst Equation</option>
        </select>
      </div>
      <div id="ecFields"></div>`;
    updateECFields();
  },

  /* ── 17. Kinetics ────────────────────────────────── */
  17(body) {
    body.innerHTML = `
      <div class="field-row">
        <label>Type</label>
        <select id="kinType" onchange="updateKinFields()">
          <option value="order">Reaction Order (2 experiments)</option>
          <option value="arrhenius">Arrhenius (find Ea or k₂)</option>
          <option value="halflife">Half-life ↔ k (1st order)</option>
          <option value="integrated">Integrated rate law (0, 1st, 2nd order)</option>
          <option value="kunits">Rate Constant Units</option>
        </select>
      </div>
      <div id="kinFields"></div>`;
    updateKinFields();
  },
};

/* ════════════════════════════════════════════════════════
   Dynamic sub-panel helpers
════════════════════════════════════════════════════════ */

/* Module 1 */
function updateMoleFields() {
  const t = document.getElementById('moleType').value;
  const needsMolar = ['mass_to_moles', 'moles_to_mass'].includes(t);
  const f = document.getElementById('moleFields');
  const labels = {
    mass_to_moles:       ['Mass (g)', 'M (g/mol) or formula'],
    moles_to_mass:       ['Moles (mol)', 'M (g/mol) or formula'],
    moles_to_particles:  ['Moles (mol)', null],
    particles_to_moles:  ['Particles', null],
    moles_to_volume:     ['Moles (mol)', null],
    volume_to_moles:     ['Volume (L)', null],
  }[t];
  f.innerHTML = `
    <div class="field-row">
      <label>${labels[0]}</label>
      <input id="mA" type="number" step="any" placeholder="value" />
    </div>
    ${labels[1] ? `<div class="field-row"><label>${labels[1]}</label><input id="mB" type="text" placeholder="18.02 or H2O" /></div>
    <div style="font-size:9px;color:var(--label-fg);margin-top:2px">Type a molar mass, or a formula and it is worked out for you.</div>` : ''}`;
}

/* Module 2 */
function addEmpRow() {
  const row = document.createElement('div');
  row.className = 'dyn-row';
  row.innerHTML = `
    <input class="w-sm" placeholder="sym" title="Element symbol" />
    <span class="dyn-label">mass(g)</span>
    <input class="w-md" type="number" step="any" placeholder="0.0" />
    <button class="rem-row-btn" onclick="this.parentElement.remove()">x</button>`;
  document.getElementById('empRows').appendChild(row);
}

/* Module 4 */
function addLimR() {
  const row = document.createElement('div');
  row.className = 'dyn-row';
  row.innerHTML = `
    <input class="w-md" placeholder="reactant" />
    <span class="dyn-label">coeff</span><input class="w-sm" type="number" step="any" placeholder="auto" />
    <span class="dyn-label lim-unit">${document.getElementById('limUnit') ? document.getElementById('limUnit').value : 'mol'}</span><input class="w-sm" type="number" step="any" placeholder="0" />
    <button class="rem-row-btn" onclick="this.parentElement.remove()">x</button>`;
  document.getElementById('limRRows').appendChild(row);
}
function addLimP() {
  const row = document.createElement('div');
  row.className = 'dyn-row';
  row.innerHTML = `
    <input class="w-md" placeholder="product" />
    <span class="dyn-label">coeff</span><input class="w-sm" type="number" step="any" placeholder="auto" />
    <button class="rem-row-btn" onclick="this.parentElement.remove()">x</button>`;
  document.getElementById('limPRows').appendChild(row);
}

/* Module 6 */
function updateVolFields() {
  const t = document.getElementById('volType').value;
  const cfg = {
    mass_to_volume: ['Mass (g)', 'Density (g/mL)'],
    volume_to_mass: ['Volume (mL)', 'Density (g/mL)'],
    density:        ['Mass (g)', 'Volume (mL)'],
  }[t];
  document.getElementById('volFields').innerHTML = `
    <div class="field-row"><label>${cfg[0]}</label><input id="vA" type="number" step="any" /></div>
    <div class="field-row"><label>${cfg[1]}</label><input id="vB" type="number" step="any" /></div>`;
}

/* Module 8 */
function addAER() {
  const row = document.createElement('div');
  row.className = 'dyn-row';
  row.innerHTML = `
    <input class="w-lg" placeholder="formula" />
    <span class="dyn-label">coeff</span>
    <input class="w-sm" type="number" step="any" value="1" />
    <button class="rem-row-btn" onclick="this.parentElement.remove()">x</button>`;
  document.getElementById('aeRRows').appendChild(row);
}

/* Module 9 */
function updateIonicFields() {
  const action = document.querySelector('input[name="ionicAction"]:checked').value;
  const f = document.getElementById('ionicFields');
  if (action === 'classify') {
    f.innerHTML = `
      <div class="field-row"><label>Element 1</label><input id="ion1" type="text" placeholder="Na" /></div>
      <div class="field-row"><label>Element 2</label><input id="ion2" type="text" placeholder="Cl" /></div>`;
  } else {
    f.innerHTML = `
      <div class="field-row"><label>Cation symbol</label><input id="ionCat" type="text" placeholder="Na" /></div>
      <div class="field-row"><label>Cation charge</label><input id="ionCatChg" type="number" value="1" /></div>
      <div class="field-row"><label>Anion symbol</label><input id="ionAni" type="text" placeholder="Cl" /></div>
      <div class="field-row"><label>Anion charge</label><input id="ionAniChg" type="number" value="-1" /></div>`;
  }
}

/* Module 10 */
function updateYieldFields() {
  const t = document.getElementById('yieldType').value;
  const cfg = {
    percent:     ['Actual yield (g)', 'Theoretical yield (g)'],
    actual:      ['% Yield', 'Theoretical yield (g)'],
    theoretical: ['Actual yield (g)', '% Yield'],
  }[t];
  document.getElementById('yieldFields').innerHTML = `
    <div class="field-row"><label>${cfg[0]}</label><input id="yA" type="number" step="any" /></div>
    <div class="field-row"><label>${cfg[1]}</label><input id="yB" type="number" step="any" /></div>`;
}

/* ════════════════════════════════════════════════════════
   Dynamic sub-panel helpers — modules 12-17
════════════════════════════════════════════════════════ */

/* Module 12 – Gas Laws */
const GAS_UNIT_LABEL = { dm3: 'dm³', cm3: 'cm³', m3: 'm³', C: '°C' };
function gasUnit(kind) {
  const el = document.getElementById({ p: 'gasPU', v: 'gasVU', t: 'gasTU' }[kind]);
  const v = el ? el.value : { p: 'atm', v: 'L', t: 'K' }[kind];
  return GAS_UNIT_LABEL[v] || v;
}
function U(kind) { return `<span class="gas-u-${kind}">${gasUnit(kind)}</span>`; }
function refreshGasUnits() {
  ['p', 'v', 't'].forEach(k =>
    document.querySelectorAll('.gas-u-' + k).forEach(s => s.textContent = gasUnit(k)));
}

function updateGasFields() {
  const t = document.getElementById('gasType').value;
  const f = document.getElementById('gasFields');
  const unitRow = document.getElementById('gasUnitRow');
  unitRow.style.display = (t === 'graham') ? 'none' : '';
  ['gasVU', 'gasTU'].forEach(id => document.getElementById(id).style.display = (t === 'dalton') ? 'none' : '');
  if (t === 'ideal') {
    f.innerHTML = `
      <div class="field-row"><label>Solve for</label>
        <select id="gasIdealSolve">
          <option value="P">Pressure P</option>
          <option value="V">Volume V</option>
          <option value="n">Moles n</option>
          <option value="T">Temperature T</option>
        </select>
      </div>
      <div class="field-row"><label>n (mol)</label><input id="gasN" type="number" step="any" placeholder="—" /></div>
      <div class="field-row"><label>V (${U('v')})</label><input id="gasV" type="number" step="any" placeholder="—" /></div>
      <div class="field-row"><label>T (${U('t')})</label><input id="gasT" type="number" step="any" placeholder="—" /></div>
      <div class="field-row"><label>P (${U('p')})</label><input id="gasP" type="number" step="any" placeholder="—" /></div>
      <div style="font-size:9px;color:var(--label-fg);margin-top:2px">Leave the solve-for field blank. R = 8.314 J/(mol·K); units are converted to SI.</div>`;
  } else if (t === 'combined') {
    f.innerHTML = `
      <div class="field-row"><label>Solve for</label>
        <select id="gasCombSolve">
          <option value="P2">P₂</option><option value="V2">V₂</option><option value="T2">T₂</option>
        </select>
      </div>
      <div class="field-row"><label>P₁ (${U('p')})</label><input id="gasP1" type="number" step="any" /></div>
      <div class="field-row"><label>V₁ (${U('v')})</label><input id="gasV1" type="number" step="any" /></div>
      <div class="field-row"><label>T₁ (${U('t')})</label><input id="gasT1" type="number" step="any" /></div>
      <div class="field-row"><label>P₂ (${U('p')})</label><input id="gasP2" type="number" step="any" placeholder="—" /></div>
      <div class="field-row"><label>V₂ (${U('v')})</label><input id="gasV2" type="number" step="any" placeholder="—" /></div>
      <div class="field-row"><label>T₂ (${U('t')})</label><input id="gasT2" type="number" step="any" placeholder="—" /></div>`;
  } else if (t === 'graham') {
    f.innerHTML = `
      <div class="field-row"><label>M₁ (g/mol)</label><input id="gasM1" type="number" step="any" /></div>
      <div class="field-row"><label>M₂ (g/mol)</label><input id="gasM2" type="number" step="any" /></div>
      <div style="font-size:9px;color:var(--label-fg);margin-top:2px">Returns rate₁/rate₂ = √(M₂/M₁)</div>`;
  } else if (t === 'dalton') {
    f.innerHTML = `
      <div style="font-size:9px;color:var(--label-fg);margin-bottom:4px">Partial pressures (${U('p')})</div>
      <div class="dynamic-rows" id="daltonRows"></div>
      <button class="add-row-btn" onclick="addDaltonRow()">+ Add Gas</button>`;
    addDaltonRow(); addDaltonRow();
  } else if (t === 'mixing') {
    f.innerHTML = `
      <div class="field-row"><label>Solve for</label>
        <select id="mixSolve" onchange="updateMixFields()">
          <option value="Pf">Final Pressure P_f</option>
          <option value="Vf">Final Volume V_f</option>
          <option value="Tf">Final Temperature T_f</option>
        </select>
      </div>
      <div style="font-size:9px;color:var(--label-fg);margin:4px 0 2px">Gas Sample 1</div>
      <div class="field-row"><label>P₁ (${U('p')})</label><input id="mixP1" type="number" step="any" /></div>
      <div class="field-row"><label>V₁ (${U('v')})</label><input id="mixV1" type="number" step="any" /></div>
      <div class="field-row"><label>T₁ (${U('t')})</label><input id="mixT1" type="number" step="any" /></div>
      <div style="font-size:9px;color:var(--label-fg);margin:4px 0 2px">Gas Sample 2</div>
      <div class="field-row"><label>P₂ (${U('p')})</label><input id="mixP2" type="number" step="any" /></div>
      <div class="field-row"><label>V₂ (${U('v')})</label><input id="mixV2" type="number" step="any" /></div>
      <div class="field-row"><label>T₂ (${U('t')})</label><input id="mixT2" type="number" step="any" /></div>
      <div style="font-size:9px;color:var(--label-fg);margin:4px 0 2px">Final (combined) state</div>
      <div id="mixFinalFields"></div>`;
    updateMixFields();
  }
}

function updateMixFields() {
  const solve = document.getElementById('mixSolve') ? document.getElementById('mixSolve').value : 'Pf';
  const f = document.getElementById('mixFinalFields');
  if (!f) return;
  const tDefault = gasUnit('t') === '°C' ? '25' : '298.15';
  if (solve === 'Pf') {
    f.innerHTML = `
      <div class="field-row"><label>V_f (${U('v')})</label><input id="mixVf" type="number" step="any" /></div>
      <div class="field-row"><label>T_f (${U('t')})</label><input id="mixTf" type="number" step="any" placeholder="${tDefault}" data-optional /></div>`;
  } else if (solve === 'Vf') {
    f.innerHTML = `
      <div class="field-row"><label>P_f (${U('p')})</label><input id="mixPf" type="number" step="any" /></div>
      <div class="field-row"><label>T_f (${U('t')})</label><input id="mixTf" type="number" step="any" placeholder="${tDefault}" data-optional /></div>`;
  } else if (solve === 'Tf') {
    f.innerHTML = `
      <div class="field-row"><label>P_f (${U('p')})</label><input id="mixPf" type="number" step="any" /></div>
      <div class="field-row"><label>V_f (${U('v')})</label><input id="mixVf" type="number" step="any" /></div>`;
  }
}
function addDaltonRow() {
  const row = document.createElement('div');
  row.className = 'dyn-row';
  row.innerHTML = `<input class="w-md" placeholder="gas name" />
    <span class="dyn-label">P (${U('p')})</span>
    <input class="w-md" type="number" step="any" placeholder="0.0" />
    <button class="rem-row-btn" onclick="this.parentElement.remove()">x</button>`;
  document.getElementById('daltonRows').appendChild(row);
}

/* Module 13 – Acid-Base */
function updateABFields() {
  const t = document.getElementById('abType').value;
  const f = document.getElementById('abFields');
  const cfgs = {
    ph_convert: `
      <div class="field-row"><label>Input type</label>
        <select id="abConvInput">
          <option value="H">Enter [H⁺] (mol/L)</option>
          <option value="OH">Enter [OH⁻] (mol/L)</option>
          <option value="pH">Enter pH</option>
          <option value="pOH">Enter pOH</option>
        </select>
      </div>
      <div class="field-row"><label>Value</label><input id="abVal" type="number" step="any" /></div>`,
    strong_acid: `
      <div class="field-row"><label>Concentration (mol/L)</label><input id="abConc" type="number" step="any" /></div>`,
    strong_base: `
      <div class="field-row"><label>Concentration (mol/L)</label><input id="abConc" type="number" step="any" /></div>`,
    weak_acid: `
      <div class="field-row"><label>Ka</label><input id="abKa" type="number" step="any" placeholder="e.g. 1.8e-5" /></div>
      <div class="field-row"><label>Concentration (mol/L)</label><input id="abConc" type="number" step="any" /></div>`,
    weak_base: `
      <div class="field-row"><label>Kb</label><input id="abKb" type="number" step="any" placeholder="e.g. 1.8e-5" /></div>
      <div class="field-row"><label>Concentration (mol/L)</label><input id="abConc" type="number" step="any" /></div>`,
    buffer: `
      <div class="field-row"><label>Ka</label><input id="abKa" type="number" step="any" /></div>
      <div class="field-row"><label>[Acid] (mol/L)</label><input id="abAcid" type="number" step="any" /></div>
      <div class="field-row"><label>[Base] (mol/L)</label><input id="abBase" type="number" step="any" /></div>`,
    identify: `
      <div class="field-row"><label>Formula</label><input id="abFormula" type="text" placeholder="HCl, NaOH, NaCl..." /></div>`,
    titration: `
      <div class="field-row"><label>Solve for</label>
        <select id="tiSolve" onchange="updateTitrationFields()">
          <option value="analyte_conc">Concentration of analyte</option>
          <option value="titrant_volume">Volume of titrant needed</option>
        </select>
      </div>
      <div class="field-row"><label>Mole ratio analyte : titrant</label>
        <span style="display:flex;gap:4px;align-items:center">
          <input id="tiRa" type="number" step="any" value="1" style="width:48px" /> :
          <input id="tiRt" type="number" step="any" value="1" style="width:48px" />
        </span>
      </div>
      <div class="field-row"><label>Titrant c (mol/dm³)</label><input id="tiCt" type="number" step="any" /></div>
      <div id="tiVars"></div>
      <div class="field-row"><label>Acid / base strength</label>
        <span style="display:flex;gap:4px">
          <select id="tiAcid"><option value="">acid —</option><option value="strong">strong acid</option><option value="weak">weak acid</option></select>
          <select id="tiBase"><option value="">base —</option><option value="strong">strong base</option><option value="weak">weak base</option></select>
        </span>
      </div>
      <div style="font-size:9px;color:var(--label-fg);margin-top:2px">e.g. H₂SO₄ (analyte) + 2NaOH (titrant) → ratio 1 : 2. Strengths are optional (equivalence-point pH).</div>`,
  };
  f.innerHTML = cfgs[t] || '';
  if (t === 'titration') updateTitrationFields();
}
function updateTitrationFields() {
  const solve = document.getElementById('tiSolve').value;
  document.getElementById('tiVars').innerHTML = solve === 'analyte_conc' ? `
      <div class="field-row"><label>Titrant V at equivalence (cm³)</label><input id="tiVt" type="number" step="any" /></div>
      <div class="field-row"><label>Analyte V (cm³)</label><input id="tiVa" type="number" step="any" /></div>` : `
      <div class="field-row"><label>Analyte c (mol/dm³)</label><input id="tiCa" type="number" step="any" /></div>
      <div class="field-row"><label>Analyte V (cm³)</label><input id="tiVa" type="number" step="any" /></div>`;
  checkButtonState();
}

/* Module 14 – Thermodynamics */
function updateThermoFields() {
  const t = document.getElementById('thermoType').value;
  const f = document.getElementById('thermoFields');
  if (t === 'calorimetry') {
    f.innerHTML = `
      <div class="field-row"><label>Solve for</label>
        <select id="calSolve">
          <option value="q">q (J)</option>
          <option value="m">m (g)</option>
          <option value="c">c (J/g·K)</option>
          <option value="dT">ΔT (K)</option>
        </select>
      </div>
      <div class="field-row"><label>q (J)</label><input id="calQ" type="number" step="any" placeholder="—" /></div>
      <div class="field-row"><label>m (g)</label><input id="calM" type="number" step="any" placeholder="—" /></div>
      <div class="field-row"><label>c (J/g·K)</label><input id="calC" type="number" step="any" placeholder="e.g. 4.18" /></div>
      <div class="field-row"><label>ΔT (K)</label><input id="calDT" type="number" step="any" placeholder="—" /></div>
      <div style="font-size:9px;color:var(--label-fg);margin-top:2px">Leave the solve-for field blank.</div>`;
  } else if (t === 'hess') {
    f.innerHTML = `
      <div style="font-size:9px;color:var(--label-fg);margin-bottom:4px">Reactions: ΔH (kJ) × multiplier (neg. to reverse)</div>
      <div class="dynamic-rows" id="hessRows"></div>
      <button class="add-row-btn" onclick="addHessRow()">+ Add Step</button>`;
    addHessRow(); addHessRow();
  } else if (t === 'bond') {
    f.innerHTML = `
      <div style="font-size:9px;color:var(--label-fg);margin-bottom:4px">Bonds broken (reactants side)</div>
      <div class="dynamic-rows" id="bondBrRows"></div>
      <button class="add-row-btn" onclick="addBondRow('bondBrRows')">+ Add Bond</button>
      <hr class="sep">
      <div style="font-size:9px;color:var(--label-fg);margin-bottom:4px">Bonds formed (products side)</div>
      <div class="dynamic-rows" id="bondFmRows"></div>
      <button class="add-row-btn" onclick="addBondRow('bondFmRows')">+ Add Bond</button>`;
    addBondRow('bondBrRows'); addBondRow('bondBrRows');
    addBondRow('bondFmRows'); addBondRow('bondFmRows');
  } else if (t === 'std_enthalpy') {
    f.innerHTML = `
      <div style="font-size:9px;color:var(--label-fg);margin-bottom:4px">Reactants (formula, coefficient, ΔH°f kJ/mol)</div>
      <div class="dynamic-rows" id="hfRRows"></div>
      <button class="add-row-btn" onclick="addHfRow('hfRRows')">+ Reactant</button>
      <hr class="sep">
      <div style="font-size:9px;color:var(--label-fg);margin-bottom:4px">Products (formula, coefficient, ΔH°f kJ/mol)</div>
      <div class="dynamic-rows" id="hfPRows"></div>
      <button class="add-row-btn" onclick="addHfRow('hfPRows')">+ Product</button>
      <div style="font-size:9px;color:var(--label-fg);margin-top:2px">Elements in their standard state (O₂, H₂, C…) have ΔH°f = 0.</div>`;
    addHfRow('hfRRows'); addHfRow('hfRRows');
    addHfRow('hfPRows'); addHfRow('hfPRows');
  } else if (t === 'gibbs_k') {
    f.innerHTML = `
      <div class="field-row"><label>Solve for</label>
        <select id="gkSolve">
          <option value="dG">ΔG° from K</option>
          <option value="K">K from ΔG°</option>
        </select>
      </div>
      <div class="field-row"><label>K</label><input id="gkK" type="number" step="any" placeholder="— if solving for K" /></div>
      <div class="field-row"><label>ΔG° (kJ/mol)</label><input id="gkDG" type="number" step="any" placeholder="— if solving for ΔG°" /></div>
      <div class="field-row"><label>T (K)</label><input id="gkT" type="number" step="any" placeholder="298.15" data-optional /></div>`;
  } else if (t === 'spontaneity') {
    f.innerHTML = `
      <div class="field-row"><label>ΔH (kJ/mol)</label><input id="spDH" type="number" step="any" /></div>
      <div class="field-row"><label>ΔS (J/mol·K)</label><input id="spDS" type="number" step="any" /></div>
      <div style="font-size:9px;color:var(--label-fg);margin-top:2px">Shows when the reaction is spontaneous and the crossover temperature.</div>`;
  } else if (t === 'gibbs') {
    f.innerHTML = `
      <div class="field-row"><label>ΔH (kJ/mol)</label><input id="gibbsDH" type="number" step="any" /></div>
      <div class="field-row"><label>ΔS (J/mol·K)</label><input id="gibbsDS" type="number" step="any" placeholder="e.g. -199" /></div>
      <div class="field-row"><label>T (K)</label><input id="gibbsT" type="number" step="any" placeholder="298.15" data-optional /></div>`;
  }
}
function addHfRow(containerId) {
  const row = document.createElement('div');
  row.className = 'dyn-row';
  row.innerHTML = `<input class="w-md" placeholder="formula" />
    <span class="dyn-label">×</span>
    <input class="w-sm" type="number" step="any" value="1" title="coefficient" />
    <span class="dyn-label">ΔH°f</span>
    <input class="w-md" type="number" step="any" placeholder="kJ/mol" />
    <button class="rem-row-btn" onclick="this.parentElement.remove()">x</button>`;
  document.getElementById(containerId).appendChild(row);
}
function addHessRow() {
  const row = document.createElement('div');
  row.className = 'dyn-row';
  row.innerHTML = `<span class="dyn-label">ΔH(kJ)</span>
    <input class="w-md" type="number" step="any" placeholder="0.0" />
    <span class="dyn-label">×</span>
    <input class="w-sm" type="number" step="any" value="1" title="multiplier (+1 / -1 / 2 etc.)" />
    <button class="rem-row-btn" onclick="this.parentElement.remove()">x</button>`;
  document.getElementById('hessRows').appendChild(row);
}
function addBondRow(containerId) {
  const row = document.createElement('div');
  row.className = 'dyn-row';
  row.innerHTML = `<input class="w-sm" placeholder="C-H" title="Bond label" />
    <span class="dyn-label">count</span>
    <input class="w-sm" type="number" step="1" value="1" />
    <span class="dyn-label">kJ/mol</span>
    <input class="w-md" type="number" step="any" placeholder="auto" title="Leave blank to use built-in table" />
    <button class="rem-row-btn" onclick="this.parentElement.remove()">x</button>`;
  document.getElementById(containerId).appendChild(row);
}

/* Module 15 – ICE Solver */
function updateIceFields() {
  const t = document.getElementById('iceType').value;
  const f = document.getElementById('iceFields');
  const cLabel = t === 'table' ? 'initial' : 'current';
  if (t === 'table' || t === 'q_vs_k') {
    f.innerHTML = `
      <div style="font-size:9px;color:var(--label-fg);margin-bottom:4px">Reactants (name, coeff, ${cLabel} mol/L)</div>
      <div class="dynamic-rows" id="iceRRows"></div>
      <button class="add-row-btn" onclick="addIceR()">+ Reactant</button>
      <hr class="sep">
      <div style="font-size:9px;color:var(--label-fg);margin-bottom:4px">Products (name, coeff, ${cLabel} mol/L)</div>
      <div class="dynamic-rows" id="icePRows"></div>
      <button class="add-row-btn" onclick="addIceP()">+ Product</button>
      <hr class="sep">
      <div class="field-row">
        <label>Kc</label>
        <input id="iceKc" type="number" step="any" placeholder="e.g. 0.04" />
      </div>`;
    addIceR(); addIceR();
    addIceP();
  } else if (t === 'kc_kp') {
    f.innerHTML = `
      <div class="field-row"><label>Convert</label>
        <select id="kpSolve">
          <option value="Kp">Kc → Kp</option>
          <option value="Kc">Kp → Kc</option>
        </select>
      </div>
      <div class="field-row"><label>Known K</label><input id="kpK" type="number" step="any" /></div>
      <div class="field-row"><label>T (K)</label><input id="kpT" type="number" step="any" /></div>
      <div class="field-row"><label>Δn (gas)</label><input id="kpDn" type="number" step="any" placeholder="e.g. -2" /></div>
      <div style="font-size:9px;color:var(--label-fg);margin-top:2px">Δn = moles of gaseous products − moles of gaseous reactants. Kp in atm.</div>`;
  } else if (t === 'le_chatelier') {
    f.innerHTML = `
      <div class="field-row"><label>Change made</label>
        <select id="lcDist" onchange="updateLeChatelierFields()">
          <option value="concentration">Concentration</option>
          <option value="pressure">Pressure</option>
          <option value="temperature">Temperature</option>
          <option value="catalyst">Add a catalyst</option>
        </select>
      </div>
      <div id="lcFields"></div>`;
    updateLeChatelierFields();
  }
  checkButtonState();
}
function updateLeChatelierFields() {
  const t = document.getElementById('lcDist').value;
  const change = `<div class="field-row"><label>Change</label>
      <select id="lcChange"><option value="increase">Increase</option><option value="decrease">Decrease</option></select></div>`;
  document.getElementById('lcFields').innerHTML = {
    concentration: `<div class="field-row"><label>Species</label>
      <select id="lcRole"><option value="reactant">a reactant</option><option value="product">a product</option></select></div>${change}`,
    pressure: `${change}<div class="field-row"><label>Δn (gas)</label><input id="lcDn" type="number" step="any" placeholder="products − reactants" /></div>`,
    temperature: `${change}<div class="field-row"><label>Forward reaction</label>
      <select id="lcRxn"><option value="exothermic">exothermic (ΔH &lt; 0)</option><option value="endothermic">endothermic (ΔH &gt; 0)</option></select></div>`,
    catalyst: `<div style="font-size:9px;color:var(--label-fg);margin-top:2px">A catalyst speeds up both directions equally.</div>`,
  }[t];
  checkButtonState();
}
function addIceR() {
  const row = document.createElement('div');
  row.className = 'dyn-row';
  row.innerHTML = `<input class="w-md" placeholder="name" />
    <span class="dyn-label">coeff</span><input class="w-sm" type="number" step="any" value="1" />
    <span class="dyn-label">[ ](M)</span><input class="w-md" type="number" step="any" value="1" />
    <button class="rem-row-btn" onclick="this.parentElement.remove()">x</button>`;
  document.getElementById('iceRRows').appendChild(row);
}
function addIceP() {
  const row = document.createElement('div');
  row.className = 'dyn-row';
  row.innerHTML = `<input class="w-md" placeholder="name" />
    <span class="dyn-label">coeff</span><input class="w-sm" type="number" step="any" value="1" />
    <span class="dyn-label">[ ](M)</span><input class="w-md" type="number" step="any" value="0" />
    <button class="rem-row-btn" onclick="this.parentElement.remove()">x</button>`;
  document.getElementById('icePRows').appendChild(row);
}

/* Module 16 – Electrochemistry */
function updateECFields() {
  const t = document.getElementById('ecType').value;
  const f = document.getElementById('ecFields');
  if (t === 'cell_pick') {
    f.innerHTML = `
      <div class="field-row"><label>Half-cell 1</label><select id="ecH1"></select></div>
      <div class="field-row"><label>Half-cell 2</label><select id="ecH2"></select></div>
      <div style="font-size:9px;color:var(--label-fg);margin-top:2px">Order doesn't matter — the higher E° becomes the cathode.</div>`;
    loadHalfCells().then(list => {
      ['ecH1', 'ecH2'].forEach((id, k) => {
        const sel = document.getElementById(id);
        if (!sel) return;
        sel.innerHTML = list.map(h =>
          `<option value="${h.label}">${h.label}   (${h.E >= 0 ? '+' : ''}${h.E.toFixed(2)} V)</option>`).join('');
        const pick = list.findIndex(h => h.label === (k === 0 ? 'Cu2+/Cu' : 'Zn2+/Zn'));
        if (pick >= 0) sel.selectedIndex = pick;
      });
    }).catch(() => showError('Could not load the half-cell table.'));
  } else if (t === 'cell') {
    f.innerHTML = `
      <div class="field-row"><label>E°cathode (V)</label><input id="ecCat" type="number" step="any" placeholder="higher E°red" /></div>
      <div class="field-row"><label>E°anode (V)</label><input id="ecAno" type="number" step="any" placeholder="lower E°red" /></div>
      <div class="field-row"><label>n (electrons)</label><input id="ecN" type="number" step="1" placeholder="e.g. 2" /></div>`;
  } else if (t === 'faraday') {
    f.innerHTML = `
      <div class="field-row"><label>Solve for</label>
        <select id="farSolve">
          <option value="mass">Mass deposited (g)</option>
          <option value="current">Current (A)</option>
          <option value="time">Time (s)</option>
          <option value="molar_mass">Molar mass (g/mol)</option>
        </select>
      </div>
      <div class="field-row"><label>Mass (g)</label><input id="farMass" type="number" step="any" placeholder="—" /></div>
      <div class="field-row"><label>Current (A)</label><input id="farI" type="number" step="any" placeholder="—" /></div>
      <div class="field-row"><label>Time (s)</label><input id="farT" type="number" step="any" placeholder="—" /></div>
      <div class="field-row"><label>Molar mass (g/mol)</label><input id="farM" type="number" step="any" placeholder="—" /></div>
      <div class="field-row"><label>n (electrons)</label><input id="farN" type="number" step="1" placeholder="e.g. 2" /></div>
      <div style="font-size:9px;color:var(--label-fg);margin-top:2px">Leave the solve-for field blank.</div>`;
  } else if (t === 'nernst') {
    f.innerHTML = `
      <div class="field-row"><label>E°cell (V)</label><input id="nernstE0" type="number" step="any" /></div>
      <div class="field-row"><label>n (electrons)</label><input id="nernstN" type="number" step="1" placeholder="e.g. 2" /></div>
      <div class="field-row"><label>Q (reaction quotient)</label><input id="nernstQ" type="number" step="any" placeholder="e.g. 0.5" /></div>
      <div class="field-row"><label>T (K)</label><input id="nernstT" type="number" step="any" placeholder="298.15" data-optional /></div>`;
  }
}

let _halfCells = null;
async function loadHalfCells() {
  if (!_halfCells) {
    const res = await fetch('/api/reduction_potentials');
    _halfCells = (await res.json()).half_cells;
  }
  return _halfCells;
}

/* Module 17 – Kinetics */
function updateKinFields() {
  const t = document.getElementById('kinType').value;
  const f = document.getElementById('kinFields');
  if (t === 'order') {
    f.innerHTML = `
      <div style="font-size:9px;color:var(--label-fg);margin-bottom:4px">Experiment 1</div>
      <div class="field-row"><label>[A]₁ (mol/L)</label><input id="kinC1" type="number" step="any" /></div>
      <div class="field-row"><label>Rate₁</label><input id="kinR1" type="number" step="any" /></div>
      <div style="font-size:9px;color:var(--label-fg);margin:4px 0 4px">Experiment 2</div>
      <div class="field-row"><label>[A]₂ (mol/L)</label><input id="kinC2" type="number" step="any" /></div>
      <div class="field-row"><label>Rate₂</label><input id="kinR2" type="number" step="any" /></div>`;
  } else if (t === 'arrhenius') {
    f.innerHTML = `
      <div class="field-row"><label>Solve for</label>
        <select id="arrSolve">
          <option value="Ea">Ea (kJ/mol)</option>
          <option value="k2">k₂ at T₂</option>
        </select>
      </div>
      <div class="field-row"><label>k₁</label><input id="arrK1" type="number" step="any" /></div>
      <div class="field-row"><label>T₁ (K)</label><input id="arrT1" type="number" step="any" /></div>
      <div class="field-row"><label>k₂</label><input id="arrK2" type="number" step="any" placeholder="— if solving for k₂" /></div>
      <div class="field-row"><label>T₂ (K)</label><input id="arrT2" type="number" step="any" /></div>
      <div class="field-row"><label>Ea (J/mol)</label><input id="arrEa" type="number" step="any" placeholder="— if solving for Ea" /></div>`;
  } else if (t === 'halflife') {
    f.innerHTML = `
      <div class="field-row"><label>Solve for</label>
        <select id="hlSolve">
          <option value="t_half">t½ from k</option>
          <option value="k">k from t½</option>
        </select>
      </div>
      <div class="field-row"><label>k (s⁻¹)</label><input id="hlK" type="number" step="any" placeholder="— if solving for k" /></div>
      <div class="field-row"><label>t½ (s)</label><input id="hlT" type="number" step="any" placeholder="— if solving for t½" /></div>`;
  } else if (t === 'integrated') {
    f.innerHTML = `
      <div class="field-row"><label>Order</label>
        <select id="irOrder">
          <option value="0">0 (zero order)</option>
          <option value="1" selected>1 (first order)</option>
          <option value="2">2 (second order)</option>
        </select>
      </div>
      <div class="field-row"><label>Solve for</label>
        <select id="irSolve">
          <option value="At">[A] after time t</option>
          <option value="t">Time to reach [A]t</option>
        </select>
      </div>
      <div class="field-row"><label>[A]₀ (mol/dm³)</label><input id="irA0" type="number" step="any" /></div>
      <div class="field-row"><label>k</label><input id="irK" type="number" step="any" /></div>
      <div class="field-row"><label>t (s)</label><input id="irT" type="number" step="any" placeholder="— if solving for t" /></div>
      <div class="field-row"><label>[A]t (mol/dm³)</label><input id="irAt" type="number" step="any" placeholder="— if solving for [A]t" /></div>`;
  } else if (t === 'kunits') {
    f.innerHTML = `
      <div class="field-row"><label>Overall order</label>
        <select id="kinOrder">
          <option value="0">0</option>
          <option value="1">1</option>
          <option value="2">2</option>
          <option value="3">3</option>
        </select>
      </div>`;
  }
}

/* ════════════════════════════════════════════════════════
   API helpers
════════════════════════════════════════════════════════ */
async function post(url, data) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return res.json();
}

function val(id) {
  const el = document.getElementById(id);
  return el ? el.value.trim() : '';
}

/* ════════════════════════════════════════════════════════
   Calculate dispatcher
════════════════════════════════════════════════════════ */
async function calculate() {
  if (!currentMod) { showError('Select a module first.'); return; }
  if (!_btn().classList.contains('ready')) { showPrompt('Fill in the required fields first.'); return; }
  setButtonLoading();
  try {
    await CALCS[currentMod]();
  } catch(e) {
    showError(e.message || String(e));
  } finally {
    setButtonDone();
  }
}

const CALCS = {
  /* ── 1. Mole Conversions ─────────────────────────── */
  async 1() {
    const t = val('moleType');
    const a = val('mA');
    const b = document.getElementById('mB') ? val('mB') : null;
    if (!a) { showError('Enter a value.'); return; }
    const body = { type: t, a };
    if (b !== null) body.b = b;
    const d = await post('/api/mole', body);
    if (d.error) { showError(d.error); return; }
    render(d);
  },

  /* ── 2. Empirical Formula ────────────────────────── */
  async 2() {
    const rows = document.querySelectorAll('#empRows .dyn-row');
    const elements = [], masses = [];
    rows.forEach(r => {
      const ins = r.querySelectorAll('input');
      if (ins[0].value.trim()) {
        elements.push(ins[0].value.trim());
        masses.push(ins[1].value.trim());
      }
    });
    if (elements.length < 1) { showError('Add at least one element.'); return; }
    const d = await post('/api/empirical', { elements, masses });
    if (d.error) { showError(d.error); return; }
    render(d);
  },

  /* ── 3. Equation Balancer ────────────────────────── */
  async 3() {
    const eq = val('eqInput');
    if (!eq) { showError('Enter an equation.'); return; }
    const d = await post('/api/equation', { equation: eq, medium: val('eqMedium') });
    if (d.error) { showError(d.error); return; }
    render(d);
  },

  /* ── 4. Limiting Reactant ────────────────────────── */
  async 4() {
    const rRows = document.querySelectorAll('#limRRows .dyn-row');
    const pRows = document.querySelectorAll('#limPRows .dyn-row');
    const reactants = [], products = [];
    rRows.forEach(r => {
      const ins = r.querySelectorAll('input');
      if (ins[0].value.trim()) reactants.push({ name: ins[0].value.trim(), coeff: ins[1].value, amount: ins[2].value });
    });
    pRows.forEach(r => {
      const ins = r.querySelectorAll('input');
      if (ins[0].value.trim()) products.push({ name: ins[0].value.trim(), coeff: ins[1].value });
    });
    if (!reactants.length || !products.length) { showError('Need at least 1 reactant and 1 product.'); return; }
    const d = await post('/api/limiting', { reactants, products, unit: val('limUnit') });
    if (d.error) { showError(d.error); return; }
    render(d);
    showChainToYield(d);
  },

  /* ── 5. Percent Composition ──────────────────────── */
  async 5() {
    const formula = val('pctFormula');
    if (!formula) { showError('Enter a formula.'); return; }
    const d = await post('/api/percent', { formula });
    if (d.error) { showError(d.error); return; }
    render(d);
  },

  /* ── 6. Volume / Mass ────────────────────────────── */
  async 6() {
    const t = val('volType'), a = val('vA'), b = val('vB');
    if (!a || !b) { showError('Enter both values.'); return; }
    const d = await post('/api/volume', { type: t, a, b });
    if (d.error) { showError(d.error); return; }
    render(d);
  },

  /* ── 7. Oxidation Numbers ────────────────────────── */
  async 7() {
    const formula = val('oxFormula');
    const charge = parseInt(val('oxCharge') || '0');
    const peroxide = document.getElementById('oxPeroxide').checked;
    if (!formula) { showError('Enter a formula.'); return; }
    const d = await post('/api/oxidation', { formula, charge, peroxide });
    if (d.error) { showError(d.error); return; }
    render(d);
  },

  /* ── 8. Atom Economy ─────────────────────────────── */
  async 8() {
    const rRows = document.querySelectorAll('#aeRRows .dyn-row');
    const reactants = [];
    rRows.forEach(r => {
      const ins = r.querySelectorAll('input');
      if (ins[0].value.trim()) reactants.push({ formula: ins[0].value.trim(), coeff: ins[1].value });
    });
    const desF = val('aeDesiredFormula'), desC = val('aeDesiredCoeff');
    if (!reactants.length || !desF) { showError('Fill in reactants and desired product.'); return; }
    const d = await post('/api/atom_eco', { reactants, desired: { formula: desF, coeff: desC || '1' } });
    if (d.error) { showError(d.error); return; }
    render(d);
  },

  /* ── 9. Ionic Bonding ────────────────────────────── */
  async 9() {
    const action = document.querySelector('input[name="ionicAction"]:checked').value;
    let body = { action };
    if (action === 'classify') {
      body.elem1 = val('ion1'); body.elem2 = val('ion2');
      if (!body.elem1 || !body.elem2) { showError('Enter both elements.'); return; }
    } else {
      body.cation = val('ionCat'); body.cation_charge = val('ionCatChg');
      body.anion  = val('ionAni'); body.anion_charge  = val('ionAniChg');
      if (!body.cation || !body.anion) { showError('Enter cation and anion.'); return; }
    }
    const d = await post('/api/ionic', body);
    if (d.error) { showError(d.error); return; }
    render(d);
  },

  /* ── 10. Percentage Yield ────────────────────────── */
  async 10() {
    const t = val('yieldType'), a = val('yA'), b = val('yB');
    if (!a || !b) { showError('Enter both values.'); return; }
    const d = await post('/api/yield_calc', { type: t, a, b });
    if (d.error) { showError(d.error); return; }
    render(d);
  },

  /* ── 11. Periodic Table ──────────────────────────── */
  async 11() {
    const t = document.querySelector('input[name="perType"]:checked').value;
    const q = val('perQuery');
    if (!q) { showError('Enter a search query.'); return; }
    const d = await post('/api/periodic', { type: t, query: q });
    if (d.error) { showError(d.error); return; }
    if (!d.found) { showError('Element not found.'); return; }
    render(d);
  },

  /* ── 12. Gas Laws ────────────────────────────────── */
  async 12() {
    const t = val('gasType');
    const units = { p_unit: val('gasPU'), v_unit: val('gasVU'), t_unit: val('gasTU') };
    if (t === 'ideal') {
      const solve = val('gasIdealSolve');
      const body = { type: 'ideal', solve, ...units,
        n: val('gasN'), v: val('gasV'), T: val('gasT'), p: val('gasP') };
      const d = await post('/api/gas_laws', body);
      if (d.error) { showError(d.error); return; }
      render(d);
    } else if (t === 'combined') {
      const solve = val('gasCombSolve');
      const body = { type: 'combined', solve, ...units,
        P1: val('gasP1'), V1: val('gasV1'), T1: val('gasT1'),
        P2: val('gasP2'), V2: val('gasV2'), T2: val('gasT2') };
      const d = await post('/api/gas_laws', body);
      if (d.error) { showError(d.error); return; }
      render(d);
    } else if (t === 'graham') {
      const d = await post('/api/gas_laws', { type: 'graham', M1: val('gasM1'), M2: val('gasM2') });
      if (d.error) { showError(d.error); return; }
      render(d);
    } else if (t === 'dalton') {
      const rows = document.querySelectorAll('#daltonRows .dyn-row');
      const gases = [];
      rows.forEach(r => {
        const ins = r.querySelectorAll('input');
        if (ins[1].value.trim()) gases.push({ name: ins[0].value.trim() || '?', p: ins[1].value });
      });
      if (!gases.length) { showError('Add at least one gas.'); return; }
      const d = await post('/api/gas_laws', { type: 'dalton', gases, ...units });
      if (d.error) { showError(d.error); return; }
      render(d);
    } else if (t === 'mixing') {
      const solve = val('mixSolve');
      const body = {
        type: 'mixing', solve, ...units,
        P1: val('mixP1'), V1: val('mixV1'), T1: val('mixT1'),
        P2: val('mixP2'), V2: val('mixV2'), T2: val('mixT2'),
      };
      if (solve === 'Pf') { body.Vf = val('mixVf'); body.Tf = val('mixTf'); }
      if (solve === 'Vf') { body.Pf = val('mixPf'); body.Tf = val('mixTf'); }
      if (solve === 'Tf') { body.Pf = val('mixPf'); body.Vf = val('mixVf'); }
      if (!body.P1 || !body.V1 || !body.T1 || !body.P2 || !body.V2 || !body.T2) {
        showError('Enter all values for both gas samples.'); return;
      }
      const d = await post('/api/gas_laws', body);
      if (d.error) { showError(d.error); return; }
      render(d);
    }
  },

  /* ── 13. Acid-Base ───────────────────────────────── */
  async 13() {
    const t = val('abType');
    let body = { type: t };
    if (t === 'ph_convert') {
      body.input_type = val('abConvInput');
      body.value = val('abVal');
      if (!body.value) { showError('Enter a value.'); return; }
    } else if (t === 'strong_acid' || t === 'strong_base') {
      body.conc = val('abConc');
      if (!body.conc) { showError('Enter concentration.'); return; }
    } else if (t === 'weak_acid') {
      body.Ka = val('abKa'); body.conc = val('abConc');
      if (!body.Ka || !body.conc) { showError('Enter Ka and concentration.'); return; }
    } else if (t === 'weak_base') {
      body.Kb = val('abKb'); body.conc = val('abConc');
      if (!body.Kb || !body.conc) { showError('Enter Kb and concentration.'); return; }
    } else if (t === 'buffer') {
      body.Ka = val('abKa'); body.acid = val('abAcid'); body.base = val('abBase');
      if (!body.Ka || !body.acid || !body.base) { showError('Enter Ka, [acid], and [base].'); return; }
    } else if (t === 'identify') {
      body.formula = val('abFormula');
      if (!body.formula) { showError('Enter a formula.'); return; }
    } else if (t === 'titration') {
      Object.assign(body, { solve: val('tiSolve'), ratio_analyte: val('tiRa'), ratio_titrant: val('tiRt'),
        C_titrant: val('tiCt'), V_titrant: val('tiVt'), V_analyte: val('tiVa'), C_analyte: val('tiCa'),
        acid_strength: val('tiAcid'), base_strength: val('tiBase') });
    }
    const d = await post('/api/acid_base', body);
    if (d.error) { showError(d.error); return; }
    render(d);
  },

  /* ── 14. Thermodynamics ──────────────────────────── */
  async 14() {
    const t = val('thermoType');
    let body = { type: t };
    if (t === 'calorimetry') {
      body.solve = val('calSolve');
      body.q = val('calQ'); body.m = val('calM'); body.c = val('calC'); body.dT = val('calDT');
      const d = await post('/api/thermo', body);
      if (d.error) { showError(d.error); return; }
      render(d);
    } else if (t === 'hess') {
      const rows = document.querySelectorAll('#hessRows .dyn-row');
      const steps = [];
      rows.forEach(r => {
        const ins = r.querySelectorAll('input');
        if (ins[0].value.trim()) steps.push({ dH: ins[0].value, mult: ins[1].value || '1' });
      });
      if (!steps.length) { showError('Add at least one step.'); return; }
      const d = await post('/api/thermo', { type: 'hess', steps });
      if (d.error) { showError(d.error); return; }
      render(d);
    } else if (t === 'bond') {
      const brRows = document.querySelectorAll('#bondBrRows .dyn-row');
      const fmRows = document.querySelectorAll('#bondFmRows .dyn-row');
      const broken = [], formed = [];
      brRows.forEach(r => {
        const ins = r.querySelectorAll('input');
        if (ins[0].value.trim()) broken.push({ bond: ins[0].value.trim(), count: ins[1].value, kJ: ins[2].value });
      });
      fmRows.forEach(r => {
        const ins = r.querySelectorAll('input');
        if (ins[0].value.trim()) formed.push({ bond: ins[0].value.trim(), count: ins[1].value, kJ: ins[2].value });
      });
      if (!broken.length && !formed.length) { showError('Add at least one bond.'); return; }
      const d = await post('/api/thermo', { type: 'bond', broken, formed });
      if (d.error) { showError(d.error); return; }
      render(d);
    } else if (t === 'std_enthalpy') {
      const species = [];
      [['hfRRows', 'reactant'], ['hfPRows', 'product']].forEach(([id, role]) => {
        document.querySelectorAll(`#${id} .dyn-row`).forEach(r => {
          const ins = r.querySelectorAll('input');
          if (ins[0].value.trim() || ins[2].value.trim())
            species.push({ formula: ins[0].value.trim(), coeff: ins[1].value, dHf: ins[2].value, role });
        });
      });
      const d = await post('/api/thermo', { type: 'std_enthalpy', species });
      if (d.error) { showError(d.error); return; }
      render(d);
    } else if (t === 'gibbs_k' || t === 'spontaneity') {
      const body2 = t === 'gibbs_k'
        ? { type: t, solve: val('gkSolve'), K: val('gkK'), dG: val('gkDG'), T: val('gkT') }
        : { type: t, dH: val('spDH'), dS: val('spDS') };
      const d = await post('/api/thermo', body2);
      if (d.error) { showError(d.error); return; }
      render(d);
    } else if (t === 'gibbs') {
      const d = await post('/api/thermo', { type: 'gibbs', dH: val('gibbsDH'), dS: val('gibbsDS'), T: val('gibbsT') || '298.15' });
      if (d.error) { showError(d.error); return; }
      render(d);
    }
  },

  /* ── 15. ICE Solver ──────────────────────────────── */
  async 15() {
    const tool = val('iceType');
    if (tool === 'kc_kp' || tool === 'le_chatelier') {
      const body = tool === 'kc_kp'
        ? { type: tool, solve: val('kpSolve'), K: val('kpK'), T: val('kpT'), delta_n: val('kpDn') }
        : { type: tool, disturbance: val('lcDist'), role: val('lcRole'), change: val('lcChange'),
            delta_n: val('lcDn'), rxn_type: val('lcRxn') };
      const d = await post('/api/ice', body);
      if (d.error) { showError(d.error); return; }
      render(d);
      return;
    }
    const rRows = document.querySelectorAll('#iceRRows .dyn-row');
    const pRows = document.querySelectorAll('#icePRows .dyn-row');
    const reactants = [], products = [];
    rRows.forEach(r => {
      const ins = r.querySelectorAll('input');
      if (ins[0].value.trim()) reactants.push({ name: ins[0].value.trim(), coeff: ins[1].value, initial: ins[2].value });
    });
    pRows.forEach(r => {
      const ins = r.querySelectorAll('input');
      if (ins[0].value.trim()) products.push({ name: ins[0].value.trim(), coeff: ins[1].value, initial: ins[2].value });
    });
    const Kc = val('iceKc');
    if (!reactants.length || !products.length) { showError('Need at least 1 reactant and 1 product.'); return; }
    if (!Kc) { showError('Enter Kc.'); return; }
    const d = await post('/api/ice', { type: tool, reactants, products, Kc });
    if (d.error) { showError(d.error); return; }
    render(d);
  },

  /* ── 16. Electrochemistry ────────────────────────── */
  async 16() {
    const t = val('ecType');
    if (t === 'cell_pick') {
      const d = await post('/api/electrochem', { type: 'cell_pick', half1: val('ecH1'), half2: val('ecH2') });
      if (d.error) { showError(d.error); return; }
      render(d);
    } else if (t === 'cell') {
      const d = await post('/api/electrochem', { type: 'cell', E_cat: val('ecCat'), E_ano: val('ecAno'), n: val('ecN') });
      if (d.error) { showError(d.error); return; }
      render(d);
    } else if (t === 'faraday') {
      const solve = val('farSolve');
      const d = await post('/api/electrochem', { type: 'faraday', solve,
        mass: val('farMass'), I: val('farI'), t: val('farT'), M: val('farM'), n: val('farN') });
      if (d.error) { showError(d.error); return; }
      render(d);
    } else if (t === 'nernst') {
      const d = await post('/api/electrochem', { type: 'nernst',
        E0: val('nernstE0'), n: val('nernstN'), Q: val('nernstQ'), T: val('nernstT') || '298.15' });
      if (d.error) { showError(d.error); return; }
      render(d);
    }
  },

  /* ── 17. Kinetics ────────────────────────────────── */
  async 17() {
    const t = val('kinType');
    if (t === 'order') {
      const d = await post('/api/kinetics', { type: 'order',
        c1: val('kinC1'), c2: val('kinC2'), r1: val('kinR1'), r2: val('kinR2') });
      if (d.error) { showError(d.error); return; }
      render(d);
    } else if (t === 'arrhenius') {
      const solve = val('arrSolve');
      const d = await post('/api/kinetics', { type: 'arrhenius', solve,
        k1: val('arrK1'), T1: val('arrT1'), k2: val('arrK2'), T2: val('arrT2'), Ea: val('arrEa') });
      if (d.error) { showError(d.error); return; }
      render(d);
    } else if (t === 'halflife') {
      const solve = val('hlSolve');
      const d = await post('/api/kinetics', { type: 'halflife', solve, k: val('hlK'), t_half: val('hlT') });
      if (d.error) { showError(d.error); return; }
      render(d);
    } else if (t === 'integrated') {
      const d = await post('/api/kinetics', { type: 'integrated', order: val('irOrder'), solve: val('irSolve'),
        A0: val('irA0'), k: val('irK'), t: val('irT'), At: val('irAt') });
      if (d.error) { showError(d.error); return; }
      render(d);
    } else if (t === 'kunits') {
      const d = await post('/api/kinetics', { type: 'kunits', order: val('kinOrder') });
      if (d.error) { showError(d.error); return; }
      render(d);
    }
  },
};
