/* screens.h - one entry point per topic, called from the main menu. */
#ifndef SCREENS_H
#define SCREENS_H

#include "../core/chem.h"

void screen_periodic_table(void);
void screen_tools(void);
void screen_stoichiometry(void);
void screen_balance(void);
void screen_gases(void);
void screen_acids(void);
void screen_energy(void);

/* ---- shared helpers ----------------------------------------------------- */

/* Ask for a formula and parse it. Returns 0 if the user backed out or the
 * formula could not be read (the message has already been shown). */
int ask_formula(const char *title, const char *prompt, char *text, int length,
                chem_formula_t *formula);

/* Ask for a number that must be greater than zero. Returns 0 on EXIT. */
int ask_positive(const char *title, const char *prompt, double *value);

/* Ask for any number. Returns 0 on EXIT. */
int ask_number(const char *title, const char *prompt, double *value);

#endif /* SCREENS_H */
