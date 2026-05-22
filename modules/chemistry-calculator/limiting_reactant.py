# limiting_reactant.py

# Only import if you actually need mole conversions later
# from mole_converter import mole_conversion_menu  

def limiting_reactant_menu(reactants, products, reactant_coeffs, product_coeffs):
    """
    Calculates the limiting reactant and theoretical yield based on given amounts.
    """
    print("\n--- Limiting Reactant Calculator ---")

    # If no data is passed, prompt the user for input
    if not reactants or not products or not reactant_coeffs or not product_coeffs:
        num_reactants = int(input("How many reactants? "))
        reactants = []
        reactant_coeffs = []
        for i in range(num_reactants):
            r = input(f"Enter reactant #{i+1} name: ")
            c = float(input(f"Enter coefficient for {r}: "))
            reactants.append(r)
            reactant_coeffs.append(c)

        num_products = int(input("How many products? "))
        products = []
        product_coeffs = []
        for i in range(num_products):
            p = input(f"Enter product #{i+1} name: ")
            c = float(input(f"Enter coefficient for {p}: "))
            products.append(p)
            product_coeffs.append(c)

    print("\nReactants in balanced equation:")
    for i, r in enumerate(reactants):
        print(f"{i + 1}. {reactant_coeffs[i]} {r}")

    try:
        # Get initial moles for each reactant
        initial_moles = []
        for i, r in enumerate(reactants):
            amount = float(input(f"Enter the number of moles of {r}: "))
            initial_moles.append(amount)

        # Determine limiting reactant
        mole_ratios = [initial_moles[i] / reactant_coeffs[i] for i in range(len(reactants))]
        limiting_index = mole_ratios.index(min(mole_ratios))
        limiting_reactant = reactants[limiting_index]

        print(f"\n[OK] Limiting Reactant: {limiting_reactant}")

        # Calculate leftover reactants
        print("\nLeftover Reactants:")
        for i, r in enumerate(reactants):
            used = reactant_coeffs[i] * mole_ratios[limiting_index]
            leftover = max(initial_moles[i] - used, 0)
            print(f"{r}: {leftover:.2f} mol remaining")

        # Theoretical yield for products
        print("\nTheoretical Yield of Products:")
        for i, p in enumerate(products):
            yield_moles = product_coeffs[i] * mole_ratios[limiting_index]
            print(f"{p}: {yield_moles:.2f} mol")

        input("Press Enter to return to the main menu...")

    except ValueError:
        print("[ERROR] Please enter numeric values for moles only.")
        limiting = input("Do you want to try again? (y/n): ").strip().lower()
        if limiting == 'y':
            limiting_reactant_menu(reactants, products, reactant_coeffs, product_coeffs)


def limiting_reactant_main_menu():
    """
    Wrapper menu for the limiting reactant module.
    """
    while True:
        print("\n--- Limiting Reactant Main Menu ---")
        print("1. Enter reaction data manually")
        print("2. Return to Main Menu")
        choice = input("Select an option: ")

        if choice == "1":
            limiting_reactant_menu([], [], [], [])
        elif choice == "2":
            break
        else:
            print("[ERROR] Invalid option. Please try again.")
