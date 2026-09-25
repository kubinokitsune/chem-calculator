from flask import Flask, request, jsonify, send_from_directory
from flask.json.provider import DefaultJSONProvider
import sys, os, math, re

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..')))

from mole_conversions import (mass_to_moles, moles_to_mass, moles_to_particles,
                               particles_to_moles, moles_to_volume, volume_to_moles)
from Empirical_Formula_Calculator import (calculate_empirical_formula, display_empirical_formula,
                                          molecular_formula, combustion_analysis)
from equation_balancer import balance_full, parse_equation
from limiting_reactant import calculate_limiting_reactant
from constants import capitalize_formula as cap
from percent_composition_calculator import compute_percent_composition
from volume_mass_conversions import mass_to_volume, volume_to_mass, density_from_mv
from oxidation_number_calculator import solve_oxidation_numbers
from atom_economy_calculator import calculate_atom_economy
from ionic_bonding_calculator import classify_bond, write_ionic_formula
from percentage_yield_calculator import calc_percentage_yield, calc_actual_yield, calc_theoretical_yield
from Periodic_table import get_element_by_name, get_element_by_symbol, get_element_by_number
from gas_laws import (ideal_gas_find_P, ideal_gas_find_V, ideal_gas_find_n, ideal_gas_find_T,
                      combined_gas_find_P2, combined_gas_find_V2, combined_gas_find_T2,
                      graham_rate_ratio, dalton_total_pressure,
                      ideal_gas_solve, combined_gas_solve, gas_mixing_solve,
                      pressure_to_Pa, volume_to_m3, temperature_to_K)
from acid_base import (all_four, strong_acid_pH, strong_base_pH,
                       weak_acid_pH, weak_base_pH, buffer_pH, identify,
                       equivalence_moles, titration_find_concentration,
                       titration_find_volume, equivalence_point_pH_description,
                       salt_pH, pKa_from_half_equivalence)
import solutions as sol
import isotopes as iso
import uncertainties as unc
from electron_config import configuration_lines, electron_configuration, noble_gas_shorthand
from organic_tools import ihd_lines, index_of_hydrogen_deficiency
from thermodynamics import (cal_q, cal_m, cal_c, cal_dT, hess_law,
                             bond_enthalpy_dH, lookup_bond, gibbs_dG,
                             standard_enthalpy_rxn, gibbs_from_K, K_from_gibbs,
                             spontaneity_analysis, standard_entropy_rxn)
from ice_solver import (build_ice_table, reaction_quotient, compare_Q_K,
                        kc_to_kp, kp_to_kc, le_chatelier_concentration,
                        le_chatelier_pressure, le_chatelier_temperature,
                        le_chatelier_catalyst)
from electrochemistry import (cell_potential, gibbs_from_cell, faraday_mass,
                               faraday_current, faraday_time, faraday_molar_mass,
                               nernst, spontaneity_check, cell_type)
from kinetics import (determine_order, rate_constant_from_experiment, arrhenius_Ea,
                      arrhenius_k2, k_units, irl_concentration, irl_time,
                      arrhenius_from_data)
from constants import REDUCTION_POTENTIALS, get_reduction_potential
from equation_balancer import parse_species
from limiting_reactant import species_molar_mass



