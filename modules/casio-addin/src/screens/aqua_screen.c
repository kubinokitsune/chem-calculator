/* aqua_screen.c - acids, bases and buffers. */

#include "screens.h"
#include "../ui/ui.h"
#include "../core/solution.h"

#include <stdio.h>

static void show_all_four(double ph)
{
    ui_result_value("pH", ph, "");
    ui_result_value("pOH", aqua_poh_from_ph(ph), "");
    ui_result_value("[H+]", aqua_h_from_ph(ph), "mol/dm3");
    ui_result_value("[OH-]", aqua_oh_from_poh(aqua_poh_from_ph(ph)), "mol/dm3");
}

static void screen_converter(void)
{
    static const char *const items[] = {
        "From pH", "From pOH", "From [H+]", "From [OH-]",
    };
    static int cursor;
    double value = 0.0, ph = 0.0;
    int choice = ui_menu("pH converter", items, 4, &cursor);

    if (choice < 0)
        return;
    ui_example("pH 3 -> pOH 11, [H+] 1e-3, [OH-] 1e-11");
    switch (choice) {
    case 0:
        if (!ask_number("pH converter", "pH:", &value))
            return;
        ph = value;
        break;
    case 1:
        if (!ask_number("pH converter", "pOH:", &value))
            return;
        ph = 14.0 - value;
        break;
    case 2:
        if (!ask_positive("pH converter", "[H+] (mol/dm3):", &value))
            return;
        ph = aqua_ph_from_h(value);
        break;
    default:
        if (!ask_positive("pH converter", "[OH-] (mol/dm3):", &value))
            return;
        ph = 14.0 - aqua_ph_from_h(value);
        break;
    }

    ui_result_begin("pH converter");
    show_all_four(ph);
    ui_result_rule();
    ui_result_line((ph < 7.0) ? "acidic" : (ph > 7.0) ? "basic" : "neutral");
    ui_result_show();
}

static void screen_strong(void)
{
    static const char *const items[] = {"Strong acid", "Strong base"};
    static int cursor;
    double concentration = 0.0, number = 1.0, ph = 0.0;
    int choice = ui_menu("Strong acid or base", items, 2, &cursor);

    if (choice < 0)
        return;
    ui_example("0.1 mol/dm3 HCl, 1 H+ per formula -> pH 1");
    if (!ask_positive("Strong acid or base", "Concentration (mol/dm3):", &concentration))
        return;
    if (!ask_positive("Strong acid or base",
                      (choice == 0) ? "H+ per formula (1, 2...):"
                                    : "OH- per formula (1, 2...):", &number))
        return;

    if (((choice == 0) ? aqua_strong_acid_ph(concentration, (int)number, &ph)
                       : aqua_strong_base_ph(concentration, (int)number, &ph)) != CHEM_OK) {
        ui_message("Strong acid or base", "Those numbers do not work");
        return;
    }

    ui_result_begin((choice == 0) ? "Strong acid" : "Strong base");
    ui_result_value("c", concentration, "mol/dm3");
    ui_result_rule();
    show_all_four(ph);
    ui_result_show();
}

static void screen_weak(void)
{
    static const char *const items[] = {"Weak acid (Ka)", "Weak base (Kb)"};
    static int cursor;
    double k = 0.0, concentration = 0.0, ph = 0.0;
    int choice = ui_menu("Weak acid or base", items, 2, &cursor);

    if (choice < 0)
        return;
    ui_example("Ka 1.74e-5, c 0.1 -> pH 2.88 (ethanoic)");
    if (!ask_positive("Weak acid or base", (choice == 0) ? "Ka:" : "Kb:", &k))
        return;
    if (!ask_positive("Weak acid or base", "Concentration (mol/dm3):", &concentration))
        return;

    if (((choice == 0) ? aqua_weak_acid_ph(k, concentration, &ph)
                       : aqua_weak_base_ph(k, concentration, &ph)) != CHEM_OK) {
        ui_message("Weak acid or base", "Those numbers do not work");
        return;
    }

    ui_result_begin((choice == 0) ? "Weak acid" : "Weak base");
    ui_result_value((choice == 0) ? "Ka" : "Kb", k, "");
    ui_result_value((choice == 0) ? "pKa" : "pKb", aqua_pka_from_ka(k), "");
    ui_result_value("c", concentration, "mol/dm3");
    ui_result_rule();
    show_all_four(ph);
    ui_result_show();
}

