# equation_balancer.py

from sympy import Matrix, lcm
import re
from mole_conversions import mole_conversion_menu
from constants import capitalize_formula

def format_subscript(compound):
    return compound


def parse_compound(compound):
    """Parse a chemical compound into a dictionary of elements and counts."""
    parts = re.findall(r'([A-Z][a-z]?)(\d*)', compound)
    composition = {}
    for (element, count) in parts:
        count = int(count) if count else 1
        if element in composition:
            composition[element] += count
        else:
            composition[element] = count
    return composition

def balance_equation(reactants, products):
    """Balance a chemical equation given lists of reactants and products."""
    elements = sorted({elem for compound in reactants + products for elem in parse_compound(compound)})
    matrix = []
    for elem in elements:
        row = []
        for reactant in reactants:
            row.append(-parse_compound(reactant).get(elem, 0))
        for product in products:
            row.append(parse_compound(product).get(elem, 0))
        matrix.append(row)
    mat = Matrix(matrix)
    null_space = mat.nullspace()
    if not null_space:
        raise ValueError("No solution found for the given equation.")
    coeffs = null_space[0]
    lcm_val = lcm([val.q for val in coeffs])
    final_coeffs = [int(val * lcm_val) for val in coeffs]
    return final_coeffs[:len(reactants)], final_coeffs[len(reactants):]

def equation_balancer_menu():
    while True:
        print("\n--- Chemical Equation Balancer ---")
        print("Example input: H2 + O2 -> H2O")
        print("Type '0' or 'exit' to return to Main Menu.")
        equation = input("Enter the unbalanced equation: ").strip()

        if equation.lower() in ("0", "exit"):
            break

        if not equation:
            print("[ERROR] Please enter an equation.")
            continue

        # Basic validation
        if "->" not in equation:
            print("[ERROR] Equation must contain '->' to separate reactants and products.")
            continue

        try:
            reactants_str, products_str = equation.split("->")
            # Capitalise each compound token before parsing
            reactants = [capitalize_formula(r.strip()) for r in reactants_str.split("+") if r.strip()]
            products  = [capitalize_formula(p.strip()) for p in products_str.split("+") if p.strip()]

            if not reactants or not products:
                print("[ERROR] You must provide both reactants and products.")
                continue

            reactant_coeffs, product_coeffs = balance_equation(reactants, products)

            # Build formatted equation with subscripts
            balanced = " + ".join(
                f"{reactant_coeffs[i]}{format_subscript(reactants[i])}" for i in range(len(reactants))
            )
            balanced += " -> "
            balanced += " + ".join(
                f"{product_coeffs[i]}{format_subscript(products[i])}" for i in range(len(products))
            )

            print(f"\n[OK] Balanced Equation: {balanced}\n")

            # Optional mole conversion step
            do_moles = input("Do a mole conversion for this equation? (y/n): ").strip().lower()
            if do_moles == 'y':
                mole_conversion_menu(reactants, products, reactant_coeffs, product_coeffs)

        except Exception as e:
            print(f"[ERROR] {e}")
            print("Make sure you input the equation correctly, e.g., H2 + O2 -> H2O")
            # Loop again for another try
            continue