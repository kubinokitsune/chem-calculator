from flask import Flask, request, jsonify, send_from_directory
import sys, os

# Make all chemistry modules importable from parent directory
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..')))

from mole_conversions import (mass_to_moles, moles_to_mass, moles_to_particles,
                               particles_to_moles, moles_to_volume, volume_to_moles)
from Empirical_Formula_Calculator import calculate_empirical_formula, display_empirical_formula
from equation_balancer import balance_equation
from percent_composition_calculator import compute_percent_composition, FormulaError
from volume_mass_conversions import mass_to_volume, volume_to_mass, density_from_mv
from oxidation_number_calculator import solve_oxidation_numbers
from atom_economy_calculator import calculate_atom_economy
from ionic_bonding_calculator import classify_bond, write_ionic_formula
from percentage_yield_calculator import calc_percentage_yield, calc_actual_yield, calc_theoretical_yield
from Periodic_table import get_element_by_name, get_element_by_symbol, get_element_by_number

app = Flask(__name__, static_folder='.', static_url_path='')


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


# ── 1. Mole Conversions ───────────────────────────────────────────────────
@app.route('/api/mole', methods=['POST'])
def api_mole():
    d = request.json or {}
    t, a, b = d.get('type'), d.get('a'), d.get('b')
    try:
        a = float(a)
        if t == 'mass_to_moles':    result, unit = mass_to_moles(a, float(b)), 'mol'
        elif t == 'moles_to_mass':  result, unit = moles_to_mass(a, float(b)), 'g'
        elif t == 'moles_to_particles': result, unit = moles_to_particles(a), 'particles'
        elif t == 'particles_to_moles': result, unit = particles_to_moles(a), 'mol'
        elif t == 'moles_to_volume':result, unit = moles_to_volume(a), 'L'
        elif t == 'volume_to_moles':result, unit = volume_to_moles(a), 'mol'
        else: return jsonify(error='Unknown conversion type'), 400
        return jsonify(result=result, unit=unit)
    except Exception as e:
        return jsonify(error=str(e)), 400


# ── 2. Empirical Formula ──────────────────────────────────────────────────
@app.route('/api/empirical', methods=['POST'])
def api_empirical():
    d = request.json or {}
    try:
        formula = calculate_empirical_formula(d['elements'], [float(m) for m in d['masses']])
        return jsonify(formula=display_empirical_formula(formula))
    except Exception as e:
        return jsonify(error=str(e)), 400


# ── 3. Equation Balancer ──────────────────────────────────────────────────
@app.route('/api/equation', methods=['POST'])
def api_equation():
    d = request.json or {}
    eq = d.get('equation', '').strip()
    if '->' not in eq:
        return jsonify(error="Equation must contain '->' to separate reactants and products."), 400
    try:
        r_str, p_str = eq.split('->', 1)
        reactants = [r.strip() for r in r_str.split('+') if r.strip()]
        products  = [p.strip() for p in p_str.split('+') if p.strip()]
        if not reactants or not products:
            return jsonify(error='Must have at least one reactant and one product.'), 400
        rc, pc = balance_equation(reactants, products)
        balanced = ' + '.join(f'{rc[i]}{reactants[i]}' for i in range(len(reactants)))
        balanced += ' -> '
        balanced += ' + '.join(f'{pc[i]}{products[i]}' for i in range(len(products)))
        return jsonify(balanced=balanced, reactant_coeffs=rc, product_coeffs=pc,
                       reactants=reactants, products=products)
    except Exception as e:
        return jsonify(error=str(e)), 400


# ── 4. Limiting Reactant ──────────────────────────────────────────────────
@app.route('/api/limiting', methods=['POST'])
def api_limiting():
    d = request.json or {}
    try:
        rd = d['reactants']
        pd = d['products']
        reactants = [r['name'] for r in rd]
        r_coeffs  = [float(r['coeff']) for r in rd]
        r_moles   = [float(r['moles']) for r in rd]
        products  = [p['name'] for p in pd]
        p_coeffs  = [float(p['coeff']) for p in pd]

        ratios    = [r_moles[i] / r_coeffs[i] for i in range(len(reactants))]
        lim_idx   = ratios.index(min(ratios))
        limiting  = reactants[lim_idx]

        leftovers = {r: round(max(r_moles[i] - r_coeffs[i] * ratios[lim_idx], 0), 4)
                     for i, r in enumerate(reactants)}
        yields    = {p: round(p_coeffs[i] * ratios[lim_idx], 4)
                     for i, p in enumerate(products)}

        return jsonify(limiting=limiting, leftovers=leftovers, yields=yields)
    except Exception as e:
        return jsonify(error=str(e)), 400


# ── 5. Percent Composition ────────────────────────────────────────────────
@app.route('/api/percent', methods=['POST'])
def api_percent():
    d = request.json or {}
    try:
        mm, percents = compute_percent_composition(d['formula'])
        return jsonify(formula=d['formula'],
                       molar_mass=round(mm, 3),
                       percents={k: round(v, 2) for k, v in percents.items()})
    except Exception as e:
        return jsonify(error=str(e)), 400


