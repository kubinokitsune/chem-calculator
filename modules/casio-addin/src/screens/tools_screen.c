/* tools_screen.c - structure, isotopes, uncertainties and the IHD. */

#include "screens.h"
#include "../ui/ui.h"
#include "../core/tools.h"

#include <stdio.h>
#include <string.h>

static void screen_configuration(void)
{
    char text[16] = "";
    tools_subshell_t shells[TOOLS_MAX_SUBSHELLS];
    char written[128], line[UI_LINE_LEN];
    double charge = 0.0;
    int z, count, core;

    ui_example("Fe, charge 0 -> ...3d6 4s2; charge 3 -> 3d5");
    if (!ui_text_input("Electron configuration", "Element:", text, (int)sizeof text))
        return;
    z = chem_find_element(text);
    if (z == 0) {
        ui_message("Electron configuration", "No such element");
        return;
    }
    if (!ui_number_input("Electron configuration", "Charge (0 for the atom):",
                         &charge, 1))
        return;

    count = tools_configuration(z, (int)charge, shells, TOOLS_MAX_SUBSHELLS);
    if (count <= 0) {
        ui_message("Electron configuration", "That ion does not work");
        return;
    }
    tools_configuration_text(shells, count, written, sizeof written);

    ui_result_begin("Electron configuration");
    if (charge == 0.0)
        snprintf(line, sizeof line, "%s  (Z = %d)", chem_element(z)->name, z);
    else
        snprintf(line, sizeof line, "%s%+d  (%d electrons)", chem_element(z)->symbol,
                 (int)charge, z - (int)charge);
    ui_result_line(line);
    ui_result_rule();

    /* Long configurations are split over two lines so nothing is lost. */
    if ((int)strlen(written) < UI_LINE_LEN - 1) {
        ui_result_line(written);
    } else {
        char *split = written + UI_LINE_LEN - 12;
        while (split > written && *split != ' ')
            split--;
        *split = 0;
        ui_result_line(written);
        ui_result_line(split + 1);
    }

    core = tools_noble_core(z - (int)charge + ((charge > 0) ? (int)charge : 0));
    if (core > 0 && charge == 0.0) {
        const chem_element_t *noble = chem_element(core);
        int i, shown = 0;

        line[0] = 0;
        snprintf(line, sizeof line, "[%s] ", noble->symbol);
        for (i = 0; i < count; i++) {
            char part[16];
            int electrons_before = 0, j;

            for (j = 0; j <= i; j++)
                electrons_before += shells[j].electrons;
            if (electrons_before <= core)
                continue;
            snprintf(part, sizeof part, "%s%d%c%d", shown ? " " : "",
                     shells[i].n, shells[i].letter, shells[i].electrons);
            strncat(line, part, sizeof line - strlen(line) - 1);
            shown = 1;
        }
        ui_result_rule();
        ui_result_line(line);
    }
    ui_result_show();
}

static void screen_oxidation(void)
{
    char text[32] = "";
    chem_formula_t formula;
    double numbers[CHEM_MAX_ATOMS], charge = 0.0;
    char line[UI_LINE_LEN];
    int peroxide = 0, i;

    ui_example("KMnO4 -> K +1, Mn +7, O -2");
    if (!ask_formula("Oxidation numbers", "Formula:", text, (int)sizeof text,
                     &formula))
        return;
    if (!ui_number_input("Oxidation numbers", "Charge (0 for a compound):",
                         &charge, 1))
        return;
    if (chem_atom_count(&formula, "O") > 0) {
        char answer[8] = "";
        if (!ui_text_input("Oxidation numbers", "A peroxide? y/blank:", answer,
                           (int)sizeof answer))
            return;
        peroxide = (answer[0] == 'y' || answer[0] == 'Y');
    }

    if (tools_oxidation_numbers(&formula, (int)charge, peroxide, numbers) != CHEM_OK) {
        ui_message("Oxidation numbers", "Too many unknowns here");
        return;
    }

    ui_result_begin("Oxidation numbers");
    ui_result_text("Formula:", text);
    ui_result_rule();
    for (i = 0; i < formula.n; i++) {
        char number[16];
        chem_format(numbers[i], 4, number, sizeof number);
        snprintf(line, sizeof line, "%-3s x%-3d %s%s", formula.atoms[i].symbol,
                 formula.atoms[i].count, (numbers[i] > 0) ? "+" : "", number);
        ui_result_line(line);
    }
    ui_result_show();
}

