# chemstoi.py - moles, formulas, solutions, yield (IB S1.4, R2.1)

import math
from chemcore import (fmt, show, line, ask_float, ask_int, ask_text, ask_choice,
                      pause, parse_formula, molar_mass, mass_or_formula,
                      formula_text, masses, gcd)

AVOGADRO = 6.02e23
MOLAR_VOL_STP = 22.7      # dm3/mol at 0 C and 100 kPa (IB)


# ---- calculations ----------------------------------------------------------

def empirical_formula(elements, amounts):
    """Masses (or percentages) -> whole-number ratio."""
    if len(elements) != len(amounts) or not elements:
        raise ValueError("One amount per element")
    table = masses()
    moles = []
    for el, m in zip(elements, amounts):
        if m <= 0:
            raise ValueError("Amounts must be > 0")
        if el not in table:
            raise ValueError("Unknown element: " + el)
        moles.append(m / table[el])
    smallest = min(moles)
    ratios = [m / smallest for m in moles]
    best = 1
    for mult in range(1, 13):
        worst = 0.0
        for r in ratios:
            diff = abs(r * mult - round(r * mult))
            if diff > worst:
                worst = diff
        if worst <= 0.1:
            best = mult
            break
    counts = {}
    for el, r in zip(elements, ratios):
        counts[el] = int(round(r * best))
    return counts, best


def molecular_formula(counts, Mr):
    """Empirical counts + molecular mass -> molecular formula."""
    table = masses()
    emp_mass = 0.0
    for el in counts:
        emp_mass += table[el] * counts[el]
    if emp_mass <= 0:
        raise ValueError("Empirical mass must be > 0")
    ratio = Mr / emp_mass
    n = int(round(ratio))
    if n < 1:
        raise ValueError("Mr is smaller than the empirical mass")
    out = {}
    for el in counts:
        out[el] = counts[el] * n
    return out, n, emp_mass


def combustion(mass_co2, mass_h2o, sample=None):
    """CO2 and H2O masses -> elements and masses of C, H (and O by difference)."""
    table = masses()
    m_co2 = table["C"] + 2 * table["O"]
    m_h2o = 2 * table["H"] + table["O"]
    mass_c = mass_co2 / m_co2 * table["C"]
    mass_h = 2 * mass_h2o / m_h2o * table["H"]
    elements, amounts = [], []
    if mass_c > 0:
        elements.append("C")
        amounts.append(mass_c)
    if mass_h > 0:
        elements.append("H")
        amounts.append(mass_h)
    note = ""
    if sample:
        mass_o = sample - mass_c - mass_h
        if mass_o < -0.01 * sample:
            raise ValueError("C and H weigh more than the sample")
        if mass_o > 0.01 * sample:
            elements.append("O")
            amounts.append(mass_o)
        else:
            note = "No oxygen in the compound"
    return elements, amounts, note


def limiting(names, coeffs, amounts, products, p_coeffs, in_grams):
    """Returns (index of the limiting reactant, extent, moles of each reactant)."""
    moles = []
    for name, amount in zip(names, amounts):
        if in_grams:
            moles.append(amount / molar_mass(name))
        else:
            moles.append(amount)
    ratios = []
    for n, c in zip(moles, coeffs):
        if c <= 0:
            raise ValueError("Coefficients must be > 0")
        ratios.append(n / c)
    extent = min(ratios)
    return ratios.index(extent), extent, moles


# ---- menus -----------------------------------------------------------------

def menu_moles():
    print("MOLES")
    key = ask_choice("Pick: ", [
        ("1", "mass -> mol"), ("2", "mol -> mass"), ("3", "mol -> particles"),
        ("4", "particles -> mol"), ("5", "mol -> volume STP"), ("6", "volume STP -> mol")])
    if key in ("1", "2"):
        M = mass_or_formula(ask_text("M (g/mol) or formula: "))
        show("M", M, "g/mol")
        if key == "1":
            m = ask_float("mass (g): ", True)
            show("n", m / M, "mol")
        else:
            n = ask_float("n (mol): ", True)
            show("mass", n * M, "g")
    elif key == "3":
        n = ask_float("n (mol): ", True)
        show("particles", n * AVOGADRO)
    elif key == "4":
        N = ask_float("particles: ", True)
        show("n", N / AVOGADRO, "mol")
    elif key == "5":
        n = ask_float("n (mol): ", True)
        show("V", n * MOLAR_VOL_STP, "dm3 (STP)")
    else:
        V = ask_float("V (dm3): ", True)
        show("n", V / MOLAR_VOL_STP, "mol")


