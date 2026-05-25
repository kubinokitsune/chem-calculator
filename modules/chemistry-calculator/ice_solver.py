
# ice_solver.py
# Equilibrium & ICE Table module
# Covers: ICE table builder, Kc/Kp converter, Q vs K, Le Chatelier predictor

import math

R_ATM = 0.08206  # L·atm / (mol·K)


# ── Core math ─────────────────────────────────────────────────────────────────

def reaction_quotient(r_coeffs, r_concs, p_coeffs, p_concs):
    """
    Q = product of [products]^coeff / product of [reactants]^coeff.
    Returns 0.0 if any reactant is 0, inf if denominator collapses to 0.
    """
    num = 1.0
    for c, conc in zip(p_coeffs, p_concs):
        num *= conc ** c

    den = 1.0
    for c, conc in zip(r_coeffs, r_concs):
        if conc == 0.0:
            return 0.0
        den *= conc ** c

    if den == 0.0:
        return math.inf
    return num / den


def _ice_Q(x, r_coeffs, r_initial, p_coeffs, p_initial):
    """Q at ICE offset x (reactants decrease, products increase)."""
    r_concs = [max(r0 - c * x, 0.0) for c, r0 in zip(r_coeffs, r_initial)]
    p_concs = [max(p0 + c * x, 0.0) for c, p0 in zip(p_coeffs, p_initial)]
    return reaction_quotient(r_coeffs, r_concs, p_coeffs, p_concs)


def solve_ice(r_coeffs, r_initial, p_coeffs, p_initial, Kc, tol=1e-12, max_iter=400):
    """
    Returns x such that Q(x) = Kc using bisection.
      x > 0  forward shift (reactants decrease, products increase)
      x < 0  reverse shift
      x = 0  already at equilibrium
    Raises ValueError if conditions are inconsistent.
    """
    if Kc < 0:
        raise ValueError("Kc must be non-negative.")

    # --- valid range for x ---
    x_max = min(r0 / c for c, r0 in zip(r_coeffs, r_initial) if c > 0)
    neg_lims = [-p0 / c for c, p0 in zip(p_coeffs, p_initial) if c > 0 and p0 > 0]
    x_min = max(neg_lims) if neg_lims else 0.0

    Q0 = _ice_Q(0, r_coeffs, r_initial, p_coeffs, p_initial)

    # Already at equilibrium?
    rel_err = abs(Q0 - Kc) / (Kc + 1e-30)
    if rel_err < 1e-9:
        return 0.0

    eps = x_max * 1e-11 + 1e-15

    if Q0 < Kc:
        # Forward: x in (0, x_max)
        lo, hi = eps, x_max - eps
    else:
        # Reverse: x in (x_min, 0)
        if x_min >= 0.0:
            raise ValueError(
                "Reaction quotient Q > Kc, but no products have initial "
                "concentration, so no reverse shift is possible. "
                "Check your inputs."
            )
        lo, hi = x_min + eps, -eps

    flo = _ice_Q(lo, r_coeffs, r_initial, p_coeffs, p_initial) - Kc
    fhi = _ice_Q(hi, r_coeffs, r_initial, p_coeffs, p_initial) - Kc

    if flo * fhi > 0:
        raise ValueError(
            f"Cannot bracket equilibrium root "
            f"(flo={flo:.4e}, fhi={fhi:.4e}). "
            "Verify Kc and initial concentrations."
        )

    for _ in range(max_iter):
        mid = (lo + hi) / 2.0
        fmid = _ice_Q(mid, r_coeffs, r_initial, p_coeffs, p_initial) - Kc
        if abs(fmid) < tol or (hi - lo) < tol:
            return mid
        if flo * fmid <= 0.0:
            hi, fhi = mid, fmid
        else:
            lo, flo = mid, fmid

    return (lo + hi) / 2.0


