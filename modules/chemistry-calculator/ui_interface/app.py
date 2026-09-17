from flask import Flask, request, jsonify, send_from_directory
from flask.json.provider import DefaultJSONProvider
import sys, os, math

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..')))

from mole_conversions import (mass_to_moles, moles_to_mass, moles_to_particles,
                               particles_to_moles, moles_to_volume, volume_to_moles)
from Empirical_Formula_Calculator import calculate_empirical_formula, display_empirical_formula
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
                       weak_acid_pH, weak_base_pH, buffer_pH, identify)
from thermodynamics import (cal_q, cal_m, cal_c, cal_dT, hess_law,
                             bond_enthalpy_dH, lookup_bond, gibbs_dG)
from ice_solver import build_ice_table
from electrochemistry import (cell_potential, gibbs_from_cell, faraday_mass,
                               faraday_current, faraday_time, faraday_molar_mass,
                               nernst, spontaneity_check, cell_type)
from kinetics import (determine_order, rate_constant_from_experiment, arrhenius_Ea,
                      arrhenius_k2, k_units)



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


app = Flask(__name__, static_folder='.', static_url_path='')
app.json = StrictJSONProvider(app)

R_GAS = 8.314   # J/mol·K
F_CONST = 96485  # C/mol


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
            bv = float(b)
            result = mass_to_moles(a, bv)
            compact  = f'Moles = {result:.4g} mol'
            detailed = [
                f'Given: mass = {a} g, molar mass M = {bv} g/mol',
                'Formula: n = mass / M',
                f'n = {a} / {bv}',
                f'n = {result:.6g} mol',
            ]
        elif t == 'moles_to_mass':
            bv = float(b)
            result = moles_to_mass(a, bv)
            compact  = f'Mass = {result:.4g} g'
            detailed = [
                f'Given: n = {a} mol, molar mass M = {bv} g/mol',
                'Formula: mass = n × M',
                f'mass = {a} × {bv}',
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
    try:
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
        return jsonify(limiting=res['limiting'][0], limiting_all=res['limiting'],
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
        return jsonify(formula=d['formula'], molar_mass=round(mm, 3),
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
        return jsonify(result=round(result, 4), unit={'mass_to_volume':'mL','volume_to_mass':'g','density':'g/mL'}[t],
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
        return jsonify(result=round(result, 4), compact=compact, detailed=detailed, warnings=warnings)
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


# ── 15. ICE Solver ────────────────────────────────────────────────────────────
@app.route('/api/ice', methods=['POST'])
def api_ice():
    d = request.json or {}
    try:
        rd = d['reactants']
        pd = d['products']
        r_names  = [r['name'] for r in rd]
        r_coeffs = [float(r['coeff']) for r in rd]
        r_init   = [float(r['initial']) for r in rd]
        p_names  = [p['name'] for p in pd]
        p_coeffs = [float(p['coeff']) for p in pd]
        p_init   = [float(p['initial']) for p in pd]
        Kc = float(d['Kc'])
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
        warnings = ([f'x/{min(r_init):.4g} = {res["approx_pct"]:.1f}% > 5% — exact (bisection) method used, not approximation']
                    if res['approx_pct'] > 5 else [])
        return jsonify(x=x, r_names=r_names, p_names=p_names,
                       r_eq=res['r_eq'], p_eq=res['p_eq'],
                       Q_initial=res['Q_initial'], Q_final=res['Q_final'],
                       approx_pct=res['approx_pct'],
                       compact=compact, detailed=detailed, warnings=warnings)
    except Exception as e:
        return _err(e)


# ── 16. Electrochemistry ──────────────────────────────────────────────────────
@app.route('/api/electrochem', methods=['POST'])
def api_electrochem():
    d = request.json or {}
    t = d.get('type')
    try:
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
            T  = float(d.get('T', 298.15))
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
    app.run(debug=True, port=5000)