def menu_percent():
    print("PERCENT COMPOSITION")
    formula = ask_text("Formula: ")
    counts = parse_formula(formula)
    M = molar_mass(formula)
    show("M", M, "g/mol")
    table = masses()
    for el in sorted(counts):
        pct = table[el] * counts[el] / M * 100
        print("  " + el + ": " + fmt(pct, 4) + " %")


def menu_empirical():
    print("EMPIRICAL FORMULA")
    key = ask_choice("Pick: ", [("1", "from masses/%"), ("2", "from combustion"),
                                ("3", "molecular from Mr")])
    if key == "2":
        co2 = ask_float("mass CO2 (g): ", True)
        h2o = ask_float("mass H2O (g): ", True)
        sample = ask_float("sample (g, EXE=skip): ", False, blank=0)
        elements, amounts, note = combustion(co2, h2o, sample if sample else None)
        for el, m in zip(elements, amounts):
            print("  " + el + ": " + fmt(m, 4) + " g")
        counts, mult = empirical_formula(elements, amounts)
        print("Empirical: " + formula_text(counts))
        if note:
            print(note)
        return
    count = ask_int("How many elements? ", 1, 8)
    elements, amounts = [], []
    for i in range(count):
        elements.append(ask_text("  element " + str(i + 1) + ": ").capitalize())
        amounts.append(ask_float("  mass or %: ", True))
    counts, mult = empirical_formula(elements, amounts)
    print("Empirical: " + formula_text(counts))
    if mult > 1:
        print("(ratios x " + str(mult) + ")")
    if key == "3":
        Mr = ask_float("Mr of molecule: ", True)
        mol, n, emp = molecular_formula(counts, Mr)
        print("Emp mass = " + fmt(emp, 4))
        print("n = Mr/emp = " + str(n))
        print("Molecular: " + formula_text(mol))


def menu_solutions():
    print("SOLUTIONS")
    key = ask_choice("Pick: ", [
        ("1", "c from n and V"), ("2", "n from c and V"), ("3", "V from n and c"),
        ("4", "c from a mass"), ("5", "mass for a solution"), ("6", "dilution"),
        ("7", "g/dm3 <-> mol/dm3"), ("8", "ppm")])
    if key == "1":
        n = ask_float("n (mol): ", True)
        V = ask_float("V (cm3): ", True)
        show("c", n / (V / 1000.0), "mol/dm3")
    elif key == "2":
        c = ask_float("c (mol/dm3): ", True)
        V = ask_float("V (cm3): ", True)
        show("n", c * V / 1000.0, "mol")
    elif key == "3":
        n = ask_float("n (mol): ", True)
        c = ask_float("c (mol/dm3): ", True)
        V = n / c
        show("V", V, "dm3")
        show("V", V * 1000, "cm3")
    elif key == "4":
        m = ask_float("mass (g): ", True)
        M = mass_or_formula(ask_text("M or formula: "))
        V = ask_float("V (cm3): ", True)
        show("n", m / M, "mol")
        show("c", m / M / (V / 1000.0), "mol/dm3")
    elif key == "5":
        c = ask_float("c wanted (mol/dm3): ", True)
        V = ask_float("V (cm3): ", True)
        M = mass_or_formula(ask_text("M or formula: "))
        show("mass", c * V / 1000.0 * M, "g")
        print("Dissolve and make up to mark")
    elif key == "6":
        print("c1V1 = c2V2")
        target = ask_choice("Solve for: ", [("a", "c1"), ("b", "V1"), ("c", "c2"), ("d", "V2")])
        if target == "a":
            V1 = ask_float("V1 (cm3): ", True)
            c2 = ask_float("c2 (mol/dm3): ", True)
            V2 = ask_float("V2 (cm3): ", True)
            show("c1", c2 * V2 / V1, "mol/dm3")
        elif target == "b":
            c1 = ask_float("c1 (mol/dm3): ", True)
            c2 = ask_float("c2 (mol/dm3): ", True)
            V2 = ask_float("V2 (cm3): ", True)
            V1 = c2 * V2 / c1
            show("V1", V1, "cm3")
            show("water to add", V2 - V1, "cm3")
        elif target == "c":
            c1 = ask_float("c1 (mol/dm3): ", True)
            V1 = ask_float("V1 (cm3): ", True)
            V2 = ask_float("V2 (cm3): ", True)
            show("c2", c1 * V1 / V2, "mol/dm3")
        else:
            c1 = ask_float("c1 (mol/dm3): ", True)
            V1 = ask_float("V1 (cm3): ", True)
            c2 = ask_float("c2 (mol/dm3): ", True)
            V2 = c1 * V1 / c2
            show("V2", V2, "cm3")
            show("water to add", V2 - V1, "cm3")
    elif key == "7":
        M = mass_or_formula(ask_text("M or formula: "))
        way = ask_choice("Way: ", [("a", "g/dm3 -> mol/dm3"), ("b", "mol/dm3 -> g/dm3")])
        value = ask_float("value: ", True)
        if way == "a":
            show("c", value / M, "mol/dm3")
        else:
            show("mass conc", value * M, "g/dm3")
    else:
        mg = ask_float("solute (mg): ", True)
        V = ask_float("solution (dm3): ", True)
        show("ppm", mg / V)


