/* tools.h - the rest of the IB syllabus: solutions, limiting reactant,
 * electron configuration, oxidation numbers, ionic formulas, isotopes,
 * uncertainties and the index of hydrogen deficiency.
 */
#ifndef TOOLS_H
#define TOOLS_H

#include "chem.h"

/* ---- solutions ---------------------------------------------------------- */

/* c = n / V, with V in dm3. */
double tools_concentration(double moles, double volume);
double tools_moles_from_concentration(double concentration, double volume);

/* c1 V1 = c2 V2: the missing one of the four, given the other three. */
chem_error_t tools_dilution(double c1, double v1, double c2, double *v2);

/* g dm-3 <-> mol dm-3, and parts per million. */
double tools_mass_concentration(double concentration, double molar_mass);
double tools_ppm(double solute_mass, double solution_mass);

/* ---- limiting reactant -------------------------------------------------- */

typedef struct {
    int limiting;         /* which reactant runs out first */
    double reacting;      /* how many "reaction units" happen */
    double left_over[CHEM_MAX_ATOMS];
} tools_limiting_t;

/* `moles` and `coefficients` describe each reactant. Returns which one limits
 * the reaction and how much of the others is left. */
chem_error_t tools_limiting_reactant(const double *moles, const int *coefficients,
                                     int count, tools_limiting_t *result);

/* ---- electron configuration --------------------------------------------- */

#define TOOLS_MAX_SUBSHELLS 20

typedef struct {
    int n;                /* principal quantum number */
    char letter;          /* 's', 'p', 'd' or 'f' */
    int electrons;
} tools_subshell_t;

/* Fill the subshells for an atom or ion. Writes the configuration in order
 * and returns how many subshells were used, or -1 on bad input.
 * Chromium and copper (and their groups) get the half-filled exception. */
int tools_configuration(int z, int charge, tools_subshell_t *out, int max);

/* Write a configuration as text: "1s2 2s2 2p6 ...". */
void tools_configuration_text(const tools_subshell_t *shells, int count,
                              char *out, int length);

/* The noble gas the shorthand starts from, or 0 if there is none. */
int tools_noble_core(int z);

/* ---- oxidation numbers -------------------------------------------------- */

/* Oxidation number of each element of a formula, in the order the formula
 * lists them. `charge` is the charge on the whole species (0 for a compound).
 * Returns CHEM_ERR_RANGE when more than one element is unknown. */
chem_error_t tools_oxidation_numbers(const chem_formula_t *formula, int charge,
                                     int peroxide, double *numbers);

/* ---- ionic formulas ----------------------------------------------------- */

/* Cross the charges over and cancel: Al3+ and O2- give Al2O3. */
chem_error_t tools_ionic_formula(const char *cation, int cation_charge,
                                 const char *anion, int anion_charge,
                                 char *out, int length);

/* ---- isotopes ----------------------------------------------------------- */

/* Relative atomic mass from isotope masses and their abundances (%). */
chem_error_t tools_relative_atomic_mass(const double *masses,
                                        const double *abundances,
                                        int count, double *ar);

/* The abundances of two isotopes that give a known Ar, as percentages. */
chem_error_t tools_abundances_from_ar(double mass_1, double mass_2, double ar,
                                      double *percent_1, double *percent_2);

/* ---- uncertainties ------------------------------------------------------ */

double tools_percent_uncertainty(double value, double absolute);
double tools_absolute_uncertainty(double value, double percent);

/* Adding or subtracting measurements adds the absolute uncertainties;
 * multiplying or dividing adds the percentage ones; a power multiplies the
 * percentage by the power. */
double tools_combine_sum(const double *absolutes, int count);
double tools_combine_product(const double *percents, int count);
double tools_combine_power(double percent, double power);

/* How far a measurement is from the accepted value, as a percentage. */
double tools_percent_error(double measured, double accepted);

/* ---- index of hydrogen deficiency --------------------------------------- */

/* Rings plus pi bonds, from a molecular formula. Returns -1 if it cannot be
 * worked out (a fractional answer means the formula is impossible). */
double tools_ihd(const chem_formula_t *formula, int charge);

#endif /* TOOLS_H */
