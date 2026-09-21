/* gas_screen.c - the gas laws and equilibrium. */

#include "screens.h"
#include "../ui/ui.h"
#include "../core/solution.h"

#include <stdio.h>

static void screen_ideal(void)
{
    static const char *const items[] = {
        "Find pressure", "Find volume", "Find amount", "Find temperature",
    };
    static int cursor;
    gas_state_t state;
    gas_unknown_t unknown;
    int choice = ui_menu("pV = nRT", items, 4, &cursor);

    if (choice < 0)
        return;
    unknown = (gas_unknown_t)choice;

    state.pressure = state.volume = state.moles = state.temperature = 0.0;
    if (unknown != GAS_PRESSURE && !ask_positive("pV = nRT", "p (kPa):", &state.pressure))
        return;
    if (unknown != GAS_VOLUME && !ask_positive("pV = nRT", "V (dm3):", &state.volume))
        return;
    if (unknown != GAS_MOLES && !ask_positive("pV = nRT", "n (mol):", &state.moles))
        return;
    if (unknown != GAS_TEMPERATURE && !ask_positive("pV = nRT", "T (K):", &state.temperature))
        return;

    if (gas_ideal(&state, unknown) != CHEM_OK) {
        ui_message("pV = nRT", "Those numbers do not work");
        return;
    }

    ui_result_begin("pV = nRT");
    ui_result_value("p", state.pressure, "kPa");
    ui_result_value("V", state.volume, "dm3");
    ui_result_value("n", state.moles, "mol");
    ui_result_value("T", state.temperature, "K");
    ui_result_rule();
    ui_result_line("R = 8.31 J/K/mol");
    ui_result_show();
}

static void screen_combined(void)
{
    static const char *const items[] = {
        "Find the new pressure", "Find the new volume", "Find the new temperature",
    };
    static int cursor;
    gas_state_t before, after;
    gas_unknown_t unknown;
    int choice = ui_menu("p1V1/T1 = p2V2/T2", items, 3, &cursor);

    if (choice < 0)
        return;
    unknown = (choice == 0) ? GAS_PRESSURE
            : (choice == 1) ? GAS_VOLUME : GAS_TEMPERATURE;

    before.moles = after.moles = 0.0;
    before.pressure = before.volume = before.temperature = 0.0;
    after.pressure = after.volume = after.temperature = 0.0;

    if (!ask_positive("Combined gas law", "p1 (kPa):", &before.pressure))
        return;
    if (!ask_positive("Combined gas law", "V1 (dm3):", &before.volume))
        return;
    if (!ask_positive("Combined gas law", "T1 (K):", &before.temperature))
        return;
    if (unknown != GAS_PRESSURE && !ask_positive("Combined gas law", "p2 (kPa):", &after.pressure))
        return;
    if (unknown != GAS_VOLUME && !ask_positive("Combined gas law", "V2 (dm3):", &after.volume))
        return;
    if (unknown != GAS_TEMPERATURE && !ask_positive("Combined gas law", "T2 (K):", &after.temperature))
        return;

    if (gas_combined(&before, &after, unknown) != CHEM_OK) {
        ui_message("Combined gas law", "Those numbers do not work");
        return;
    }

    ui_result_begin("Combined gas law");
    ui_result_value("p1", before.pressure, "kPa");
    ui_result_value("V1", before.volume, "dm3");
    ui_result_value("T1", before.temperature, "K");
    ui_result_rule();
    ui_result_value("p2", after.pressure, "kPa");
    ui_result_value("V2", after.volume, "dm3");
    ui_result_value("T2", after.temperature, "K");
    ui_result_show();
}

static void screen_graham(void)
{
    char first[24] = "", second[24] = "";
    chem_formula_t formula;
    double mass_1, mass_2, ratio = 0.0;

    if (!ask_formula("Graham's law", "First gas:", first, (int)sizeof first, &formula))
        return;
    mass_1 = chem_formula_mass(&formula);
    if (!ask_formula("Graham's law", "Second gas:", second, (int)sizeof second, &formula))
        return;
    mass_2 = chem_formula_mass(&formula);

    if (gas_effusion_ratio(mass_1, mass_2, &ratio) != CHEM_OK) {
        ui_message("Graham's law", "Those numbers do not work");
        return;
    }

    ui_result_begin("Graham's law");
    ui_result_value(first, mass_1, "g/mol");
    ui_result_value(second, mass_2, "g/mol");
    ui_result_rule();
    ui_result_value("rate 1 / rate 2", ratio, "");
    ui_result_show();
}

static void screen_kc_kp(void)
{
    static const char *const items[] = {"Kc to Kp", "Kp to Kc"};
    static int cursor;
    double k = 0.0, temperature = 0.0, delta_n = 0.0, answer = 0.0;
    int choice = ui_menu("Kc and Kp", items, 2, &cursor);

    if (choice < 0)
        return;
    if (!ask_positive("Kc and Kp", (choice == 0) ? "Kc:" : "Kp:", &k))
        return;
    if (!ask_positive("Kc and Kp", "T (K):", &temperature))
        return;
    if (!ask_number("Kc and Kp", "change in moles of gas:", &delta_n))
        return;

    if (((choice == 0) ? eq_kc_to_kp(k, temperature, (int)delta_n, &answer)
                       : eq_kp_to_kc(k, temperature, (int)delta_n, &answer)) != CHEM_OK) {
        ui_message("Kc and Kp", "Those numbers do not work");
        return;
    }

    ui_result_begin("Kc and Kp");
    ui_result_value((choice == 0) ? "Kc" : "Kp", k, "");
    ui_result_value("T", temperature, "K");
    ui_result_value("dn", delta_n, "");
    ui_result_rule();
    ui_result_value((choice == 0) ? "Kp" : "Kc", answer, "");
    ui_result_show();
}

static void screen_ice(void)
{
    double a = 0.0, b = 0.0, c = 0.0, d = 0.0, k = 0.0, x = 0.0;

    ui_message("ICE table", "A + B <-> C + D");
    if (!ask_number("ICE table", "[A] at the start:", &a))
        return;
    if (!ask_number("ICE table", "[B] at the start:", &b))
        return;
    if (!ask_number("ICE table", "[C] at the start:", &c))
        return;
    if (!ask_number("ICE table", "[D] at the start:", &d))
        return;
    if (!ask_positive("ICE table", "Kc:", &k))
        return;

    if (eq_ice_extent(a, b, c, d, k, &x) != CHEM_OK) {
        ui_message("ICE table", "Those numbers do not work");
        return;
    }

    ui_result_begin("ICE table");
    ui_result_value("x", x, "");
    ui_result_rule();
    ui_result_value("[A]", a - x, "");
    ui_result_value("[B]", b - x, "");
    ui_result_value("[C]", c + x, "");
    ui_result_value("[D]", d + x, "");
    ui_result_rule();
    if ((a - x) > 0 && (b - x) > 0)
        ui_result_value("check Kc", (c + x) * (d + x) / ((a - x) * (b - x)), "");
    ui_result_show();
}

void screen_gases(void)
{
    static const char *const items[] = {
        "pV = nRT",
        "Combined gas law",
        "Graham's law",
        "Kc and Kp",
        "ICE table",
    };
    static int cursor;

    for (;;) {
        switch (ui_menu("Gases and equilibrium", items, 5, &cursor)) {
        case 0: screen_ideal(); break;
        case 1: screen_combined(); break;
        case 2: screen_graham(); break;
        case 3: screen_kc_kp(); break;
        case 4: screen_ice(); break;
        default: return;
        }
    }
}
