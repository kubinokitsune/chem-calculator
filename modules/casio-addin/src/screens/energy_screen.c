/* energy_screen.c - energetics, cells and rates. */

#include "screens.h"
#include "../ui/ui.h"
#include "../core/energy.h"

#include <stdio.h>
#include <string.h>

static void screen_calorimetry(void)
{
    double mass = 0.0, capacity = CHEM_C_WATER, delta_t = 0.0, moles = 0.0;
    double heat, molar = 0.0;

    if (!ask_positive("Calorimetry", "Mass of solution (g):", &mass))
        return;
    if (!ask_positive("Calorimetry", "c (J/g/K), water 4.18:", &capacity))
        return;
    if (!ask_number("Calorimetry", "Temperature change (K):", &delta_t))
        return;

    heat = energy_heat(mass, capacity, delta_t);

    ui_result_begin("Calorimetry");
    ui_result_value("q", heat, "J");
    ui_result_value("q", heat / 1000.0, "kJ");

    if (ui_number_input("Calorimetry", "Moles reacting (blank to skip):", &moles, 1)
        && moles > 0.0) {
        if (energy_molar_enthalpy(heat, moles, &molar) == CHEM_OK) {
            ui_result_rule();
            ui_result_value("n", moles, "mol");
            ui_result_value("dH", molar, "kJ/mol");
            ui_result_line((molar < 0) ? "exothermic" : "endothermic");
        }
    }
    ui_result_show();
}

/* Add up bond enthalpies from the booklet, one bond at a time. */
static int collect_bonds(const char *title, double *total)
{
    char line[UI_LINE_LEN];

    *total = 0.0;
    for (;;) {
        char bond[16] = "";
        double how_many = 0.0;
        int enthalpy;

        if (!ui_text_input(title, "Bond (blank = done), e.g. C-H:", bond,
                           (int)sizeof bond))
            return 0;
        if (bond[0] == 0)
            return 1;
        enthalpy = energy_bond_enthalpy(bond);
        if (enthalpy == 0) {
            ui_message(title, "That bond is not in the booklet");
            continue;
        }
        snprintf(line, sizeof line, "How many %s bonds?", bond);
        if (!ask_positive(title, line, &how_many))
            return 0;
        *total += how_many * enthalpy;
    }
}

static void screen_bonds(void)
{
    double broken = 0.0, formed = 0.0;

    ui_message("Bond enthalpies", "First the bonds broken");
    if (!collect_bonds("Bonds broken", &broken))
        return;
    ui_message("Bond enthalpies", "Now the bonds formed");
    if (!collect_bonds("Bonds formed", &formed))
        return;

    ui_result_begin("Bond enthalpies");
    ui_result_value("broken", broken, "kJ/mol");
    ui_result_value("formed", formed, "kJ/mol");
    ui_result_rule();
    ui_result_value("dH", energy_from_bonds(broken, formed), "kJ/mol");
    ui_result_line((broken < formed) ? "exothermic" : "endothermic");
    ui_result_show();
}