static void screen_buffer(void)
{
    double ka = 0.0, acid = 0.0, salt = 0.0, ph = 0.0;

    ui_example("Ka 1.74e-5, acid 0.1, salt 0.1 -> pH 4.76");

    if (!ask_positive("Buffer", "Ka of the acid:", &ka))
        return;
    if (!ask_positive("Buffer", "[acid] (mol/dm3):", &acid))
        return;
    if (!ask_positive("Buffer", "[salt] (mol/dm3):", &salt))
        return;

    if (aqua_buffer_ph(ka, acid, salt, &ph) != CHEM_OK) {
        ui_message("Buffer", "Those numbers do not work");
        return;
    }

    ui_result_begin("Buffer");
    ui_result_value("Ka", ka, "");
    ui_result_value("pKa", aqua_pka_from_ka(ka), "");
    ui_result_value("[salt]/[acid]", salt / acid, "");
    ui_result_rule();
    show_all_four(ph);
    ui_result_show();
}

static void screen_ka_kb(void)
{
    static const char *const items[] = {
        "Ka to pKa", "pKa to Ka", "Ka to Kb", "Kb to Ka",
    };
    static int cursor;
    double value = 0.0, answer = 0.0;
    int choice = ui_menu("Ka, Kb, pKa, pKb", items, 4, &cursor);

    if (choice < 0)
        return;
    ui_example("Ka 1.74e-5 -> pKa 4.76, Kb 5.75e-10");
    if (choice == 1) {
        if (!ask_number("Ka, Kb, pKa, pKb", "pKa:", &value))
            return;
        answer = aqua_ka_from_pka(value);
    } else {
        if (!ask_positive("Ka, Kb, pKa, pKb",
                          (choice == 3) ? "Kb:" : "Ka:", &value))
            return;
        if (choice == 0)
            answer = aqua_pka_from_ka(value);
        else if (aqua_kb_from_ka(value, &answer) != CHEM_OK) {
            ui_message("Ka, Kb, pKa, pKb", "Those numbers do not work");
            return;
        }
    }

    ui_result_begin("Ka, Kb, pKa, pKb");
    switch (choice) {
    case 0:
        ui_result_value("Ka", value, "");
        ui_result_value("pKa", answer, "");
        break;
    case 1:
        ui_result_value("pKa", value, "");
        ui_result_value("Ka", answer, "");
        break;
    case 2:
        ui_result_value("Ka", value, "");
        ui_result_value("Kb", answer, "");
        ui_result_value("pKa", aqua_pka_from_ka(value), "");
        ui_result_value("pKb", aqua_pka_from_ka(answer), "");
        break;
    default:
        ui_result_value("Kb", value, "");
        ui_result_value("Ka", answer, "");
        break;
    }
    ui_result_rule();
    ui_result_line("Ka x Kb = Kw = 1.00e-14");
    ui_result_show();
}

void screen_acids(void)
{
    static const char *const items[] = {
        "pH, pOH, [H+], [OH-]",
        "Strong acid or base",
        "Weak acid or base",
        "Buffer",
        "Ka, Kb, pKa, pKb",
    };
    static const char *const hints[] = {
        "pH 3 -> pOH 11 and [H+] 1e-3",
        "0.1 mol/dm3 HCl -> pH 1",
        "ethanoic acid 0.1 mol/dm3 -> pH 2.88",
        "equal acid and salt -> pH = pKa",
        "Ka 1.74e-5 -> pKa 4.76",
    };
    static int cursor;

    for (;;) {
        switch (ui_menu_hints("Acids and bases", items, hints, 5, &cursor)) {
        case 0: screen_converter(); break;
        case 1: screen_strong(); break;
        case 2: screen_weak(); break;
        case 3: screen_buffer(); break;
        case 4: screen_ka_kb(); break;
        default: return;
        }
    }
}
