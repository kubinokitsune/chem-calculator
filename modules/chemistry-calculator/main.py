import traceback
import os
import sys


def _ensure_script_dir_on_path():
    """Ensure the directory containing this script is on sys.path and return it.

    Returns the resolved script directory path (string)."""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if script_dir and script_dir not in sys.path:
            sys.path.insert(0, script_dir)
    except Exception:
        script_dir = os.getcwd()
    return script_dir

def show_menu():
    print("\n=== Physical Chemistry Calculator ===")
    print("1. Mole Conversions")
    print("2. Empirical Formula Calculator")
    print("3. Balanced Chemical Equations")
    print("4. Limiting Reactant Calculator")
    print("5. Percent Composition Calculator")
    print("6. Volume-to-Mass Conversions")
    print("7. Oxidation Number Calculator")
    print("8. Element Economy Calculator")
    print("9. Ionic Bonding Calculator")
    print("10. Percentage Yield Calculator")
    print("11. Periodic Table")
    print("12. Gas Laws Calculator")
    print("13. Acid-Base Chemistry Calculator")
    print("0. Exit")


# --- Placeholder implementations ---

def open_percent_composition():
    print("\n[INFO] Opening Percent Composition Calculator...", flush=True)

    # Ensure the directory of this script is on sys.path
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if script_dir and script_dir not in sys.path:
            sys.path.insert(0, script_dir)
    except Exception:
        script_dir = os.getcwd()

    try:
        from percent_composition_calculator import percent_composition_menu
        return percent_composition_menu()
    except Exception as e:
        print(f"[ERROR] Failed to load Percent Composition Calculator (standard import): {e}")
        print(f"[DEBUG] CWD: {os.getcwd()}")
        print("[DEBUG] sys.path:")
        for p in sys.path:
            print(" -", p)
        try:
            files = os.listdir(script_dir)
            print(f"[DEBUG] Files in script_dir ({script_dir}):")
            for name in files:
                print(" -", name)
        except Exception as ls_e:
            print(f"[DEBUG] Could not list directory: {ls_e}")
        traceback.print_exc()
        # Fallback: dynamic load from file path
        try:
            from importlib.machinery import SourceFileLoader
            module_path = os.path.join(script_dir, 'percent_composition_calculator.py')
            print(f"[DEBUG] Attempting fallback load from {module_path}")
            mod = SourceFileLoader('percent_composition_calculator_fallback', module_path).load_module()
            return mod.percent_composition_menu()
        except Exception as e2:
            print(f"[ERROR] Fallback load for Percent Composition failed: {e2}")
            traceback.print_exc()
            return


def volume_to_mass_conversions():
    print("\n[INFO] Opening Volume-to-Mass Conversions...", flush=True)
    try:
        from volume_mass_conversions import volume_mass_menu
    except Exception as e:
        print(f"[ERROR] Failed to load Volume-to-Mass Conversions: {e}")
        traceback.print_exc()
        return
    volume_mass_menu()


def oxidation_number_calculator():
    print("\n[INFO] Opening Oxidation Number Calculator...", flush=True)
    try:
        from oxidation_number_calculator import oxidation_number_menu
    except Exception as e:
        print(f"[ERROR] Failed to load Oxidation Number Calculator: {e}")
        traceback.print_exc()
        return
    oxidation_number_menu()


def element_economy_calculator():
    print("\n[INFO] Opening Element Economy Calculator...", flush=True)
    try:
        from atom_economy_calculator import atom_economy_menu
    except Exception as e:
        print(f"[ERROR] Failed to load Element Economy Calculator: {e}")
        traceback.print_exc()
        return
    atom_economy_menu()


def ionic_bonding_calculator():
    print("\n[INFO] Opening Ionic Bonding Calculator...", flush=True)
    try:
        from ionic_bonding_calculator import ionic_bonding_menu
    except Exception as e:
        print(f"[ERROR] Failed to load Ionic Bonding Calculator: {e}")
        traceback.print_exc()
        return
    ionic_bonding_menu()


def percentage_yield_calculator():
    print("\n[INFO] Opening Percentage Yield Calculator...", flush=True)
    try:
        from percentage_yield_calculator import percentage_yield_menu
    except Exception as e:
        print(f"[ERROR] Failed to load Percentage Yield Calculator: {e}")
        traceback.print_exc()
        return
    percentage_yield_menu()


def open_acid_base():
    print("\n[INFO] Opening Acid-Base Chemistry Calculator...", flush=True)
    try:
        from acid_base import acid_base_menu
    except Exception as e:
        print(f"[ERROR] Failed to load Acid-Base Calculator: {e}")
        traceback.print_exc()
        return
    acid_base_menu()


