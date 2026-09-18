# chemptab.py - the periodic table for ChemCalc on the Casio fx-CG50
# MicroPython: no f-strings, ASCII only, keep it small.
#
# One packed string holds all 118 elements as
#   symbol,name,relative atomic mass,electronegativity
# separated by ";". Nothing is unpacked until a lookup asks for it, so the
# table costs little memory. "-" means the value is not tabulated.

from chemcore import line, ask_text, ask_int, fmt

_DATA = (
    "H,Hydrogen,1.01,2.20;He,Helium,4.00,-;Li,Lithium,6.94,0.98;"
    "Be,Beryllium,9.01,1.57;B,Boron,10.81,2.04;C,Carbon,12.01,2.55;"
    "N,Nitrogen,14.01,3.04;O,Oxygen,16.00,3.44;F,Fluorine,19.00,3.98;"
    "Ne,Neon,20.18,-;Na,Sodium,22.99,0.93;Mg,Magnesium,24.31,1.31;"
    "Al,Aluminium,26.98,1.61;Si,Silicon,28.09,1.90;"
    "P,Phosphorus,30.97,2.19;S,Sulfur,32.07,2.58;"
    "Cl,Chlorine,35.45,3.16;Ar,Argon,39.95,-;K,Potassium,39.10,0.82;"
    "Ca,Calcium,40.08,1.00;Sc,Scandium,44.96,1.36;"
    "Ti,Titanium,47.87,1.54;V,Vanadium,50.94,1.63;"
    "Cr,Chromium,52.00,1.66;Mn,Manganese,54.94,1.55;Fe,Iron,55.85,1.83;"
    "Co,Cobalt,58.93,1.88;Ni,Nickel,58.69,1.91;Cu,Copper,63.55,1.90;"
    "Zn,Zinc,65.38,1.65;Ga,Gallium,69.72,1.81;Ge,Germanium,72.63,2.01;"
    "As,Arsenic,74.92,2.18;Se,Selenium,78.97,2.55;"
    "Br,Bromine,79.90,2.96;Kr,Krypton,83.80,3.00;"
    "Rb,Rubidium,85.47,0.82;Sr,Strontium,87.62,0.95;"
    "Y,Yttrium,88.91,1.22;Zr,Zirconium,91.22,1.33;"
    "Nb,Niobium,92.91,1.60;Mo,Molybdenum,95.95,2.16;"
    "Tc,Technetium,98.00,1.90;Ru,Ruthenium,101.07,2.20;"
    "Rh,Rhodium,102.91,2.28;Pd,Palladium,106.42,2.20;"
    "Ag,Silver,107.87,1.93;Cd,Cadmium,112.41,1.69;"
    "In,Indium,114.82,1.78;Sn,Tin,118.71,1.96;Sb,Antimony,121.76,2.05;"
    "Te,Tellurium,127.60,2.10;I,Iodine,126.90,2.66;"
    "Xe,Xenon,131.29,2.60;Cs,Caesium,132.91,0.79;Ba,Barium,137.33,0.89;"
    "La,Lanthanum,138.91,1.10;Ce,Cerium,140.12,1.12;"
    "Pr,Praseodymium,140.91,-;Nd,Neodymium,144.24,-;"
    "Pm,Promethium,145.00,-;Sm,Samarium,150.36,-;Eu,Europium,151.96,-;"
    "Gd,Gadolinium,157.25,-;Tb,Terbium,158.93,-;Dy,Dysprosium,162.50,-;"
    "Ho,Holmium,164.93,-;Er,Erbium,167.26,-;Tm,Thulium,168.93,-;"
    "Yb,Ytterbium,173.05,-;Lu,Lutetium,174.97,-;Hf,Hafnium,178.49,1.30;"
    "Ta,Tantalum,180.95,1.50;W,Tungsten,183.84,2.36;"
    "Re,Rhenium,186.21,1.90;Os,Osmium,190.23,2.20;"
    "Ir,Iridium,192.22,2.20;Pt,Platinum,195.08,2.28;"
    "Au,Gold,196.97,2.54;Hg,Mercury,200.59,2.00;"
    "Tl,Thallium,204.38,1.62;Pb,Lead,207.20,2.33;"
    "Bi,Bismuth,208.98,2.02;Po,Polonium,209.00,2.00;"
    "At,Astatine,210.00,2.20;Rn,Radon,222.00,-;Fr,Francium,223.00,0.70;"
    "Ra,Radium,226.00,0.90;Ac,Actinium,227.00,1.10;"
    "Th,Thorium,232.04,1.30;Pa,Protactinium,231.04,1.50;"
    "U,Uranium,238.03,1.38;Np,Neptunium,237.00,-;Pu,Plutonium,244.00,-;"
    "Am,Americium,243.00,-;Cm,Curium,247.00,-;Bk,Berkelium,247.00,-;"
    "Cf,Californium,251.00,-;Es,Einsteinium,252.00,-;"
    "Fm,Fermium,257.00,-;Md,Mendelevium,258.00,-;No,Nobelium,259.00,-;"
    "Lr,Lawrencium,262.00,-;Rf,Rutherfordium,267.00,-;"
    "Db,Dubnium,270.00,-;Sg,Seaborgium,271.00,-;Bh,Bohrium,270.00,-;"
    "Hs,Hassium,277.00,-;Mt,Meitnerium,276.00,-;"
    "Ds,Darmstadtium,281.00,-;Rg,Roentgenium,282.00,-;"
    "Cn,Copernicium,285.00,-;Nh,Nihonium,286.00,-;"
    "Fl,Flerovium,289.00,-;Mc,Moscovium,288.00,-;"
    "Lv,Livermorium,293.00,-;Ts,Tennessine,294.00,-;"
    "Og,Oganesson,294.00,-"
)

