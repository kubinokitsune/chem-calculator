
# thermodynamics.py
# Enthalpy & Thermodynamics module
# Covers: calorimetry, Hess's law, bond enthalpy, standard enthalpy of
# reaction (ΔH°rxn), entropy, and Gibbs free energy.

# ── IB data-booklet bond enthalpies (kJ/mol) ────────────────────────────────
# Keys are canonical: always put the lighter/more common element first,
# separated by "-" for single bonds and "=" / "#" for double/triple.
BOND_ENTHALPIES = {
    # C bonds
    "C-H":  413,
    "C-C":  347,
    "C=C":  614,
    "C#C":  839,
    "C-O":  358,
    "C=O":  805,   # as in CO2 / aldehydes (IB uses 743 for C=O in ketones; 805 for CO2)
    "C-N":  305,
    "C=N":  615,
    "C#N":  887,
    "C-F":  485,
    "C-Cl": 339,
    "C-Br": 285,
    "C-I":  213,
    "C-S":  272,
    # H bonds
    "H-H":  436,
    "H-O":  463,
    "H-N":  391,
    "H-F":  562,
    "H-Cl": 431,
    "H-Br": 366,
    "H-I":  299,
    "H-S":  338,
    # O bonds
    "O=O":  498,
    "O-O":  146,
    "O-N":  201,
    "O=N":  607,
    # N bonds
    "N-N":  163,
    "N=N":  418,
    "N#N":  945,
    "N-F":  272,
    "N-Cl": 200,
    # Halogen bonds
    "F-F":  158,
    "Cl-Cl":242,
    "Br-Br":193,
    "I-I":  151,
    "Cl-F": 253,
    "Br-Cl":219,
    "Br-F": 237,
    "I-Cl": 208,
    # S bonds
    "S-S":  264,
    "S=O":  523,
}

# Specific heat capacities (J/g·K) — IB data booklet
SPECIFIC_HEATS = {
    "water":    4.18,
    "H2O":      4.18,
    "iron":     0.449,
    "Fe":       0.449,
    "aluminum": 0.897,
    "Al":       0.897,
    "copper":   0.385,
    "Cu":       0.385,
    "gold":     0.129,
    "Au":       0.129,
    "silver":   0.233,
    "Ag":       0.233,
    "ethanol":  2.44,
    "glass":    0.840,
    "ice":      2.09,
    "steam":    2.01,
}


# ── 1. CALORIMETRY  q = mcΔT ─────────────────────────────────────────────────

def cal_q(m, c, dT):
    """q = m * c * ΔT  (J)"""
    return m * c * dT

def cal_m(q, c, dT):
    if c == 0 or dT == 0:
        raise ValueError("c and ΔT must be non-zero to solve for m.")
    return q / (c * dT)

def cal_c(q, m, dT):
    if m == 0 or dT == 0:
        raise ValueError("m and ΔT must be non-zero to solve for c.")
    return q / (m * dT)

def cal_dT(q, m, c):
    if m == 0 or c == 0:
        raise ValueError("m and c must be non-zero to solve for ΔT.")
    return q / (m * c)


# ── 2. HESS'S LAW ────────────────────────────────────────────────────────────

def hess_law(dH_values, multipliers):
    """
    dH_values  : list of ΔH values for each step reaction (kJ)
    multipliers: list of floats — positive keeps direction, negative flips it,
                 any non-1 magnitude scales the reaction
    Returns total ΔH for the target reaction.
    """
    if len(dH_values) != len(multipliers):
        raise ValueError("dH_values and multipliers must have the same length.")
    return sum(dh * m for dh, m in zip(dH_values, multipliers))


# ── 3. BOND ENTHALPY ─────────────────────────────────────────────────────────

def bond_enthalpy_dH(bonds_broken, bonds_formed):
    """
    bonds_broken / bonds_formed : list of (bond_label, count, enthalpy_kJ_per_mol)
        bond_label   – string like "C-H" (used only for display)
        count        – number of that bond type
        enthalpy     – kJ/mol for that bond type
    ΔH ≈ Σ(broken) − Σ(formed)
    Returns (dH, sum_broken, sum_formed).
    """
    sum_broken = sum(cnt * enth for _, cnt, enth in bonds_broken)
    sum_formed = sum(cnt * enth for _, cnt, enth in bonds_formed)
    return sum_broken - sum_formed, sum_broken, sum_formed