static void screen_gibbs(void)
{
    static const char *const items[] = {
        "dG from dH and dS",
        "The temperature where dG = 0",
        "dG from K",
        "K from dG",
    };
    static int cursor;
    double delta_h = 0.0, delta_s = 0.0, temperature = 298.0, k = 0.0, answer = 0.0;
    int choice = ui_menu("Gibbs energy", items, 4, &cursor);

    if (choice < 0)
        return;

    switch (choice) {
    case 0:
        if (!ask_number("Gibbs energy", "dH (kJ/mol):", &delta_h))
            return;
        if (!ask_number("Gibbs energy", "dS (J/K/mol):", &delta_s))
            return;
        if (!ask_positive("Gibbs energy", "T (K):", &temperature))
            return;
        answer = energy_gibbs(delta_h, temperature, delta_s);
        ui_result_begin("Gibbs energy");
        ui_result_value("dH", delta_h, "kJ/mol");
        ui_result_value("dS", delta_s, "J/K/mol");
        ui_result_value("T", temperature, "K");
        ui_result_rule();
        ui_result_value("dG", answer, "kJ/mol");
        ui_result_line((answer < 0) ? "spontaneous" : "not spontaneous");
        break;
    case 1:
        if (!ask_number("Gibbs energy", "dH (kJ/mol):", &delta_h))
            return;
        if (!ask_number("Gibbs energy", "dS (J/K/mol):", &delta_s))
            return;
        if (energy_crossover_temperature(delta_h, delta_s, &answer) != CHEM_OK) {
            ui_message("Gibbs energy", "dS cannot be zero here");
            return;
        }
        ui_result_begin("Gibbs energy");
        ui_result_value("dH", delta_h, "kJ/mol");
        ui_result_value("dS", delta_s, "J/K/mol");
        ui_result_rule();
        ui_result_value("T at dG = 0", answer, "K");
        break;
    case 2:
        if (!ask_positive("Gibbs energy", "K:", &k))
            return;
        if (!ask_positive("Gibbs energy", "T (K):", &temperature))
            return;
        if (energy_gibbs_from_k(k, temperature, &answer) != CHEM_OK) {
            ui_message("Gibbs energy", "Those numbers do not work");
            return;
        }
        ui_result_begin("Gibbs energy");
        ui_result_value("K", k, "");
        ui_result_value("T", temperature, "K");
        ui_result_rule();
        ui_result_value("dG", answer, "kJ/mol");
        break;
    default:
        if (!ask_number("Gibbs energy", "dG (kJ/mol):", &answer))
            return;
        if (!ask_positive("Gibbs energy", "T (K):", &temperature))
            return;
        if (energy_k_from_gibbs(answer, temperature, &k) != CHEM_OK) {
            ui_message("Gibbs energy", "That gives a K too big to show");
            return;
        }
        ui_result_begin("Gibbs energy");
        ui_result_value("dG", answer, "kJ/mol");
        ui_result_value("T", temperature, "K");
        ui_result_rule();
        ui_result_value("K", k, "");
        break;
    }
    ui_result_show();
}

static void screen_cells(void)
{
    static int cursor;
    int choice, i;
    const char *names[32];
    char line[UI_LINE_LEN];
    double cathode = 0.0, anode = 0.0, electrons = 2.0;

    for (i = 0; i < energy_half_cell_count && i < 32; i++)
        names[i] = energy_half_cells[i].half_cell;

    choice = ui_menu("Half-cell being reduced", names, energy_half_cell_count, &cursor);
    if (choice < 0)
        return;
    cathode = energy_half_cells[choice].potential;
    snprintf(line, sizeof line, "%s", energy_half_cells[choice].half_cell);

    choice = ui_menu("Half-cell being oxidised", names, energy_half_cell_count, &cursor);
    if (choice < 0)
        return;
    anode = energy_half_cells[choice].potential;

    if (!ask_positive("Cell potential", "Electrons transferred:", &electrons))
        return;

    ui_result_begin("Cell potential");
    ui_result_text("reduced:", line);
    ui_result_value("E(red)", cathode, "V");
    ui_result_text("oxidised:", energy_half_cells[choice].half_cell);
    ui_result_value("E(ox)", anode, "V");
    ui_result_rule();
    ui_result_value("E(cell)", cathode - anode, "V");
    ui_result_value("dG", energy_gibbs_from_cell((int)electrons, cathode - anode), "kJ/mol");
    ui_result_line((cathode - anode > 0) ? "spontaneous" : "not spontaneous");
    ui_result_show();
}

