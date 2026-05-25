# percent_composition_calculator.py

import re
from collections import defaultdict

# Molar masses (g/mol) for common elements
MOLAR_MASS = {
    'H': 1.008, 'He': 4.0026, 'Li': 6.94, 'Be': 9.0122, 'B': 10.81,
    'C': 12.011, 'N': 14.007, 'O': 15.999, 'F': 18.998, 'Ne': 20.180,
    'Na': 22.990, 'Mg': 24.305, 'Al': 26.982, 'Si': 28.085, 'P': 30.974,
    'S': 32.06, 'Cl': 35.45, 'Ar': 39.948, 'K': 39.098, 'Ca': 40.078,
    'Sc': 44.956, 'Ti': 47.867, 'V': 50.941, 'Cr': 51.996, 'Mn': 54.938,
    'Fe': 55.845, 'Co': 58.933, 'Ni': 58.693, 'Cu': 63.546, 'Zn': 65.38,
    'Ga': 69.723, 'Ge': 72.630, 'As': 74.922, 'Se': 78.971, 'Br': 79.904,
    'Kr': 83.798, 'Rb': 85.467, 'Sr': 87.62, 'Y': 88.906, 'Zr': 91.224,
    'Nb': 92.906, 'Mo': 95.95, 'Tc': 98, 'Ru': 101.07, 'Rh': 102.91,
    'Pd': 106.42, 'Ag': 107.87, 'Cd': 112.41, 'In': 114.82, 'Sn': 118.71,
    'Sb': 121.76, 'Te': 127.60, 'I': 126.90, 'Xe': 131.29, 'Cs': 132.91,
    'Ba': 137.33, 'La': 138.91, 'Ce': 140.12, 'Pr': 140.91, 'Nd': 144.24,
    'Pm': 145, 'Sm': 150.36, 'Eu': 151.96, 'Gd': 157.25, 'Tb': 158.93,
    'Dy': 162.50, 'Ho': 164.93, 'Er': 167.26, 'Tm': 168.93, 'Yb': 173.04,
    'Lu': 174.97, 'Hf': 178.49, 'Ta': 180.95, 'W': 183.84, 'Re': 186.21,
    'Os': 190.23, 'Ir': 192.22, 'Pt': 195.08, 'Au': 196.97, 'Hg': 200.59,
    'Tl': 204.38, 'Pb': 207.2, 'Bi': 208.98, 'Po': 209, 'At': 210,
    'Rn': 222, 'Fr': 223, 'Ra': 226, 'Ac': 227, 'Th': 232.04,
    'Pa': 231.04, 'U': 238.03, 'Np': 237, 'Pu': 244, 'Am': 243,
    'Cm': 247, 'Bk': 247, 'Cf': 251, 'Es': 252, 'Fm': 257, 'Md': 258,
    'No': 259, 'Lr': 262, 'Rf': 267, 'Db': 270, 'Sg': 271, 'Bh': 270,
    'Hs': 277, 'Mt': 276, 'Ds': 281, 'Rg': 282, 'Cn': 285, 'Nh': 286,
    'Fl': 289, 'Mc': 288, 'Lv': 293, 'Ts': 294, 'Og': 294
}


class FormulaError(ValueError):
    pass


def _parse_number(s, i):
    """Parse an integer starting at s[i]; return (value, new_index). Default is 1 if no number."""
    n = len(s)
    if i >= n or not s[i].isdigit():
        return 1, i
    j = i
    while j < n and s[j].isdigit():
        j += 1
    return int(s[i:j]), j


def _parse_group(s, i):
    """Parse a group (possibly nested) starting at index i. Returns (counts_dict, new_index)."""
    n = len(s)
    counts = defaultdict(int)

    while i < n:
        ch = s[i]
        if ch in '([{':
            inner, i = _parse_group(s, i + 1)
            mult, i = _parse_number(s, i)
            for el, cnt in inner.items():
                counts[el] += cnt * mult
            continue
        if ch in ')]}':
            return counts, i + 1

        if ch.isupper():
            j = i + 1
            if j < n and s[j].islower():
                j += 1
            element = s[i:j]
            mult, i2 = _parse_number(s, j)
            counts[element] += mult
            i = i2
            continue

        # Unexpected character
        raise FormulaError("Unexpected character '{}' at position {} in '{}'.".format(ch, i+1, s))

    return counts, i


def parse_formula(formula):
    """Parse a chemical formula into a dict of element -> count.
    Supports nested parentheses/brackets/braces and hydrates with middle dot (e.g., CuSO4·5H2O).
    """
    if not formula or not isinstance(formula, str):
        raise FormulaError("Formula must be a non-empty string.")

    # Remove spaces and normalize hydrate separator
    f = formula.replace(' ', '')

    # Split on middle-dot variants and * for hydrates (e.g. CuSO4*5H2O or CuSO4·5H2O)
    parts = re.split(r'[·•*]', f)

    total = defaultdict(int)

    for part in parts:
        if not part:
            continue
        # Leading multiplier for the entire part, e.g., 5H2O
        m = re.match(r'^(\d+)(.*)$', part)
        if m:
            lead_mult = int(m.group(1))
            rest = m.group(2)
        else:
            lead_mult = 1
            rest = part

        group_counts, end_idx = _parse_group(rest, 0)
        if end_idx != len(rest):
            raise FormulaError("Unexpected trailing characters in '{}'.".format(rest[end_idx:]))

        for el, cnt in group_counts.items():
            total[el] += cnt * lead_mult

    # Validate elements exist in molar mass table
    unknown = [el for el in total.keys() if el not in MOLAR_MASS]
    if unknown:
        raise FormulaError(
            "Unknown element(s) not in periodic table reference: " + ", ".join(unknown)
        )

    return dict(total)


def compute_percent_composition(formula):
    """Return (molar_mass, percent_by_element) for the given formula string."""
    composition = parse_formula(formula)

    molar_mass = 0.0
    for el, cnt in composition.items():
        molar_mass += MOLAR_MASS[el] * cnt

    if molar_mass <= 0:
        raise FormulaError("Computed molar mass is non-positive. Check the formula.")

    percents = {}
    for el, cnt in composition.items():
        mass = MOLAR_MASS[el] * cnt
        percents[el] = (mass / molar_mass) * 100.0

    return molar_mass, percents


def print_percent_table(formula, molar_mass, percents):
    print("\nFormula: {}".format(formula))
    print("Molar Mass: {:.3f} g/mol\n".format(molar_mass))
    print("Element  Percent by mass")
    print("-------------------------")
    for el, pct in sorted(percents.items(), key=lambda x: (-x[1], x[0])):
        print("{:<7} {:>7.2f} %".format(el, pct))


def percent_composition_menu():
    while True:
        print("\n--- Percent Composition Calculator ---")
        print("1. Calculate percent composition from chemical formula")
        print("0. Exit")
        choice = input("Select an option (0-1): ").strip().lower()

        if choice in ('0', 'exit'):
            break
        elif choice == '1':
            from constants import capitalize_formula
            raw = input("Enter chemical formula (e.g., C6H12O6, Ca(OH)2, CuSO4*5H2O): ").strip()
            if not raw:
                print("[ERROR] Please enter a formula.")
                continue
            formula = capitalize_formula(raw)
            try:
                molar_mass, percents = compute_percent_composition(formula)
                print_percent_table(formula, molar_mass, percents)
            except FormulaError as fe:
                print("[ERROR] {}".format(fe))
            except Exception as e:
                print("[ERROR] Unexpected error: {}".format(e))
        else:
            print("Invalid choice. Please try again.")