def lookup_bond(bond_label):
    """
    Return bond enthalpy from the built-in table, trying both key orderings.
    Returns None if not found.
    """
    key = bond_label.strip()
    if key in BOND_ENTHALPIES:
        return BOND_ENTHALPIES[key]
    # Try reversing around the bond-order symbol
    for sep in ("#", "=", "-"):
        if sep in key:
            parts = key.split(sep, 1)
            rev = parts[1] + sep + parts[0]
            if rev in BOND_ENTHALPIES:
                return BOND_ENTHALPIES[rev]
    return None


# ── 4. STANDARD ENTHALPY OF REACTION ────────────────────────────────────────

def standard_enthalpy_rxn(species):
    """
    species: list of dicts, each with keys:
        'formula'  : str
        'dHf'      : float  ΔH°f in kJ/mol
        'coeff'    : float  stoichiometric coefficient
        'role'     : 'product' or 'reactant'
    Returns ΔH°rxn = Σ coeff*ΔH°f(products) − Σ coeff*ΔH°f(reactants)
    """
    total = 0.0
    for s in species:
        role = s['role'].lower()
        contribution = s['coeff'] * s['dHf']
        if role == 'product':
            total += contribution
        elif role == 'reactant':
            total -= contribution
        else:
            raise ValueError(f"Role must be 'product' or 'reactant', got '{role}'.")
    return total


# ── 5. GIBBS FREE ENERGY  ΔG = ΔH − TΔS ────────────────────────────────────

def celsius_to_kelvin(T_C):
    return T_C + 273.15

def gibbs_dG(dH_kJ, T_K, dS_J_per_K):
    """ΔG (kJ) = ΔH (kJ) − T(K) × ΔS (J/K) / 1000"""
    return dH_kJ - T_K * (dS_J_per_K / 1000.0)

def gibbs_dH(dG_kJ, T_K, dS_J_per_K):
    return dG_kJ + T_K * (dS_J_per_K / 1000.0)

def gibbs_T(dH_kJ, dG_kJ, dS_J_per_K):
    if dS_J_per_K == 0:
        raise ValueError("ΔS cannot be zero when solving for T.")
    return (dH_kJ - dG_kJ) / (dS_J_per_K / 1000.0)

def gibbs_dS(dH_kJ, dG_kJ, T_K):
    if T_K == 0:
        raise ValueError("T cannot be 0 K when solving for ΔS.")
    return ((dH_kJ - dG_kJ) / T_K) * 1000.0

def spontaneity(dG_kJ, tol=1e-6):
    if dG_kJ < -tol:
        return "Spontaneous (ΔG < 0)"
    elif dG_kJ > tol:
        return "Non-spontaneous (ΔG > 0)"
    else:
        return "At equilibrium (ΔG = 0)"

def spontaneity_analysis(dH_kJ, dS_J_per_K):
    """
    Returns a qualitative description of spontaneity across all T ranges,
    based on signs of ΔH and ΔS (without needing T).
    """
    if dH_kJ < 0 and dS_J_per_K > 0:
        return "Always spontaneous at all temperatures (ΔH<0, ΔS>0)"
    elif dH_kJ > 0 and dS_J_per_K < 0:
        return "Never spontaneous at any temperature (ΔH>0, ΔS<0)"
    elif dH_kJ < 0 and dS_J_per_K < 0:
        return "Spontaneous at low T only (ΔH<0, ΔS<0 — enthalpy driven)"
    else:
        return "Spontaneous at high T only (ΔH>0, ΔS>0 — entropy driven)"


# ── Input helper ─────────────────────────────────────────────────────────────

def _get_float(prompt):
    while True:
        try:
            return float(input(prompt).strip())
        except ValueError:
            print("  Please enter a valid number.")


# ── Sub-menus ─────────────────────────────────────────────────────────────────

