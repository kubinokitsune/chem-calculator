/* balance_screen.c - typing in an equation and balancing it. */

#include "screens.h"
#include "../ui/ui.h"
#include "../core/balance.h"

#include <stdio.h>
#include <string.h>

#define SIDE_MAX 5

/* Collect formulas one at a time until the user leaves one blank. */
static int collect(const char *title, const char *what,
                   char store[SIDE_MAX][24], const char *pointers[SIDE_MAX])
{
    int count = 0;

    while (count < SIDE_MAX) {
        char prompt[UI_LINE_LEN];
        chem_formula_t formula;

        store[count][0] = 0;
        if (count == 0)
            snprintf(prompt, sizeof prompt, "%s 1:", what);
        else
            snprintf(prompt, sizeof prompt, "%s %d (blank = done):", what, count + 1);

        if (!ui_text_input(title, prompt, store[count], 24))
            return -1;
        if (store[count][0] == 0) {
            if (count == 0)
                continue;          /* at least one is needed */
            break;
        }
        if (chem_parse_formula(store[count], &formula, NULL, 0) != CHEM_OK) {
            ui_message(title, "Check that formula");
            continue;
        }
        pointers[count] = store[count];
        count++;
    }
    return count;
}

void screen_balance(void)
{
    char left_store[SIDE_MAX][24], right_store[SIDE_MAX][24];
    const char *left[SIDE_MAX], *right[SIDE_MAX];
    int coefficients[BAL_MAX_SPECIES];
    char line[UI_LINE_LEN];
    int n_left, n_right, i;
    chem_error_t error;

    n_left = collect("Balancer", "Reactant", left_store, left);
    if (n_left <= 0)
        return;
    n_right = collect("Balancer", "Product", right_store, right);
    if (n_right <= 0)
        return;

    error = bal_balance(left, n_left, right, n_right, coefficients);
    if (error != CHEM_OK) {
        ui_message("Balancer",
                   (error == CHEM_ERR_RANGE) ? "That will not balance"
                                             : chem_error_text(error));
        return;
    }

    ui_result_begin("Balanced equation");
    for (i = 0; i < n_left + n_right; i++) {
        const char *text = (i < n_left) ? left[i] : right[i - n_left];
        const char *lead = (i == 0) ? "" : ((i == n_left) ? "->  " : "+   ");

        if (coefficients[i] == 1)
            snprintf(line, sizeof line, "%s%s", lead, text);
        else
            snprintf(line, sizeof line, "%s%d %s", lead, coefficients[i], text);
        ui_result_line(line);
    }
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