def build_ice_table(r_names, r_coeffs, r_initial,
                    p_names, p_coeffs, p_initial, Kc):
    """
    Full ICE table solver.
    Returns dict:
      x           float    ICE variable
      r_eq        list     reactant equilibrium concs
      p_eq        list     product  equilibrium concs
      Q_initial   float
      Q_final     float    should be ≈ Kc
      approx_pct  float    x / min(r_initial) * 100  (5% check)
    """
    x = solve_ice(r_coeffs, r_initial, p_coeffs, p_initial, Kc)
    r_eq = [r0 - c * x for c, r0 in zip(r_coeffs, r_initial)]
    p_eq = [p0 + c * x for c, p0 in zip(p_coeffs, p_initial)]
    Q_initial = _ice_Q(0, r_coeffs, r_initial, p_coeffs, p_initial)
    Q_final   = reaction_quotient(r_coeffs, r_eq, p_coeffs, p_eq)
    nonzero_initial = [c for c in r_initial if c > 0]
    approx_pct = (abs(x) / min(nonzero_initial) * 100) if nonzero_initial else 0.0
    return {
        'x': x,
        'r_eq': r_eq,
        'p_eq': p_eq,
        'Q_initial': Q_initial,
        'Q_final': Q_final,
        'approx_pct': approx_pct,
    }


def print_ice_table(r_names, r_coeffs, r_initial,
                    p_names, p_coeffs, p_initial, Kc, result):
    """Pretty-print the full ICE table."""
    x = result['x']
    all_names   = r_names + p_names
    all_initial = list(r_initial) + list(p_initial)
    all_changes = [-c * x for c in r_coeffs] + [c * x for c in p_coeffs]
    all_eq      = result['r_eq'] + result['p_eq']

    col_w = max(10, max(len(n) for n in all_names) + 2)
    label_w = 12
    sep = "-" * (label_w + col_w * len(all_names))

    header = " " * label_w + "".join(f"{n:>{col_w}}" for n in all_names)
    print(header)
    print(sep)

    def row(label, values, signed=False):
        cells = []
        for v in values:
            if signed:
                cells.append(f"{v:>+{col_w}.4f}")
            else:
                cells.append(f"{v:>{col_w}.4f}")
        return f"{label:<{label_w}}" + "".join(cells)

    print(row("Initial  :", all_initial))
    print(row("Change   :", all_changes, signed=True))
    print(row("Equilib. :", all_eq))
    print(sep)
    print(f"  Kc (given)  = {Kc:.6g}")
    print(f"  Q (result)  = {result['Q_final']:.6g}")
    rel = abs(result['Q_final'] - Kc) / (Kc + 1e-30)
    print(f"  Verification: {'PASS' if rel < 1e-6 else 'WARN — re-check inputs'}")
    print(f"  x = {x:+.6f}  ({'forward' if x >= 0 else 'reverse'} shift)")
    pct = result['approx_pct']
    if pct < 5.0:
        print(f"  5%% rule: x/[init] = {pct:.2f}%% — approximation WOULD be valid")
    else:
        print(f"  5%% rule: x/[init] = {pct:.2f}%% — approximation NOT valid (exact method used)")


# ── Kc / Kp converter ────────────────────────────────────────────────────────

def kc_to_kp(Kc, T_K, delta_n):
    """Kp = Kc * (RT)^delta_n  (R = 0.08206 L·atm/mol·K)"""
    return Kc * (R_ATM * T_K) ** delta_n

def kp_to_kc(Kp, T_K, delta_n):
    """Kc = Kp / (RT)^delta_n"""
    return Kp / (R_ATM * T_K) ** delta_n


# ── Q vs K ────────────────────────────────────────────────────────────────────

def compare_Q_K(Q, Kc, tol_frac=1e-6):
    """
    Returns one of 'forward', 'reverse', 'equilibrium'
    and a plain-English explanation string.
    """
    if abs(Q - Kc) / (Kc + 1e-30) < tol_frac:
        return ('equilibrium',
                f"Q = K = {Kc:.4g}  -->  System is already at equilibrium. No net shift.")
    elif Q < Kc:
        return ('forward',
                f"Q ({Q:.4g}) < K ({Kc:.4g})  -->  "
                f"Reaction shifts RIGHT (forward) to produce more products.")
    else:
        return ('reverse',
                f"Q ({Q:.4g}) > K ({Kc:.4g})  -->  "
                f"Reaction shifts LEFT (reverse) to produce more reactants.")


# ── Le Chatelier predictor ────────────────────────────────────────────────────