static void screen_faraday(void)
{
    char text[24] = "";
    chem_formula_t formula;
    double current = 0.0, seconds = 0.0, charge = 2.0, mass = 0.0;

    if (!ask_formula("Electrolysis", "Element deposited:", text, (int)sizeof text,
                     &formula))
        return;
    if (!ask_positive("Electrolysis", "Current (A):", &current))
        return;
    if (!ask_positive("Electrolysis", "Time (s):", &seconds))
        return;
    if (!ask_positive("Electrolysis", "Charge on the ion (1, 2, 3):", &charge))
        return;

    if (energy_electrolysis_mass(current, seconds, chem_formula_mass(&formula),
                                 (int)charge, &mass) != CHEM_OK) {
        ui_message("Electrolysis", "Those numbers do not work");
        return;
    }

    ui_result_begin("Electrolysis");
    ui_result_value("Q", current * seconds, "C");
    ui_result_value("M", chem_formula_mass(&formula), "g/mol");
    ui_result_rule();
    ui_result_value("mass", mass, "g");
    ui_result_value("moles", mass / chem_formula_mass(&formula), "mol");
    ui_result_line("F = 96500 C/mol");
    ui_result_show();
}

static void screen_rates(void)
{
    static const char *const items[] = {
        "Ea from two rate constants",
        "k from the Arrhenius equation",
        "Half-life from k",
        "k from the half-life",
    };
    static int cursor;
    double k1 = 0.0, t1 = 0.0, k2 = 0.0, t2 = 0.0, answer = 0.0;
    int choice = ui_menu("Rates", items, 4, &cursor);

    if (choice < 0)
        return;

    switch (choice) {
    case 0:
        if (!ask_positive("Rates", "k1:", &k1))
            return;
        if (!ask_positive("Rates", "T1 (K):", &t1))
            return;
        if (!ask_positive("Rates", "k2:", &k2))
            return;
        if (!ask_positive("Rates", "T2 (K):", &t2))
            return;
        if (energy_activation_from_two(k1, t1, k2, t2, &answer) != CHEM_OK) {
            ui_message("Rates", "Two different temperatures are needed");
            return;
        }
        ui_result_begin("Activation energy");
        ui_result_value("k1", k1, "");
        ui_result_value("T1", t1, "K");
        ui_result_value("k2", k2, "");
        ui_result_value("T2", t2, "K");
        ui_result_rule();
        ui_result_value("Ea", answer, "kJ/mol");
        break;
    case 1:
        if (!ask_positive("Rates", "A (same units as k):", &k1))
            return;
        if (!ask_number("Rates", "Ea (kJ/mol):", &t1))
            return;
        if (!ask_positive("Rates", "T (K):", &t2))
            return;
        if (energy_rate_constant(k1, t1, t2, &answer) != CHEM_OK) {
            ui_message("Rates", "Those numbers do not work");
            return;
        }
        ui_result_begin("Arrhenius");
        ui_result_value("A", k1, "");
        ui_result_value("Ea", t1, "kJ/mol");
        ui_result_value("T", t2, "K");
        ui_result_rule();
        ui_result_value("k", answer, "");
        break;
    case 2:
        if (!ask_positive("Rates", "k (s-1):", &k1))
            return;
        energy_half_life(k1, &answer);
        ui_result_begin("Half-life");
        ui_result_value("k", k1, "s-1");
        ui_result_rule();
        ui_result_value("half-life", answer, "s");
        break;
    default:
        if (!ask_positive("Rates", "Half-life (s):", &k1))
            return;
        energy_k_from_half_life(k1, &answer);
        ui_result_begin("Half-life");
        ui_result_value("half-life", k1, "s");
        ui_result_rule();
        ui_result_value("k", answer, "s-1");
        break;
    }
    ui_result_show();
}

void screen_energy(void)
{
    static const char *const items[] = {
        "Calorimetry q = mcdT",
        "Bond enthalpies",
        "Gibbs energy and K",
        "Cell potential",
        "Electrolysis (Faraday)",
        "Rates and Arrhenius",
    };
    static int cursor;

    for (;;) {
        switch (ui_menu("Energy, cells, rates", items, 6, &cursor)) {
        case 0: screen_calorimetry(); break;
        case 1: screen_bonds(); break;
        case 2: screen_gibbs(); break;
        case 3: screen_cells(); break;
        case 4: screen_faraday(); break;
        case 5: screen_rates(); break;
        default: return;
        }
    }
}
