
#mole_conversions.py

Avogrado_number = 6.022e23  # particles per mole
Molar_Volume_At_STP = 22.7  # liters per mole at STP (IUPAC: 0 °C, 100 kPa)


def mass_to_moles(mass, molar_mass):
    """Convert mass (g) to moles."""
    return mass / molar_mass

def moles_to_mass(moles, molar_mass):
    """Convert moles to mass (g)."""
    return moles * molar_mass

def moles_to_particles(moles):
    """Convert moles to number of atoms/molecules."""
    return moles * Avogrado_number

def particles_to_moles(particles):
    """Convert number of atoms/molecules to moles."""
    return particles / Avogrado_number

def moles_to_volume(moles):
    """Convert moles to volume (liters) at STP."""
    return moles * Molar_Volume_At_STP

def volume_to_moles(volume):
    """Convert volume (liters) at STP to moles."""
    return volume / Molar_Volume_At_STP


# ── Input helpers ──────────────────────────────────────────────────────────────

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


def mole_conversions_menu():
    """Display mole conversions options and handle user input."""
    while True:
        print("\nMole Conversions Menu:")
        print("1. Mass to Moles")
        print("2. Moles to Mass")
        print("3. Moles to Particles")
        print("4. Particles to Moles")
        print("5. Moles to Volume (at STP)")
        print("6. Volume (at STP) to Moles")
        print("0. Return to Main Menu")

        choice = input("Select an option (0-6): ").strip()

        if choice == '1':
            mass = _get_float("Enter mass (g): ", "mass")
            if mass is None: continue
            molar_mass = _get_float("Enter molar mass (g/mol): ", "molar mass", positive=True)
            if molar_mass is None: continue
            moles = mass_to_moles(mass, molar_mass)
            print(f"Moles: {moles:.4f} mol")

        elif choice == '2':
            moles = _get_float("Enter moles (mol): ", "moles")
            if moles is None: continue
            molar_mass = _get_float("Enter molar mass (g/mol): ", "molar mass", positive=True)
            if molar_mass is None: continue
            mass = moles_to_mass(moles, molar_mass)
            print(f"Mass: {mass:.4f} g")

        elif choice == '3':
            moles = _get_float("Enter moles (mol): ", "moles")
            if moles is None: continue
            particles = moles_to_particles(moles)
            print(f"Particles: {particles:.4e} particles")

        elif choice == '4':
            particles = _get_float("Enter number of particles: ", "particle count")
            if particles is None: continue
            if particles < 0:
                print("  [ERROR] Particle count cannot be negative.")
                continue
            moles = particles_to_moles(particles)
            print(f"Moles: {moles:.4f} mol")

        elif choice == '5':
            moles = _get_float("Enter moles (mol): ", "moles")
            if moles is None: continue
            volume = moles_to_volume(moles)
            print(f"Volume at STP: {volume:.4f} L")

        elif choice == '6':
            volume = _get_float("Enter volume at STP (L): ", "volume", positive=True)
            if volume is None: continue
            moles = volume_to_moles(volume)
            print(f"Moles: {moles:.4f} mol")

        elif choice == '0':
            break

        else:
            print("Invalid choice. Please try again.")


def mole_conversion_menu(reactants, products, reactant_coeffs, product_coeffs):
    compounds = reactants + products
    coeffs = reactant_coeffs + product_coeffs

    print("\nMole Step:")
    print("Known compound? ", ", ".join(compounds))
    known = input("Enter known compound: ").strip()
    if known not in compounds:
        print("Compound not found in equation.")
        return

    idx = compounds.index(known)
    known_coeff = coeffs[idx]
    known_moles = _get_float("Enter moles: ", "moles")
    if known_moles is None:
        return

    print("\nResult:")
    for i, compound in enumerate(compounds):
        compound_moles = (known_moles / known_coeff) * coeffs[i]
        print(f"{compound}: {compound_moles:.2f} mol")
    input("Press Enter to return to the main menu...")
