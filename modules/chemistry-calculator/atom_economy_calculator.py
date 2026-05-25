# atom_economy_calculator.py
# Atom Economy (Element Economy) measures what fraction of reactant atoms
# end up in the desired product.
# Formula: Atom Economy = (MW of desired product x its coefficient)
#                         / (sum of MW x coefficient for ALL reactants) x 100%

from percent_composition_calculator import parse_formula, MOLAR_MASS, FormulaError
from constants import capitalize_formula


def get_molar_mass(formula):
    """Return molar mass (g/mol) of a formula string."""
    counts = parse_formula(formula)
    return sum(MOLAR_MASS[el] * cnt for el, cnt in counts.items())


def calculate_atom_economy(reactants, r_coeffs, desired_product, d_coeff):
    """
    Returns atom economy as a percentage.
    reactants      : list of formula strings
    r_coeffs       : list of stoichiometric coefficients (same order)
    desired_product: formula string of the wanted product
    d_coeff        : stoichiometric coefficient of the desired product
    """
    mw_desired = get_molar_mass(desired_product) * d_coeff
    mw_reactants = sum(get_molar_mass(r) * c for r, c in zip(reactants, r_coeffs))
    if mw_reactants <= 0:
        raise ValueError("Total reactant molar mass is zero.")
    return (mw_desired / mw_reactants) * 100, mw_desired, mw_reactants


def atom_economy_menu():
    while True:
        print("\n--- Element Economy (Atom Economy) Calculator ---")
        print("Measures what percentage of reactant atoms end up in the desired product.")
        print()
        print("1. Calculate atom economy for a reaction")
        print("2. Show formula and explanation")
        print("0. Return to Main Menu")
        choice = input("Select an option (0-2): ").strip()

        if choice == '1':
            try:
                n = int(input("How many reactants in the balanced equation? "))
                if n < 1:
                    print("[ERROR] Must have at least one reactant.")
                    continue
            except ValueError:
                print("[ERROR] Enter a whole number.")
                continue

            reactants = []
            r_coeffs = []
            for i in range(n):
                raw_r = input(f"  Reactant #{i+1} formula (e.g., H2, O2, C6H12O6): ").strip()
                if not raw_r:
                    print("[ERROR] Formula cannot be empty.")
                    break
                r = capitalize_formula(raw_r)
                raw_c = input(f"  Coefficient for {r}: ").strip()
                try:
                    c = float(raw_c)
                    if c <= 0:
                        print(f"[ERROR] Coefficient for {r} must be greater than zero.")
                        break
                    get_molar_mass(r)   # validate formula now
                    reactants.append(r)
                    r_coeffs.append(c)
                except FormulaError as e:
                    print(f"[ERROR] Bad formula '{r}': {e}")
                    break
                except ValueError:
                    print(f"[ERROR] Invalid input: expected a number for coefficient of {r}.")
                    break
            else:
                raw_desired = input("Enter the desired product formula: ").strip()
                if not raw_desired:
                    print("[ERROR] Product formula cannot be empty.")
                    continue
                desired = capitalize_formula(raw_desired)
                raw_dc = input(f"Coefficient for {desired}: ").strip()
                try:
                    d_coeff = float(raw_dc)
                    if d_coeff <= 0:
                        print("[ERROR] Coefficient must be greater than zero.")
                        continue
                    ae, mw_d, mw_r = calculate_atom_economy(reactants, r_coeffs, desired, d_coeff)

                    print(f"\nAtom Economy Results")
                    print("-" * 40)
                    print(f"  Desired product ({desired}):")
                    print(f"    Molar mass            : {get_molar_mass(desired):.3f} g/mol")
                    print(f"    Coefficient           : {d_coeff}")
                    print(f"    MW x coeff            : {mw_d:.3f} g/mol")
                    print()
                    print(f"  Total reactant MW x coeff : {mw_r:.3f} g/mol")
                    print(f"  Atom Economy              : {ae:.2f}%")
                    print()
                    if ae >= 100:
                        print("  [NOTE] 100% - no atoms wasted (ideal reaction).")
                    elif ae >= 70:
                        print("  [NOTE] Good atom economy (above 70%).")
                    else:
                        print("  [NOTE] Low atom economy - significant by-products.")
                except FormulaError as e:
                    print(f"[ERROR] Bad formula '{desired}': {e}")
                except ValueError as e:
                    print(f"[ERROR] {e}")

        elif choice == '2':
            print()
            print("Atom Economy Formula:")
            print()
            print("  Atom Economy (%) = MW of desired product x coefficient")
            print("                     ---------------------------------------- x 100")
            print("                     Sum of (MW x coefficient) for all reactants")
            print()
            print("Example: CH4 + 2 O2 -> CO2 + 2 H2O  (desired product: H2O)")
            print("  MW(CH4)=16.04  MW(O2)=32.00  MW(H2O)=18.02")
            print("  Reactant total = 16.04*1 + 32.00*2 = 80.04")
            print("  Desired (H2O) = 18.02 * 2 = 36.04")
            print("  Atom Economy = 36.04 / 80.04 x 100 = 45.03%")

        elif choice == '0':
            break

        else:
            print("Invalid choice. Please try again.")
