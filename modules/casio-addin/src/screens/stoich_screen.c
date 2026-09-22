/* stoich_screen.c - moles, percentage composition and formulas. */

#include "screens.h"
#include "../ui/ui.h"
#include "../core/stoich.h"

#include <stdio.h>
#include <string.h>

/* mass <-> moles <-> particles <-> volume at STP */
static void screen_moles(void)
{
    static const char *const items[] = {
        "Mass to moles",
        "Moles to mass",
        "Moles to particles",
        "Particles to moles",
        "Moles to volume at STP",
        "Volume at STP to moles",
    };
    static const char *const hints[] = {
        "CaCO3, 10 g -> 0.0999 mol",
        "H2O, 2 mol -> 36.04 g",
        "0.25 mol -> 1.505e23 particles",
        "3.01e23 particles -> 0.5 mol",
        "0.5 mol -> 11.35 dm3 at STP",
        "11.35 dm3 at STP -> 0.5 mol",
    };
    static int cursor;
    char text[32] = "";
    chem_formula_t formula;
    double mass, moles = 0.0, value = 0.0;
    int choice = ui_menu_hints("Moles", items, hints, 6, &cursor);

    if (choice < 0)
        return;
    ui_example("CaCO3 then 10 gives 0.0999 mol");

    if (choice <= 1) {
        if (!ask_formula("Moles", "Formula:", text, (int)sizeof text, &formula))
            return;
        mass = chem_formula_mass(&formula);
        if (choice == 0) {
            if (!ask_positive("Moles", "Mass (g):", &value))
                return;
            moles = value / mass;
        } else {
            if (!ask_positive("Moles", "Amount (mol):", &value))
                return;
            moles = value;
        }
    } else if (choice == 2 || choice == 4) {
        if (!ask_positive("Moles", "Amount (mol):", &value))
            return;
        moles = value;
        mass = 0.0;
    } else if (choice == 3) {
        if (!ask_positive("Moles", "Particles:", &value))
            return;
        moles = value / CHEM_AVOGADRO;
        mass = 0.0;
    } else {
        if (!ask_positive("Moles", "Volume at STP (dm3):", &value))
            return;
        moles = value / CHEM_MOLAR_VOLUME;
        mass = 0.0;
    }

    ui_result_begin("Moles");
    if (choice <= 1) {
        ui_result_text("Formula:", text);
        ui_result_value("M", mass, "g/mol");
        ui_result_rule();
    }
    ui_result_value("n", moles, "mol");
    if (choice == 1)
        ui_result_value("m", moles * mass, "g");
    if (choice <= 1)
        ui_result_value("particles", moles * CHEM_AVOGADRO, "");
    if (choice == 2 || choice == 4)
        ui_result_value("particles", moles * CHEM_AVOGADRO, "");
    ui_result_value("V at STP", moles * CHEM_MOLAR_VOLUME, "dm3");
    ui_result_show();
}

static void screen_percent(void)
{
    char text[32] = "";
    chem_formula_t formula;
    float percent[CHEM_MAX_ATOMS];
    char line[UI_LINE_LEN];
    int i;

    ui_example("H2O -> 11.2 % H and 88.8 % O");
    if (!ask_formula("Percent composition", "Formula:", text, (int)sizeof text,
                     &formula))
        return;

    stoich_percent_composition(&formula, percent);
    ui_result_begin("Percent composition");
    ui_result_text("Formula:", text);
    ui_result_value("M", chem_formula_mass(&formula), "g/mol");
    ui_result_rule();
    for (i = 0; i < formula.n; i++) {
        char number[16];
        chem_format(percent[i], 4, number, sizeof number);
        snprintf(line, sizeof line, "%-3s x%-3d %s %%",
                 formula.atoms[i].symbol, formula.atoms[i].count, number);
        ui_result_line(line);
    }
    ui_result_show();
}

