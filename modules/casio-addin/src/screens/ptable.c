/* ptable.c - the periodic table screens. */

#include "screens.h"
#include "../ui/ui.h"

#include <stdio.h>
#include <string.h>

static void element_card(int z)
{
    const chem_element_t *e = chem_element(z);
    char line[UI_LINE_LEN];

    if (e == NULL)
        return;

    snprintf(line, sizeof line, "%d  %s  %s", z, e->symbol, e->name);
    ui_result_begin(line);
    ui_result_value("Ar", e->mass, "");
    ui_result_rule();
    if (chem_is_f_block(z))
        snprintf(line, sizeof line, "f block      Period %d", chem_period(z));
    else
        snprintf(line, sizeof line, "Group %-8d Period %d", chem_group(z), chem_period(z));
    ui_result_line(line);
    snprintf(line, sizeof line, "%c block", chem_block(z));
    ui_result_line(line);
    ui_result_line(chem_category(z));
    ui_result_text("State:", chem_state(z));
    ui_result_text("Usual ion:", chem_usual_ion(z));
    if (e->en > 0.0f)
        ui_result_value("Electronegativity", e->en, "");
    else
        ui_result_text("Electronegativity", "not tabulated");
    ui_result_show();
}

static void screen_lookup(void)
{
    char text[24] = "";
    int z;

    for (;;) {
        if (!ui_text_input("Element lookup", "Symbol, name or number:", text,
                           (int)sizeof text))
            return;
        z = chem_find_element(text);
        if (z > 0) {
            element_card(z);
            return;
        }
        ui_message("Element lookup", "No such element");
    }
}

static void list_elements(const char *title, int group, int period)
{
    char line[UI_LINE_LEN];
    int z, found = 0;

    ui_result_begin(title);
    for (z = 1; z <= CHEM_ELEMENT_COUNT; z++) {
        const chem_element_t *e = chem_element(z);
        char mass[16];

        if (group > 0 && (chem_group(z) != group || chem_is_f_block(z)))
            continue;
        if (period > 0 && chem_period(z) != period)
            continue;
        chem_format(e->mass, 4, mass, sizeof mass);
        snprintf(line, sizeof line, "%3d %-3s %-12s %s", z, e->symbol, e->name, mass);
        ui_result_line(line);
        found++;
    }
    if (found == 0)
        ui_result_line("Nothing there");
    ui_result_show();
}

static void screen_group(void)
{
    double value = 0.0;
    char title[UI_LINE_LEN];

    for (;;) {
        if (!ui_number_input("List a group", "Group (1-18):", &value, 0))
            return;
        if (value >= 1 && value <= 18) {
            snprintf(title, sizeof title, "Group %d", (int)value);
            list_elements(title, (int)value, 0);
            return;
        }
        ui_message("List a group", "Groups run from 1 to 18");
    }
}

static void screen_period(void)
{
    double value = 0.0;
    char title[UI_LINE_LEN];

    for (;;) {
        if (!ui_number_input("List a period", "Period (1-7):", &value, 0))
            return;
        if (value >= 1 && value <= 7) {
            snprintf(title, sizeof title, "Period %d", (int)value);
            list_elements(title, 0, (int)value);
            return;
        }
        ui_message("List a period", "Periods run from 1 to 7");
    }
}

static void screen_bond(void)
{
    char first[16] = "", second[16] = "";
    const chem_element_t *a, *b;
    int za, zb;
    double gap;
    char line[UI_LINE_LEN];

    if (!ui_text_input("Bond type", "First element:", first, (int)sizeof first))
        return;
    za = chem_find_element(first);
    if (za == 0) {
        ui_message("Bond type", "No such element");
        return;
    }
    if (!ui_text_input("Bond type", "Second element:", second, (int)sizeof second))
        return;
    zb = chem_find_element(second);
    if (zb == 0) {
        ui_message("Bond type", "No such element");
        return;
    }
    a = chem_element(za);
    b = chem_element(zb);
    if (a->en <= 0.0f || b->en <= 0.0f) {
        ui_message("Bond type", "No electronegativity for that one");
        return;
    }

    gap = (a->en > b->en) ? a->en - b->en : b->en - a->en;
    ui_result_begin("Bond type");
    {
        char first_en[16], second_en[16];
        chem_format(a->en, 3, first_en, sizeof first_en);
        chem_format(b->en, 3, second_en, sizeof second_en);
        snprintf(line, sizeof line, "%s %s      %s %s",
                 a->symbol, first_en, b->symbol, second_en);
    }
    ui_result_line(line);
    ui_result_value("Difference", gap, "");
    ui_result_rule();
    ui_result_text("Bond:", chem_bond_type((float)gap));
    if (gap >= 0.4) {
        snprintf(line, sizeof line, "Electrons pulled to %s",
                 (a->en > b->en) ? a->symbol : b->symbol);
        ui_result_line(line);
    }
    ui_result_show();
}

void screen_periodic_table(void)
{
    static const char *const items[] = {
        "Element lookup",
        "List a group",
        "List a period",
        "Bond type from electronegativity",
    };
    static int cursor;

    for (;;) {
        switch (ui_menu("Periodic table", items, 4, &cursor)) {
        case 0: screen_lookup(); break;
        case 1: screen_group(); break;
        case 2: screen_period(); break;
        case 3: screen_bond(); break;
        default: return;
        }
    }
}
