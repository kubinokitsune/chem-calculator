# ionic_bonding_calculator.py
# Tools:
#   1. Bond type classifier  (ionic / polar covalent / nonpolar covalent)
#      based on Pauling electronegativity difference.
#   2. Ionic formula writer  (cross-multiplication method).
#   3. Common ion charge reference.

import math

# Pauling electronegativities
ELECTRONEGATIVITIES = {
    'H': 2.20, 'He': 0.00,
    'Li': 0.98, 'Be': 1.57, 'B': 2.04, 'C': 2.55, 'N': 3.04, 'O': 3.44, 'F': 3.98, 'Ne': 0.00,
    'Na': 0.93, 'Mg': 1.31, 'Al': 1.61, 'Si': 1.90, 'P': 2.19, 'S': 2.58, 'Cl': 3.16, 'Ar': 0.00,
    'K': 0.82, 'Ca': 1.00, 'Sc': 1.36, 'Ti': 1.54, 'V': 1.63, 'Cr': 1.66, 'Mn': 1.55,
    'Fe': 1.83, 'Co': 1.88, 'Ni': 1.91, 'Cu': 1.90, 'Zn': 1.65, 'Ga': 1.81, 'Ge': 2.01,
    'As': 2.18, 'Se': 2.55, 'Br': 2.96, 'Kr': 3.00,
    'Rb': 0.82, 'Sr': 0.95, 'Y': 1.22, 'Zr': 1.33, 'Nb': 1.60, 'Mo': 2.16, 'Tc': 1.90,
    'Ru': 2.20, 'Rh': 2.28, 'Pd': 2.20, 'Ag': 1.93, 'Cd': 1.69, 'In': 1.78, 'Sn': 1.96,
    'Sb': 2.05, 'Te': 2.10, 'I': 2.66, 'Xe': 2.60,
    'Cs': 0.79, 'Ba': 0.89, 'La': 1.10, 'Ce': 1.12, 'Hf': 1.30, 'Ta': 1.50, 'W': 2.36,
    'Re': 1.90, 'Os': 2.20, 'Ir': 2.20, 'Pt': 2.28, 'Au': 2.54, 'Hg': 2.00,
    'Tl': 1.62, 'Pb': 2.33, 'Bi': 2.02, 'Po': 2.00, 'At': 2.20,
    'Fr': 0.70, 'Ra': 0.90, 'Ac': 1.10, 'Th': 1.30, 'Pa': 1.50, 'U': 1.38,
}

# Common ion charges. Variable-charge metals list both options.
COMMON_ION_CHARGES = {
    # Group 1 cations
    'Li': [+1], 'Na': [+1], 'K': [+1], 'Rb': [+1], 'Cs': [+1],
    # Group 2 cations
    'Be': [+2], 'Mg': [+2], 'Ca': [+2], 'Sr': [+2], 'Ba': [+2],
    # Transition metals (common charges)
    'Al': [+3],
    'Fe': [+2, +3],
    'Cu': [+1, +2],
    'Zn': [+2],
    'Ag': [+1],
    'Mn': [+2, +4, +7],
    'Cr': [+2, +3],
    'Co': [+2, +3],
    'Ni': [+2],
    'Pb': [+2, +4],
    'Sn': [+2, +4],
    'Hg': [+1, +2],
    # Nonmetal anions
    'F':  [-1], 'Cl': [-1], 'Br': [-1], 'I': [-1],
    'O':  [-2], 'S':  [-2], 'Se': [-2],
    'N':  [-3], 'P':  [-3],
}


def classify_bond(elem1, elem2):
    """
    Returns (bond_type, en1, en2, diff).
    Thresholds: diff >= 1.7 = ionic, 0.4-1.7 = polar covalent, < 0.4 = nonpolar covalent.
    """
    en1 = ELECTRONEGATIVITIES.get(elem1)
    en2 = ELECTRONEGATIVITIES.get(elem2)
    if en1 is None:
        raise ValueError(f"Electronegativity not available for '{elem1}'.")
    if en2 is None:
        raise ValueError(f"Electronegativity not available for '{elem2}'.")
    diff = abs(en1 - en2)
    if diff >= 1.7:
        bond_type = "Ionic"
    elif diff >= 0.4:
        bond_type = "Polar Covalent"
    else:
        bond_type = "Nonpolar Covalent"
    return bond_type, en1, en2, diff


