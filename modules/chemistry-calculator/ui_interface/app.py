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
from gas_laws import (ideal_gas_find_P, ideal_gas_find_V, ideal_gas_find_n, ideal_gas_find_T,
                      combined_gas_find_P2, combined_gas_find_V2, combined_gas_find_T2,
                      graham_rate_ratio, dalton_total_pressure)
from acid_base import (all_four, strong_acid_pH, strong_base_pH,
                       weak_acid_pH, weak_base_pH, buffer_pH, identify)
from thermodynamics import (cal_q, cal_m, cal_c, cal_dT, hess_law,
                             bond_enthalpy_dH, lookup_bond, BOND_ENTHALPIES)
from ice_solver import build_ice_table
from electrochemistry import (cell_potential, gibbs_from_cell, faraday_mass,
                               faraday_current, faraday_time, faraday_molar_mass,
                               nernst, spontaneity_check, cell_type)
from kinetics import (determine_order, rate_constant_from_experiment, arrhenius_Ea,
                      arrhenius_k2, k_units)

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
        if t == 'mass_to_moles':
            bv = float(b)
            result, unit = mass_to_moles(a, bv), 'mol'
            compact = f'Moles = {result:.4g} mol'
            steps   = [
                f'Formula:  n = mass / M',
                f'Values:   n = {a} g / {bv} g·mol⁻¹',
                f'Result:   n = {result:.6g} mol',
            ]
        elif t == 'moles_to_mass':
            bv = float(b)
            result, unit = moles_to_mass(a, bv), 'g'
            compact = f'Mass = {result:.4g} g'
            steps   = [
                f'Formula:  m = n × M',
                f'Values:   m = {a} mol × {bv} g·mol⁻¹',
                f'Result:   m = {result:.6g} g',
            ]
        elif t == 'moles_to_particles':
            result, unit = moles_to_particles(a), 'particles'
            compact = f'Particles = {result:.4g}'
            steps   = [
                f'Formula:  N = n × Nₐ',
                f'Values:   N = {a} mol × 6.022 × 10²³',
                f'Result:   N = {result:.6g} particles',
            ]
        elif t == 'particles_to_moles':
            result, unit = particles_to_moles(a), 'mol'
            compact = f'Moles = {result:.4g} mol'
            steps   = [
                f'Formula:  n = N / Nₐ',
                f'Values:   n = {a} / 6.022 × 10²³',
                f'Result:   n = {result:.6g} mol',
            ]
        elif t == 'moles_to_volume':
            result, unit = moles_to_volume(a), 'L'
            compact = f'Volume = {result:.4g} L'
            steps   = [
                f'Formula:  V = n × 22.4 L·mol⁻¹  (STP)',
                f'Values:   V = {a} mol × 22.4',
                f'Result:   V = {result:.6g} L',
            ]
        elif t == 'volume_to_moles':
            result, unit = volume_to_moles(a), 'mol'
            compact = f'Moles = {result:.4g} mol'
            steps   = [
                f'Formula:  n = V / 22.4 L·mol⁻¹  (STP)',
                f'Values:   n = {a} L / 22.4',
                f'Result:   n = {result:.6g} mol',
            ]
        else:
            return jsonify(error='Unknown conversion type'), 400
        return jsonify(result=result, unit=unit, compact=compact, steps=steps)
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


# ── 12. Gas Laws ─────────────────────────────────────────────────────────────
@app.route('/api/gas_laws', methods=['POST'])
def api_gas_laws():
    d = request.json or {}
    t = d.get('type')
    try:
        if t == 'ideal':
            solve = d.get('solve')
            vals = {k: float(d[k]) for k in ('n', 'v', 'T', 'p') if d.get(k)}
            if solve == 'P':
                result = ideal_gas_find_P(vals['n'], vals['v'], vals['T']); unit = 'atm'
            elif solve == 'V':
                result = ideal_gas_find_V(vals['n'], vals['T'], vals['p']); unit = 'L'
            elif solve == 'n':
                result = ideal_gas_find_n(vals['p'], vals['v'], vals['T']); unit = 'mol'
            elif solve == 'T':
                result = ideal_gas_find_T(vals['p'], vals['v'], vals['n']); unit = 'K'
            else:
                return jsonify(error='Unknown solve target'), 400
            return jsonify(result=result, unit=unit)

        elif t == 'combined':
            solve = d.get('solve')
            P1, V1, T1 = float(d['P1']), float(d['V1']), float(d['T1'])
            if solve == 'P2':
                result = combined_gas_find_P2(P1, V1, T1, float(d['V2']), float(d['T2'])); unit = 'atm'
            elif solve == 'V2':
                result = combined_gas_find_V2(P1, V1, T1, float(d['P2']), float(d['T2'])); unit = 'L'
            elif solve == 'T2':
                result = combined_gas_find_T2(P1, V1, T1, float(d['P2']), float(d['V2'])); unit = 'K'
            else:
                return jsonify(error='Unknown solve target'), 400
            return jsonify(result=result, unit=unit)

        elif t == 'graham':
            M1, M2 = float(d['M1']), float(d['M2'])
            if M1 <= 0 or M2 <= 0:
                return jsonify(error='Molar masses must be positive'), 400
            return jsonify(result=graham_rate_ratio(M1, M2))

        elif t == 'dalton':
            gases = d.get('gases', [])
            partials = [{'name': g['name'], 'p': float(g['p'])} for g in gases]
            total = dalton_total_pressure([g['p'] for g in partials])
            return jsonify(total=total, partials=partials)

        else:
            return jsonify(error='Unknown gas law type'), 400
    except Exception as e:
        return jsonify(error=str(e)), 400