static void screen_ionic(void)
{
    char cation[16] = "", anion[16] = "", formula[32];
    double cation_charge = 0.0, anion_charge = 0.0;

    ui_example("Al charge 3, O charge 2 -> Al2O3");
    if (!ui_text_input("Ionic formula", "Cation, e.g. Ca or NH4:", cation,
                       (int)sizeof cation))
        return;
    if (!ask_positive("Ionic formula", "Its charge (1, 2, 3):", &cation_charge))
        return;
    if (!ui_text_input("Ionic formula", "Anion, e.g. Cl or OH:", anion,
                       (int)sizeof anion))
        return;
    if (!ask_positive("Ionic formula", "Its charge, without the sign:", &anion_charge))
        return;

    if (tools_ionic_formula(cation, (int)cation_charge, anion, -(int)anion_charge,
                            formula, (int)sizeof formula) != CHEM_OK) {
        ui_message("Ionic formula", "Those charges do not work");
        return;
    }

    ui_result_begin("Ionic formula");
    ui_result_value("cation charge", cation_charge, "");
    ui_result_value("anion charge", -anion_charge, "");
    ui_result_rule();
    ui_result_text("Formula:", formula);
    ui_result_show();
}

static void screen_isotopes(void)
{
    static const char *const items[] = {
        "Ar from the abundances", "Abundances from Ar",
    };
    static int cursor;
    double masses[6], abundances[6], ar = 0.0, first = 0.0, second = 0.0;
    double how_many = 0.0;
    char line[UI_LINE_LEN];
    int count, i;
    int choice = ui_menu("Isotopes", items, 2, &cursor);

    if (choice < 0)
        return;
    ui_example("34.969 at 75.77 %, 36.966 at 24.23 % -> 35.45");

    if (choice == 0) {
        if (!ui_number_input("Isotopes", "How many isotopes? (2-6)", &how_many, 0))
            return;
        count = (int)how_many;
        if (count < 2 || count > 6) {
            ui_message("Isotopes", "Between 2 and 6");
            return;
        }
        for (i = 0; i < count; i++) {
            snprintf(line, sizeof line, "Isotope %d mass:", i + 1);
            if (!ask_positive("Isotopes", line, &masses[i]))
                return;
            snprintf(line, sizeof line, "Isotope %d abundance (%%):", i + 1);
            if (!ask_positive("Isotopes", line, &abundances[i]))
                return;
        }
        if (tools_relative_atomic_mass(masses, abundances, count, &ar) != CHEM_OK) {
            ui_message("Isotopes", "Those numbers do not work");
            return;
        }
        ui_result_begin("Relative atomic mass");
        for (i = 0; i < count; i++) {
            char mass[16], percent[16];
            chem_format(masses[i], 4, mass, sizeof mass);
            chem_format(abundances[i], 4, percent, sizeof percent);
            snprintf(line, sizeof line, "%s at %s %%", mass, percent);
            ui_result_line(line);
        }
        ui_result_rule();
        ui_result_value("Ar", ar, "");
    } else {
        if (!ask_positive("Isotopes", "Lighter isotope mass:", &masses[0]))
            return;
        if (!ask_positive("Isotopes", "Heavier isotope mass:", &masses[1]))
            return;
        if (!ask_positive("Isotopes", "Ar of the element:", &ar))
            return;
        if (tools_abundances_from_ar(masses[0], masses[1], ar, &first, &second)
            != CHEM_OK) {
            ui_message("Isotopes", "Ar must lie between the two masses");
            return;
        }
        ui_result_begin("Abundances");
        ui_result_value("Ar", ar, "");
        ui_result_rule();
        ui_result_value("lighter", first, "%");
        ui_result_value("heavier", second, "%");
    }
    ui_result_show();
}

