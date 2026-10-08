/* balance_screen.c - typing in an equation and balancing it. */

#include "screens.h"
#include "../ui/ui.h"
#include "../core/balance.h"

#include <stdio.h>
#include <string.h>

void screen_balance(void)
{
    char text[UI_EQUATION_LEN] = "";
    chem_species_t left[EQ_SIDE_MAX], right[EQ_SIDE_MAX];
    const char *names[2 * EQ_SIDE_MAX];
    int coefficients[BAL_MAX_SPECIES];
    char line[UI_LINE_LEN];
    int n_left, n_right, i;

    ui_example("C3H8+O2->CO2+H2O gives 1, 5, 3, 4");
    for (;;) {
        chem_error_t error;

        if (!ask_equation("Balancer", "Equation (numbers in front are ignored):",
                          text, (int)sizeof text, left, &n_left, right, &n_right))
            return;
        for (i = 0; i < n_left + n_right; i++)
            names[i] = (i < n_left) ? left[i].formula : right[i - n_left].formula;

        error = bal_balance(names, n_left, names + n_left, n_right, coefficients);
        if (error == CHEM_OK)
            break;
        ui_message("Balancer",
                   (error == CHEM_ERR_RANGE) ? "That will not balance"
                                             : chem_error_text(error));
    }

    ui_result_begin("Balanced equation");
    show_equation(left, n_left, right, n_right, coefficients);
    ui_result_rule();

    /* Show the coefficients on their own too: that is what gets written down. */
    line[0] = 0;
    for (i = 0; i < n_left + n_right; i++) {
        char part[8];
        snprintf(part, sizeof part, "%s%d", (i == 0) ? "" : ", ", coefficients[i]);
        strncat(line, part, sizeof line - strlen(line) - 1);
    }
    ui_result_text("Coefficients:", line);
    ui_result_show();
}
