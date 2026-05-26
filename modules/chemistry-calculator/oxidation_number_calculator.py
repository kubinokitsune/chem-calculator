# oxidation_number_calculator.py
# Rule-based oxidation number solver.
# Applies known fixed oxidation states, then solves algebraically for one unknown element.

from percent_composition_calculator import parse_formula, FormulaError

# Fixed oxidation states applied in priority order.
# Higher-priority rules are listed first; lower entries do not override them.
FIXED_STATES = {
    'F':  -1,                                          # Always -1 (most electronegative)
    'Li': +1, 'Na': +1, 'K': +1, 'Rb': +1, 'Cs': +1, 'Fr': +1,  # Group 1
    'Be': +2, 'Mg': +2, 'Ca': +2, 'Sr': +2, 'Ba': +2, 'Ra': +2,  # Group 2
    'Al': +3,
    'Zn': +2, 'Cd': +2,
    'Ag': +1,
    'H':  +1,   # +1 with nonmetals (default; user should note hydrides are -1)
    'O':  -2,   # -2 default; peroxides = -1 (user selects)
    # Cl, Br, I are NOT pre-fixed so they can be solved as unknowns in oxoacids
    # (HClO4 → Cl=+7, HBrO3 → Br=+5, etc.). They will still evaluate to -1 in
    # simple halides where the metal/H fixes the other element(s).
}

OXIDATION_RULES = [
    "1. Pure element (O2, Fe, S8, ...): 0",
    "2. Fluorine (F): always -1",
    "3. Group 1 metals (Li, Na, K, Rb, Cs): +1 in compounds",
    "4. Group 2 metals (Be, Mg, Ca, Sr, Ba): +2 in compounds",
    "5. Hydrogen (H): +1 with nonmetals, -1 in metal hydrides (e.g. NaH)",
    "6. Oxygen (O): -2 normally; -1 in peroxides (H2O2, Na2O2)",
    "7. Halogens (Cl, Br, I): -1 when less electronegative element present",
    "8. Sum of all oxidation numbers = overall ionic charge (0 for neutral)",
]

PEROXIDES = {'H2O2', 'Na2O2', 'K2O2', 'BaO2', 'CaO2'}


def solve_oxidation_numbers(formula, charge=0, peroxide=False):
    """
    Returns a dict of {element: oxidation_number}.
    Raises ValueError if formula has more than one unknown element.
    """
    try:
        counts = parse_formula(formula)
    except FormulaError as e:
        raise ValueError(str(e))

    # Pure element: all atoms are 0
    if len(counts) == 1:
        return {list(counts.keys())[0]: 0}

    states = dict(FIXED_STATES)
    if peroxide:
        states['O'] = -1

    known_sum = 0
    unknowns = []

    for elem, cnt in counts.items():
        if elem in states:
            known_sum += states[elem] * cnt
        else:
            unknowns.append(elem)

    if len(unknowns) == 0:
        total = sum(states[e] * c for e, c in counts.items())
        if abs(total - charge) > 0.01:
            raise ValueError(
                f"All elements have fixed states but charge doesn't balance "
                f"(calculated {total:+.0f}, expected {charge:+d})."
            )
        return {e: states[e] for e in counts}

    if len(unknowns) > 1:
        raise ValueError(
            f"Cannot solve: more than one element with unknown oxidation state "
            f"({', '.join(unknowns)}). Specify the charge or simplify the formula."
        )

    unknown_elem = unknowns[0]
    unknown_count = counts[unknown_elem]
    ox = (charge - known_sum) / unknown_count

    result = {}
    for elem in counts:
        result[elem] = states[elem] if elem in states else ox
    return result


def _fmt_ox(value):
    if value == int(value):
        n = int(value)
        return f"{n:+d}"
    return f"{value:+.2f}"


def oxidation_number_menu():
    while True:
        print("\n--- Oxidation Number Calculator ---")
        print("1. Calculate oxidation numbers in a compound or ion")
        print("2. Show oxidation number rules")
        print("0. Return to Main Menu")
        choice = input("Select an option (0-2): ").strip()

        if choice == '1':
            from constants import capitalize_formula
            raw = input("Enter formula (e.g., KMnO4, H2SO4, Cr2O3, MnO4): ").strip()
            if not raw:
                print("[ERROR] Please enter a formula.")
                continue
            formula = capitalize_formula(raw)
            charge_raw = input("Overall ionic charge (0 for neutral, e.g. -1, +2): ").strip()
            if not charge_raw:
                print("[ERROR] Please enter the ionic charge (use 0 for neutral).")
                continue
            try:
                charge = int(charge_raw.replace('+', ''))
            except ValueError:
                print("[ERROR] Invalid charge: expected a whole number like 0, -1, +2.")
                continue

            peroxide = formula in PEROXIDES
            if not peroxide and 'O' in formula:
                p = input("Is this a peroxide (O has -1 state)? (y/n): ").strip().lower()
                peroxide = p == 'y'

            try:
                result = solve_oxidation_numbers(formula, charge, peroxide)
                print(f"\nOxidation Numbers in {formula}  (overall charge = {charge:+d})")
                print("-" * 40)
                for elem, ox in result.items():
                    print(f"  {elem:4s}: {_fmt_ox(ox)}")
                print()
                # Verify
                counts = parse_formula(formula)
                total = sum(result[e] * counts[e] for e in counts)
                print(f"  Verification: sum = {total:+.0f}  (expected {charge:+d})")
            except ValueError as e:
                print(f"[ERROR] {e}")

        elif choice == '2':
            print("\nOxidation Number Rules:")
            for rule in OXIDATION_RULES:
                print(f"  {rule}")

        elif choice == '0':
            break

        else:
            print("Invalid choice. Please try again.")