static void screen_uncertainty(void)
{
    static const char *const items[] = {
        "Absolute to percentage",
        "Percentage to absolute",
        "Adding measurements",
        "Multiplying measurements",
        "Raising to a power",
        "Percentage error",
    };
    static int cursor;
    double value = 0.0, second = 0.0, parts[2];
    int choice = ui_menu("Uncertainties", items, 6, &cursor);

    if (choice < 0)
        return;
    ui_example("25.00 give or take 0.05 -> 0.2 %");

    switch (choice) {
    case 0:
        if (!ask_number("Uncertainties", "Measurement:", &value))
            return;
        if (!ask_positive("Uncertainties", "Its uncertainty:", &second))
            return;
        ui_result_begin("Uncertainty");
        ui_result_value("measurement", value, "");
        ui_result_value("absolute", second, "");
        ui_result_rule();
        ui_result_value("percentage", tools_percent_uncertainty(value, second), "%");
        break;
    case 1:
        if (!ask_number("Uncertainties", "Measurement:", &value))
            return;
        if (!ask_positive("Uncertainties", "Its uncertainty (%):", &second))
            return;
        ui_result_begin("Uncertainty");
        ui_result_value("measurement", value, "");
        ui_result_value("percentage", second, "%");
        ui_result_rule();
        ui_result_value("absolute", tools_absolute_uncertainty(value, second), "");
        break;
    case 2:
        if (!ask_positive("Uncertainties", "First absolute uncertainty:", &parts[0]))
            return;
        if (!ask_positive("Uncertainties", "Second absolute uncertainty:", &parts[1]))
            return;
        ui_result_begin("Adding measurements");
        ui_result_line("absolute uncertainties add");
        ui_result_rule();
        ui_result_value("total", tools_combine_sum(parts, 2), "");
        break;
    case 3:
        if (!ask_positive("Uncertainties", "First percentage:", &parts[0]))
            return;
        if (!ask_positive("Uncertainties", "Second percentage:", &parts[1]))
            return;
        ui_result_begin("Multiplying measurements");
        ui_result_line("percentage uncertainties add");
        ui_result_rule();
        ui_result_value("total", tools_combine_product(parts, 2), "%");
        break;
    case 4:
        if (!ask_positive("Uncertainties", "Percentage uncertainty:", &value))
            return;
        if (!ask_number("Uncertainties", "Power:", &second))
            return;
        ui_result_begin("Raising to a power");
        ui_result_rule();
        ui_result_value("uncertainty", tools_combine_power(value, second), "%");
        break;
    default:
        if (!ask_number("Uncertainties", "Measured value:", &value))
            return;
        if (!ask_number("Uncertainties", "Accepted value:", &second))
            return;
        ui_result_begin("Percentage error");
        ui_result_value("measured", value, "");
        ui_result_value("accepted", second, "");
        ui_result_rule();
        ui_result_value("error", tools_percent_error(value, second), "%");
        break;
    }
    ui_result_show();
}

static void screen_ihd(void)
{
    char text[32] = "";
    chem_formula_t formula;
    double ihd;

    ui_example("C6H6 -> 4 (a ring and three double bonds)");
    if (!ask_formula("Index of hydrogen deficiency", "Molecular formula:", text,
                     (int)sizeof text, &formula))
        return;

    ihd = tools_ihd(&formula, 0);
    ui_result_begin("Hydrogen deficiency");
    ui_result_text("Formula:", text);
    ui_result_rule();
    ui_result_value("IHD", ihd, "");
    if (ihd < 0)
        ui_result_line("Too many hydrogens: check it");
    else if (ihd == 0)
        ui_result_line("saturated: no rings, no");
    else
        ui_result_line("rings + pi bonds together");
    ui_result_show();
}

void screen_tools(void)
{
    static const char *const items[] = {
        "Electron configuration",
        "Oxidation numbers",
        "Ionic formula",
        "Isotopes and Ar",
        "Uncertainties",
        "Index of hydrogen deficiency",
    };
    static const char *const hints[] = {
        "Fe -> 1s2 2s2 2p6 3s2 3p6 3d6 4s2",
        "KMnO4 -> manganese is +7",
        "Al 3+ with O 2- -> Al2O3",
        "chlorine's two isotopes -> Ar 35.45",
        "25.00 +/- 0.05 -> 0.2 %",
        "C6H6 -> 4 rings and pi bonds",
    };
    static int cursor;

    for (;;) {
        switch (ui_menu_hints("Structure and data", items, hints, 6, &cursor)) {
        case 0: screen_configuration(); break;
        case 1: screen_oxidation(); break;
        case 2: screen_ionic(); break;
        case 3: screen_isotopes(); break;
        case 4: screen_uncertainty(); break;
        case 5: screen_ihd(); break;
        default: return;
        }
    }
}
