
#mole_conversions.py

Avogrado_number = 6.022e23 #particles per mole
Molar_Volume_At_STP = 22.4 #liters per mole at STP

def mass_to_moles(mass, molar_mass):
    """Convert mass (g) to moles."""
    return mass / molar_mass

def moles_to_mass(moles, molar_mass):
    """Convert moles to mass (g)."""
    return moles * molar_mass

def moles_to_particles(moles):
    """convert moles to number of atoms/molecules"""
    return moles * Avogrado_number

def particles_to_moles(particles):
    """convert number of atoms/molecules to moles"""
    return particles / Avogrado_number

def moles_to_volume(moles):
    """convert moles to volume (liters) at STP"""
    return moles * Molar_Volume_At_STP 

def volume_to_moles(volume):
    """convert volume (liters) at STP to moles"""
    return volume / Molar_Volume_At_STP

def mole_conversions_menu():
    """Display mole conversions options and handle usser input."""
    while True:
        print("\nMole Conversions Menu:")
        print("1. Mass to Moles")
        print("2. Moles to Mass")
        print("3. Moles to Particles")
        print("4. Particles to Moles")
        print("5. Moles to Volume (at STP)")
        print("6. Volume (at STP) to Moles")
        print("0. Return to Main Menu")
        
        choice = input("Select an option (0-6): ")
        
        if choice == '1':
            mass = float(input("Enter mass (g): "))
            molar_mass = float(input("Enter molar mass (g/mol): "))
            moles = mass_to_moles(mass, molar_mass)
            print(f"Moles: {moles:.4f} mol")
        
        elif choice == '2':
            moles = float(input("Enter moles (mol): "))
            molar_mass = float(input("Enter molar mass (g/mol): "))
            mass = moles_to_mass(moles, molar_mass)
            print(f"Mass: {mass:.4f} g")
        
        elif choice == '3':
            moles = float(input("Enter moles (mol): "))
            particles = moles_to_particles(moles)
            print(f"Particles: {particles:.4e} particles")
        
        elif choice == '4':
            particles = float(input("Enter number of particles: "))
            moles = particles_to_moles(particles)
            print(f"Moles: {moles:.4f} mol")
        
        elif choice == '5':
            moles = float(input("Enter moles (mol): "))
            volume = moles_to_volume(moles)
            print(f"Volume at STP: {volume:.4f} L")
        
        elif choice == '6':
            volume = float(input("Enter volume at STP (L): "))
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
    known_moles = float(input("Enter moles: "))

    print("\nResult:")
    for i, compound in enumerate(compounds):
        compound_moles = (known_moles / known_coeff) * coeffs[i]
        print(f"{compound}: {compound_moles:.2f} mol")
    input("Press Enter to return to the main menu...")