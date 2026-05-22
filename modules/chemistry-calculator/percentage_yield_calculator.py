# percentage_yield_calculator.py
# Formula: % Yield = (Actual Yield / Theoretical Yield) x 100


def calc_percentage_yield(actual, theoretical):
    return (actual / theoretical) * 100


def calc_actual_yield(pct_yield, theoretical):
    return (pct_yield / 100) * theoretical


def calc_theoretical_yield(actual, pct_yield):
    return actual / (pct_yield / 100)


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
            try:
                actual = float(input("Enter actual yield (g): "))
                theoretical = float(input("Enter theoretical yield (g): "))
                if theoretical <= 0:
                    print("[ERROR] Theoretical yield must be greater than zero.")
                    continue
                pct = calc_percentage_yield(actual, theoretical)
                print(f"\nPercentage Yield: {pct:.2f}%")
                if pct > 100:
                    print("[NOTE] Yield above 100% suggests impurities or measurement error.")
            except ValueError:
                print("[ERROR] Please enter numeric values.")

        elif choice == '2':
            try:
                pct = float(input("Enter percentage yield (%): "))
                theoretical = float(input("Enter theoretical yield (g): "))
                if pct <= 0 or theoretical <= 0:
                    print("[ERROR] Values must be greater than zero.")
                    continue
                actual = calc_actual_yield(pct, theoretical)
                print(f"\nActual Yield: {actual:.4f} g")
            except ValueError:
                print("[ERROR] Please enter numeric values.")

        elif choice == '3':
            try:
                actual = float(input("Enter actual yield (g): "))
                pct = float(input("Enter percentage yield (%): "))
                if pct <= 0:
                    print("[ERROR] Percentage yield must be greater than zero.")
                    continue
                theoretical = calc_theoretical_yield(actual, pct)
                print(f"\nTheoretical Yield: {theoretical:.4f} g")
            except ValueError:
                print("[ERROR] Please enter numeric values.")

        elif choice == '0':
            break

        else:
            print("Invalid choice. Please try again.")
