# volume_mass_conversions.py


def mass_to_volume(mass, density):
    """V = m / d"""
    return mass / density


def volume_to_mass(volume, density):
    """m = V x d"""
    return volume * density


def density_from_mv(mass, volume):
    """d = m / V"""
    return mass / volume


def volume_mass_menu():
    while True:
        print("\n--- Volume-to-Mass Conversions ---")
        print("Uses density to convert between mass (g) and volume (mL).")
        print()
        print("1. Mass to Volume    (V = m / d)")
        print("2. Volume to Mass    (m = V x d)")
        print("3. Calculate Density (d = m / V)")
        print("0. Return to Main Menu")
        choice = input("Select an option (0-3): ").strip()

        if choice == '1':
            try:
                mass = float(input("Enter mass (g): "))
                density = float(input("Enter density (g/mL): "))
                if density <= 0:
                    print("[ERROR] Density must be greater than zero.")
                    continue
                vol = mass_to_volume(mass, density)
                print(f"Volume: {vol:.4f} mL")
            except ValueError:
                print("[ERROR] Please enter numeric values.")

        elif choice == '2':
            try:
                volume = float(input("Enter volume (mL): "))
                density = float(input("Enter density (g/mL): "))
                if density <= 0:
                    print("[ERROR] Density must be greater than zero.")
                    continue
                mass = volume_to_mass(volume, density)
                print(f"Mass: {mass:.4f} g")
            except ValueError:
                print("[ERROR] Please enter numeric values.")

        elif choice == '3':
            try:
                mass = float(input("Enter mass (g): "))
                volume = float(input("Enter volume (mL): "))
                if volume <= 0:
                    print("[ERROR] Volume must be greater than zero.")
                    continue
                density = density_from_mv(mass, volume)
                print(f"Density: {density:.4f} g/mL")
            except ValueError:
                print("[ERROR] Please enter numeric values.")

        elif choice == '0':
            break

        else:
            print("Invalid choice. Please try again.")