def menu_calorimetry():
    print("\n-- Calorimetry  q = mcΔT --")
    print("Solve for:")
    print("1. Heat (q)  in Joules")
    print("2. Mass (m)  in grams")
    print("3. Specific heat capacity (c)  in J/g·K")
    print("4. Temperature change (ΔT)  in K or °C")
    choice = input("Select (1-4): ").strip()

    if choice not in ("1","2","3","4"):
        print("Invalid choice."); return

    # Get specific heat
    print("\n  Common specific heats (J/g·K):")
    for name, val in SPECIFIC_HEATS.items():
        if len(name) <= 8:
            print(f"    {name:<12} {val}")
    print()

    def get_c_or_mass_or_dT(label, unit):
        return _get_float(f"  {label} ({unit}): ")

    def get_c():
        raw = input("  Substance name OR enter custom c value (J/g·K): ").strip().lower()
        if raw in SPECIFIC_HEATS:
            c = SPECIFIC_HEATS[raw]
            print(f"  Using c = {c} J/g·K")
            return c
        try:
            return float(raw)
        except ValueError:
            print("  Not found in table — enter a numeric value.")
            return _get_float("  c (J/g·K): ")

    def get_dT():
        mode = input("  Enter (1) ΔT directly  or  (2) T_initial and T_final: ").strip()
        if mode == "2":
            ti = _get_float("  T_initial (°C or K): ")
            tf = _get_float("  T_final   (°C or K): ")
            return tf - ti
        return _get_float("  ΔT (K or °C): ")

    try:
        if choice == "1":
            m  = get_c_or_mass_or_dT("Mass m", "g")
            c  = get_c()
            dT = get_dT()
            q  = cal_q(m, c, dT)
            print(f"\n  q = {q:.4f} J  ({q/1000:.4f} kJ)")
            print(f"  {'Endothermic' if q > 0 else 'Exothermic'} process")

        elif choice == "2":
            q  = _get_float("  q (J): ")
            c  = get_c()
            dT = get_dT()
            m  = cal_m(q, c, dT)
            print(f"\n  m = {m:.4f} g")

        elif choice == "3":
            q  = _get_float("  q (J): ")
            m  = get_c_or_mass_or_dT("Mass m", "g")
            dT = get_dT()
            c  = cal_c(q, m, dT)
            print(f"\n  c = {c:.4f} J/g·K")

        elif choice == "4":
            q  = _get_float("  q (J): ")
            m  = get_c_or_mass_or_dT("Mass m", "g")
            c  = get_c()
            dT = cal_dT(q, m, c)
            print(f"\n  ΔT = {dT:.4f} °C (or K)")
            print(f"  (If T_initial is known, T_final = T_initial + ΔT)")

    except ValueError as e:
        print(f"  Error: {e}")


def menu_hess():
    print("\n-- Hess's Law --")
    print("  ΔH_target = Σ (multiplier × ΔH_step)")
    print("  Use a positive multiplier to keep the reaction direction.")
    print("  Use a negative multiplier to reverse (flip) a reaction.")
    print("  Use a non-1 magnitude to scale a reaction (e.g. 2 or 0.5).")
    print()
    try:
        n = int(_get_float("  Number of step reactions: "))
        if n < 1:
            print("  Must have at least one step."); return
    except ValueError:
        print("  Invalid number."); return

    dH_values = []
    multipliers = []
    for i in range(1, n+1):
        print(f"\n  Step {i}:")
        dh = _get_float(f"    ΔH for step {i} (kJ): ")
        mult = _get_float(f"    Multiplier for step {i} (e.g. 1, -1, 2, -0.5): ")
        dH_values.append(dh)
        multipliers.append(mult)

    total = hess_law(dH_values, multipliers)
    print(f"\n  Calculation:")
    for i, (dh, m) in enumerate(zip(dH_values, multipliers), 1):
        print(f"    Step {i}: {m:+g} × ({dh:+.2f}) = {m*dh:+.2f} kJ")
    print(f"    {'─'*35}")
    print(f"    ΔH_target = {total:+.2f} kJ")