def _finite(obj):
    """Replace inf/NaN with None: browsers' JSON.parse rejects Infinity/NaN."""
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    if isinstance(obj, dict):
        return {k: _finite(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_finite(v) for v in obj]
    return obj


class StrictJSONProvider(DefaultJSONProvider):
    def dumps(self, obj, **kwargs):
        return super().dumps(_finite(obj), **kwargs)


# Only ui_interface/static (style.css, app.js, fonts) is served to the browser,
# so app.py, server.log and the calculator modules are never downloadable.
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.json = StrictJSONProvider(app)

# Formulas and equations are short; a request body this big is either a mistake
# or an attempt to make the parsers chew on something enormous. Flask answers
# 413 on its own once the body exceeds this.
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024

# Longest plausible input is a full equation with hydrates and phases, well
# under this. The balancer and formula parsers build matrices from what they
# are given, so cost grows with length -- cap it rather than trusting callers.
_MAX_FIELD_LEN = 512


@app.before_request
def _reject_oversized_fields():
    """Reject absurdly long string inputs before any parser sees them.

    Public deployments get hostile input eventually, and every /api route feeds
    strings to the chemistry parsers. One guard here beats 22 scattered checks.
    """
    if request.method != 'POST' or not request.path.startswith('/api/'):
        return None
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return None
    for key, value in body.items():
        if isinstance(value, str) and len(value) > _MAX_FIELD_LEN:
            return jsonify(error=f"'{key}' is too long "
                                 f"(max {_MAX_FIELD_LEN} characters)"), 400
    return None


R_GAS = 8.314   # J/mol·K
F_CONST = 96485  # C/mol


def _answer(label, value, unit=''):
    return {'label': label, 'value': value, 'unit': unit}


def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


_UNIT_AFTER = re.compile(
    r'=\s*[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?\s*([^,(\n]*)')


def _derive_answers(d):
    """Numeric answers (label, value, unit) for the page's significant-figure
    setting, worked out from a response body. Returns (answers, headline)."""
    compact = d.get('compact') or ''
    a, headline = [], None
    if 'E_cell' in d:
        a = [_answer('E°cell', d['E_cell'], 'V'), _answer('ΔG°', d['dG'], 'kJ/mol')]
        headline = f"{d['spontaneity']} ({d['cell_type']} cell)"
    elif 'pH' in d and 'pOH' in d:
        a = [_answer('pH', d['pH']), _answer('pOH', d['pOH']),
             _answer('[H⁺]', d['H'], 'mol/dm³'), _answer('[OH⁻]', d['OH'], 'mol/dm³')]
    elif 'r_eq' in d:
        a = [_answer('x', d['x'], 'mol/dm³')] + \
            [_answer(f'[{n}]', v, 'mol/dm³') for n, v in zip(d['r_names'] + d['p_names'], d['r_eq'] + d['p_eq'])]
    elif 'direction' in d and 'Q' in d:
        a = [_answer('Q', d['Q'])] if _is_num(d['Q']) else []
        headline = f"Shifts {d['direction']}"
    elif 'total' in d:
        a = [_answer('P_total', d['total'], d.get('unit') or compact.rsplit(' ', 1)[-1])]
    elif 'E' in d and _is_num(d.get('E')):
        a = [_answer('E', d['E'], 'V')]
    elif 'Ea_kJ' in d:
        a = [_answer('Ea', d['Ea_kJ'], 'kJ/mol')]
    elif 'k2' in d:
        a = [_answer('k₂', d['k2'])]
    elif 't_half' in d:
        a = [_answer('t½', d['t_half'], 's')]
    elif 'order' in d and 'k' in d:
        a = [_answer('k', d['k'], d.get('k_units', ''))]
        headline = f"Order ≈ {round(d['order'])}"
    elif 'k' in d and _is_num(d.get('k')):
        a = [_answer('k', d['k'], 's⁻¹')]
    elif 'T_crossover' in d:
        a = [_answer('Crossover T', d['T_crossover'], 'K')] if _is_num(d['T_crossover']) else []
        headline = d.get('result')
    elif _is_num(d.get('result')):
        label = compact.split(' = ')[0].strip() if ' = ' in compact else 'Result'
        unit = d.get('unit_label') or d.get('unit')
        if unit is None:
            m = _UNIT_AFTER.search(compact)
            unit = m.group(1).strip() if m else ''
        a = [_answer(label, d['result'], unit)]
        if 'spontaneous' in d:
            headline = 'Spontaneous' if d['spontaneous'] else (
                'At equilibrium' if d['result'] == 0 else 'Non-spontaneous')
    a = [x for x in a if _is_num(x['value'])]
    return a, headline


@app.after_request
def _security_headers(resp):
    resp.headers.setdefault('X-Content-Type-Options', 'nosniff')
    resp.headers.setdefault('Referrer-Policy', 'no-referrer')
    resp.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    resp.headers.setdefault('Content-Security-Policy',
                            "default-src 'self'; style-src 'self' 'unsafe-inline'; "
                            "script-src 'self' 'unsafe-inline'; img-src 'self' data:; "
                            "font-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'")
    return resp


@app.after_request
def _add_answers(resp):
    if resp.status_code != 200 or not resp.is_json:
        return resp
    d = resp.get_json(silent=True)
    if not isinstance(d, dict) or 'error' in d or 'answers' in d or 'compact' not in d:
        return resp
    answers, headline = _derive_answers(d)
    d['answers'] = answers
    if headline and 'headline' not in d:
        d['headline'] = headline
    resp.set_data(app.json.dumps(d))
    return resp


def _sign(v):
    return f'+{v}' if v > 0 else str(v)


def _err(e):
    """Turn Python exception text into a message a student can act on."""
    msg = str(e)
    if isinstance(e, KeyError):
        msg = f"Missing value: {msg.strip(chr(39))}"
    elif isinstance(e, TypeError) and 'NoneType' in msg:
        msg = 'A required value is missing or not a number.'
    elif msg.startswith('could not convert string to float') or msg.startswith('invalid literal for int()'):
        bad = msg.split(':', 1)[1].strip() if ':' in msg else ''
        msg = ('A required number is blank.' if bad in ("''", '')
               else f'{bad} is not a valid number.')
    elif isinstance(e, ZeroDivisionError):
        msg = 'Division by zero: check that no required value is 0.'
    return jsonify(error=msg), 400


def _molar_mass_input(b):
    """Molar mass typed as a number ('18.02') or a formula ('H2O').
    Returns (value, note)."""
    text = str(b if b is not None else '').strip()
    if not text:
        raise ValueError('A required number is blank.')
    try:
        return float(text), None
    except ValueError:
        pass
    m = species_molar_mass(text)
    if m is None:
        raise ValueError(f"'{text}' is not a number or a chemical formula.")
    shown = cap(text)
    return m, f'Molar mass of {shown} = {m:.3f} g/mol (from atomic masses)'


def _num(d, key, label=None, positive=False, allow_zero=False):
    """Read a required number from the request with a readable error."""
    label = label or key
    raw = d.get(key)
    if raw is None or str(raw).strip() == '':
        raise ValueError(f'Missing value: {label}')
    try:
        v = float(raw)
    except (TypeError, ValueError):
        raise ValueError(f"'{raw}' is not a valid number for {label}.")
    if not math.isfinite(v):
        raise ValueError(f'{label} must be a finite number.')
    if positive and (v < 0 or (v == 0 and not allow_zero)):
        raise ValueError(f'{label} must be {"zero or " if allow_zero else ""}greater than zero.')
    return v


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


# ── 1. Mole Conversions ───────────────────────────────────────────────────────
@app.route('/api/mole', methods=['POST'])
def api_mole():
    d = request.json or {}
    t, a, b = d.get('type'), d.get('a'), d.get('b')
    try:
        a = float(a)
        if t == 'mass_to_moles':
            bv, m_note = _molar_mass_input(b)
            result = mass_to_moles(a, bv)
            compact  = f'Moles = {result:.4g} mol'
            detailed = [
                *([m_note] if m_note else []),
                f'Given: mass = {a} g, molar mass M = {bv:.6g} g/mol',
                'Formula: n = mass / M',
                f'n = {a} / {bv:.6g}',
                f'n = {result:.6g} mol',
            ]
        elif t == 'moles_to_mass':
            bv, m_note = _molar_mass_input(b)
            result = moles_to_mass(a, bv)
            compact  = f'Mass = {result:.4g} g'
            detailed = [
                *([m_note] if m_note else []),
                f'Given: n = {a} mol, molar mass M = {bv:.6g} g/mol',
                'Formula: mass = n × M',
                f'mass = {a} × {bv:.6g}',
                f'mass = {result:.6g} g',
            ]
        elif t == 'moles_to_particles':
            result = moles_to_particles(a)
            compact  = f'Particles = {result:.4g}'
            detailed = [
                f'Given: n = {a} mol',
                'Formula: N = n × Nₐ',
                f'N = {a} × 6.022 × 10²³',
                f'N = {result:.4e} particles',
            ]
        elif t == 'particles_to_moles':
            result = particles_to_moles(a)
            compact  = f'Moles = {result:.4g} mol'
            detailed = [
                f'Given: N = {a:.4e} particles',
                'Formula: n = N / Nₐ',
                f'n = {a:.4e} / 6.022 × 10²³',
                f'n = {result:.6g} mol',
            ]
        elif t == 'moles_to_volume':
            result = moles_to_volume(a)
            compact  = f'Volume = {result:.4g} L'
            detailed = [
                f'Given: n = {a} mol  (STP: 0 °C, 100 kPa)',
                'Formula: V = n × 22.7 L/mol',
                f'V = {a} × 22.7',
                f'V = {result:.6g} L',
            ]
        elif t == 'volume_to_moles':
            result = volume_to_moles(a)
            compact  = f'Moles = {result:.4g} mol'
            detailed = [
                f'Given: V = {a} L  (STP: 0 °C, 100 kPa)',
                'Formula: n = V / 22.7 L/mol',
                f'n = {a} / 22.7',
                f'n = {result:.6g} mol',
            ]
        else:
            return jsonify(error='Unknown conversion type'), 400
        return jsonify(compact=compact, detailed=detailed, warnings=[], result=result)
    except Exception as e:
        return _err(e)


# ── 2. Empirical Formula ──────────────────────────────────────────────────────
@app.route('/api/empirical', methods=['POST'])
def api_empirical():
    d = request.json or {}
    t = d.get('type') or 'masses'
    try:
        if t == 'molecular':
            elements = [cap(e.strip()) for e in d['elements']]
            counts = [int(_num({'v': c}, 'v', f'subscript of {e}', positive=True))
                      for e, c in zip(elements, d.get('counts', []))]
            if len(counts) != len(elements) or not elements:
                return jsonify(error='Give a subscript for each element.'), 400
            empirical = dict(zip(elements, counts))
            Mr = _num(d, 'Mr', 'molecular mass', positive=True)
            molecular, n, emp_mass = molecular_formula(empirical, Mr)
            emp_text = display_empirical_formula(empirical)
            mol_text = display_empirical_formula(molecular)
            detailed = [
                f'Empirical formula: {emp_text}',
                f'Empirical formula mass = {emp_mass:.3f} g/mol',
                f'n = Mr ÷ empirical mass = {Mr:g} ÷ {emp_mass:.3f} = {Mr / emp_mass:.3f} ≈ {n}',
                f'Molecular formula = ({emp_text})_{n} = {mol_text}',
            ]
            return jsonify(formula=mol_text, empirical=emp_text, multiplier=n,
                           empirical_mass=emp_mass, answers=[_answer('n (multiplier)', n)],
                           headline=f'Molecular formula: {mol_text}',
                           compact=f'Molecular formula: {mol_text}', detailed=detailed, warnings=[])

        if t == 'combustion':
            co2 = _num(d, 'CO2', 'mass of CO2', positive=True, allow_zero=True)
            h2o = _num(d, 'H2O', 'mass of H2O', positive=True, allow_zero=True)
            sample = d.get('sample')
            nitrogen = float(d['N']) if str(d.get('N') or '').strip() else 0.0
            elements, masses, notes = combustion_analysis(
                co2, h2o, sample if str(sample or '').strip() else None, nitrogen)
            formula = calculate_empirical_formula(elements, masses)
            display = display_empirical_formula(formula)
            detailed = [
                f'Given: {co2:g} g CO2, {h2o:g} g H2O'
                + (f', sample {float(sample):g} g' if str(sample or '').strip() else ''),
                'All the carbon ends up as CO2 and all the hydrogen as H2O:',
                *[f'  {el}: {m:.4f} g' for el, m in zip(elements, masses)],
                f'Empirical formula: {display}',
            ]
            answers = [_answer(f'mass of {el}', m, 'g') for el, m in zip(elements, masses)]
            out = jsonify(formula=display, elements=elements, masses=masses, answers=answers,
                          headline=f'Empirical formula: {display}',
                          compact=f'Empirical formula: {display}', detailed=detailed, warnings=notes)
            return out

        elements = [cap(e.strip()) for e in d['elements']]
        masses   = [float(m) for m in d['masses']]
        formula  = calculate_empirical_formula(elements, masses)
        display  = display_empirical_formula(formula)
        compact  = f'Empirical formula: {display}'

        # Reconstruct steps manually
        from Periodic_table import get_element_by_symbol
        moles = []
        step_moles = []
        for el, mass in zip(elements, masses):
            elem = get_element_by_symbol(el)
            aw = elem['atomic_weight'] if elem else 1.0
            mol = mass / aw
            moles.append(mol)
            step_moles.append(f'  {el}: {mass} g ÷ {aw:.3f} g/mol = {mol:.4f} mol')
        min_mol = min(moles)
        ratios = [m / min_mol for m in moles]
        step_ratios = [f'  {el}: {m:.4f} / {min_mol:.4f} = {r:.4f}'
                       for el, m, r in zip(elements, moles, ratios)]
        mult = formula[elements[moles.index(min_mol)]]  # smallest-mole element's subscript = multiplier
        if mult > 1:
            step_ratios.append(f'Ratios are not all whole numbers — multiply by {mult}:')
            step_ratios += [f'  {el}: {r:.4f} × {mult} = {r * mult:.3f} ≈ {formula[el]}'
                            for el, r in zip(elements, ratios)]
        else:
            step_ratios.append('Round to whole numbers: ' +
                               ', '.join(f'{el} = {formula[el]}' for el in elements))
        detailed = [
            f'Given masses: {", ".join(f"{el}={m}g" for el,m in zip(elements,masses))}',
            'Convert to moles (mass ÷ atomic mass):',
            *step_moles,
            f'Smallest mole value: {min_mol:.4f} mol ({elements[moles.index(min_mol)]})',
            'Divide all by smallest:',
            *step_ratios,
            f'Empirical formula: {display}',
        ]
        return jsonify(formula=display, compact=compact, detailed=detailed, warnings=[])
    except Exception as e:
        return _err(e)


# ── 3. Equation Balancer ──────────────────────────────────────────────────────
@app.route('/api/equation', methods=['POST'])
def api_equation():
    d = request.json or {}
    eq = (d.get('equation') or '').strip()
    medium = (d.get('medium') or '').strip() or None
    try:
        reactants, products = parse_equation(eq)
        res = balance_full(reactants, products, medium)
        balanced = res['equation']
        compact  = f'Balanced: {balanced}'
        fmt = lambda terms: ', '.join(f'{s.display()} = {c}' for c, s in terms)
        detailed = [
            f'Unbalanced: {eq}',
            'Species: ' + ', '.join(s.display() for s in
                                    [x for _, x in res['reactants']] + [x for _, x in res['products']]),
            'Method: conserve every element' + (' and total charge' if any(
                s.charge for _, s in res['reactants'] + res['products']) else ''),
            f'Reactant coefficients: {fmt(res["reactants"])}',
            f'Product  coefficients: {fmt(res["products"])}',
        ]
        warnings = list(res['notes'])
        if res['added']:
            detailed.append(f'Added for {medium} solution: {", ".join(res["added"])}')
        detailed.append(f'Balanced equation: {balanced}')
        return jsonify(balanced=balanced, added=res['added'],
                       reactants=[{'species': s.display(), 'coeff': c} for c, s in res['reactants']],
                       products=[{'species': s.display(), 'coeff': c} for c, s in res['products']],
                       compact=compact, detailed=detailed, warnings=warnings)
    except Exception as e:
        return _err(e)


# ── 4. Limiting Reactant ──────────────────────────────────────────────────────
@app.route('/api/limiting', methods=['POST'])
def api_limiting():
    d = request.json or {}
    try:
        rd, pd = d['reactants'], d['products']
        unit = d.get('unit') or 'mol'
        res = calculate_limiting_reactant(
            [r['name'] for r in rd], [r.get('amount', r.get('moles')) for r in rd],
            [p['name'] for p in pd],
            [r.get('coeff') for r in rd], [p.get('coeff') for p in pd], unit)
        g = lambda v: f'{v:.4g} g' if v is not None else '—'
        lim = ' and '.join(res['limiting'])
        compact = f'Limiting reactant: {lim}'
        detailed = [f'Equation: {res["equation"]}'
                    + ('  (coefficients balanced automatically)' if res['balanced'] else '')]
        if unit == 'g':
            detailed.append('Convert masses to moles (n = m / M):')
            detailed += [f'  {r["name"]}: {r["grams"]:.4g} g ÷ {r["molar_mass"]:.3f} g/mol = {r["moles"]:.4g} mol'
                         for r in res['reactants']]
        detailed.append('Mole ratios (moles ÷ coefficient):')
        detailed += [f'  {r["name"]}: {r["moles"]:.4g} ÷ {r["coeff"]:g} = {r["ratio"]:.4g}'
                     for r in res['reactants']]
        detailed.append(f'Smallest ratio → limiting reactant: {lim} ({res["extent"]:.4g})')
        if len(res['limiting']) > 1:
            detailed.append('  (reactants are in the exact stoichiometric ratio)')
        detailed.append('Left over after reaction:')
        detailed += [f'  {r["name"]}: {r["leftover_mol"]:.4g} mol  ({g(r["leftover_g"])})'
                     for r in res['reactants']]
        detailed.append('Theoretical yield (coefficient × smallest ratio):')
        detailed += [f'  {p["name"]}: {p["coeff"]:g} × {res["extent"]:.4g} = {p["moles"]:.4g} mol  ({g(p["grams"])})'
                     for p in res['products']]
        warnings = list(res['warnings'])
        answers = [_answer(f'{p["name"]} (theoretical)', p['grams'], 'g') if p['grams'] is not None
                   else _answer(f'{p["name"]} (theoretical)', p['moles'], 'mol') for p in res['products']]
        return jsonify(limiting=res['limiting'][0], limiting_all=res['limiting'],
                       answers=answers, headline=compact,
                       equation=res['equation'], balanced=res['balanced'], unit=unit,
                       leftovers={r['name']: round(r['leftover_mol'], 6) for r in res['reactants']},
                       leftovers_g={r['name']: r['leftover_g'] for r in res['reactants']},
                       yields={p['name']: round(p['moles'], 6) for p in res['products']},
                       yields_g={p['name']: p['grams'] for p in res['products']},
                       compact=compact, detailed=detailed, warnings=warnings)
    except Exception as e:
        return _err(e)


# ── 5. Percent Composition ────────────────────────────────────────────────────
@app.route('/api/percent', methods=['POST'])
def api_percent():
    d = request.json or {}
    try:
        d['formula'] = cap(d['formula'].strip())
        mm, percents = compute_percent_composition(d['formula'])
        percents_r = {k: round(v, 2) for k, v in percents.items()}
        compact  = f'{d["formula"]}: ' + ', '.join(f'{el}={p:.2f}%' for el, p in percents_r.items())
        detailed = [
            f'Formula: {d["formula"]}',
            f'Molar mass: {mm:.3f} g/mol',
            'Percent composition:',
            *[f'  {el}: {p:.2f}%' for el, p in percents_r.items()],
            f'Sum: {sum(percents.values()):.1f}%',
        ]
        answers = [_answer(f'M({d["formula"]})', mm, 'g/mol')] + \
                  [_answer(f'% {el}', v, '%') for el, v in percents.items()]
        return jsonify(formula=d['formula'], molar_mass=round(mm, 3), answers=answers,
                       percents=percents_r, compact=compact, detailed=detailed, warnings=[])
    except Exception as e:
        return _err(e)


# ── 6. Volume / Mass ──────────────────────────────────────────────────────────
@app.route('/api/volume', methods=['POST'])
def api_volume():
    d = request.json or {}
    t, a, b = d.get('type'), d.get('a'), d.get('b')
    try:
        a, b = float(a), float(b)
        if t == 'mass_to_volume':
            if b <= 0: return jsonify(error='Density must be > 0'), 400
            result = mass_to_volume(a, b)
            compact  = f'Volume = {result:.4g} mL'
            detailed = [
                f'Given: mass = {a} g, density ρ = {b} g/mL',
                'Formula: V = m / ρ',
                f'V = {a} / {b}',
                f'V = {result:.4g} mL',
            ]
        elif t == 'volume_to_mass':
            if b <= 0: return jsonify(error='Density must be > 0'), 400
            result = volume_to_mass(a, b)
            compact  = f'Mass = {result:.4g} g'
            detailed = [
                f'Given: volume = {a} mL, density ρ = {b} g/mL',
                'Formula: m = V × ρ',
                f'm = {a} × {b}',
                f'm = {result:.4g} g',
            ]
        elif t == 'density':
            if b <= 0: return jsonify(error='Volume must be > 0'), 400
            result = density_from_mv(a, b)
            compact  = f'Density = {result:.4g} g/mL'
            detailed = [
                f'Given: mass = {a} g, volume = {b} mL',
                'Formula: ρ = m / V',
                f'ρ = {a} / {b}',
                f'ρ = {result:.4g} g/mL',
            ]
        else:
            return jsonify(error='Unknown type'), 400
        return jsonify(result=result, unit={'mass_to_volume':'mL','volume_to_mass':'g','density':'g/mL'}[t],
                       compact=compact, detailed=detailed, warnings=[])
    except Exception as e:
        return _err(e)


# ── 7. Oxidation Numbers ──────────────────────────────────────────────────────
@app.route('/api/oxidation', methods=['POST'])
def api_oxidation():
    d = request.json or {}
    try:
        charge   = int(d.get('charge', 0))
        peroxide = bool(d.get('peroxide', False))
        d['formula'] = cap(d['formula'].strip())
        numbers  = solve_oxidation_numbers(d['formula'], charge, peroxide)
        numbers_r = {k: round(v, 4) for k, v in numbers.items()}
        compact   = ', '.join(f'{el}: {_sign(v)}' for el, v in numbers_r.items())
        detailed  = [
            f'Formula: {d["formula"]},  overall charge: {_sign(charge)}',
            'Rules applied in order:',
            '  1. Free elements → 0',
            '  2. Monatomic ions → their charge',
            '  3. O = −2  (peroxides: −1)' + ('  ← peroxide flag set' if peroxide else ''),
            '  4. H = +1 (with non-metals), H = −1 (metal hydrides)',
            '  5. Group 1 metals = +1,  Group 2 = +2',
            '  6. Remaining element solved algebraically: sum = overall charge',
            'Results:',
            *[f'  {el}: {_sign(v)}' for el, v in numbers_r.items()],
        ]
        warnings = ['Peroxide compound: O assigned −1 instead of −2'] if peroxide else []
        return jsonify(formula=d['formula'], charge=charge, numbers=numbers_r,
                       compact=compact, detailed=detailed, warnings=warnings)
    except Exception as e:
        return _err(e)


# ── 8. Atom Economy ───────────────────────────────────────────────────────────
@app.route('/api/atom_eco', methods=['POST'])
def api_atom_eco():
    d = request.json or {}
    try:
        rd = d['reactants']
        desired = d['desired']
        formulas = [cap(r['formula'].strip()) for r in rd]
        desired['formula'] = cap(desired['formula'].strip())
        coeffs   = [float(r['coeff']) for r in rd]
        des_c    = float(desired['coeff'])
        ae, mw_d, mw_r = calculate_atom_economy(formulas, coeffs, desired['formula'], des_c)
        compact  = f'Atom economy = {ae:.2f}%'
        detailed = [
            f'Desired product: {desired["formula"]}  (coeff: {des_c:.4g})',
            f'MW of desired product: {mw_d:.3f} g/mol',
            'Reactants entered:',
            *[f'  {f}  (coeff: {c:.4g})' for f, c in zip(formulas, coeffs)],
            f'Total reactant MW (all, scaled by coeff): {mw_r:.3f} g/mol',
            'Formula: AE = MW(desired) / MW(reactants) × 100',
            f'AE = {mw_d:.3f} / {mw_r:.3f} × 100',
            f'AE = {ae:.2f}%',
        ]
        warnings = ['Atom economy < 50% — significant waste produced'] if ae < 50 else []
        return jsonify(atom_economy=round(ae, 2), mw_desired=round(mw_d, 3),
                       answers=[_answer('Atom economy', ae, '%')],
                       mw_reactants=round(mw_r, 3), compact=compact, detailed=detailed, warnings=warnings)
    except Exception as e:
        return _err(e)


# ── 9. Ionic Bonding ──────────────────────────────────────────────────────────
@app.route('/api/ionic', methods=['POST'])
def api_ionic():
    d = request.json or {}
    action = d.get('action')
    try:
        if action == 'classify':
            d['elem1'], d['elem2'] = cap(d['elem1'].strip()), cap(d['elem2'].strip())
            bond_type, en1, en2, diff = classify_bond(d['elem1'], d['elem2'])
            compact  = f'Bond type: {bond_type}  (ΔEN = {diff:.2f})'
            detailed = [
                f'Element 1: {d["elem1"]},  electronegativity: {en1:.2f}',
                f'Element 2: {d["elem2"]},  electronegativity: {en2:.2f}',
                f'ΔEN = |{en1:.2f} − {en2:.2f}| = {diff:.2f}',
                'Classification thresholds:',
                '  ΔEN < 0.4  → nonpolar covalent',
                '  0.4 ≤ ΔEN < 1.7 → polar covalent',
                '  ΔEN ≥ 1.7  → ionic',
                f'Result: {bond_type}',
            ]
            return jsonify(bond_type=bond_type, en1=round(en1,2), en2=round(en2,2),
                           diff=round(diff,2), elem1=d['elem1'], elem2=d['elem2'],
                           compact=compact, detailed=detailed, warnings=[])
        else:
            d['cation'], d['anion'] = cap(d['cation'].strip()), cap(d['anion'].strip())
            cat_c = int(d['cation_charge'])
            ani_c = int(d['anion_charge'])
            formula = write_ionic_formula(d['cation'], cat_c, d['anion'], ani_c)
            compact  = f'Ionic formula: {formula}'
            detailed = [
                f'Cation: {d["cation"]}  (charge: {_sign(cat_c)})',
                f'Anion:  {d["anion"]}  (charge: {_sign(ani_c)})',
                'Criss-cross method: use |charge| of each ion as the subscript of the other',
                f'  {d["cation"]} gets subscript |{ani_c}| = {abs(ani_c)}',
                f'  {d["anion"]}  gets subscript |{cat_c}| = {abs(cat_c)}',
                'Simplify subscripts by dividing by their GCD',
                f'Ionic formula: {formula}',
            ]
            return jsonify(formula=formula, cation=d['cation'], anion=d['anion'],
                           cation_charge=cat_c, anion_charge=ani_c,
                           compact=compact, detailed=detailed, warnings=[])
    except Exception as e:
        return _err(e)


# ── 10. Percentage Yield ──────────────────────────────────────────────────────
@app.route('/api/yield_calc', methods=['POST'])
def api_yield():
    d = request.json or {}
    t, a, b = d.get('type'), d.get('a'), d.get('b')
    try:
        a, b = float(a), float(b)
        warnings = []
        if t == 'percent':
            if b <= 0: return jsonify(error='Theoretical yield must be > 0'), 400
            result = calc_percentage_yield(a, b)
            compact  = f'% Yield = {result:.4g}%'
            detailed = [
                f'Given: actual yield = {a} g,  theoretical yield = {b} g',
                'Formula: % yield = (actual / theoretical) × 100',
                f'= ({a} / {b}) × 100',
                f'= {result:.4g}%',
            ]
            if result > 100:
                warnings.append('Yield > 100% — check for impurities or measurement error')
        elif t == 'actual':
            if b <= 0: return jsonify(error='Theoretical yield must be > 0'), 400
            result = calc_actual_yield(a, b)
            compact  = f'Actual yield = {result:.4g} g'
            detailed = [
                f'Given: % yield = {a}%,  theoretical yield = {b} g',
                'Formula: actual = (% yield / 100) × theoretical',
                f'= ({a} / 100) × {b}',
                f'= {result:.4g} g',
            ]
        elif t == 'theoretical':
            if b <= 0: return jsonify(error='% yield must be > 0'), 400
            result = calc_theoretical_yield(a, b)
            compact  = f'Theoretical yield = {result:.4g} g'
            detailed = [
                f'Given: actual yield = {a} g,  % yield = {b}%',
                'Formula: theoretical = actual / (% yield / 100)',
                f'= {a} / ({b} / 100)',
                f'= {result:.4g} g',
            ]
        else:
            return jsonify(error='Unknown type'), 400
        return jsonify(result=result, compact=compact, detailed=detailed, warnings=warnings)
    except Exception as e:
        return _err(e)


# ── 11. Periodic Table ────────────────────────────────────────────────────────
@app.route('/api/periodic', methods=['POST'])
def api_periodic():
    d = request.json or {}
    t, q = d.get('type'), d.get('query', '').strip()
    try:
        method_label = {'symbol': 'symbol', 'name': 'name', 'number': 'atomic number'}.get(t, t)
        if t == 'symbol':   elem = get_element_by_symbol(q)
        elif t == 'name':   elem = get_element_by_name(q)
        elif t == 'number': elem = get_element_by_number(int(q))
        else: return jsonify(error='Unknown search type'), 400
        if not elem:
            return jsonify(found=False)
        name = elem['name'].capitalize()
        compact  = f'{name} ({elem["symbol"]}),  Z = {elem["number"]},  Ar = {elem["atomic_weight"]} g/mol'
        detailed = [
            f'Search method: by {method_label} → "{q}"',
            f'Name:          {name}',
            f'Symbol:        {elem["symbol"]}',
            f'Atomic number: {elem["number"]}',
            f'Atomic weight: {elem["atomic_weight"]} g/mol',
        ]
        return jsonify(found=True, number=elem['number'], symbol=elem['symbol'],
                       name=name, atomic_weight=elem['atomic_weight'],
                       compact=compact, detailed=detailed, warnings=[])
    except Exception as e:
        return _err(e)


# ── 12. Gas Laws ──────────────────────────────────────────────────────────────
@app.route('/api/gas_laws', methods=['POST'])
def api_gas_laws():
    d = request.json or {}
    t = d.get('type')
    R = 0.08206  # L·atm/mol·K
    try:
        pu = d.get('p_unit') or 'atm'
        vu = d.get('v_unit') or 'L'
        tu = d.get('t_unit') or 'K'
        tl = '°C' if tu == 'C' else 'K'
        vl = {'dm3': 'dm³', 'cm3': 'cm³', 'm3': 'm³'}.get(vu, vu)
        unit_of = {'P': pu, 'V': vl, 'n': 'mol', 'T': tl}
        raw_of = {'P': pu, 'V': vu, 'n': 'mol', 'T': tl}
        num = lambda k: float(d[k]) if str(d.get(k, '')).strip() != '' else None
        si_note = []
        if (pu, vu, tu) != ('Pa', 'm3', 'K'):
            si_note = ['Convert to SI units (Pa, m³, K):']

        if t == 'ideal':
            solve = d.get('solve')
            vals = {'P': num('p'), 'V': num('v'), 'n': num('n'), 'T': num('T')}
            given = {k: v for k, v in vals.items() if k != solve}
            result = ideal_gas_solve(solve, P_unit=pu, V_unit=vu, T_unit=tu, **given)
            unit, raw_unit = unit_of[solve], raw_of[solve]
            conv = []
            if si_note:
                conv = si_note[:]
                if 'P' in given: conv.append(f'  P = {given["P"]} {pu} = {pressure_to_Pa(given["P"], pu):.6g} Pa')
                if 'V' in given: conv.append(f'  V = {given["V"]} {vl} = {volume_to_m3(given["V"], vu):.6g} m³')
                if 'T' in given: conv.append(f'  T = {given["T"]} {tl} = {temperature_to_K(given["T"], tu):.6g} K')
            rearr = {'P': 'P = nRT / V', 'V': 'V = nRT / P', 'n': 'n = PV / RT', 'T': 'T = PV / nR'}[solve]
            detailed = [
                'Law: Ideal Gas Law — PV = nRT',
                'Given: ' + ', '.join(f'{k} = {v} {unit_of[k]}' for k, v in given.items()),
                *conv,
                'R = 8.314 J/(mol·K)',
                f'Rearranging: {rearr}',
                f'{solve} = {result:.4g} {unit}',
            ]
            compact = f'{solve} = {result:.4g} {unit}'
            return jsonify(result=result, unit=raw_unit, unit_label=unit, compact=compact, detailed=detailed, warnings=[])

        elif t == 'combined':
            solve = d.get('solve')
            vals = {k: num(k) for k in ('P1', 'V1', 'T1', 'P2', 'V2', 'T2') if k != solve}
            result = combined_gas_solve(solve, P_unit=pu, V_unit=vu, T_unit=tu, **vals)
            unit, raw_unit = unit_of[solve[0]], raw_of[solve[0]]
            detailed = [
                'Law: Combined Gas Law — P₁V₁/T₁ = P₂V₂/T₂',
                'Given: ' + ', '.join(f'{k} = {v} {unit_of[k[0]]}' for k, v in vals.items()),
            ]
            if tu == 'C':
                detailed.append('Temperatures must be in kelvin: T(K) = T(°C) + 273.15')
                detailed += [f'  {k} = {v} °C = {v + 273.15:.2f} K' for k, v in vals.items() if k[0] == 'T']
            detailed += [
                f'Solve for {solve} (P and V units cancel, so they stay as {pu} and {vl})',
                f'{solve} = {result:.4g} {unit}',
            ]
            compact = f'{solve} = {result:.4g} {unit}'
            return jsonify(result=result, unit=raw_unit, unit_label=unit, compact=compact, detailed=detailed, warnings=[])

        elif t == 'mixing':
            solve = d.get('solve')
            result, n1, n2 = gas_mixing_solve(
                solve, num('P1'), num('V1'), num('T1'), num('P2'), num('V2'), num('T2'),
                Pf=num('Pf'), Vf=num('Vf'), Tf=num('Tf') if num('Tf') is not None else
                (25.0 if tu == 'C' else 298.15),
                P_unit=pu, V_unit=vu, T_unit=tu)
            unit, raw_unit = unit_of[solve[0]], raw_of[solve[0]]
            label = {'Pf': 'P_final', 'Vf': 'V_final', 'Tf': 'T_final'}[solve]
            compact = f'{label} = {result:.4g} {unit}'
            detailed = [
                'Gas Mixing — two samples combined',
                f'Gas 1: P={num("P1")} {pu}, V={num("V1")} {vl}, T={num("T1")} {tl}',
                f'Gas 2: P={num("P2")} {pu}, V={num("V2")} {vl}, T={num("T2")} {tl}',
                'Step 1 — moles in each sample, n = PV/RT (SI units, R = 8.314):',
                f'  n₁ = {n1:.4g} mol,  n₂ = {n2:.4g} mol,  n_total = {n1 + n2:.4g} mol',
                'Step 2 — apply PV = nRT to the combined sample',
                f'{label} = {result:.4g} {unit}',
            ]
            return jsonify(result=result, unit=raw_unit, unit_label=unit, n1=n1, n2=n2,
                           compact=compact, detailed=detailed, warnings=[])

        elif t == 'graham':
            M1, M2 = float(d['M1']), float(d['M2'])
            if M1 <= 0 or M2 <= 0:
                return jsonify(error='Molar masses must be positive'), 400
            result = graham_rate_ratio(M1, M2)
            compact  = f'Rate₁/Rate₂ = {result:.4g}'
            faster   = 'Gas 1 effuses faster than Gas 2' if result > 1 else 'Gas 2 effuses faster than Gas 1'
            detailed = [
                "Law: Graham's Law of Effusion",
                f'Given: M₁ = {M1} g/mol,  M₂ = {M2} g/mol',
                'Formula: rate₁/rate₂ = √(M₂/M₁)',
                f'= √({M2} / {M1})',
                f'= √{M2/M1:.4g}',
                f'= {result:.4g}',
                faster,
            ]
            return jsonify(result=result, compact=compact, detailed=detailed, warnings=[])

        elif t == 'dalton':
            gases    = d.get('gases', [])
            partials = [{'name': g['name'], 'p': float(g['p'])} for g in gases]
            if not partials:
                return jsonify(error='Add at least one gas.'), 400
            if any(g['p'] < 0 for g in partials):
                return jsonify(error='Partial pressures cannot be negative.'), 400
            pressure_to_Pa(0, pu)   # validates the unit
            total    = dalton_total_pressure([g['p'] for g in partials])
            compact  = f'P_total = {total:.4g} {pu}'
            parts_str = ' + '.join(f'{g["p"]:.4g}' for g in partials)
            detailed = [
                "Law: Dalton's Law of Partial Pressures",
                'Formula: P_total = Σ P_i',
                *[f'  P({g["name"]}) = {g["p"]:.4g} {pu}' for g in partials],
                f'P_total = {parts_str} = {total:.4g} {pu}',
            ]
            return jsonify(total=total, partials=partials, compact=compact, detailed=detailed, warnings=[])

        else:
            return jsonify(error='Unknown gas law type'), 400
    except Exception as e:
        return _err(e)


# ── 13. Acid-Base ─────────────────────────────────────────────────────────────
@app.route('/api/acid_base', methods=['POST'])
def api_acid_base():
    d = request.json or {}
    t = d.get('type')
    try:
        warnings = []
        if t == 'ph_convert':
            it = d.get('input_type')
            v  = float(d['value'])
            label_map = {'H': '[H⁺]', 'OH': '[OH⁻]', 'pH': 'pH', 'pOH': 'pOH'}
            kwargs = {'H': v} if it == 'H' else {'OH': v} if it == 'OH' else \
                     {'pH': v} if it == 'pH' else {'pOH': v}
            pH, pOH, H, OH = all_four(**kwargs)
            compact  = f'pH = {pH:.4f},  pOH = {pOH:.4f}'
            detailed = [
                f'Given: {label_map[it]} = {v}',
                f'pH  = {pH:.4f}',
                f'pOH = {pOH:.4f}  (pH + pOH = 14 at 25 °C)',
                f'[H⁺]  = 10^(−pH) = {H:.4e} mol/L',
                f'[OH⁻] = 10^(−pOH) = {OH:.4e} mol/L',
            ]

        elif t == 'strong_acid':
            conc = float(d['conc'])
            pH   = strong_acid_pH(conc)
            _, pOH, H, OH = all_four(pH=pH)
            compact  = f'pH = {pH:.4f}'
            detailed = [
                f'Acid type: strong acid — fully dissociates',
                f'Given: concentration = {conc} mol/L',
                f'[H⁺] = concentration = {conc:.4e} mol/L',
                f'pH = −log[H⁺] = −log({conc:.4e})',
                f'pH = {pH:.4f}',
                f'pOH = 14 − pH = {pOH:.4f}',
            ]

        elif t == 'strong_base':
            conc = float(d['conc'])
            pH   = strong_base_pH(conc)
            _, pOH, H, OH = all_four(pH=pH)
            compact  = f'pH = {pH:.4f}'
            detailed = [
                f'Base type: strong base — fully dissociates',
                f'Given: concentration = {conc} mol/L',
                f'[OH⁻] = concentration = {conc:.4e} mol/L',
                f'pOH = −log[OH⁻] = −log({conc:.4e}) = {pOH:.4f}',
                f'pH = 14 − pOH = 14 − {pOH:.4f} = {pH:.4f}',
            ]

        elif t == 'weak_acid':
            Ka   = float(d['Ka'])
            conc = float(d['conc'])
            pH, approx, x = weak_acid_pH(Ka, conc)
            _, pOH, H, OH = all_four(pH=pH)
            x_approx = (Ka * conc) ** 0.5
            pct      = x_approx / conc * 100
            compact  = f'pH = {pH:.4f}'
            detailed = [
                f'Acid type: weak acid — partial dissociation',
                f'Equilibrium: HA ⇌ H⁺ + A⁻',
                f'Given: Ka = {Ka:.4e},  C = {conc} mol/L',
                f'Approximation: [H⁺] ≈ √(Ka × C) = √({Ka:.4e} × {conc}) = {x_approx:.4e}',
                f'5% check: {x_approx:.4e} / {conc} × 100 = {pct:.2f}%  → {"valid ✓" if approx else "invalid ✗ — using quadratic"}',
                f'[H⁺] = {x:.4e} mol/L',
                f'pH = −log({x:.4e}) = {pH:.4f}',
                f'pOH = 14 − {pH:.4f} = {pOH:.4f}',
            ]
            if not approx:
                warnings.append(f'Approximation invalid ({pct:.1f}% > 5%) — quadratic formula was used')

        elif t == 'weak_base':
            Kb   = float(d['Kb'])
            conc = float(d['conc'])
            pH, approx, x = weak_base_pH(Kb, conc)
            _, pOH, H, OH = all_four(pH=pH)
            x_approx = (Kb * conc) ** 0.5
            pct      = x_approx / conc * 100
            compact  = f'pH = {pH:.4f}'
            detailed = [
                f'Base type: weak base — partial protonation',
                f'Equilibrium: B + H₂O ⇌ BH⁺ + OH⁻',
                f'Given: Kb = {Kb:.4e},  C = {conc} mol/L',
                f'Approximation: [OH⁻] ≈ √(Kb × C) = √({Kb:.4e} × {conc}) = {x_approx:.4e}',
                f'5% check: {pct:.2f}%  → {"valid ✓" if approx else "invalid ✗ — using quadratic"}',
                f'[OH⁻] = {x:.4e} mol/L',
                f'pOH = −log({x:.4e}) = {pOH:.4f}',
                f'pH = 14 − {pOH:.4f} = {pH:.4f}',
            ]
            if not approx:
                warnings.append(f'Approximation invalid ({pct:.1f}% > 5%) — quadratic formula was used')

        elif t == 'buffer':
            Ka   = float(d['Ka'])
            acid = float(d['acid'])
            base = float(d['base'])
            pKa  = -math.log10(Ka)
            pH   = buffer_pH(Ka, acid, base)
            _, pOH, H, OH = all_four(pH=pH)
            ratio = base / acid
            compact  = f'Buffer pH = {pH:.4f}'
            detailed = [
                'Henderson-Hasselbalch: pH = pKa + log([A⁻]/[HA])',
                f'Given: Ka = {Ka:.4e},  [HA] = {acid} mol/L,  [A⁻] = {base} mol/L',
                f'pKa = −log({Ka:.4e}) = {pKa:.4f}',
                f'[A⁻]/[HA] = {base} / {acid} = {ratio:.4f}',
                f'pH = {pKa:.4f} + log({ratio:.4f})',
                f'pH = {pKa:.4f} + ({math.log10(ratio):.4f})',
                f'pH = {pH:.4f}',
            ]
            if abs(ratio - 1) > 0.9:
                warnings.append('Buffer ratio far from 1:1 — buffering capacity is reduced at this ratio')

        elif t == 'titration':
            solve = d.get('solve') or 'analyte_conc'
            ra = _num(d, 'ratio_analyte', 'analyte coefficient', positive=True) if str(d.get('ratio_analyte') or '').strip() else 1.0
            rt = _num(d, 'ratio_titrant', 'titrant coefficient', positive=True) if str(d.get('ratio_titrant') or '').strip() else 1.0
            Ct = _num(d, 'C_titrant', 'titrant concentration', positive=True)
            Va = _num(d, 'V_analyte', 'analyte volume', positive=True)
            if solve == 'analyte_conc':
                Vt = _num(d, 'V_titrant', 'titrant volume (at equivalence)', positive=True)
                n_t = equivalence_moles(Ct, Vt / 1000)
                n_a = n_t * ra / rt
                result = titration_find_concentration(n_a, Va / 1000)
                unit, label = 'mol/dm³', 'Analyte concentration'
                detailed = [
                    'Titration: find the concentration of the analyte',
                    f'Mole ratio analyte : titrant = {ra:g} : {rt:g}',
                    f'n(titrant) = c × V = {Ct:g} mol/dm³ × {Vt:g} cm³ ÷ 1000 = {n_t:.4g} mol',
                    f'n(analyte) = n(titrant) × {ra:g}/{rt:g} = {n_a:.4g} mol',
                    f'c(analyte) = n / V = {n_a:.4g} mol ÷ ({Va:g} cm³ ÷ 1000)',
                    f'c(analyte) = {result:.4g} mol/dm³',
                ]
            elif solve == 'titrant_volume':
                Ca = _num(d, 'C_analyte', 'analyte concentration', positive=True)
                n_a = equivalence_moles(Ca, Va / 1000)
                n_t = n_a * rt / ra
                result = titration_find_volume(n_t, Ct) * 1000
                unit, label = 'cm³', 'Titrant volume at equivalence'
                detailed = [
                    'Titration: find the volume of titrant needed',
                    f'Mole ratio analyte : titrant = {ra:g} : {rt:g}',
                    f'n(analyte) = c × V = {Ca:g} mol/dm³ × {Va:g} cm³ ÷ 1000 = {n_a:.4g} mol',
                    f'n(titrant) = n(analyte) × {rt:g}/{ra:g} = {n_t:.4g} mol',
                    f'V(titrant) = n / c = {n_t:.4g} mol ÷ {Ct:g} mol/dm³ = {result / 1000:.4g} dm³',
                    f'V(titrant) = {result:.4g} cm³',
                ]
            else:
                return jsonify(error='Unknown titration target'), 400
            acid_s, base_s = d.get('acid_strength'), d.get('base_strength')
            if acid_s in ('strong', 'weak') and base_s in ('strong', 'weak'):
                detailed.append(f'Equivalence point ({acid_s} acid + {base_s} base): '
                                + equivalence_point_pH_description(f'{acid_s} acid', f'{base_s} base'))
            compact = f'{label} = {result:.4g} {unit}'
            return jsonify(result=result, unit=unit, compact=compact,
                           detailed=detailed, warnings=[])

        elif t == 'salt':
            kind = d.get('kind')
            if kind not in ('weak_acid_salt', 'weak_base_salt'):
                return jsonify(error='Choose the salt of a weak acid or of a weak base.'), 400
            K_parent = _num(d, 'K', 'Ka or Kb of the parent', positive=True)
            conc = _num(d, 'conc', 'concentration', positive=True)
            pH, K_ion, x = salt_pH(kind, K_parent, conc)
            _, pOH, H, OH = all_four(pH=pH)
            if kind == 'weak_acid_salt':
                detailed = [
                    'Salt of a weak acid and a strong base (e.g. CH3COONa): the anion is a weak base.',
                    f'Kb = Kw / Ka = 1.00e-14 / {K_parent:.4g} = {K_ion:.4e}',
                    f'[OH⁻] = √(Kb × C) = √({K_ion:.4e} × {conc:g}) = {x:.4e} mol/dm³',
                    f'pOH = {pOH:.4f}, so pH = 14 − pOH = {pH:.4f}',
                    'The solution is basic (pH > 7).',
                ]
            else:
                detailed = [
                    'Salt of a weak base and a strong acid (e.g. NH4Cl): the cation is a weak acid.',
                    f'Ka = Kw / Kb = 1.00e-14 / {K_parent:.4g} = {K_ion:.4e}',
                    f'[H⁺] = √(Ka × C) = √({K_ion:.4e} × {conc:g}) = {x:.4e} mol/dm³',
                    f'pH = {pH:.4f}',
                    'The solution is acidic (pH < 7).',
                ]
            return jsonify(pH=pH, pOH=pOH, H=H, OH=OH, K_ion=K_ion,
                           compact=f'pH = {pH:.4f}', detailed=detailed, warnings=[])

        elif t == 'half_equivalence':
            pH_half = _num(d, 'pH', 'pH at half-equivalence')
            pKa, Ka = pKa_from_half_equivalence(pH_half)
            detailed = [
                'At the half-equivalence point half the weak acid has reacted, so [HA] = [A⁻].',
                'Henderson-Hasselbalch: pH = pKa + log([A⁻]/[HA]) = pKa + log(1) = pKa',
                f'pKa = pH at half-equivalence = {pKa:.4g}',
                f'Ka = 10^(−pKa) = {Ka:.4e}',
            ]
            return jsonify(pKa=pKa, Ka=Ka, answers=[_answer('pKa', pKa), _answer('Ka', Ka)],
                           compact=f'pKa = {pKa:.4g},  Ka = {Ka:.4e}', detailed=detailed, warnings=[])

        elif t == 'identify':
            identity = identify(d['formula'])
            compact  = f'{d["formula"]} → {identity}'
            detailed = [
                f'Formula entered: {d["formula"]}',
                f'Classification: {identity}',
            ]
            return jsonify(formula=d['formula'], identity=identity,
                           compact=compact, detailed=detailed, warnings=[])
        else:
            return jsonify(error='Unknown type'), 400

        return jsonify(pH=pH, pOH=pOH, H=H, OH=OH,
                       compact=compact, detailed=detailed, warnings=warnings)
    except Exception as e:
        return _err(e)


# ── 14. Thermodynamics ────────────────────────────────────────────────────────
@app.route('/api/thermo', methods=['POST'])
def api_thermo():
    d = request.json or {}
    t = d.get('type')
    try:
        if t == 'calorimetry':
            solve = d.get('solve')
            q  = float(d['q'])  if d.get('q')  else None
            m  = float(d['m'])  if d.get('m')  else None
            c  = float(d['c'])  if d.get('c')  else None
            dT = float(d['dT']) if d.get('dT') else None
            formulas = {'q':'q = m×c×ΔT', 'm':'m = q/(c×ΔT)', 'c':'c = q/(m×ΔT)', 'dT':'ΔT = q/(m×c)'}
            labels   = {'q':('q','J'), 'm':('m','g'), 'c':('c','J/g·K'), 'dT':('ΔT','K')}
            if solve == 'q':   result = cal_q(m, c, dT)
            elif solve == 'm': result = cal_m(q, c, dT)
            elif solve == 'c': result = cal_c(q, m, dT)
            elif solve == 'dT':result = cal_dT(q, m, c)
            else: return jsonify(error='Unknown solve target'), 400
            lbl, unit = labels[solve]
            given = {k:v for k,v in {'q':q,'m':m,'c':c,'ΔT':dT}.items() if v is not None}
            compact  = f'{lbl} = {result:.4g} {unit}'
            detailed = [
                'Method: Calorimetry',
                f'Formula: {formulas[solve]}',
                f'Given: ' + ', '.join(f'{k}={v}' for k,v in given.items()),
                f'Solving for {lbl}:',
                f'{lbl} = {result:.4g} {unit}',
            ]
            return jsonify(result=result, unit=unit, compact=compact, detailed=detailed, warnings=[])

        elif t == 'hess':
            steps   = d.get('steps', [])
            dH_vals = [float(s['dH']) for s in steps]
            mults   = [float(s['mult']) for s in steps]
            result  = hess_law(dH_vals, mults)
            compact  = f'ΔH_rxn = {result:.4g} kJ/mol'
            detailed = [
                "Method: Hess's Law  —  ΔH_rxn = Σ(ΔH_step × multiplier)",
                *[f'  Step {i+1}: ΔH = {dh:.4g} kJ  ×  {m:.4g}  = {dh*m:.4g} kJ'
                  for i,(dh,m) in enumerate(zip(dH_vals,mults))],
                f'ΔH_rxn = {" + ".join(f"({dh*m:.4g})" for dh,m in zip(dH_vals,mults))} = {result:.4g} kJ/mol',
            ]
            return jsonify(result=result, compact=compact, detailed=detailed, warnings=[])

        elif t == 'bond':
            def parse_bonds(lst):
                out = []
                for b in lst:
                    label = b['bond']
                    count = float(b.get('count', 1))
                    kj    = b.get('kJ', '')
                    enth  = float(kj) if kj else lookup_bond(label)
                    if enth is None:
                        raise KeyError(f"Bond '{label}' not in table. Provide kJ/mol manually.")
                    out.append((label, count, enth))
                return out
            broken = parse_bonds(d.get('broken', []))
            formed = parse_bonds(d.get('formed', []))
            dH, sb, sf = bond_enthalpy_dH(broken, formed)
            compact  = f'ΔH = {dH:.4g} kJ/mol'
            detailed = [
                'Method: Bond Enthalpy  —  ΔH = Σ(broken) − Σ(formed)',
                'Bonds broken (reactants side):',
                *[f'  {lbl}  ×{cnt:.4g}:  {cnt*enth:.4g} kJ' for lbl,cnt,enth in broken],
                f'  Subtotal broken: {sb:.4g} kJ',
                'Bonds formed (products side):',
                *[f'  {lbl}  ×{cnt:.4g}:  {cnt*enth:.4g} kJ' for lbl,cnt,enth in formed],
                f'  Subtotal formed: {sf:.4g} kJ',
                f'ΔH = {sb:.4g} − {sf:.4g} = {dH:.4g} kJ/mol',
            ]
            return jsonify(result=dH, sum_broken=sb, sum_formed=sf,
                           compact=compact, detailed=detailed,
                           warnings=['Bond enthalpies are average values — result is approximate'])

        elif t == 'std_enthalpy':
            species = []
            for row in d.get('species', []):
                f = str(row.get('formula') or '').strip()
                if not f and str(row.get('dHf') or '').strip() == '':
                    continue
                role = row.get('role')
                if role not in ('reactant', 'product'):
                    return jsonify(error='Each species must be a reactant or a product.'), 400
                species.append({'formula': cap(f) or '?',
                                'dHf': _num(row, 'dHf', f'ΔH°f of {f or "a species"}'),
                                'coeff': _num(row, 'coeff', f'coefficient of {f or "a species"}', positive=True)
                                         if str(row.get('coeff') or '').strip() else 1.0,
                                'role': role})
            if not any(x['role'] == 'reactant' for x in species) or \
               not any(x['role'] == 'product' for x in species):
                return jsonify(error='Add at least one reactant and one product.'), 400
            result = standard_enthalpy_rxn(species)
            prods = [x for x in species if x['role'] == 'product']
            reacs = [x for x in species if x['role'] == 'reactant']
            sp = sum(x['coeff'] * x['dHf'] for x in prods)
            sr = sum(x['coeff'] * x['dHf'] for x in reacs)
            line = lambda x: f'  {x["coeff"]:g} × ΔH°f({x["formula"]}) = {x["coeff"]:g} × {x["dHf"]:g} = {x["coeff"] * x["dHf"]:.4g} kJ'
            detailed = [
                'Formula: ΔH°rxn = ΣnΔH°f(products) − ΣnΔH°f(reactants)',
                'Products:', *[line(x) for x in prods], f'  Σ = {sp:.4g} kJ',
                'Reactants:', *[line(x) for x in reacs], f'  Σ = {sr:.4g} kJ',
                f'ΔH°rxn = {sp:.4g} − ({sr:.4g}) = {result:.4g} kJ/mol',
            ]
            warnings = []
            for x in species:
                try:
                    counts = parse_species(x['formula']).counts
                except ValueError:
                    continue
                if len(counts) == 1 and x['dHf'] != 0 and x['formula'] in ('H2', 'O2', 'N2', 'F2', 'Cl2', 'Br2', 'I2', 'C', 'S', 'Na', 'Mg', 'Fe', 'Cu', 'Zn', 'Al', 'Ca', 'K', 'P4', 'S8'):
                    warnings.append(f'{x["formula"]} is an element in its standard state: its ΔH°f should be 0.')
            return jsonify(result=result, sum_products=sp, sum_reactants=sr,
                           compact=f'ΔH°rxn = {result:.4g} kJ/mol', detailed=detailed, warnings=warnings)

        elif t == 'entropy':
            species = []
            for row in d.get('species', []):
                f = str(row.get('formula') or '').strip()
                if not f and str(row.get('S') or '').strip() == '':
                    continue
                role = row.get('role')
                if role not in ('reactant', 'product'):
                    return jsonify(error='Each species must be a reactant or a product.'), 400
                species.append({'formula': cap(f) or '?',
                                'S': _num(row, 'S', f'S° of {f or "a species"}', positive=True),
                                'coeff': _num(row, 'coeff', f'coefficient of {f or "a species"}', positive=True)
                                         if str(row.get('coeff') or '').strip() else 1.0,
                                'role': role})
            if not any(x['role'] == 'reactant' for x in species) or \
               not any(x['role'] == 'product' for x in species):
                return jsonify(error='Add at least one reactant and one product.'), 400
            result = standard_entropy_rxn(species)
            prods = [x for x in species if x['role'] == 'product']
            reacs = [x for x in species if x['role'] == 'reactant']
            sp = sum(x['coeff'] * x['S'] for x in prods)
            sr = sum(x['coeff'] * x['S'] for x in reacs)
            line = lambda x: f'  {x["coeff"]:g} × S°({x["formula"]}) = {x["coeff"]:g} × {x["S"]:g} = {x["coeff"] * x["S"]:.4g} J/(mol·K)'
            detailed = [
                'Formula: ΔS°rxn = Σ n·S°(products) − Σ n·S°(reactants)',
                'Products:', *[line(x) for x in prods], f'  Σ = {sp:.4g} J/(mol·K)',
                'Reactants:', *[line(x) for x in reacs], f'  Σ = {sr:.4g} J/(mol·K)',
                f'ΔS°rxn = {sp:.4g} − {sr:.4g} = {result:.4g} J/(mol·K)',
                ('Entropy increases (more ways to arrange the particles).' if result > 0
                 else 'Entropy decreases (fewer ways to arrange the particles).' if result < 0
                 else 'No change in entropy.'),
            ]
            return jsonify(result=result, unit='J/(mol·K)', sum_products=sp, sum_reactants=sr,
                           compact=f'ΔS°rxn = {result:.4g} J/(mol·K)', detailed=detailed, warnings=[])

        elif t == 'gibbs_k':
            solve = d.get('solve')
            T = _num(d, 'T', 'T', positive=True) if str(d.get('T') or '').strip() else 298.15
            if solve == 'dG':
                K = _num(d, 'K', 'K', positive=True)
                result = gibbs_from_K(K, T)
                unit = 'kJ/mol'
                compact = f'ΔG° = {result:.4g} kJ/mol'
                detailed = ['Formula: ΔG° = −RT ln K  (R = 8.314 J/(mol·K))',
                            f'Given: K = {K:g}, T = {T:g} K',
                            f'ln K = {math.log(K):.4f}',
                            f'ΔG° = −8.314 × {T:g} × {math.log(K):.4f} ÷ 1000',
                            f'ΔG° = {result:.4g} kJ/mol']
                K_val = K
            elif solve == 'K':
                dG = _num(d, 'dG', 'ΔG°')
                expo = -dG * 1000 / (8.314 * T)
                if expo > 700:
                    return jsonify(error=f'K is too large to show (about 10^{expo / math.log(10):.0f}).'), 400
                result = K_from_gibbs(dG, T)
                unit = ''
                compact = f'K = {result:.4g}'
                detailed = ['Formula: K = e^(−ΔG°/RT)',
                            f'Given: ΔG° = {dG:g} kJ/mol, T = {T:g} K',
                            f'−ΔG°/RT = −({dG:g} × 1000) ÷ (8.314 × {T:g}) = {expo:.4f}',
                            f'K = e^{expo:.4f} = {result:.4g}']
                K_val = result
            else:
                return jsonify(error='Unknown solve target'), 400
            if K_val > 1:
                detailed.append('K > 1 (ΔG° < 0): products are favoured at equilibrium.')
            elif K_val < 1:
                detailed.append('K < 1 (ΔG° > 0): reactants are favoured at equilibrium.')
            else:
                detailed.append('K = 1 (ΔG° = 0): neither side is favoured.')
            return jsonify(result=result, unit=unit, compact=compact, detailed=detailed, warnings=[])

        elif t == 'spontaneity':
            dH = _num(d, 'dH', 'ΔH')
            dS = _num(d, 'dS', 'ΔS')
            desc = spontaneity_analysis(dH, dS)
            detailed = ['ΔG = ΔH − TΔS, so the signs of ΔH and ΔS decide when ΔG < 0',
                        f'Given: ΔH = {dH:g} kJ/mol, ΔS = {dS:g} J/(mol·K)',
                        desc]
            T_cross = None
            if dH != 0 and dS != 0 and (dH > 0) == (dS > 0):
                T_cross = dH * 1000 / dS
                side = 'below' if dH < 0 else 'above'
                detailed += [f'Crossover temperature (ΔG = 0): T = ΔH ÷ ΔS = {dH:g} × 1000 ÷ {dS:g} = {T_cross:.4g} K',
                             f'Spontaneous {side} {T_cross:.4g} K ({T_cross - 273.15:.4g} °C)']
            return jsonify(result=desc, T_crossover=T_cross, compact=desc,
                           detailed=detailed, warnings=[])

        elif t == 'gibbs':
            dH = float(d['dH'])
            dS = float(d['dS'])
            T  = float(d.get('T') or 298.15)
            dG = gibbs_dG(dH, T, dS)   # ΔS in J/(mol·K)
            spont = 'spontaneous (ΔG < 0)' if dG < 0 else ('at equilibrium (ΔG = 0)' if dG == 0 else 'non-spontaneous (ΔG > 0)')
            compact  = f'ΔG = {dG:.4g} kJ/mol  ({spont})'
            detailed = [
                'Formula: ΔG = ΔH − TΔS',
                f'Given: ΔH = {dH} kJ/mol,  ΔS = {dS} J/(mol·K),  T = {T} K',
                f'Convert ΔS to kJ: {dS} ÷ 1000 = {dS/1000:.4g} kJ/(mol·K)',
                f'TΔS = {T} × {dS/1000:.4g} = {T*dS/1000:.4g} kJ/mol',
                f'ΔG = {dH} − ({T*dS/1000:.4g})',
                f'ΔG = {dG:.4g} kJ/mol',
                f'Conclusion: reaction is {spont}',
            ]
            return jsonify(result=dG, spontaneous=dG < 0,
                           compact=compact, detailed=detailed, warnings=[])

        else:
            return jsonify(error='Unknown type'), 400
    except Exception as e:
        return _err(e)


# ── 18. Solutions: concentration & dilution ──────────────────────────────────
@app.route('/api/solutions', methods=['POST'])
def api_solutions():
    d = request.json or {}
    t = d.get('type')
    try:
        vu = d.get('v_unit') or 'cm3'
        vlabel = {'dm3': 'dm³', 'cm3': 'cm³', 'm3': 'm³'}.get(vu, vu)

        def volume_dm3(key='V', label='volume'):
            return sol.volume_to_dm3(_num(d, key, label, positive=True), vu)

        if t == 'concentration':
            n = _num(d, 'n', 'moles', positive=True)
            V = volume_dm3()
            result = sol.concentration(n, V)
            detailed = ['Formula: c = n / V', f'Given: n = {n:g} mol, V = {_num(d, "V", "volume"):g} {vlabel}',
                        f'V = {V:.6g} dm³', f'c = {n:g} ÷ {V:.6g} = {result:.4g} mol/dm³']
            unit = 'mol/dm³'
        elif t == 'moles':
            c = _num(d, 'c', 'concentration', positive=True)
            V = volume_dm3()
            result = sol.moles_from_concentration(c, V)
            detailed = ['Formula: n = c × V', f'Given: c = {c:g} mol/dm³, V = {_num(d, "V", "volume"):g} {vlabel}',
                        f'V = {V:.6g} dm³', f'n = {c:g} × {V:.6g} = {result:.4g} mol']
            unit = 'mol'
        elif t == 'volume':
            n = _num(d, 'n', 'moles', positive=True)
            c = _num(d, 'c', 'concentration', positive=True)
            V_dm3 = sol.volume_from_concentration(n, c)
            result = sol.volume_from_dm3(V_dm3, vu)
            detailed = ['Formula: V = n / c', f'Given: n = {n:g} mol, c = {c:g} mol/dm³',
                        f'V = {n:g} ÷ {c:g} = {V_dm3:.4g} dm³ = {result:.4g} {vlabel}']
            unit = vlabel
        elif t == 'from_mass':
            m = _num(d, 'mass', 'mass', positive=True)
            M, note = _molar_mass_input(d.get('M'))
            V = volume_dm3()
            result = sol.concentration_from_mass(m, M, V)
            detailed = [*([note] if note else []), 'Formula: c = (mass ÷ M) ÷ V',
                        f'n = {m:g} ÷ {M:.6g} = {m / M:.4g} mol',
                        f'V = {V:.6g} dm³', f'c = {m / M:.4g} ÷ {V:.6g} = {result:.4g} mol/dm³']
            unit = 'mol/dm³'
        elif t == 'mass_needed':
            c = _num(d, 'c', 'concentration', positive=True)
            V = volume_dm3()
            M, note = _molar_mass_input(d.get('M'))
            result = sol.mass_for_solution(c, V, M)
            detailed = [*([note] if note else []), 'Formula: mass = c × V × M',
                        f'V = {V:.6g} dm³',
                        f'mass = {c:g} × {V:.6g} × {M:.6g} = {result:.4g} g',
                        'Weigh this out, dissolve it, and make the solution up to the mark.']
            unit = 'g'
        elif t == 'convert':
            M, note = _molar_mass_input(d.get('M'))
            if d.get('direction') == 'to_mol':
                v = _num(d, 'value', 'mass concentration', positive=True)
                result = sol.g_per_dm3_to_mol_per_dm3(v, M)
                detailed = [*([note] if note else []), 'Formula: c = (g/dm³) ÷ M',
                            f'c = {v:g} ÷ {M:.6g} = {result:.4g} mol/dm³']
                unit = 'mol/dm³'
            else:
                v = _num(d, 'value', 'concentration', positive=True)
                result = sol.mol_per_dm3_to_g_per_dm3(v, M)
                detailed = [*([note] if note else []), 'Formula: g/dm³ = c × M',
                            f'= {v:g} × {M:.6g} = {result:.4g} g/dm³']
                unit = 'g/dm³'
        elif t == 'dilution':
            solve = d.get('solve')
            if solve not in ('c1', 'V1', 'c2', 'V2'):
                return jsonify(error='Choose c1, V1, c2 or V2 to solve for.'), 400
            vals = {k: _num(d, k, k, positive=True) for k in ('c1', 'V1', 'c2', 'V2') if k != solve}
            result = sol.dilution_solve(solve, **vals)
            unit = 'mol/dm³' if solve.startswith('c') else vlabel
            detailed = ['Formula: c₁V₁ = c₂V₂  (the moles of solute do not change)',
                        'Given: ' + ', '.join(f'{k} = {v:g}' for k, v in vals.items()),
                        f'{solve} = {result:.4g} {unit}']
            if solve == 'V2':
                detailed.append(f'Water to add = {result - vals["V1"]:.4g} {vlabel}')
            elif solve == 'V1':
                detailed.append(f'Water to add = {vals["V2"] - result:.4g} {vlabel}')
            if solve.startswith('c'):
                other = vals['c2'] if solve == 'c1' else vals['c1']
                detailed.append(f'Dilution factor = {max(result, other) / min(result, other):.4g}×')
        elif t == 'ppm':
            mg = _num(d, 'mass_mg', 'mass in mg', positive=True)
            V = volume_dm3()
            result = sol.ppm_from_mass(mg, V)
            detailed = ['For a dilute aqueous solution 1 dm³ ≈ 1 kg, so mg/dm³ ≈ mg/kg = ppm',
                        f'{mg:g} mg ÷ {V:.6g} dm³ = {result:.4g} ppm']
            unit = 'ppm'
        else:
            return jsonify(error='Unknown type'), 400
        label = {'concentration': 'c', 'moles': 'n', 'volume': 'V', 'from_mass': 'c',
                 'mass_needed': 'Mass needed', 'convert': 'Converted', 'ppm': 'Concentration'}.get(t, 'Result')
        if t == 'dilution':
            label = d.get('solve')
        return jsonify(result=result, unit=unit, compact=f'{label} = {result:.4g} {unit}',
                       detailed=detailed, warnings=[])
    except Exception as e:
        return _err(e)


# ── 19. Isotopes & relative atomic mass ──────────────────────────────────────
@app.route('/api/isotopes', methods=['POST'])
def api_isotopes():
    d = request.json or {}
    t = d.get('type') or 'ar'
    try:
        if t == 'ar':
            rows = [r for r in d.get('isotopes', [])
                    if str(r.get('mass') or '').strip() or str(r.get('abundance') or '').strip()]
            data = [(_num(r, 'mass', 'isotope mass', positive=True),
                     _num(r, 'abundance', 'abundance', positive=True, allow_zero=True)) for r in rows]
            Ar = iso.relative_atomic_mass(data)
            percents = iso.percentage_abundances(data)
            detailed = iso.mass_spectrum_summary(data, d.get('symbol', ''))
            answers = [_answer('Ar', Ar)] + [
                _answer(f'{m:g} abundance', p, '%') for (m, _), p in zip(data, percents)]
            return jsonify(Ar=Ar, percents=percents, answers=answers,
                           compact=f'Ar = {Ar:.4f}', detailed=detailed, warnings=[])
        if t == 'abundance':
            Ar = _num(d, 'Ar', 'Ar', positive=True)
            m1 = _num(d, 'mass1', 'mass of isotope 1', positive=True)
            m2 = _num(d, 'mass2', 'mass of isotope 2', positive=True)
            p1, p2 = iso.abundance_from_Ar(Ar, m1, m2)
            detailed = [
                'Let x = % of the first isotope, so (100 − x) = % of the second.',
                f'Ar = [x × {m1:g} + (100 − x) × {m2:g}] ÷ 100 = {Ar:g}',
                f'x = 100(Ar − m₂) ÷ (m₁ − m₂) = 100({Ar:g} − {m2:g}) ÷ ({m1:g} − {m2:g})',
                f'Isotope {m1:g}: {p1:.2f} %',
                f'Isotope {m2:g}: {p2:.2f} %',
            ]
            return jsonify(percent1=p1, percent2=p2,
                           answers=[_answer(f'{m1:g} abundance', p1, '%'),
                                    _answer(f'{m2:g} abundance', p2, '%')],
                           compact=f'{m1:g}: {p1:.2f} %,  {m2:g}: {p2:.2f} %',
                           detailed=detailed, warnings=[])
        return jsonify(error='Unknown type'), 400
    except Exception as e:
        return _err(e)


# ── 20. Uncertainties & significant figures ──────────────────────────────────
@app.route('/api/uncertainty', methods=['POST'])
def api_uncertainty():
    d = request.json or {}
    t = d.get('type')
    try:
        if t == 'convert':
            value = _num(d, 'value', 'measurement')
            if str(d.get('absolute') or '').strip():
                absolute = _num(d, 'absolute', 'absolute uncertainty', positive=True, allow_zero=True)
                percent = unc.percentage_uncertainty(value, absolute)
            elif str(d.get('percent') or '').strip():
                percent = _num(d, 'percent', 'percentage uncertainty', positive=True, allow_zero=True)
                absolute = unc.absolute_uncertainty(value, percent)
            else:
                return jsonify(error='Enter either the absolute or the percentage uncertainty.'), 400
            detailed = [
                '% uncertainty = absolute ÷ value × 100',
                f'= {absolute:.4g} ÷ {abs(value):g} × 100 = {percent:.4g} %',
                f'Written out: {unc.format_with_uncertainty(value, absolute)}',
            ]
            return jsonify(value=value, absolute=absolute, percent=percent,
                           answers=[_answer('Absolute uncertainty', absolute),
                                    _answer('Percentage uncertainty', percent, '%')],
                           compact=unc.format_with_uncertainty(value, absolute),
                           detailed=detailed, warnings=[])

        if t in ('add', 'multiply'):
            rows = [r for r in d.get('measurements', [])
                    if str(r.get('value') or '').strip() != '']
            if len(rows) < 2:
                return jsonify(error='Enter at least two measurements.'), 400
            values = [_num(r, 'value', 'measurement') for r in rows]
            uncs = [_num(r, 'unc', 'uncertainty', positive=True, allow_zero=True) for r in rows]
            if t == 'add':
                result, absolute, percent = unc.combine_add_subtract(values, uncs)
                detailed = ['Adding or subtracting: the ABSOLUTE uncertainties add.',
                            *[f'  {v:g} ± {u:g}' for v, u in zip(values, uncs)],
                            f'Result = {result:.4g}',
                            f'Absolute uncertainty = ' + ' + '.join(f'{u:g}' for u in uncs) + f' = ± {absolute:.4g}',
                            f'= {percent:.4g} % of the result']
            else:
                ops = [r.get('op', '*') for r in rows[1:]]
                result, absolute, percent = unc.combine_multiply_divide(values, uncs, ops)
                detailed = ['Multiplying or dividing: the PERCENTAGE uncertainties add.',
                            *[f'  {v:g} ± {u:g} %' for v, u in zip(values, uncs)],
                            'Calculation: ' + ' '.join(
                                [f'{values[0]:g}'] + [f'{o} {v:g}' for o, v in zip(ops, values[1:])]),
                            f'Result = {result:.4g}',
                            f'Percentage uncertainty = ' + ' + '.join(f'{u:g}' for u in uncs) + f' = {percent:.4g} %',
                            f'Absolute uncertainty = ± {absolute:.4g}']
            return jsonify(result=result, absolute=absolute, percent=percent,
                           answers=[_answer('Result', result), _answer('Uncertainty', absolute),
                                    _answer('Percentage uncertainty', percent, '%')],
                           compact=unc.format_with_uncertainty(result, absolute),
                           detailed=detailed, warnings=[])

        if t == 'power':
            value = _num(d, 'value', 'value')
            percent = _num(d, 'percent', 'percentage uncertainty', positive=True, allow_zero=True)
            power = _num(d, 'power', 'power')
            result, absolute, pct = unc.power_uncertainty(value, percent, power)
            detailed = [f'Raising to a power multiplies the percentage uncertainty by |n|.',
                        f'{value:g}^{power:g} = {result:.4g}',
                        f'% uncertainty = {percent:g} × |{power:g}| = {pct:.4g} %',
                        f'Absolute uncertainty = ± {absolute:.4g}']
            return jsonify(result=result, absolute=absolute, percent=pct,
                           answers=[_answer('Result', result), _answer('Percentage uncertainty', pct, '%')],
                           compact=unc.format_with_uncertainty(result, absolute),
                           detailed=detailed, warnings=[])

        if t == 'error':
            experimental = _num(d, 'experimental', 'experimental value')
            accepted = _num(d, 'accepted', 'accepted value')
            pct = unc.percentage_error(experimental, accepted)
            detailed = ['% error = |experimental − accepted| ÷ |accepted| × 100',
                        f'= |{experimental:g} − {accepted:g}| ÷ |{accepted:g}| × 100',
                        f'= {pct:.4g} %',
                        'This measures accuracy (how close to the true value), not precision.']
            return jsonify(result=pct, unit='%', compact=f'Percentage error = {pct:.4g} %',
                           detailed=detailed, warnings=[])

        if t == 'sigfig':
            value = _num(d, 'value', 'value')
            figures = int(_num(d, 'figures', 'significant figures', positive=True))
            rounded = unc.round_to_sig_figs(value, figures)
            detailed = [f'{value:g} to {figures} significant figures', f'= {rounded:g}']
            return jsonify(result=rounded, compact=f'{rounded:g}', detailed=detailed, warnings=[])

        return jsonify(error='Unknown type'), 400
    except Exception as e:
        return _err(e)


# ── 21. Electron configuration ───────────────────────────────────────────────
@app.route('/api/electron_config', methods=['POST'])
def api_electron_config():
    d = request.json or {}
    try:
        element = str(d.get('element') or '').strip()
        if not element:
            return jsonify(error='Enter an element symbol, name or atomic number.'), 400
        charge = int(_num(d, 'charge', 'charge')) if str(d.get('charge') or '').strip() else 0
        text, config, info = electron_configuration(element, charge)
        detailed = configuration_lines(element, charge)
        return jsonify(configuration=text, shorthand=noble_gas_shorthand(element, charge),
                       element=info['symbol'], number=info['number'],
                       compact=text, headline=f'{info["symbol"]}: {text}',
                       detailed=detailed, warnings=[])
    except Exception as e:
        return _err(e)


# ── 22. Index of hydrogen deficiency ─────────────────────────────────────────
@app.route('/api/ihd', methods=['POST'])
def api_ihd():
    d = request.json or {}
    try:
        formula = str(d.get('formula') or '').strip()
        if not formula:
            return jsonify(error='Enter a molecular formula, e.g. C6H6.'), 400
        value = index_of_hydrogen_deficiency(formula)
        detailed = ihd_lines(formula)
        return jsonify(result=value, ihd=value, answers=[_answer('IHD', value)],
                       compact=f'IHD = {value}', detailed=detailed, warnings=[])
    except Exception as e:
        return _err(e)


# ── 15. ICE Solver ────────────────────────────────────────────────────────────
@app.route('/api/ice', methods=['POST'])
def api_ice():
    d = request.json or {}
    t = d.get('type') or 'table'
    try:
        if t != 'table':
            return _ice_tools(d, t)
        rd = d['reactants']
        pd = d['products']
        r_names  = [r['name'] for r in rd]
        r_coeffs = [float(r['coeff']) for r in rd]
        r_init   = [float(r['initial']) for r in rd]
        p_names  = [p['name'] for p in pd]
        p_coeffs = [float(p['coeff']) for p in pd]
        p_init   = [float(p['initial']) for p in pd]
        Kc = float(d['Kc'])
        if any(c <= 0 for c in r_coeffs + p_coeffs):
            return jsonify(error='Coefficients must be greater than zero.'), 400
        if any(c < 0 for c in r_init + p_init):
            return jsonify(error='Initial concentrations cannot be negative.'), 400
        if Kc <= 0:
            return jsonify(error='Kc must be greater than zero.'), 400
        res = build_ice_table(r_names, r_coeffs, r_init, p_names, p_coeffs, p_init, Kc)
        x = res['x']

        # Build ICE table rows as text
        all_names = r_names + p_names
        all_init  = list(r_init) + list(p_init)
        all_chg   = [f'-{c}x' for c in r_coeffs] + [f'+{c}x' for c in p_coeffs]
        all_eq    = res['r_eq'] + res['p_eq']
        col_w = max(10, max(len(n) for n in all_names) + 2)
        header = ' | '.join(n.center(col_w) for n in all_names)
        row_i  = ' | '.join(f'{v:.4g}'.center(col_w) for v in all_init)
        row_c  = ' | '.join(s.center(col_w) for s in all_chg)
        row_e  = ' | '.join(f'{v:.4e}'.center(col_w) for v in all_eq)

        compact  = f'x = {x:.4e},  Kc_verified = {res["Q_final"]:.4g}'
        detailed = [
            f'Given: Kc = {Kc}',
            'ICE Table:',
            f'  Species:   {header}',
            f'  Initial:   {row_i}',
            f'  Change:    {row_c}',
            f'  Equilib.:  {row_e}',
            f'Solving for x using bisection method',
            f'x = {x:.4e}',
            f'Kc_verified = {res["Q_final"]:.4g}  (target: {Kc})',
            f'5% approximation check: x/[min initial] = {res["approx_pct"]:.2f}%',
        ]
        warnings = ([f'x is {res["approx_pct"]:.1f}% of the smallest starting concentration (> 5%) — '
                     'the exact (bisection) answer is shown, not the approximation']
                    if res['approx_pct'] > 5 else [])
        return jsonify(x=x, r_names=r_names, p_names=p_names,
                       r_eq=res['r_eq'], p_eq=res['p_eq'],
                       Q_initial=res['Q_initial'], Q_final=res['Q_final'],
                       approx_pct=res['approx_pct'],
                       compact=compact, detailed=detailed, warnings=warnings)
    except Exception as e:
        return _err(e)


def _ice_tools(d, t):
    if t == 'kc_kp':
        solve = d.get('solve')
        T = _num(d, 'T', 'T (K)', positive=True)
        dn = _num(d, 'delta_n', 'Δn')
        K = _num(d, 'K', 'Kc' if solve == 'Kp' else 'Kp', positive=True)
        if solve == 'Kp':
            result, frm = kc_to_kp(K, T, dn), f'Kp = Kc(RT)^Δn = {K:g} × (0.08206 × {T:g})^{dn:g}'
        elif solve == 'Kc':
            result, frm = kp_to_kc(K, T, dn), f'Kc = Kp ÷ (RT)^Δn = {K:g} ÷ (0.08206 × {T:g})^{dn:g}'
        else:
            return jsonify(error='Unknown solve target'), 400
        detailed = ['Kp = Kc(RT)^Δn, with R = 0.08206 L·atm/(mol·K) and Kp in atm',
                    'Δn = moles of gaseous products − moles of gaseous reactants',
                    f'RT = {0.08206 * T:.4g}', frm, f'{solve} = {result:.4g}']
        warnings = ['Δn = 0, so Kp = Kc.'] if dn == 0 else []
        return jsonify(result=result, compact=f'{solve} = {result:.4g}', detailed=detailed, warnings=warnings)

    if t == 'q_vs_k':
        rd, pd = d.get('reactants', []), d.get('products', [])
        if not rd or not pd:
            return jsonify(error='Need at least 1 reactant and 1 product.'), 400
        rc = [_num(r, 'coeff', f'coefficient of {r.get("name") or "a reactant"}', positive=True) for r in rd]
        pc = [_num(p, 'coeff', f'coefficient of {p.get("name") or "a product"}', positive=True) for p in pd]
        rx = [_num(r, 'initial', f'[{r.get("name") or "reactant"}]', positive=True, allow_zero=True) for r in rd]
        px = [_num(p, 'initial', f'[{p.get("name") or "product"}]', positive=True, allow_zero=True) for p in pd]
        K = _num(d, 'Kc', 'K', positive=True)
        if all(v == 0 for v in rx + px):
            return jsonify(error='All concentrations are zero, so Q is undefined.'), 400
        Q = reaction_quotient(rc, rx, pc, px)
        direction, explanation = compare_Q_K(Q, K)
        term = lambda n, c: f'[{n}]^{c:g}' if c != 1 else f'[{n}]'
        num = ' × '.join(term(p.get('name') or '?', c) for p, c in zip(pd, pc))
        den = ' × '.join(term(r.get('name') or '?', c) for r, c in zip(rd, rc))
        Q_text = '∞ (a reactant is at zero)' if math.isinf(Q) else f'{Q:.4g}'
        detailed = [f'Q = ({num}) ÷ ({den})',
                    'Values: ' + ', '.join(f'[{x.get("name") or "?"}] = {v:g}' for x, v in zip(rd + pd, rx + px)),
                    f'Q = {Q_text},  K = {K:g}',
                    explanation]
        return jsonify(Q=Q, K=K, direction=direction,
                       compact=f'Q = {Q_text} → {direction}', detailed=detailed, warnings=[])

    if t == 'le_chatelier':
        dist = d.get('disturbance')
        k_effect = 'unchanged'
        if dist == 'concentration':
            direction, explanation = le_chatelier_concentration(d.get('role', ''), d.get('change', ''))
        elif dist == 'pressure':
            direction, explanation = le_chatelier_pressure(d.get('change', ''), _num(d, 'delta_n', 'Δn'))
        elif dist == 'temperature':
            direction, explanation, k_effect = le_chatelier_temperature(d.get('change', ''), d.get('rxn_type', ''))
        elif dist == 'catalyst':
            direction, explanation = le_chatelier_catalyst()
        else:
            return jsonify(error='Choose a disturbance.'), 400
        shift = {'left': 'Shifts LEFT (towards reactants)', 'right': 'Shifts RIGHT (towards products)',
                 'none': 'No shift'}[direction]
        detailed = [explanation, f'Value of K: {k_effect}' + ('' if dist == 'temperature' else ' (only temperature changes K)')]
        return jsonify(direction=direction, k_effect=k_effect, compact=shift,
                       detailed=detailed, warnings=[])

    return jsonify(error='Unknown type'), 400


# ── 16. Electrochemistry ──────────────────────────────────────────────────────
@app.route('/api/reduction_potentials', methods=['GET'])
def api_reduction_potentials():
    rows = sorted(REDUCTION_POTENTIALS.items(), key=lambda kv: -kv[1])
    return jsonify(half_cells=[{'label': k, 'E': v} for k, v in rows])


def _half_cell(label):
    """(E°, ox species, red species, medium, electrons) for 'Cu2+/Cu'."""
    E = get_reduction_potential(label)
    ox, red = label.split('/')
    has_o = any('O' in parse_species(x).counts for x in (ox, red))
    medium = 'acidic' if has_o else None
    half = balance_full([ox, 'e-'], [red], medium)
    n = next(c for c, sp in half['reactants'] if sp.is_electron)
    ox_coeff = next(c for c, sp in half['reactants'] if not sp.is_electron
                    and (sp.formula, sp.charge) == (parse_species(ox).formula, parse_species(ox).charge))
    return E, ox, red, medium, n, ox_coeff, half['equation']
@app.route('/api/electrochem', methods=['POST'])
def api_electrochem():
    d = request.json or {}
    t = d.get('type')
    try:
        if t == 'cell_pick':
            l1, l2 = d.get('half1'), d.get('half2')
            if not l1 or not l2:
                return jsonify(error='Choose two half-cells.'), 400
            if l1 == l2:
                return jsonify(error='Choose two different half-cells.'), 400
            h1, h2 = _half_cell(l1), _half_cell(l2)
            (cat_l, cat), (ano_l, ano) = sorted([(l1, h1), (l2, h2)], key=lambda x: -x[1][0])
            E_cat, E_ano = cat[0], ano[0]
            E_cell = cell_potential(E_cat, E_ano)
            n = math.lcm(cat[4], ano[4])
            warnings, equation = [], None
            if E_cell == 0:
                warnings.append('Both half-cells have the same E°, so E°cell = 0.')
            try:
                medium = 'acidic' if (cat[3] or ano[3]) else None
                # cathode is reduced, anode is oxidised; merge duplicates (Fe2+ made twice)
                r_raw, p_raw = [cat[1], ano[2]], [cat[2], ano[1]]
                key = lambda x: (parse_species(x).formula, parse_species(x).charge)
                if medium and ('H', 1) in {key(x) for x in r_raw + p_raw}:
                    # let the acidic option put H+ on whichever side it belongs
                    r_raw = [x for x in r_raw if key(x) != ('H', 1)]
                    p_raw = [x for x in p_raw if key(x) != ('H', 1)]
                r_list = list({key(x): x for x in r_raw}.values())
                p_list = list({key(x): x for x in p_raw}.values())
                overall = balance_full(r_list, p_list, medium)
                equation = overall['equation']
                ox_c = next(c for c, sp in overall['reactants'] if (sp.formula, sp.charge) == key(cat[1]))
                n = cat[4] * ox_c // cat[5]
            except (ValueError, StopIteration):
                warnings.append('Could not write the overall equation for this pair.')
            dG = gibbs_from_cell(n, E_cell)
            spont, ctype = spontaneity_check(E_cell), cell_type(E_cell)
            compact = f'E°cell = {E_cell:+.2f} V,  ΔG° = {dG:.4g} kJ/mol'
            detailed = [
                f'Cathode (reduction, higher E°): {cat_l}   E° = {E_cat:+.2f} V',
                f'   {cat[6]}',
                f'Anode (oxidation, lower E°):    {ano_l}   E° = {E_ano:+.2f} V',
                f'   {" → ".join(reversed(ano[6].split(" → ")))}',
                *([f'Overall: {equation}'] if equation else []),
                f'E°cell = E°cathode − E°anode = {E_cat:+.2f} − ({E_ano:+.2f}) = {E_cell:+.2f} V',
                f'Electrons transferred: n = {n}',
                f'ΔG° = −nFE° = −{n} × 96485 × {E_cell:.2f} ÷ 1000 = {dG:.4g} kJ/mol',
                f'Conclusion: {spont} → {ctype} cell',
            ]
            return jsonify(E_cell=E_cell, dG=dG, n=n, cathode=cat_l, anode=ano_l,
                           equation=equation, spontaneity=spont, cell_type=ctype,
                           compact=compact, detailed=detailed, warnings=warnings)

        if t == 'cell':
            E_cat  = float(d['E_cat'])
            E_ano  = float(d['E_ano'])
            n      = int(d['n'])
            E_cell = cell_potential(E_cat, E_ano)
            dG     = gibbs_from_cell(n, E_cell)
            spont  = spontaneity_check(E_cell)
            ctype  = cell_type(E_cell)
            compact  = f'E°cell = {E_cell:+.4f} V  ({spont}, {ctype} cell)'
            detailed = [
                f'Cathode (reduction): E° = {E_cat:+.4f} V',
                f'Anode   (oxidation): E° = {E_ano:+.4f} V',
                'Formula: E°cell = E°cathode − E°anode',
                f'E°cell = {E_cat:+.4f} − ({E_ano:+.4f}) = {E_cell:+.4f} V',
                f'Electrons transferred: n = {n}',
                'Gibbs free energy: ΔG° = −nFE°cell',
                f'ΔG° = −{n} × 96485 × ({E_cell:+.4f})',
                f'ΔG° = {dG:.2f} kJ/mol',
                f'Conclusion: {spont} → {ctype} cell',
            ]
            return jsonify(E_cell=E_cell, dG=dG, spontaneity=spont, cell_type=ctype,
                           compact=compact, detailed=detailed, warnings=[])

        elif t == 'faraday':
            solve = d.get('solve')
            mass  = float(d['mass']) if d.get('mass') else None
            I     = float(d['I'])    if d.get('I')    else None
            time  = float(d['t'])    if d.get('t')    else None
            M     = float(d['M'])    if d.get('M')    else None
            n     = int(d['n'])      if d.get('n')    else None
            fml_map = {
                'mass':       'mass = (I × t × M) / (n × F)',
                'current':    'I = (mass × n × F) / (t × M)',
                'time':       't = (mass × n × F) / (I × M)',
                'molar_mass': 'M = (mass × n × F) / (I × t)',
            }
            if solve == 'mass':       result, unit = faraday_mass(I, time, M, n), 'g'
            elif solve == 'current':  result, unit = faraday_current(mass, time, M, n), 'A'
            elif solve == 'time':     result, unit = faraday_time(mass, I, M, n), 's'
            elif solve == 'molar_mass': result, unit = faraday_molar_mass(mass, I, time, n), 'g/mol'
            else: return jsonify(error='Unknown solve target'), 400
            given = {k:v for k,v in {'mass':mass,'I':I,'t':time,'M':M,'n':n}.items() if v is not None}
            compact  = f'{solve} = {result:.4g} {unit}'
            detailed = [
                "Faraday's Law of Electrolysis",
                f'Formula: {fml_map[solve]}',
                f'F = 96485 C/mol',
                f'Given: ' + ', '.join(f'{k}={v}' for k,v in given.items()),
                f'Result: {result:.4g} {unit}',
            ]
            return jsonify(result=result, unit=unit, compact=compact, detailed=detailed, warnings=[])

        elif t == 'nernst':
            E0 = float(d['E0'])
            n  = int(d['n'])
            Q  = float(d['Q'])
            T  = float(d.get('T') or 298.15)
            E  = nernst(E0, n, Q, T)
            factor = R_GAS * T / (n * F_CONST)
            ln_Q   = math.log(Q)
            compact  = f'E = {E:+.4f} V'
            detailed = [
                'Nernst Equation: E = E° − (RT/nF) × ln(Q)',
                f'Given: E° = {E0:+.4f} V,  n = {n},  Q = {Q},  T = {T} K',
                f'RT/nF = (8.314 × {T}) / ({n} × 96485) = {factor:.6f} V',
                f'ln(Q) = ln({Q}) = {ln_Q:.4f}',
                f'E = {E0:+.4f} − ({factor:.6f} × {ln_Q:.4f})',
                f'E = {E0:+.4f} − {factor*ln_Q:.4f}',
                f'E = {E:+.4f} V',
            ]
            return jsonify(E=E, compact=compact, detailed=detailed, warnings=[])

        else:
            return jsonify(error='Unknown type'), 400
    except Exception as e:
        return _err(e)


# ── 17. Kinetics ──────────────────────────────────────────────────────────────
@app.route('/api/kinetics', methods=['POST'])
def api_kinetics():
    d = request.json or {}
    t = d.get('type')
    try:
        if t == 'order':
            c1, c2 = float(d['c1']), float(d['c2'])
            r1, r2 = float(d['r1']), float(d['r2'])
            order  = determine_order(c1, c2, r1, r2)
            k      = rate_constant_from_experiment(r1, [c1], [order])
            ku     = k_units(round(order))
            compact  = f'Order = {order:.3f} ≈ {round(order)},  k = {k:.4g} {ku}'
            detailed = [
                'Determining reaction order from two experiments',
                f'Experiment 1: [A] = {c1} mol/L,  rate = {r1}',
                f'Experiment 2: [A] = {c2} mol/L,  rate = {r2}',
                'Formula: order = log(r₂/r₁) / log(c₂/c₁)',
                f'= log({r2}/{r1}) / log({c2}/{c1})',
                f'= log({r2/r1:.4g}) / log({c2/c1:.4g})',
                f'= {order:.4f}  ≈  {round(order)}',
                f'Rate constant: k = rate / [A]^order',
                f'k = {r1} / {c1}^{order:.3f} = {k:.4g} {ku}',
            ]
            warnings = ([f'Non-integer order ({order:.3f}) — verify experimental data']
                        if abs(order - round(order)) > 0.15 else [])
            return jsonify(order=order, k=k, k_units=ku,
                           compact=compact, detailed=detailed, warnings=warnings)

        elif t == 'arrhenius':
            solve = d.get('solve')
            k1 = float(d['k1']); T1 = float(d['T1']); T2 = float(d['T2'])
            inv_diff = 1/T2 - 1/T1
            if solve == 'Ea':
                k2   = float(d['k2'])
                Ea_J = arrhenius_Ea(k1, T1, k2, T2)
                compact  = f'Ea = {Ea_J/1000:.2f} kJ/mol'
                detailed = [
                    'Arrhenius equation: ln(k₂/k₁) = −Ea/R × (1/T₂ − 1/T₁)',
                    f'Given: k₁={k1}, T₁={T1} K,  k₂={k2}, T₂={T2} K',
                    f'ln(k₂/k₁) = ln({k2/k1:.4g}) = {math.log(k2/k1):.4f}',
                    f'1/T₂ − 1/T₁ = {inv_diff:.6e} K⁻¹',
                    'Ea = −R × ln(k₂/k₁) / (1/T₂ − 1/T₁)',
                    f'Ea = −8.314 × {math.log(k2/k1):.4f} / ({inv_diff:.6e})',
                    f'Ea = {Ea_J:.2f} J/mol = {Ea_J/1000:.2f} kJ/mol',
                ]
                return jsonify(Ea_J=Ea_J, Ea_kJ=Ea_J/1000,
                               compact=compact, detailed=detailed, warnings=[])
            else:
                Ea_J = float(d['Ea'])
                k2   = arrhenius_k2(k1, T1, T2, Ea_J)
                compact  = f'k₂ = {k2:.4g} at T₂ = {T2} K'
                detailed = [
                    'Arrhenius equation: k₂ = k₁ × exp(−Ea/R × (1/T₂ − 1/T₁))',
                    f'Given: k₁={k1}, T₁={T1} K, T₂={T2} K, Ea={Ea_J} J/mol',
                    f'Ea/R = {Ea_J}/8.314 = {Ea_J/R_GAS:.2f} K',
                    f'1/T₂ − 1/T₁ = {inv_diff:.6e} K⁻¹',
                    f'Exponent = −(Ea/R)(1/T₂−1/T₁) = {-Ea_J/R_GAS * inv_diff:.4f}',
                    f'k₂ = {k1} × exp({-Ea_J/R_GAS * inv_diff:.4f})',
                    f'k₂ = {k2:.4g}',
                ]
                return jsonify(k2=k2, compact=compact, detailed=detailed, warnings=[])

        elif t == 'halflife':
            solve = d.get('solve')
            if solve == 't_half':
                k_val   = float(d['k'])
                t_half  = math.log(2) / k_val
                compact  = f't½ = {t_half:.4g} s'
                detailed = [
                    'First-order half-life: t½ = ln(2) / k',
                    f'Given: k = {k_val} s⁻¹',
                    f't½ = 0.6931 / {k_val}',
                    f't½ = {t_half:.4g} s',
                    f't½ = {t_half/60:.4g} min',
                ]
                return jsonify(t_half=t_half, compact=compact, detailed=detailed, warnings=[])
            else:
                t_half  = float(d['t_half'])
                k_val   = math.log(2) / t_half
                compact  = f'k = {k_val:.4g} s⁻¹'
                detailed = [
                    'Solving for k: k = ln(2) / t½',
                    f'Given: t½ = {t_half} s',
                    f'k = 0.6931 / {t_half}',
                    f'k = {k_val:.4g} s⁻¹',
                ]
                return jsonify(k=k_val, compact=compact, detailed=detailed, warnings=[])

        elif t == 'arrhenius_graph':
            rows = [r for r in d.get('points', [])
                    if str(r.get('T') or '').strip() or str(r.get('k') or '').strip()]
            if len(rows) < 2:
                return jsonify(error='Enter at least two (T, k) pairs.'), 400
            temps = [_num(r, 'T', 'temperature', positive=True) for r in rows]
            ks = [_num(r, 'k', 'rate constant', positive=True) for r in rows]
            res = arrhenius_from_data(temps, ks)
            detailed = [
                'Graphical Arrhenius method: plot ln k (y) against 1/T (x)',
                'Points:',
                *[f'  T = {T:g} K → 1/T = {1/T:.6g} K⁻¹,  k = {k:g} → ln k = {math.log(k):.4f}'
                  for T, k in zip(temps, ks)],
                f'Line of best fit: ln k = {res["gradient"]:.4g} × (1/T) + {res["intercept"]:.4g}   (r² = {res["r2"]:.5f})',
                'gradient = −Ea/R, so Ea = −R × gradient',
                f'Ea = −8.314 × {res["gradient"]:.4g} = {res["Ea_J"]:.4g} J/mol = {res["Ea_kJ"]:.4g} kJ/mol',
                f'intercept = ln A, so A = e^{res["intercept"]:.4g} = {res["A"]:.4g}',
            ]
            warnings = ([f'r² = {res["r2"]:.4f} — the points do not lie close to a straight line.']
                        if res['r2'] < 0.95 else [])
            return jsonify(Ea_J=res['Ea_J'], Ea_kJ=res['Ea_kJ'], A=res['A'], gradient=res['gradient'],
                           intercept=res['intercept'], r2=res['r2'],
                           answers=[_answer('Ea', res['Ea_kJ'], 'kJ/mol'), _answer('A', res['A']),
                                    _answer('r²', res['r2'])],
                           compact=f'Ea = {res["Ea_kJ"]:.4g} kJ/mol,  A = {res["A"]:.4g}',
                           detailed=detailed, warnings=warnings)

        elif t == 'integrated':
            order = int(_num(d, 'order', 'order'))
            if order not in (0, 1, 2):
                return jsonify(error='Order must be 0, 1 or 2.'), 400
            solve = d.get('solve')
            A0 = _num(d, 'A0', '[A]₀', positive=True)
            k = _num(d, 'k', 'k', positive=True)
            law = {0: '[A]t = [A]₀ − kt', 1: 'ln[A]t = ln[A]₀ − kt  ([A]t = [A]₀e^(−kt))',
                   2: '1/[A]t = 1/[A]₀ + kt'}[order]
            half = {0: A0 / (2 * k), 1: math.log(2) / k, 2: 1 / (k * A0)}[order]
            half_f = {0: 't½ = [A]₀ ÷ 2k', 1: 't½ = ln 2 ÷ k', 2: 't½ = 1 ÷ (k[A]₀)'}[order]
            ku = k_units(order)
            if solve == 'At':
                tt = _num(d, 't', 't', positive=True, allow_zero=True)
                result = irl_concentration(order, A0, k, tt)
                compact = f'[A]t = {result:.4g} mol/dm³'
                given = f'Given: [A]₀ = {A0:g} mol/dm³, k = {k:g} {ku}, t = {tt:g} s'
                last = f'[A] after {tt:g} s = {result:.4g} mol/dm³'
            elif solve == 't':
                At = _num(d, 'At', '[A]t', positive=True)
                result = irl_time(order, A0, At, k)
                compact = f't = {result:.4g} s'
                given = f'Given: [A]₀ = {A0:g} mol/dm³, [A]t = {At:g} mol/dm³, k = {k:g} {ku}'
                last = f'Time to fall from {A0:g} to {At:g} mol/dm³ = {result:.4g} s'
            else:
                return jsonify(error='Unknown solve target'), 400
            detailed = [f'Order {order} integrated rate law: {law}', given, last,
                        f'Half-life for this order: {half_f} = {half:.4g} s']
            return jsonify(result=result, half_life=half, compact=compact,
                           detailed=detailed, warnings=[])

        elif t == 'kunits':
            order_i  = int(d.get('order', 1))
            units_str = k_units(order_i)
            compact  = f'Order {order_i}: k units = {units_str}'
            detailed = [
                f'Overall reaction order: {order_i}',
                f'Rate law: rate = k × [A]^{order_i}',
                'Units of rate: mol·L⁻¹·s⁻¹',
                f'Units of [A]^{order_i}: (mol·L⁻¹)^{order_i}',
                'Solving for k: k = rate / [A]^order',
                f'k units = (mol·L⁻¹·s⁻¹) / (mol·L⁻¹)^{order_i}',
                f'k units = {units_str}',
            ]
            return jsonify(order=order_i, units=units_str,
                           compact=compact, detailed=detailed, warnings=[])

        else:
            return jsonify(error='Unknown type'), 400
    except Exception as e:
        return _err(e)


if __name__ == '__main__':
    # Debug mode exposes an interactive debugger — keep it opt-in, and stay on
    # localhost unless CHEMCALC_HOST says otherwise.
    debug = os.environ.get('CHEMCALC_DEBUG') == '1'
    host = os.environ.get('CHEMCALC_HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', '5000'))
    print(f'ChemCalc FX-17 on http://{host}:{port}   (debug={"on" if debug else "off"})')
    app.run(debug=debug, host=host, port=port)