def le_chatelier_concentration(species_role, change):
    """
    species_role : 'reactant' or 'product'
    change       : 'increase' or 'decrease'
    Returns (direction, explanation).
    """
    role  = species_role.lower()
    delta = change.lower()

    if role == 'reactant' and delta == 'increase':
        return ('right',
                "Increasing a reactant concentration lowers Q below K. "
                "The system shifts RIGHT (forward) to consume the added reactant.")
    if role == 'reactant' and delta == 'decrease':
        return ('left',
                "Decreasing a reactant concentration raises Q above K. "
                "The system shifts LEFT (reverse) to replenish the reactant.")
    if role == 'product' and delta == 'increase':
        return ('left',
                "Increasing a product concentration raises Q above K. "
                "The system shifts LEFT (reverse) to consume the added product.")
    if role == 'product' and delta == 'decrease':
        return ('right',
                "Decreasing a product concentration lowers Q below K. "
                "The system shifts RIGHT (forward) to replenish the product.")
    raise ValueError(f"Invalid role '{role}' or change '{delta}'.")


def le_chatelier_pressure(pressure_change, delta_n):
    """
    pressure_change : 'increase' or 'decrease'
    delta_n         : moles gas products - moles gas reactants
    Returns (direction, explanation).
    """
    pc = pressure_change.lower()
    if delta_n == 0:
        return ('none',
                "Delta_n = 0 (equal moles of gas on both sides). "
                "A pressure change has NO effect on equilibrium position.")
    if pc == 'increase':
        if delta_n > 0:
            return ('left',
                    f"Increasing pressure favours the side with FEWER moles of gas. "
                    f"Delta_n = {delta_n:+g} (more moles on products side). "
                    f"Equilibrium shifts LEFT.")
        else:
            return ('right',
                    f"Increasing pressure favours the side with FEWER moles of gas. "
                    f"Delta_n = {delta_n:+g} (more moles on reactants side). "
                    f"Equilibrium shifts RIGHT.")
    elif pc == 'decrease':
        if delta_n > 0:
            return ('right',
                    f"Decreasing pressure favours the side with MORE moles of gas. "
                    f"Delta_n = {delta_n:+g} (more moles on products side). "
                    f"Equilibrium shifts RIGHT.")
        else:
            return ('left',
                    f"Decreasing pressure favours the side with MORE moles of gas. "
                    f"Delta_n = {delta_n:+g} (more moles on reactants side). "
                    f"Equilibrium shifts LEFT.")
    raise ValueError(f"Invalid pressure_change '{pressure_change}'.")


def le_chatelier_temperature(temp_change, rxn_type):
    """
    temp_change : 'increase' or 'decrease'
    rxn_type    : 'exothermic' or 'endothermic'
    Returns (direction, explanation, K_effect).
    K_effect is 'increases', 'decreases', or 'unchanged'.
    """
    tc  = temp_change.lower()
    rxn = rxn_type.lower()

    if rxn == 'exothermic':
        if tc == 'increase':
            return ('left',
                    "Exothermic reaction: heat is a product. "
                    "Increasing T shifts equilibrium LEFT to absorb the added heat. "
                    "K decreases.",
                    'decreases')
        else:
            return ('right',
                    "Exothermic reaction: heat is a product. "
                    "Decreasing T shifts equilibrium RIGHT to release heat. "
                    "K increases.",
                    'increases')
    elif rxn == 'endothermic':
        if tc == 'increase':
            return ('right',
                    "Endothermic reaction: heat is a reactant. "
                    "Increasing T shifts equilibrium RIGHT to absorb the added heat. "
                    "K increases.",
                    'increases')
        else:
            return ('left',
                    "Endothermic reaction: heat is a reactant. "
                    "Decreasing T shifts equilibrium LEFT to release heat. "
                    "K decreases.",
                    'decreases')
    raise ValueError(f"Invalid rxn_type '{rxn_type}'.")


def le_chatelier_catalyst():
    """Returns (direction, explanation)."""
    return ('none',
            "A catalyst speeds up BOTH the forward and reverse reactions equally. "
            "It lowers the activation energy but does NOT change the equilibrium "
            "position or the value of K. Equilibrium is reached faster, not differently.")


# ── Input helper ─────────────────────────────────────────────────────────────

def _get_float(prompt, label=None, positive=False):
    label = label or prompt.strip().rstrip(':')
    while True:
        raw = input(prompt).strip()
        try:
            val = float(raw)
        except ValueError:
            print(f"  [ERROR] Invalid input: expected a number for {label}.")
            continue
        if positive and val <= 0:
            print(f"  [ERROR] {label} must be greater than zero.")
            continue
        return val