def open_gas_laws():
    print("\n[INFO] Opening Gas Laws Calculator...", flush=True)
    try:
        from gas_laws import gas_laws_menu
    except Exception as e:
        print(f"[ERROR] Failed to load Gas Laws Calculator: {e}")
        traceback.print_exc()
        return
    gas_laws_menu()


def open_periodic_table():
    print("\n[INFO] Opening Periodic Table...", flush=True)
    try:
        # ensure directory in sys.path before importing
        script_dir = _ensure_script_dir_on_path()
        from Periodic_table import periodic_table_menu
    except Exception as e:
        print(f"[ERROR] Failed to load Periodic Table module (standard import): {e}")
        print(f"[DEBUG] CWD: {os.getcwd()}")
        print("[DEBUG] sys.path:")
        for p in sys.path:
            print(" -", p)
        try:
            files = os.listdir(script_dir)
            print(f"[DEBUG] Files in script_dir ({script_dir}):")
            for name in files:
                print(" -", name)
        except Exception as ls_e:
            print(f"[DEBUG] Could not list directory: {ls_e}")
        traceback.print_exc()

        # Fallback: dynamic load from file path
        try:
            from importlib.machinery import SourceFileLoader
            module_path = os.path.join(script_dir, 'Periodic_table.py')
            print(f"[DEBUG] Attempting fallback load from {module_path}")
            mod = SourceFileLoader('Periodic_table_fallback', module_path).load_module()
            return mod.periodic_table_menu()
        except Exception as e2:
            print(f"[ERROR] Fallback load for Periodic_table failed: {e2}")
            traceback.print_exc()
            return
    periodic_table_menu()


# --- Lazy-loaded wrappers to avoid import-time crashes ---

def open_mole_conversions():
    print("\n[INFO] Opening Mole Conversions...", flush=True)
    try:
        from mole_conversions import mole_conversions_menu
    except Exception as e:
        print(f"[ERROR] Failed to load Mole Conversions module: {e}")
        traceback.print_exc()
        return
    mole_conversions_menu()


def open_empirical_formula():
    print("\n[INFO] Opening Empirical Formula Calculator...", flush=True)
    try:
        from Empirical_Formula_Calculator import empirical_formula_menu
    except Exception as e:
        print(f"[ERROR] Failed to load Empirical Formula Calculator: {e}")
        traceback.print_exc()
        return
    empirical_formula_menu()


def open_equation_balancer():
    print("\n[INFO] Opening Equation Balancer...", flush=True)
    try:
        # sympy is required inside equation_balancer
        from equation_balancer import equation_balancer_menu
    except ModuleNotFoundError as e:
        # Most likely sympy isn't installed
        print("[ERROR] Equation Balancer requires 'sympy'. Install it with:")
        print("  pip install sympy")
        print(f"[DETAILS] {e}")
        return
    except Exception as e:
        print(f"[ERROR] Failed to load Equation Balancer: {e}")
        traceback.print_exc()
        return
    equation_balancer_menu()


def open_limiting_reactant():
    print("\n[INFO] Opening Limiting Reactant Calculator...", flush=True)
    try:
        from limiting_reactant import limiting_reactant_main_menu
    except Exception as e:
        print(f"[ERROR] Failed to load Limiting Reactant Calculator: {e}")
        traceback.print_exc()
        return
    limiting_reactant_main_menu()

    

def main():
    _ensure_script_dir_on_path()

    actions = {
        "1": open_mole_conversions,
        "2": open_empirical_formula,
        "3": open_equation_balancer,
        "4": open_limiting_reactant,
        "5": open_percent_composition,
        "6": volume_to_mass_conversions,
        "7": oxidation_number_calculator,
        "8": element_economy_calculator,
        "9": ionic_bonding_calculator,
        "10": percentage_yield_calculator,
    "11": open_periodic_table,
        "12": open_gas_laws,
        "13": open_acid_base,
        "0": None,
    }

    while True:
        show_menu()
        try:
            choice = input("Select an option (0-13): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting the program.")
            break

        func = actions.get(choice)
        if func is None:
            if choice == "0":
                print("Exiting the program.")
                break
            print("Invalid choice. Please try again.")
            continue

        try:
            func()
        except Exception as exc:
            print(f"[ERROR] An error occurred while executing the selected option: {exc}")
            traceback.print_exc()


if __name__ == "__main__":
    main()
