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
            mass    = _get_float("Enter mass (g): ", "mass")
            if mass is None: continue
            density = _get_float("Enter density (g/mL): ", "density", positive=True)
            if density is None: continue
            vol = mass_to_volume(mass, density)
            print(f"Volume: {vol:.4f} mL")

        elif choice == '2':
            volume  = _get_float("Enter volume (mL): ", "volume")
            if volume is None: continue
            density = _get_float("Enter density (g/mL): ", "density", positive=True)
            if density is None: continue
            mass = volume_to_mass(volume, density)
            print(f"Mass: {mass:.4f} g")

        elif choice == '3':
            mass   = _get_float("Enter mass (g): ", "mass")
            if mass is None: continue
            volume = _get_float("Enter volume (mL): ", "volume", positive=True)
            if volume is None: continue
            density = density_from_mv(mass, volume)
            print(f"Density: {density:.4f} g/mL")

        elif choice == '0':
            break

        else:
            print("Invalid choice. Please try again.")