# ── 13. Acid-Base ─────────────────────────────────────────────────────────────
@app.route('/api/acid_base', methods=['POST'])
def api_acid_base():
    d = request.json or {}
    t = d.get('type')
    try:
        if t == 'ph_convert':
            it = d.get('input_type')
            v = float(d['value'])
            kwargs = {'H': v} if it == 'H' else {'OH': v} if it == 'OH' else \
                     {'pH': v} if it == 'pH' else {'pOH': v}
            pH, pOH, H, OH = all_four(**kwargs)
        elif t == 'strong_acid':
            pH = strong_acid_pH(float(d['conc']))
            _, pOH, H, OH = all_four(pH=pH)
        elif t == 'strong_base':
            pH = strong_base_pH(float(d['conc']))
            _, pOH, H, OH = all_four(pH=pH)
        elif t == 'weak_acid':
            pH, approx, x = weak_acid_pH(float(d['Ka']), float(d['conc']))
            _, pOH, H, OH = all_four(pH=pH)
            note = f"Approximation {'valid (x/C ≤ 5%)' if approx else 'invalid — quadratic used'}; [H⁺] = {x:.4e}"
            return jsonify(pH=pH, pOH=pOH, H=H, OH=OH, note=note)
        elif t == 'weak_base':
            pH, approx, x = weak_base_pH(float(d['Kb']), float(d['conc']))
            _, pOH, H, OH = all_four(pH=pH)
            note = f"Approximation {'valid' if approx else 'invalid — quadratic used'}; [OH⁻] = {x:.4e}"
            return jsonify(pH=pH, pOH=pOH, H=H, OH=OH, note=note)
        elif t == 'buffer':
            pH = buffer_pH(float(d['Ka']), float(d['acid']), float(d['base']))
            _, pOH, H, OH = all_four(pH=pH)
        elif t == 'identify':
            return jsonify(formula=d['formula'], identity=identify(d['formula']))
        else:
            return jsonify(error='Unknown type'), 400
        return jsonify(pH=pH, pOH=pOH, H=H, OH=OH)
    except Exception as e:
        return jsonify(error=str(e)), 400


# ── 14. Thermodynamics ────────────────────────────────────────────────────────
@app.route('/api/thermo', methods=['POST'])
def api_thermo():
    d = request.json or {}
    t = d.get('type')
    try:
        if t == 'calorimetry':
            solve = d.get('solve')
            q = float(d['q']) if d.get('q') else None
            m = float(d['m']) if d.get('m') else None
            c = float(d['c']) if d.get('c') else None
            dT = float(d['dT']) if d.get('dT') else None
            if solve == 'q':   result, unit = cal_q(m, c, dT), 'J'
            elif solve == 'm': result, unit = cal_m(q, c, dT), 'g'
            elif solve == 'c': result, unit = cal_c(q, m, dT), 'J/g·K'
            elif solve == 'dT':result, unit = cal_dT(q, m, c), 'K'
            else: return jsonify(error='Unknown solve target'), 400
            return jsonify(result=result, unit=unit)

        elif t == 'hess':
            steps = d.get('steps', [])
            dH_vals = [float(s['dH']) for s in steps]
            mults   = [float(s['mult']) for s in steps]
            return jsonify(result=hess_law(dH_vals, mults))

        elif t == 'bond':
            def parse_bonds(lst):
                out = []
                for b in lst:
                    label = b['bond']
                    count = float(b.get('count', 1))
                    kj = b.get('kJ', '')
                    if kj:
                        enth = float(kj)
                    else:
                        enth = lookup_bond(label)
                        if enth is None:
                            raise KeyError(f"Bond '{label}' not in table. Provide kJ/mol manually.")
                    out.append((label, count, enth))
                return out
            broken = parse_bonds(d.get('broken', []))
            formed = parse_bonds(d.get('formed', []))
            dH, sb, sf = bond_enthalpy_dH(broken, formed)
            return jsonify(result=dH, sum_broken=sb, sum_formed=sf)

        elif t == 'gibbs':
            dH = float(d['dH'])  # kJ/mol
            dS = float(d['dS'])  # J/mol·K
            T  = float(d.get('T', 298.15))  # K
            dG = dH - T * dS / 1000  # kJ/mol
            return jsonify(result=dG, spontaneous=dG < 0)

        else:
            return jsonify(error='Unknown type'), 400
    except Exception as e:
        return jsonify(error=str(e)), 400


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
        result = build_ice_table(r_names, r_coeffs, r_init, p_names, p_coeffs, p_init, Kc)
        return jsonify(
            x=result['x'],
            r_names=r_names, p_names=p_names,
            r_eq=result['r_eq'], p_eq=result['p_eq'],
            Q_initial=result['Q_initial'], Q_final=result['Q_final'],
            approx_pct=result['approx_pct']
        )
    except Exception as e:
        return jsonify(error=str(e)), 400