def _get_int(prompt, label="value"):
    while True:
        raw = input(prompt).strip()
        try:
            v = int(raw)
            if v < 1:
                print(f"  [ERROR] {label} must be at least 1.")
                continue
            return v
        except ValueError:
            print(f"  [ERROR] Invalid input: expected a positive whole number for {label}.")


# ── Sub-menus ─────────────────────────────────────────────────────────────────

def menu_ice_table():
    print("\n-- ICE Table Builder --")
    print("  Sets up and solves the equilibrium ICE table automatically.")
    print("  Reactants decrease by (coeff * x); products increase by (coeff * x).")
    print()

    from constants import capitalize_formula
    nr = _get_int("  Number of reactants: ", "number of reactants")
    r_names, r_coeffs, r_initial = [], [], []
    for i in range(nr):
        name  = capitalize_formula(input(f"    Reactant {i+1} formula: ").strip()) or f"R{i+1}"
        coeff = _get_float(f"    Coefficient for {name}: ", f"coefficient for {name}", positive=True)
        init  = _get_float(f"    Initial concentration of {name} (mol/L): ", f"[{name}]₀")
        if init < 0:
            print(f"  [ERROR] Concentration of {name} cannot be negative.")
            return
        r_names.append(name); r_coeffs.append(coeff); r_initial.append(init)

    np_ = _get_int("  Number of products: ", "number of products")
    p_names, p_coeffs, p_initial = [], [], []
    for i in range(np_):
        name  = capitalize_formula(input(f"    Product {i+1} formula: ").strip()) or f"P{i+1}"
        coeff = _get_float(f"    Coefficient for {name}: ", f"coefficient for {name}", positive=True)
        init  = _get_float(f"    Initial concentration of {name} (mol/L, 0 if none): ", f"[{name}]₀")
        if init < 0:
            print(f"  [ERROR] Concentration of {name} cannot be negative.")
            return
        p_names.append(name); p_coeffs.append(coeff); p_initial.append(init)

    Kc = _get_float("  Kc value: ", "Kc", positive=True)

    print(f"\n  Equation: {' + '.join(f'{int(c) if c==int(c) else c}{n}' for c,n in zip(r_coeffs,r_names))}"
          f"  <=>  {' + '.join(f'{int(c) if c==int(c) else c}{n}' for c,n in zip(p_coeffs,p_names))}")
    print(f"  Kc = {Kc:.4g}\n")

    try:
        result = build_ice_table(r_names, r_coeffs, r_initial,
                                  p_names, p_coeffs, p_initial, Kc)
        print_ice_table(r_names, r_coeffs, r_initial,
                        p_names, p_coeffs, p_initial, Kc, result)
    except ValueError as e:
        print(f"\n  [ERROR] {e}")


def menu_kc_kp():
    print("\n-- Kc / Kp Converter --")
    print("  Kp = Kc * (RT)^delta_n   (R = 0.08206 L*atm/mol*K)")
    print("  delta_n = moles gaseous products - moles gaseous reactants")
    print()
    print("1. Kc  -->  Kp")
    print("2. Kp  -->  Kc")
    choice = input("Select (1-2): ").strip()

    T_input = _get_float("  Temperature (K or °C): ", "temperature")
    unit = input("  Is that (1) Kelvin or (2) Celsius? ").strip()
    T_K = T_input + 273.15 if unit == "2" else T_input
    if T_K <= 0:
        print("  [ERROR] Temperature must be above absolute zero (> 0 K).")
        return
    dn  = _get_float("  Delta_n (mol gas products - mol gas reactants): ", "delta_n")

    try:
        if choice == "1":
            Kc = _get_float("  Kc: ")
            Kp = kc_to_kp(Kc, T_K, dn)
            print(f"\n  Kc = {Kc:.6g}")
            print(f"  T  = {T_K:.2f} K")
            print(f"  Delta_n = {dn:+g}")
            print(f"  RT  = {R_ATM * T_K:.4f}")
            print(f"  Kp = Kc * (RT)^delta_n = {Kc:.6g} * {R_ATM*T_K:.4f}^{dn:+g} = {Kp:.6g}")
        elif choice == "2":
            Kp = _get_float("  Kp: ")
            Kc = kp_to_kc(Kp, T_K, dn)
            print(f"\n  Kp = {Kp:.6g}")
            print(f"  T  = {T_K:.2f} K")
            print(f"  Delta_n = {dn:+g}")
            print(f"  RT  = {R_ATM * T_K:.4f}")
            print(f"  Kc = Kp / (RT)^delta_n = {Kp:.6g} / {R_ATM*T_K:.4f}^{dn:+g} = {Kc:.6g}")
        else:
            print("  Invalid choice.")
    except (ValueError, ZeroDivisionError) as e:
        print(f"  [ERROR] {e}")


