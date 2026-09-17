# limiting_reactant.py
import math

from constants import capitalize_formula
from percent_composition_calculator import MOLAR_MASS


def _get_int(prompt, label, minimum=1):
    raw = input(prompt).strip()
    try:
        val = int(raw)
        if val < minimum:
            print(f"  [ERROR] {label} must be at least {minimum}.")
            return None
        return val
    except ValueError:
        print(f"  [ERROR] Invalid input: expected a whole number for {label}.")
        return None


def _get_float(prompt, label, positive=False, allow_blank=False):
    raw = input(prompt).strip()
    if allow_blank and not raw:
        return ""
    try:
        val = float(raw)
    except ValueError:
        print(f"  [ERROR] Invalid input: expected a number for {label}.")
        return None
    if positive and val <= 0:
        print(f"  [ERROR] {label} must be greater than zero.")
        return None
    return val


# ── Core calculation ─────────────────────────────────────────────────────────

def species_molar_mass(name):
    """Molar mass (g/mol) of a formula or ion (e.g. 'H2O', 'SO4^2-');
    None if the name isn't a readable formula."""
    from equation_balancer import parse_species
    try:
        sp = parse_species(name)
    except ValueError:
        return None
    if sp.is_electron:
        return None
    return sum(MOLAR_MASS[el] * n for el, n in sp.counts.items())


def _balance_problem(reactants, products, r_coeffs, p_coeffs):
    """None if atoms and charge balance with these coefficients, otherwise a
    short description like 'O: 2 on the left, 3 on the right'."""
    from equation_balancer import parse_species
    totals = [{}, {}]
    for side, names, coeffs in ((0, reactants, r_coeffs), (1, products, p_coeffs)):
        for name, c in zip(names, coeffs):
            sp = parse_species(name)
            for el, n in sp.counts.items():
                totals[side][el] = totals[side].get(el, 0) + c * n
            totals[side]["charge"] = totals[side].get("charge", 0) + c * sp.charge
    for key in sorted(set(totals[0]) | set(totals[1])):
        left, right = totals[0].get(key, 0), totals[1].get(key, 0)
        if not math.isclose(left, right, rel_tol=1e-9, abs_tol=1e-9):
            return f"{key}: {left:g} on the left, {right:g} on the right"
    return None


def _is_blank(v):
    return v is None or (isinstance(v, str) and not v.strip())