# Room-temperature states; everything not listed here is a solid.
_GASES = ("H", "He", "N", "O", "F", "Ne", "Cl", "Ar", "Kr", "Xe", "Rn")
_LIQUIDS = ("Br", "Hg")
_METALLOIDS = ("B", "Si", "Ge", "As", "Sb", "Te", "Po")
_NON_METALS = ("H", "C", "N", "O", "P", "S", "Se")
_PERIOD_STARTS = (1, 3, 11, 19, 37, 55, 87)


def count():
    return 118


def record(z):
    """(symbol, name, mass, electronegativity or None) for atomic number z."""
    if z < 1 or z > 118:
        raise ValueError("Atomic number must be 1-118")
    parts = _DATA.split(";")[z - 1].split(",")
    en = None if parts[3] == "-" else float(parts[3])
    return parts[0], parts[1], float(parts[2]), en


def find(text):
    """Look an element up by atomic number, symbol or name. Returns z."""
    key = text.strip()
    if key == "":
        raise ValueError("Type a symbol, a name or a number")
    if key[0].isdigit():
        return int(key)
    low = key.lower()
    items = _DATA.split(";")
    for i in range(len(items)):
        parts = items[i].split(",")
        if parts[0].lower() == low or parts[1].lower() == low:
            return i + 1
    raise ValueError("No element called " + key)


def mass(symbol):
    """Relative atomic mass, or None if the symbol is not an element."""
    low = symbol.lower()
    for item in _DATA.split(";"):
        parts = item.split(",")
        if parts[0].lower() == low:
            return float(parts[2])
    return None


def is_f_block(z):
    return (57 <= z <= 71) or (89 <= z <= 103)


def group_period(z):
    """(group, period). Group 3 covers the lanthanoid and actinoid rows."""
    period = 1
    for i in range(7):
        if z >= _PERIOD_STARTS[i]:
            period = i + 1
    offset = z - _PERIOD_STARTS[period - 1]
    if period == 1:
        return (1 if z == 1 else 18), 1
    if period == 2 or period == 3:
        return (offset + 1 if offset < 2 else offset + 11), period
    if period == 4 or period == 5:
        return offset + 1, period
    if offset < 2:
        return offset + 1, period
    if offset <= 16:
        return 3, period
    return offset - 13, period


def block(z):
    if is_f_block(z):
        return "f"
    group, _period = group_period(z)
    if z == 2 or group <= 2:
        return "s"
    if group <= 12:
        return "d"
    return "p"