def write_ionic_formula(cation_sym, cation_charge, anion_sym, anion_charge):
    """
    Returns the ionic formula string using cross-multiplication.
    e.g. Ca(+2) + Cl(-1) -> CaCl2
    """
    if cation_charge <= 0 or anion_charge >= 0:
        raise ValueError("Cation charge must be positive and anion charge must be negative.")
    g = math.gcd(cation_charge, abs(anion_charge))
    c_sub = abs(anion_charge) // g
    a_sub = cation_charge // g
    formula = cation_sym + (str(c_sub) if c_sub > 1 else '')
    formula += anion_sym + (str(a_sub) if a_sub > 1 else '')
    return formula


def ionic_bonding_menu():
    while True:
        print("\n--- Ionic Bonding Calculator ---")
        print("1. Classify bond type (ionic / polar covalent / nonpolar covalent)")
        print("2. Write ionic formula from two elements")
        print("3. Common ion charges reference")
        print("0. Return to Main Menu")
        choice = input("Select an option (0-3): ").strip()

        if choice == '1':
            elem1 = input("Enter first element symbol (e.g., Na): ").strip().capitalize()
            elem2 = input("Enter second element symbol (e.g., Cl): ").strip().capitalize()
            # Handle two-letter symbols where second char is lowercase
            if len(elem1) == 2:
                elem1 = elem1[0].upper() + elem1[1].lower()
            if len(elem2) == 2:
                elem2 = elem2[0].upper() + elem2[1].lower()
            try:
                bond_type, en1, en2, diff = classify_bond(elem1, elem2)
                print(f"\nBond Analysis: {elem1} - {elem2}")
                print(f"  {elem1} electronegativity : {en1:.2f}")
                print(f"  {elem2} electronegativity : {en2:.2f}")
                print(f"  Difference              : {diff:.2f}")
                print(f"  Bond type               : {bond_type}")
                print()
                print("  Reference thresholds:")
                print("    >= 1.7  -> Ionic")
                print("    0.4-1.7 -> Polar Covalent")
                print("    < 0.4   -> Nonpolar Covalent")
            except ValueError as e:
                print(f"[ERROR] {e}")

        elif choice == '2':
            print("\nWrite an ionic formula from a cation and an anion.")
            cation = input("Enter cation element symbol (e.g., Ca): ").strip().capitalize()
            anion  = input("Enter anion element symbol  (e.g., Cl): ").strip().capitalize()

            # Look up known charges or ask
            c_charges = COMMON_ION_CHARGES.get(cation)
            a_charges = COMMON_ION_CHARGES.get(anion)

            try:
                if c_charges and len(c_charges) == 1:
                    c_charge = c_charges[0]
                    print(f"  {cation} charge: {c_charge:+d} (from reference)")
                else:
                    if c_charges:
                        opts = ', '.join(f"{x:+d}" for x in c_charges)
                        print(f"  {cation} has variable charges: {opts}")
                    c_charge = int(input(f"  Enter charge for {cation} (e.g., +2): ").strip().replace('+',''))

                if a_charges and len(a_charges) == 1:
                    a_charge = a_charges[0]
                    print(f"  {anion} charge: {a_charge:+d} (from reference)")
                else:
                    if a_charges:
                        opts = ', '.join(f"{x:+d}" for x in a_charges)
                        print(f"  {anion} has variable charges: {opts}")
                    a_charge = int(input(f"  Enter charge for {anion} (e.g., -1): ").strip().replace('+',''))

                formula = write_ionic_formula(cation, c_charge, anion, a_charge)
                print(f"\n  Ionic formula: {formula}")
                print(f"  ({cation}{c_charge:+d} and {anion}{a_charge:+d} combine to give a neutral compound)")
            except ValueError as e:
                print(f"[ERROR] {e}")

        elif choice == '3':
            print("\nCommon Ion Charges Reference")
            print("-" * 40)
            cations = {k: v for k, v in COMMON_ION_CHARGES.items() if v[0] > 0}
            anions  = {k: v for k, v in COMMON_ION_CHARGES.items() if v[0] < 0}
            print("Cations:")
            for sym, charges in cations.items():
                charges_str = ' or '.join(f"{c:+d}" for c in charges)
                print(f"  {sym:4s}: {charges_str}")
            print("\nAnions:")
            for sym, charges in anions.items():
                charges_str = ' or '.join(f"{c:+d}" for c in charges)
                print(f"  {sym:4s}: {charges_str}")

        elif choice == '0':
            break

        else:
            print("Invalid choice. Please try again.")