def calculate_limiting_reactant(reactants, amounts, products,
                                r_coeffs=None, p_coeffs=None, unit="mol"):
    """
    Find the limiting reactant, what is left over and the theoretical yield.

    reactants : list of formulas (e.g. ['N2', 'H2'])
    amounts   : amount of each reactant, in `unit`
    products  : list of formulas
    r_coeffs, p_coeffs : stoichiometric coefficients; leave both out (or all
                blank) to balance the equation automatically
    unit      : 'mol' or 'g'

    Returns a dict with:
      limiting  : list of limiting reactant names (more than one = exact ratio)
      extent    : moles of "reaction" (amount ÷ coefficient of the limiting one)
      reactants : [{name, coeff, molar_mass, moles, grams, ratio, used_mol,
                    leftover_mol, leftover_g}, ...]
      products  : [{name, coeff, molar_mass, moles, grams}, ...]
      balanced  : True if the coefficients were worked out automatically
      equation  : 'N2 + 3H2 → 2NH3'
    """
    if unit not in ("mol", "g"):
        raise ValueError("Unit must be 'mol' or 'g'.")
    reactants = [capitalize_formula(str(r).strip()) for r in reactants]
    products = [capitalize_formula(str(p).strip()) for p in products]
    if not reactants or not products:
        raise ValueError("Enter at least one reactant and one product.")
    if any(not n for n in reactants + products):
        raise ValueError("Every reactant and product needs a name or formula.")
    if len(amounts) != len(reactants):
        raise ValueError("Give one amount for each reactant.")

    amounts = [float(a) for a in amounts]
    if any(not math.isfinite(a) or a < 0 for a in amounts):
        raise ValueError("Amounts must be zero or positive numbers.")

    r_coeffs = list(r_coeffs) if r_coeffs is not None else [None] * len(reactants)
    p_coeffs = list(p_coeffs) if p_coeffs is not None else [None] * len(products)
    if len(r_coeffs) != len(reactants) or len(p_coeffs) != len(products):
        raise ValueError("Give one coefficient for each species.")
    blanks = [_is_blank(c) for c in r_coeffs + p_coeffs]
    balanced = False
    if all(blanks):
        from equation_balancer import balance_equation
        r_coeffs, p_coeffs = balance_equation(reactants, products)
        balanced = True
    elif any(blanks):
        raise ValueError("Fill in every coefficient, or leave them all blank "
                         "to balance the equation automatically.")
    else:
        r_coeffs = [float(c) for c in r_coeffs]
        p_coeffs = [float(c) for c in p_coeffs]
        if any(not math.isfinite(c) or c <= 0 for c in r_coeffs + p_coeffs):
            raise ValueError("Coefficients must be positive numbers.")

    # Masses only mean something when every name is a real formula AND the
    # equation balances by atoms with these coefficients; otherwise the names
    # are probably labels ("A", "B" would read as boron) or a coefficient is wrong.
    warnings = []
    r_mm = [species_molar_mass(r) for r in reactants]
    p_mm = [species_molar_mass(p) for p in products]
    not_formulas = [n for n, m in zip(reactants + products, r_mm + p_mm) if m is None]
    problem = None if not_formulas else _balance_problem(reactants, products, r_coeffs, p_coeffs)
    if unit == "g":
        bad = [r for r, m in zip(reactants, r_mm) if m is None]
        if bad:
            raise ValueError(f"Can't work out the molar mass of {', '.join(bad)}; "
                             "use a chemical formula or enter moles.")
        if not_formulas:
            raise ValueError(f"{', '.join(not_formulas)} is not a chemical formula, so the "
                             "masses can't be checked; use formulas or enter moles.")
        if problem:
            raise ValueError(f"The equation isn't balanced with these coefficients ({problem}). "
                             "Fix the coefficients or leave them all blank.")
        moles = [a / m for a, m in zip(amounts, r_mm)]
    else:
        moles = amounts
        if not_formulas or problem:
            if len(not_formulas) < len(reactants) + len(products) or problem:
                why = (f"{', '.join(not_formulas)} "
                       + ("is not a chemical formula" if len(not_formulas) == 1
                          else "are not chemical formulas") if not_formulas
                       else f"the equation isn't balanced by atoms with these coefficients ({problem})")
                warnings.append(f"Masses not shown: {why}. Mole answers use the coefficients as given.")
            r_mm = [None] * len(reactants)
            p_mm = [None] * len(products)

    ratios = [n / c for n, c in zip(moles, r_coeffs)]
    extent = min(ratios)
    limiting_idx = [i for i, r in enumerate(ratios)
                    if math.isclose(r, extent, rel_tol=1e-9, abs_tol=1e-15)]

    r_rows = []
    for i, name in enumerate(reactants):
        used = r_coeffs[i] * extent
        left = 0.0 if i in limiting_idx else moles[i] - used
        if left < 1e-12 * max(moles[i], 1e-300):
            left = 0.0
        r_rows.append({
            "name": name, "coeff": r_coeffs[i], "molar_mass": r_mm[i],
            "moles": moles[i], "grams": moles[i] * r_mm[i] if r_mm[i] else None,
            "ratio": ratios[i], "used_mol": used,
            "leftover_mol": left, "leftover_g": left * r_mm[i] if r_mm[i] else None,
        })
    p_rows = []
    for i, name in enumerate(products):
        n = p_coeffs[i] * extent
        p_rows.append({
            "name": name, "coeff": p_coeffs[i], "molar_mass": p_mm[i],
            "moles": n, "grams": n * p_mm[i] if p_mm[i] else None,
        })

    def term(c, name):
        c = int(c) if float(c).is_integer() else c
        return name if c == 1 else f"{c}{name}"

    return {
        "limiting": [reactants[i] for i in limiting_idx],
        "extent": extent,
        "reactants": r_rows,
        "products": p_rows,
        "balanced": balanced,
        "warnings": warnings,
        "equation": " + ".join(term(c, n) for c, n in zip(r_coeffs, reactants))
                    + " → " + " + ".join(term(c, n) for c, n in zip(p_coeffs, products)),
    }