def menu_limiting():
    print("LIMITING REACTANT")
    in_grams = ask_choice("Amounts in: ", [("m", "mol"), ("g", "grams")]) == "g"
    count = ask_int("How many reactants? ", 1, 5)
    names, coeffs, amounts = [], [], []
    for i in range(count):
        names.append(ask_text("  reactant " + str(i + 1) + ": "))
        coeffs.append(ask_float("   coefficient: ", True))
        amounts.append(ask_float("   amount: ", True))
    pcount = ask_int("How many products? ", 1, 5)
    products, p_coeffs = [], []
    for i in range(pcount):
        products.append(ask_text("  product " + str(i + 1) + ": "))
        p_coeffs.append(ask_float("   coefficient: ", True))
    idx, extent, moles = limiting(names, coeffs, amounts, products, p_coeffs, in_grams)
    line()
    print("Limiting: " + names[idx])
    for i, name in enumerate(names):
        left = moles[i] - coeffs[i] * extent
        if left < 1e-12:
            left = 0.0
        print("  " + name + " left " + fmt(left, 3) + " mol")
    for name, c in zip(products, p_coeffs):
        n = c * extent
        text = "  " + name + ": " + fmt(n, 4) + " mol"
        try:
            text += " (" + fmt(n * molar_mass(name), 4) + " g)"
        except ValueError:
            pass
        print(text)


def menu_yield():
    print("PERCENTAGE YIELD")
    key = ask_choice("Find: ", [("1", "% yield"), ("2", "actual"), ("3", "theoretical")])
    if key == "1":
        actual = ask_float("actual (g): ", True)
        theory = ask_float("theoretical (g): ", True)
        show("% yield", actual / theory * 100, "%")
    elif key == "2":
        pct = ask_float("% yield: ", True)
        theory = ask_float("theoretical (g): ", True)
        show("actual", pct / 100 * theory, "g")
    else:
        actual = ask_float("actual (g): ", True)
        pct = ask_float("% yield: ", True)
        show("theoretical", actual / (pct / 100), "g")


def menu_atom_economy():
    print("ATOM ECONOMY")
    count = ask_int("How many reactants? ", 1, 5)
    total = 0.0
    for i in range(count):
        formula = ask_text("  reactant " + str(i + 1) + ": ")
        coeff = ask_float("   coefficient: ", True)
        total += molar_mass(formula) * coeff
    wanted = ask_text("Desired product: ")
    wcoeff = ask_float(" coefficient: ", True)
    mass = molar_mass(wanted) * wcoeff
    show("AE", mass / total * 100, "%")


MENU = [
    ("1", "Moles", menu_moles),
    ("2", "Percent composition", menu_percent),
    ("3", "Empirical/molecular", menu_empirical),
    ("4", "Solutions", menu_solutions),
    ("5", "Limiting reactant", menu_limiting),
    ("6", "Percentage yield", menu_yield),
    ("7", "Atom economy", menu_atom_economy),
]
