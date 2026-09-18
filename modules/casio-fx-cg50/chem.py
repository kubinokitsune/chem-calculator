# chem.py - ChemCalc for the Casio fx-CG50
# Run this file from the Python app; the others are loaded when you pick a topic.
#
# Files: chemcore chemstoi chemgas chemaqua chemener chemstruct chemtools
#        chembal chemptab

from chemcore import line, ask_text

TOPICS = [
    ("1", "Stoichiometry", "chemstoi"),
    ("2", "Gases & equilibrium", "chemgas"),
    ("3", "Acids & bases", "chemaqua"),
    ("4", "Energy, cells, rates", "chemener"),
    ("5", "Structure & bonding", "chemstruct"),
    ("6", "Isotopes, errors, IHD", "chemtools"),
    ("7", "Equation balancer", "chembal"),
    ("8", "Periodic table", "chemptab"),
]


def run_topic(module_name):
    module = __import__(module_name)
    while True:
        print("")
        line("=")
        for key, label, _fn in module.MENU:
            print(" " + key + " " + label)
        print(" 0 back")
        choice = ask_text("Pick: ").lower()
        if choice in ("0", ""):
            return
        picked = None
        for key, label, fn in module.MENU:
            if key == choice:
                picked = fn
        if picked is None:
            print("No such option")
            continue
        print("")
        try:
            picked()
        except ValueError as e:
            print("Error: " + str(e))
        except ZeroDivisionError:
            print("Error: divide by zero")
        except MemoryError:
            print("Out of memory - restart the app")
        print("")
        ask_text("[EXE] ")


def main():
    while True:
        print("")
        line("=")
        print("  CHEMCALC  fx-CG50")
        line("=")
        for key, label, _mod in TOPICS:
            print(" " + key + " " + label)
        print(" 0 quit")
        choice = ask_text("Topic: ").lower()
        if choice in ("0", "q"):
            print("Bye")
            return
        found = None
        for key, label, module_name in TOPICS:
            if key == choice:
                found = module_name
        if found is None:
            print("No such topic")
            continue
        try:
            run_topic(found)
        except ImportError:
            print("Missing file: " + found + ".py")
            ask_text("[EXE] ")


main()