def menu_bond_enthalpy():
    print("\n-- Bond Enthalpy  ΔH ≈ Σ(broken) − Σ(formed) --")
    print("  NOTE: This gives an approximation using average bond enthalpies.")
    print()
    print("  Built-in bonds (kJ/mol):")
    cols = list(BOND_ENTHALPIES.items())
    for i in range(0, len(cols), 4):
        row = cols[i:i+4]
        print("    " + "   ".join(f"{k:<6} {v:>4}" for k,v in row))
    print()

    def collect_bonds(label):
        bonds = []
        try:
            n = int(_get_float(f"  Number of {label} bond types: "))
        except ValueError:
            return []
        for i in range(n):
            bond = input(f"    Bond type {i+1} (e.g. C-H, O=O): ").strip()
            val  = lookup_bond(bond)
            if val is not None:
                print(f"    Found in table: {bond} = {val} kJ/mol")
                use_table = input(f"    Use table value {val}? (y/n): ").strip().lower()
                if use_table != 'y':
                    val = _get_float(f"    Enter custom value (kJ/mol): ")
            else:
                print(f"    '{bond}' not in built-in table.")
                val = _get_float(f"    Enter enthalpy for {bond} (kJ/mol): ")
            count = _get_float(f"    Count of {bond} bonds: ")
            bonds.append((bond, count, val))
        return bonds

    broken = collect_bonds("broken")
    formed = collect_bonds("formed")

    dH, sb, sf = bond_enthalpy_dH(broken, formed)

    print(f"\n  Bonds broken:  Σ = {sb:.2f} kJ")
    for label, cnt, enth in broken:
        print(f"    {cnt:.0f} × {label} ({enth} kJ/mol) = {cnt*enth:.2f} kJ")

    print(f"  Bonds formed:  Σ = {sf:.2f} kJ")
    for label, cnt, enth in formed:
        print(f"    {cnt:.0f} × {label} ({enth} kJ/mol) = {cnt*enth:.2f} kJ")

    print(f"\n  ΔH ≈ {sb:.2f} − {sf:.2f} = {dH:+.2f} kJ/mol")
    print(f"  {'Endothermic' if dH > 0 else 'Exothermic'} (approximate)")
    print("  [NOTE] Bond enthalpies give estimates; actual ΔH may differ.")


def menu_standard_enthalpy():
    print("\n-- Standard Enthalpy of Reaction  ΔH°rxn --")
    print("  ΔH°rxn = Σ coeff·ΔH°f(products) − Σ coeff·ΔH°f(reactants)")
    print("  NOTE: ΔH°f for elements in standard state = 0 kJ/mol")
    print()

    species = []
    for role in ("reactant", "product"):
        try:
            n = int(_get_float(f"  Number of {role}s: "))
        except ValueError:
            print("  Invalid number."); return
        for i in range(n):
            formula = input(f"    {role.capitalize()} {i+1} formula: ").strip()
            coeff   = _get_float(f"    Stoichiometric coefficient for {formula}: ")
            dHf     = _get_float(f"    ΔH°f for {formula} (kJ/mol, 0 for elements): ")
            species.append({'formula': formula, 'dHf': dHf, 'coeff': coeff, 'role': role})

    try:
        dH_rxn = standard_enthalpy_rxn(species)
    except ValueError as e:
        print(f"  Error: {e}"); return

    print(f"\n  Calculation:")
    products  = [s for s in species if s['role'] == 'product']
    reactants = [s for s in species if s['role'] == 'reactant']
    print("  Products:")
    for s in products:
        print(f"    {s['coeff']} × ΔH°f({s['formula']}) = {s['coeff']} × {s['dHf']} = {s['coeff']*s['dHf']:+.2f} kJ")
    print("  Reactants:")
    for s in reactants:
        print(f"    {s['coeff']} × ΔH°f({s['formula']}) = {s['coeff']} × {s['dHf']} = {s['coeff']*s['dHf']:+.2f} kJ  (subtracted)")
    print(f"  {'─'*40}")
    print(f"  ΔH°rxn = {dH_rxn:+.2f} kJ")
    print(f"  {'Endothermic' if dH_rxn > 0 else 'Exothermic'} reaction")


