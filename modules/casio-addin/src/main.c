/* main.c - ChemCalc for the Casio fx-CG50.
 *
 * An IB chemistry add-in: it appears in the calculator's MENU next to
 * Statistics and Financial, and is driven the same way - arrows to move,
 * EXE to choose, EXIT to go back, F1-F6 along the bottom.
 */

#include "screens/screens.h"
#include "ui/ui.h"

#include <gint/display.h>
#include <gint/gint.h>
#include <gint/keyboard.h>

int main(void)
{
    static const char *const topics[] = {
        "Stoichiometry",
        "Gases and equilibrium",
        "Acids and bases",
        "Energy, cells, rates",
        "Equation balancer",
        "Periodic table",
        "Structure and data",
    };
    static const char *const about[] = {
        "moles, formulas, yield, atom economy",
        "pV = nRT, gas laws, Kc and Kp, ICE",
        "pH, strong and weak, buffers, Ka and Kb",
        "calorimetry, dG, cells, rates",
        "C3H8 + O2 -> CO2 + H2O",
        "118 elements, groups, bond types",
        "configurations, oxidation numbers, errors",
    };
    static int cursor;

    /* Without this, leaving the add-in stops it from starting again until
     * some other application has been opened: the OS tries to *resume* the
     * add-in, which immediately exits once more. This makes gint jump back to
     * the entry point instead, so ChemCalc simply starts afresh. */
    gint_setrestart(1);

    for (;;) {
        switch (ui_menu_hints("ChemCalc  -  IB chemistry", topics, about, 7,
                              &cursor)) {
        case 0: screen_stoichiometry(); break;
        case 1: screen_gases(); break;
        case 2: screen_acids(); break;
        case 3: screen_energy(); break;
        case 4: screen_balance(); break;
        case 5: screen_periodic_table(); break;
        case 6: screen_tools(); break;
        default:
            return 1;        /* EXIT at the top level leaves the add-in */
        }
    }
}
