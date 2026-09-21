/* common.c - the small asking-and-checking helpers the screens share. */

#include "screens.h"
#include "../ui/ui.h"

#include <stdio.h>
#include <string.h>

int ask_formula(const char *title, const char *prompt, char *text, int length,
                chem_formula_t *formula)
{
    char bad[8];
    chem_error_t error;

    for (;;) {
        if (!ui_text_input(title, prompt, text, length))
            return 0;
        error = chem_parse_formula(text, formula, bad, sizeof bad);
        if (error == CHEM_OK)
            return 1;
        {
            char message[UI_LINE_LEN];
            if (error == CHEM_ERR_UNKNOWN_ELEMENT && bad[0] != 0)
                snprintf(message, sizeof message, "No element called %s", bad);
            else
                snprintf(message, sizeof message, "%s", chem_error_text(error));
            ui_message(title, message);
        }
    }
}

int ask_positive(const char *title, const char *prompt, double *value)
{
    for (;;) {
        double entered = 0.0;

        if (!ui_number_input(title, prompt, &entered, 0))
            return 0;
        if (entered > 0.0) {
            *value = entered;
            return 1;
        }
        ui_message(title, "Must be more than zero");
    }
}

int ask_number(const char *title, const char *prompt, double *value)
{
    return ui_number_input(title, prompt, value, 0);
}
