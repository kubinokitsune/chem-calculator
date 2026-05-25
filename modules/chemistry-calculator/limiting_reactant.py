# limiting_reactant.py
from constants import capitalize_formula


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


def _get_float(prompt, label, positive=False):
    raw = input(prompt).strip()
    try:
        val = float(raw)
    except ValueError:
        print(f"  [ERROR] Invalid input: expected a number for {label}.")
        return None
    if positive and val <= 0:
        print(f"  [ERROR] {label} must be greater than zero.")
        return None
    return val


def limiting_reactant_menu(reactants, products, reactant_coeffs, product_coeffs):
    """Calculates the limiting reactant and theoretical yield."""
    print("\n--- Limiting Reactant Calculator ---")

    if not reactants or not products or not reactant_coeffs or not product_coeffs:
        num_reactants = _get_int("How many reactants? ", "number of reactants")
        if num_reactants is None:
            return
        reactants = []
        reactant_coeffs = []
        for i in range(num_reactants):
            r = capitalize_formula(input(f"Enter reactant #{i+1} formula: ").strip()) or f"R{i+1}"
            c = _get_float(f"Enter coefficient for {r}: ", f"coefficient for {r}", positive=True)
            if c is None:
                return
            reactants.append(r)
            reactant_coeffs.append(c)

        num_products = _get_int("How many products? ", "number of products")
        if num_products is None:
            return
        products = []
        product_coeffs = []
        for i in range(num_products):
            p = capitalize_formula(input(f"Enter product #{i+1} formula: ").strip()) or f"P{i+1}"
            c = _get_float(f"Enter coefficient for {p}: ", f"coefficient for {p}", positive=True)
            if c is None:
                return
            products.append(p)
            product_coeffs.append(c)

    print("\nReactants in balanced equation:")
    for i, r in enumerate(reactants):
        print(f"{i + 1}. {reactant_coeffs[i]} {r}")

    initial_moles = []
    for r in reactants:
        amt = _get_float(f"Enter the number of moles of {r}: ", f"moles of {r}", positive=True)
        if amt is None:
            return
        initial_moles.append(amt)

    mole_ratios = [initial_moles[i] / reactant_coeffs[i] for i in range(len(reactants))]
    limiting_index = mole_ratios.index(min(mole_ratios))
    limiting_reactant = reactants[limiting_index]

    print(f"\n[OK] Limiting Reactant: {limiting_reactant}")

    print("\nLeftover Reactants:")
    for i, r in enumerate(reactants):
        used = reactant_coeffs[i] * mole_ratios[limiting_index]
        leftover = max(initial_moles[i] - used, 0)
        print(f"{r}: {leftover:.2f} mol remaining")

    print("\nTheoretical Yield of Products:")
    for i, p in enumerate(products):
        yield_moles = product_coeffs[i] * mole_ratios[limiting_index]
        print(f"{p}: {yield_moles:.2f} mol")

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
