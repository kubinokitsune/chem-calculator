# percent_composition_calculator.py

import re
from collections import defaultdict

from Periodic_table import ELEMENTS

# Molar masses (g/mol), from the one element table in Periodic_table.py.
MOLAR_MASS = {symbol: mass for _z, symbol, _name, mass in ELEMENTS}


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


def _parse_group(s, i, depth=0):
    """Parse a group (possibly nested) starting at index i. Returns (counts_dict, new_index)."""
    n = len(s)
    counts = defaultdict(int)

    while i < n:
        ch = s[i]
        if ch in '([{':
            inner, i = _parse_group(s, i + 1, depth + 1)
            mult, i = _parse_number(s, i)
            for el, cnt in inner.items():
                counts[el] += cnt * mult
            continue
        if ch in ')]}':
            if depth == 0:
                raise FormulaError("Unmatched '{}' at position {} in '{}'.".format(ch, i+1, s))
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

    if depth > 0:
        raise FormulaError("Missing closing bracket in '{}'.".format(s))
    return counts, i


def parse_formula(formula):
    """Parse a chemical formula into a dict of element -> count.
    Supports nested parentheses/brackets/braces and hydrates with middle dot (e.g., CuSO4·5H2O).
    """
    if not formula or not isinstance(formula, str):
        raise FormulaError("Formula must be a non-empty string.")

    # Remove spaces and normalize hydrate separator
    f = formula.replace(' ', '')

    # Split on middle-dot variants, * and . for hydrates (e.g. CuSO4*5H2O, CuSO4·5H2O, CuSO4.5H2O)
    parts = re.split(r'[·•*.]', f)

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