def category(z):
    symbol, _name, _mass, _en = record(z)
    if 57 <= z <= 71:
        return "Lanthanoid"
    if 89 <= z <= 103:
        return "Actinoid"
    group, _period = group_period(z)
    if group == 18:
        return "Noble gas"
    if group == 17:
        return "Halogen"
    if group == 1:
        return "Non-metal" if z == 1 else "Alkali metal"
    if group == 2:
        return "Alkaline earth metal"
    if group <= 12:
        return "Transition metal"
    if symbol in _METALLOIDS:
        return "Metalloid"
    if symbol in _NON_METALS:
        return "Non-metal"
    return "Metal"


def state(z):
    symbol, _name, _mass, _en = record(z)
    if symbol in _GASES:
        return "gas"
    if symbol in _LIQUIDS:
        return "liquid"
    return "solid"


def typical_ion(z):
    """The charge the element usually forms, as text."""
    if is_f_block(z):
        return "+3"
    group, _period = group_period(z)
    if group == 1:
        return "+1"
    if group == 2:
        return "+2"
    if group == 13:
        return "+3"
    if group == 15:
        return "-3"
    if group == 16:
        return "-2"
    if group == 17:
        return "-1"
    if group == 18:
        return "none"
    return "varies"


def bond_type(difference):
    if difference >= 1.8:
        return "ionic"
    if difference >= 0.4:
        return "polar covalent"
    return "non-polar covalent"


# ---- screens ---------------------------------------------------------------

def card(z):
    symbol, name, ar, en = record(z)
    group, period = group_period(z)
    line("=")
    print(" " + str(z) + "  " + symbol + "  " + name)
    line("=")
    print("Ar = " + fmt(ar))
    group_text = "Group " + str(group)
    if is_f_block(z):
        group_text = "f block"
    print(group_text + "  Period " + str(period) + "  " + block(z) + " block")
    print(category(z) + ", " + state(z))
    if en is None:
        print("Electronegativity: n/a")
    else:
        print("Electronegativity " + fmt(en, 3))
    print("Usual ion: " + typical_ion(z))


def menu_lookup():
    print("Symbol, name or number")
    z = find(ask_text("Element: "))
    print("")
    card(z)
    if ask_text("Config? y/[EXE] ").lower().startswith("y"):
        struct = __import__("chemstruct")
        config = struct.configuration(z)
        print(struct.config_text(config))
        print(struct.shorthand(config, z))


def _list(label, members):
    line("=")
    print(label)
    line("=")
    if not members:
        print("Nothing there")
        return
    for z in members:
        symbol, name, ar, _en = record(z)
        text = str(z) + " " + symbol
        while len(text) < 7:
            text = text + " "
        print(text + name[:11] + " " + fmt(ar))


def menu_group():
    group = ask_int("Group (1-18): ", 1, 18)
    members = []
    for z in range(1, 119):
        g, _p = group_period(z)
        if g == group and not is_f_block(z):
            members.append(z)
    print("")
    _list("Group " + str(group), members)


def menu_period():
    period = ask_int("Period (1-7): ", 1, 7)
    members = []
    for z in range(1, 119):
        _g, p = group_period(z)
        if p == period:
            members.append(z)
    print("")
    _list("Period " + str(period), members)


def menu_bond():
    print("Bond type from the")
    print("electronegativity gap")
    first = record(find(ask_text("Element 1: ")))
    second = record(find(ask_text("Element 2: ")))
    if first[3] is None or second[3] is None:
        raise ValueError("No electronegativity for that element")
    gap = abs(first[3] - second[3])
    print("")
    print(first[0] + " " + fmt(first[3], 3) + "   " + second[0] + " " + fmt(second[3], 3))
    print("Difference " + fmt(gap, 3))
    print("Bond: " + bond_type(gap))
    if gap >= 0.4:
        puller = first if first[3] > second[3] else second
        print("Electrons pulled to " + puller[0])


MENU = [
    ("1", "Element lookup", menu_lookup),
    ("2", "List a group", menu_group),
    ("3", "List a period", menu_period),
    ("4", "Bond type (EN gap)", menu_bond),
]
