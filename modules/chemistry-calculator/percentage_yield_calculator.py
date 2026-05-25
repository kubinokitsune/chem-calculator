# percentage_yield_calculator.py
# Formula: % Yield = (Actual Yield / Theoretical Yield) x 100


def calc_percentage_yield(actual, theoretical):
    return (actual / theoretical) * 100


def calc_actual_yield(pct_yield, theoretical):
    return (pct_yield / 100) * theoretical


def calc_theoretical_yield(actual, pct_yield):
    return actual / (pct_yield / 100)


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


def percentage_yield_menu():
    while True:
        print("\n--- Percentage Yield Calculator ---")
        print("Formula: % Yield = (Actual Yield / Theoretical Yield) x 100")
        print()
        print("1. Find Percentage Yield   (given actual and theoretical)")
        print("2. Find Actual Yield       (given % yield and theoretical)")
        print("3. Find Theoretical Yield  (given actual and % yield)")
        print("0. Return to Main Menu")
        choice = input("Select an option (0-3): ").strip()

        if choice == '1':
            actual      = _get_float("Enter actual yield (g): ", "actual yield")
            if actual is None: continue
            if actual < 0:
                print("  [ERROR] Actual yield cannot be negative.")
                continue
            theoretical = _get_float("Enter theoretical yield (g): ", "theoretical yield", positive=True)
            if theoretical is None: continue
            pct = calc_percentage_yield(actual, theoretical)
            print(f"\nPercentage Yield: {pct:.2f}%")
            if pct > 100:
                print("[NOTE] Yield above 100% suggests impurities or measurement error.")

        elif choice == '2':
            pct         = _get_float("Enter percentage yield (%): ", "percentage yield", positive=True)
            if pct is None: continue
            theoretical = _get_float("Enter theoretical yield (g): ", "theoretical yield", positive=True)
            if theoretical is None: continue
            actual = calc_actual_yield(pct, theoretical)
            print(f"\nActual Yield: {actual:.4f} g")

        elif choice == '3':
            actual = _get_float("Enter actual yield (g): ", "actual yield")
            if actual is None: continue
            if actual < 0:
                print("  [ERROR] Actual yield cannot be negative.")
                continue
            pct = _get_float("Enter percentage yield (%): ", "percentage yield", positive=True)
            if pct is None: continue
            theoretical = calc_theoretical_yield(actual, pct)
            print(f"\nTheoretical Yield: {theoretical:.4f} g")

        elif choice == '0':
            break

        else:
            print("Invalid choice. Please try again.")