/* Empirical formula from percentages or masses, and the molecular formula. */
static void screen_empirical(void)
{
    char symbols[CHEM_MAX_ATOMS][CHEM_SYMBOL_LEN];
    const char *pointers[CHEM_MAX_ATOMS];
    float amounts[CHEM_MAX_ATOMS];
    int counts[CHEM_MAX_ATOMS];
    char line[UI_LINE_LEN], formula_text[UI_LINE_LEN];
    double how_many = 0.0, value = 0.0, molar = 0.0;
    float empirical_mass = 0.0f;
    int n, i;

    ui_example("C 40, H 6.7, O 53.3 -> CH2O, Mr 180 -> C6H12O6");
    if (!ui_number_input("Empirical formula", "How many elements? (2-6)",
                         &how_many, 0))
        return;
    n = (int)how_many;
    if (n < 2 || n > 6) {
        ui_message("Empirical formula", "Between 2 and 6 elements");
        return;
    }

    for (i = 0; i < n; i++) {
        char prompt[UI_LINE_LEN];
        char entered[8] = "";
        int z;

        snprintf(prompt, sizeof prompt, "Element %d symbol:", i + 1);
        if (!ui_text_input("Empirical formula", prompt, entered, (int)sizeof entered))
            return;
        z = chem_find_element(entered);
        if (z == 0) {
            ui_message("Empirical formula", "No such element");
            return;
        }
        snprintf(symbols[i], sizeof symbols[i], "%s", chem_element(z)->symbol);
        pointers[i] = symbols[i];

        snprintf(prompt, sizeof prompt, "%s: mass or %%", symbols[i]);
        if (!ask_positive("Empirical formula", prompt, &value))
            return;
        amounts[i] = (float)value;
    }

    if (stoich_empirical(pointers, amounts, n, counts) != CHEM_OK) {
        ui_message("Empirical formula", "Those amounts do not work");
        return;
    }

    formula_text[0] = 0;
    empirical_mass = 0.0f;
    for (i = 0; i < n; i++) {
        char part[16];
        if (counts[i] == 1)
            snprintf(part, sizeof part, "%s", symbols[i]);
        else
            snprintf(part, sizeof part, "%s%d", symbols[i], counts[i]);
        strncat(formula_text, part, sizeof formula_text - strlen(formula_text) - 1);
        empirical_mass += chem_element_mass(symbols[i]) * (float)counts[i];
    }

    ui_result_begin("Empirical formula");
    ui_result_text("Empirical:", formula_text);
    ui_result_value("its M", empirical_mass, "g/mol");

    /* Offer the molecular formula when a molar mass is given. */
    if (ui_number_input("Molecular formula", "Mr (blank to skip):", &molar, 1)
        && molar > 0.0) {
        int multiplier = stoich_formula_multiplier(empirical_mass, (float)molar);
        char molecular[UI_LINE_LEN];

        molecular[0] = 0;
        for (i = 0; i < n; i++) {
            char part[16];
            int total = counts[i] * multiplier;
            if (total == 1)
                snprintf(part, sizeof part, "%s", symbols[i]);
            else
                snprintf(part, sizeof part, "%s%d", symbols[i], total);
            strncat(molecular, part, sizeof molecular - strlen(molecular) - 1);
        }
        ui_result_rule();
        snprintf(line, sizeof line, "x%d", multiplier);
        ui_result_text("Multiplier:", line);
        ui_result_text("Molecular:", molecular);
    }
    ui_result_show();
}

static void screen_yield(void)
{
    double actual = 0.0, theoretical = 0.0;

    ui_example("4.2 g made of 5.0 g possible -> 84 %");

    if (!ask_positive("Percentage yield", "Actual yield:", &actual))
        return;
    if (!ask_positive("Percentage yield", "Theoretical yield:", &theoretical))
        return;

    ui_result_begin("Percentage yield");
    ui_result_value("actual", actual, "");
    ui_result_value("theoretical", theoretical, "");
    ui_result_rule();
    ui_result_value("yield", stoich_percent_yield((float)actual, (float)theoretical), "%");
    ui_result_show();
}

static void screen_atom_economy(void)
{
    char wanted[32] = "", other[32] = "";
    chem_formula_t formula;
    double wanted_mass, total;

    ui_example("want CO2, other product H2O -> 71.0 %");

    if (!ask_formula("Atom economy", "Wanted product:", wanted,
                     (int)sizeof wanted, &formula))
        return;
    wanted_mass = chem_formula_mass(&formula);
    total = wanted_mass;

    for (;;) {
        double mass;
        other[0] = 0;
        if (!ui_text_input("Atom economy", "Other product (blank = done):",
                           other, (int)sizeof other))
            break;
        if (other[0] == 0)
            break;
        {
            float value = 0.0f;
            if (chem_molar_mass(other, &value) != CHEM_OK) {
                ui_message("Atom economy", "Check that formula");
                continue;
            }
            mass = value;
        }
        total += mass;
    }

    ui_result_begin("Atom economy");
    ui_result_text("Wanted:", wanted);
    ui_result_value("its M", wanted_mass, "g/mol");
    ui_result_value("all products", total, "g/mol");
    ui_result_rule();
    ui_result_value("atom economy",
                    stoich_atom_economy((float)wanted_mass, (float)total), "%");
    ui_result_show();
}

void screen_stoichiometry(void)
{
    static const char *const items[] = {
        "Moles, mass, particles, volume",
        "Percent composition",
        "Empirical and molecular formula",
        "Percentage yield",
        "Atom economy",
    };
    static const char *const hints[] = {
        "10 g of CaCO3 -> 0.0999 mol",
        "H2O -> 11.2 % H, 88.8 % O",
        "40 % C, 6.7 % H, 53.3 % O -> CH2O",
        "4.2 g of a possible 5.0 g -> 84 %",
        "mass wanted / mass of everything made",
    };
    static int cursor;

    for (;;) {
        switch (ui_menu_hints("Stoichiometry", items, hints, 5, &cursor)) {
        case 0: screen_moles(); break;
        case 1: screen_percent(); break;
        case 2: screen_empirical(); break;
        case 3: screen_yield(); break;
        case 4: screen_atom_economy(); break;
        default: return;
        }
    }
}