def menu_q_vs_k():
    print("\n-- Reaction Quotient Q vs K --")
    print("  Calculate Q and compare it to Kc to determine shift direction.")
    print()

    nr = _get_int("  Number of reactants: ")
    r_coeffs, r_concs = [], []
    for i in range(nr):
        name  = input(f"    Reactant {i+1} formula (label): ").strip() or f"R{i+1}"
        coeff = _get_float(f"    Coefficient for {name}: ")
        conc  = _get_float(f"    Current concentration of {name} (mol/L): ")
        r_coeffs.append(coeff); r_concs.append(conc)

    np_ = _get_int("  Number of products: ")
    p_coeffs, p_concs = [], []
    for i in range(np_):
        name  = input(f"    Product {i+1} formula (label): ").strip() or f"P{i+1}"
        coeff = _get_float(f"    Coefficient for {name}: ")
        conc  = _get_float(f"    Current concentration of {name} (mol/L): ")
        p_coeffs.append(coeff); p_concs.append(conc)

    Kc = _get_float("  Kc: ")

    Q = reaction_quotient(r_coeffs, r_concs, p_coeffs, p_concs)
    direction, explanation = compare_Q_K(Q, Kc)

    print(f"\n  Q = {Q:.6g}")
    print(f"  K = {Kc:.6g}")
    print(f"\n  --> {explanation}")


def menu_le_chatelier():
    print("\n-- Le Chatelier's Principle Predictor --")
    print("Select stress type:")
    print("1. Concentration change")
    print("2. Pressure change  (gases only)")
    print("3. Temperature change")
    print("4. Catalyst added")
    choice = input("Select (1-4): ").strip()

    try:
        if choice == "1":
            print("  Which species is affected?")
            role  = input("  (1) Reactant  (2) Product: ").strip()
            role  = "reactant" if role == "1" else "product"
            delta = input("  (1) Increased  (2) Decreased: ").strip()
            delta = "increase" if delta == "1" else "decrease"
            direction, explanation = le_chatelier_concentration(role, delta)
            print(f"\n  Shift: {direction.upper()}")
            print(f"  {explanation}")

        elif choice == "2":
            pc = input("  Pressure (1) Increased  (2) Decreased: ").strip()
            pc = "increase" if pc == "1" else "decrease"
            dn = _get_float("  Delta_n (gas products - gas reactants): ")
            direction, explanation = le_chatelier_pressure(pc, dn)
            print(f"\n  Shift: {direction.upper()}")
            print(f"  {explanation}")

        elif choice == "3":
            tc  = input("  Temperature (1) Increased  (2) Decreased: ").strip()
            tc  = "increase" if tc == "1" else "decrease"
            rxn = input("  Reaction is (1) Exothermic  (2) Endothermic: ").strip()
            rxn = "exothermic" if rxn == "1" else "endothermic"
            direction, explanation, k_effect = le_chatelier_temperature(tc, rxn)
            print(f"\n  Shift: {direction.upper()}")
            print(f"  {explanation}")
            print(f"  Effect on K: K {k_effect}")

        elif choice == "4":
            direction, explanation = le_chatelier_catalyst()
            print(f"\n  Shift: {direction.upper()}")
            print(f"  {explanation}")

        else:
            print("  Invalid choice.")

    except ValueError as e:
        print(f"  [ERROR] {e}")


# ── Main menu ─────────────────────────────────────────────────────────────────

def ice_solver_menu():
    while True:
        print("\n=== Equilibrium & ICE Table Solver ===")
        print("1. ICE Table Builder  (solves for equilibrium concentrations)")
        print("2. Kc / Kp Converter")
        print("3. Reaction Quotient Q vs K  (shift direction)")
        print("4. Le Chatelier Predictor")
        print("0. Return to Main Menu")

        choice = input("Select an option (0-4): ").strip()

        if choice == "1":
            menu_ice_table()
        elif choice == "2":
            menu_kc_kp()
        elif choice == "3":
            menu_q_vs_k()
        elif choice == "4":
            menu_le_chatelier()
        elif choice == "0":
            break
        else:
            print("Invalid choice. Please try again.")