# ── Menu ─────────────────────────────────────────────────────────────────────

def limiting_reactant_menu(reactants, products, reactant_coeffs, product_coeffs):
    """Calculates the limiting reactant and theoretical yield."""
    print("\n--- Limiting Reactant Calculator ---")

    if not reactants or not products or not reactant_coeffs or not product_coeffs:
        print("Leave every coefficient blank to balance the equation automatically.")
        num_reactants = _get_int("How many reactants? ", "number of reactants")
        if num_reactants is None:
            return
        reactants, reactant_coeffs = [], []
        for i in range(num_reactants):
            r = capitalize_formula(input(f"Enter reactant #{i+1} formula: ").strip()) or f"R{i+1}"
            c = _get_float(f"Enter coefficient for {r} (blank = auto): ",
                           f"coefficient for {r}", positive=True, allow_blank=True)
            if c is None:
                return
            reactants.append(r)
            reactant_coeffs.append(c)

        num_products = _get_int("How many products? ", "number of products")
        if num_products is None:
            return
        products, product_coeffs = [], []
        for i in range(num_products):
            p = capitalize_formula(input(f"Enter product #{i+1} formula: ").strip()) or f"P{i+1}"
            c = _get_float(f"Enter coefficient for {p} (blank = auto): ",
                           f"coefficient for {p}", positive=True, allow_blank=True)
            if c is None:
                return
            products.append(p)
            product_coeffs.append(c)

    unit = "g" if input("Amounts in (m)oles or (g)rams? [m]: ").strip().lower().startswith("g") else "mol"
    amounts = []
    for r in reactants:
        amt = _get_float(f"Enter the {'mass (g)' if unit == 'g' else 'moles'} of {r}: ",
                         f"amount of {r}", positive=True)
        if amt is None:
            return
        amounts.append(amt)

    try:
        res = calculate_limiting_reactant(reactants, amounts, products,
                                          reactant_coeffs, product_coeffs, unit)
    except ValueError as e:
        print(f"  [ERROR] {e}")
        return

    print(f"\nEquation: {res['equation']}" + ("  (balanced automatically)" if res["balanced"] else ""))
    print(f"[OK] Limiting Reactant: {' and '.join(res['limiting'])}")
    for w in res["warnings"]:
        print(f"  [!] {w}")

    print("\nLeftover Reactants:")
    for r in res["reactants"]:
        grams = f"  ({r['leftover_g']:.4g} g)" if r["leftover_g"] is not None else ""
        print(f"{r['name']}: {r['leftover_mol']:.4g} mol remaining{grams}")

    print("\nTheoretical Yield of Products:")
    for p in res["products"]:
        grams = f"  ({p['grams']:.4g} g)" if p["grams"] is not None else ""
        print(f"{p['name']}: {p['moles']:.4g} mol{grams}")

    input("Press Enter to return to the main menu...")


def limiting_reactant_main_menu():
    """Wrapper menu for the limiting reactant module."""
    while True:
        print("\n--- Limiting Reactant Main Menu ---")
        print("1. Enter reaction data manually")
        print("2. Return to Main Menu")
        choice = input("Select an option: ").strip()

        if choice == "1":
            limiting_reactant_menu([], [], [], [])
        elif choice == "2":
            break
        else:
            print("[ERROR] Invalid option. Please try again.")