def menu_gibbs():
    print("\n-- Gibbs Free Energy  ΔG = ΔH − TΔS --")
    print("  Units: ΔH in kJ, ΔS in J/K, T in K (auto-converts from °C)")
    print("  ΔG < 0 → spontaneous  |  ΔG > 0 → non-spontaneous  |  ΔG = 0 → equilibrium")
    print()
    print("Solve for:")
    print("1. ΔG")
    print("2. ΔH")
    print("3. T (temperature at which ΔG = 0, i.e. crossover point)")
    print("4. ΔS")
    print("5. Qualitative spontaneity analysis (from signs of ΔH and ΔS)")
    choice = input("Select (1-5): ").strip()

    def get_T():
        mode = input("  Temperature in (1) Kelvin  or  (2) Celsius: ").strip()
        T = _get_float("  T: ")
        if mode == "2":
            T = celsius_to_kelvin(T)
            print(f"  Converted: T = {T:.2f} K")
        return T

    try:
        if choice == "1":
            dH = _get_float("  ΔH (kJ): ")
            T  = get_T()
            dS = _get_float("  ΔS (J/K): ")
            dG = gibbs_dG(dH, T, dS)
            print(f"\n  ΔG = {dG:+.4f} kJ")
            print(f"  {spontaneity(dG)}")
            print(f"  T·ΔS term = {T * dS / 1000:.4f} kJ")

        elif choice == "2":
            dG = _get_float("  ΔG (kJ): ")
            T  = get_T()
            dS = _get_float("  ΔS (J/K): ")
            dH = gibbs_dH(dG, T, dS)
            print(f"\n  ΔH = {dH:+.4f} kJ")

        elif choice == "3":
            dH = _get_float("  ΔH (kJ): ")
            dS = _get_float("  ΔS (J/K): ")
            T  = gibbs_T(dH, 0, dS)
            print(f"\n  Crossover T (where ΔG = 0) = {T:.2f} K  ({T - 273.15:.2f} °C)")
            print(f"  Below this T: {'spontaneous' if dH < 0 else 'non-spontaneous'}")
            print(f"  Above this T: {'non-spontaneous' if dH < 0 else 'spontaneous'}")

        elif choice == "4":
            dH = _get_float("  ΔH (kJ): ")
            dG = _get_float("  ΔG (kJ): ")
            T  = get_T()
            dS = gibbs_dS(dH, dG, T)
            print(f"\n  ΔS = {dS:+.4f} J/K")

        elif choice == "5":
            dH = _get_float("  ΔH (kJ): ")
            dS = _get_float("  ΔS (J/K): ")
            desc = spontaneity_analysis(dH, dS)
            print(f"\n  {desc}")
            if dS != 0:
                T_cross = gibbs_T(dH, 0, dS)
                if T_cross > 0:
                    print(f"  Crossover temperature = {T_cross:.2f} K  ({T_cross - 273.15:.2f} °C)")

        else:
            print("Invalid choice.")

    except ValueError as e:
        print(f"  Error: {e}")


# ── Main menu ────────────────────────────────────────────────────────────────

def thermodynamics_menu():
    while True:
        print("\n=== Enthalpy & Thermodynamics Calculator ===")
        print("1. Calorimetry  (q = mcΔT)")
        print("2. Hess's Law")
        print("3. Bond Enthalpy")
        print("4. Standard Enthalpy of Reaction  (ΔH°rxn)")
        print("5. Entropy & Gibbs Free Energy  (ΔG = ΔH − TΔS)")
        print("0. Return to Main Menu")

        choice = input("Select an option (0-5): ").strip()

        if choice == "1":
            menu_calorimetry()
        elif choice == "2":
            menu_hess()
        elif choice == "3":
            menu_bond_enthalpy()
        elif choice == "4":
            menu_standard_enthalpy()
        elif choice == "5":
            menu_gibbs()
        elif choice == "0":
            break
        else:
            print("Invalid choice. Please try again.")