# ── 16. Electrochemistry ──────────────────────────────────────────────────────
@app.route('/api/electrochem', methods=['POST'])
def api_electrochem():
    d = request.json or {}
    t = d.get('type')
    try:
        if t == 'cell':
            E_cat = float(d['E_cat'])
            E_ano = float(d['E_ano'])
            n     = int(d['n'])
            E_cell = cell_potential(E_cat, E_ano)
            dG     = gibbs_from_cell(n, E_cell)
            return jsonify(E_cell=E_cell, dG=dG,
                           spontaneity=spontaneity_check(E_cell),
                           cell_type=cell_type(E_cell))

        elif t == 'faraday':
            solve = d.get('solve')
            mass = float(d['mass']) if d.get('mass') else None
            I    = float(d['I'])    if d.get('I')    else None
            time = float(d['t'])    if d.get('t')    else None
            M    = float(d['M'])    if d.get('M')    else None
            n    = int(d['n'])      if d.get('n')    else None
            if solve == 'mass':
                return jsonify(result=faraday_mass(I, time, M, n), unit='g')
            elif solve == 'current':
                return jsonify(result=faraday_current(mass, time, M, n), unit='A')
            elif solve == 'time':
                return jsonify(result=faraday_time(mass, I, M, n), unit='s')
            elif solve == 'molar_mass':
                return jsonify(result=faraday_molar_mass(mass, I, time, n), unit='g/mol')
            else:
                return jsonify(error='Unknown solve target'), 400

        elif t == 'nernst':
            E0 = float(d['E0'])
            n  = int(d['n'])
            Q  = float(d['Q'])
            T  = float(d.get('T', 298.15))
            E  = nernst(E0, n, Q, T)
            return jsonify(E=E)

        else:
            return jsonify(error='Unknown type'), 400
    except Exception as e:
        return jsonify(error=str(e)), 400


# ── 17. Kinetics ──────────────────────────────────────────────────────────────
@app.route('/api/kinetics', methods=['POST'])
def api_kinetics():
    d = request.json or {}
    t = d.get('type')
    try:
        if t == 'order':
            c1, c2 = float(d['c1']), float(d['c2'])
            r1, r2 = float(d['r1']), float(d['r2'])
            order = determine_order(c1, c2, r1, r2)
            k = rate_constant_from_experiment(r1, [c1], [order])
            return jsonify(order=order, k=k, k_units=k_units(round(order)))

        elif t == 'arrhenius':
            solve = d.get('solve')
            k1 = float(d['k1']); T1 = float(d['T1']); T2 = float(d['T2'])
            if solve == 'Ea':
                k2 = float(d['k2'])
                Ea_J = arrhenius_Ea(k1, T1, k2, T2)
                return jsonify(Ea_J=Ea_J, Ea_kJ=Ea_J / 1000)
            else:
                Ea_J = float(d['Ea'])
                k2 = arrhenius_k2(k1, T1, T2, Ea_J)
                return jsonify(k2=k2)

        elif t == 'halflife':
            solve = d.get('solve')
            import math
            if solve == 't_half':
                k = float(d['k'])
                return jsonify(t_half=math.log(2) / k)
            else:
                t_half = float(d['t_half'])
                return jsonify(k=math.log(2) / t_half)

        elif t == 'kunits':
            order = int(d.get('order', 1))
            return jsonify(order=order, units=k_units(order))

        else:
            return jsonify(error='Unknown type'), 400
    except Exception as e:
        return jsonify(error=str(e)), 400


if __name__ == '__main__':
    app.run(debug=True, port=5000)
