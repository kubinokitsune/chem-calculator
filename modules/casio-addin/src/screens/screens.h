/* screens.h - one entry point per topic, called from the main menu. */
#ifndef SCREENS_H
#define SCREENS_H

#include "../core/chem.h"
#include "../core/balance.h"

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

/* Ask for a whole equation ("CH4+2O2->CO2+2H2O") and split it into species,
 * at most EQ_SIDE_MAX a side. A bad one is explained and the field reopens
 * with the text kept, so it can be fixed. `text` holds what is typed and is
 * returned as is. Returns 0 if the user backed out. */
#define EQ_SIDE_MAX 5
int ask_equation(const char *title, const char *prompt, char *text, int length,
                 chem_species_t *left, int *n_left,
                 chem_species_t *right, int *n_right);

/* Add the equation to the open result page, one species a line, using
 * `coefficients` (reactants first, 1 is left out). */
void show_equation(const chem_species_t *left, int n_left,
                   const chem_species_t *right, int n_right, const int *coefficients);

/* Ask for a number that must be greater than zero. Returns 0 on EXIT. */
int ask_positive(const char *title, const char *prompt, double *value);

/* Ask for any number. Returns 0 on EXIT. */
int ask_number(const char *title, const char *prompt, double *value);

#endif /* SCREENS_H */
