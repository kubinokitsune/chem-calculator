/* stoich.h - moles, percentage composition and empirical formulas.
 *
 * IB data booklet values: Avogadro's constant 6.02e23 mol-1 and a molar volume
 * of 22.7 dm3 mol-1 at STP (0 C, 100 kPa).
 */
#ifndef STOICH_H
#define STOICH_H

#include "chem.h"

#define CHEM_AVOGADRO      6.02e23
#define CHEM_MOLAR_VOLUME  22.7    /* dm3 mol-1 at STP */

/* Percentage by mass of each element in a formula. `percent` must have room
 * for formula->n values, in the same order as formula->atoms. */
void stoich_percent_composition(const chem_formula_t *formula, float *percent);

/* Empirical formula from masses (g) or percentages: the same calculation.
 * `counts` receives the whole-number ratio for each of the `n` symbols.
 * Returns CHEM_ERR_RANGE if an amount is negative or they are all zero. */
chem_error_t stoich_empirical(const char *const *symbols, const float *amounts,
                              int n, int *counts);

/* How many times the empirical formula fits into a molar mass, rounded to the
 * nearest whole number (at least 1). */
int stoich_formula_multiplier(float empirical_mass, float molar_mass);

/* Percentage yield and atom economy, as percentages. */
float stoich_percent_yield(float actual, float theoretical);
float stoich_atom_economy(float wanted_mass, float total_mass);

#endif /* STOICH_H */