# ── 6. Volume-to-Mass ─────────────────────────────────────────────────────
@app.route('/api/volume', methods=['POST'])
def api_volume():
    d = request.json or {}
    t, a, b = d.get('type'), d.get('a'), d.get('b')
    try:
        a, b = float(a), float(b)
        if t == 'mass_to_volume':
            if b <= 0: return jsonify(error='Density must be greater than zero.'), 400
            result, unit = mass_to_volume(a, b), 'mL'
        elif t == 'volume_to_mass':
            if b <= 0: return jsonify(error='Density must be greater than zero.'), 400
            result, unit = volume_to_mass(a, b), 'g'
        elif t == 'density':
            if b <= 0: return jsonify(error='Volume must be greater than zero.'), 400
            result, unit = density_from_mv(a, b), 'g/mL'
        else:
            return jsonify(error='Unknown conversion type'), 400
        return jsonify(result=round(result, 4), unit=unit)
    except Exception as e:
        return jsonify(error=str(e)), 400


# ── 7. Oxidation Numbers ──────────────────────────────────────────────────
@app.route('/api/oxidation', methods=['POST'])
def api_oxidation():
    d = request.json or {}
    try:
        result = solve_oxidation_numbers(d['formula'], int(d.get('charge', 0)), bool(d.get('peroxide', False)))
        return jsonify(formula=d['formula'], charge=int(d.get('charge', 0)),
                       numbers={k: round(v, 4) for k, v in result.items()})
    except Exception as e:
        return jsonify(error=str(e)), 400


# ── 8. Atom Economy ───────────────────────────────────────────────────────
@app.route('/api/atom_eco', methods=['POST'])
def api_atom_eco():
    d = request.json or {}
    try:
        rd = d['reactants']
        desired = d['desired']
        formulas = [r['formula'] for r in rd]
        coeffs   = [float(r['coeff']) for r in rd]
        ae, mw_d, mw_r = calculate_atom_economy(formulas, coeffs, desired['formula'], float(desired['coeff']))
        return jsonify(atom_economy=round(ae, 2), mw_desired=round(mw_d, 3), mw_reactants=round(mw_r, 3))
    except Exception as e:
        return jsonify(error=str(e)), 400


# ── 9. Ionic Bonding ──────────────────────────────────────────────────────
@app.route('/api/ionic', methods=['POST'])
def api_ionic():
    d = request.json or {}
    action = d.get('action')
    try:
        if action == 'classify':
            bond_type, en1, en2, diff = classify_bond(d['elem1'], d['elem2'])
            return jsonify(bond_type=bond_type, en1=round(en1, 2), en2=round(en2, 2),
                           diff=round(diff, 2), elem1=d['elem1'], elem2=d['elem2'])
        else:
            formula = write_ionic_formula(d['cation'], int(d['cation_charge']), d['anion'], int(d['anion_charge']))
            return jsonify(formula=formula, cation=d['cation'], anion=d['anion'],
                           cation_charge=int(d['cation_charge']), anion_charge=int(d['anion_charge']))
    except Exception as e:
        return jsonify(error=str(e)), 400


# ── 10. Percentage Yield ──────────────────────────────────────────────────
@app.route('/api/yield_calc', methods=['POST'])
def api_yield():
    d = request.json or {}
    t, a, b = d.get('type'), d.get('a'), d.get('b')
    try:
        a, b = float(a), float(b)
        if t == 'percent':
            if b <= 0: return jsonify(error='Theoretical yield must be > 0'), 400
            result, unit = calc_percentage_yield(a, b), '%'
            warning = 'Yield > 100% suggests impurities or measurement error.' if result > 100 else None
        elif t == 'actual':
            if b <= 0: return jsonify(error='Theoretical yield must be > 0'), 400
            result, unit = calc_actual_yield(a, b), 'g'
            warning = None
        elif t == 'theoretical':
            if a <= 0: return jsonify(error='Percentage yield must be > 0'), 400
            result, unit = calc_theoretical_yield(b, a), 'g'
            warning = None
        else:
            return jsonify(error='Unknown type'), 400
        resp = dict(result=round(result, 4), unit=unit)
        if warning:
            resp['warning'] = warning
        return jsonify(**resp)
    except Exception as e:
        return jsonify(error=str(e)), 400


# ── 11. Periodic Table ────────────────────────────────────────────────────
@app.route('/api/periodic', methods=['POST'])
def api_periodic():
    d = request.json or {}
    t, q = d.get('type'), d.get('query', '').strip()
    try:
        if t == 'symbol':   elem = get_element_by_symbol(q)
        elif t == 'name':   elem = get_element_by_name(q)
        elif t == 'number': elem = get_element_by_number(int(q))
        else: return jsonify(error='Unknown search type'), 400

        if not elem:
            return jsonify(found=False)
        return jsonify(found=True, number=elem['number'], symbol=elem['symbol'],
                       name=elem['name'].capitalize(), atomic_weight=elem['atomic_weight'])
    except Exception as e:
        return jsonify(error=str(e)), 400


if __name__ == '__main__':
    app.run(debug=True, port=5000)
