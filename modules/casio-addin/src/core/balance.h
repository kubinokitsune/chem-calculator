/* balance.h - balancing equations with exact whole-number arithmetic.
 *
 * The coefficients come from the null space of the element matrix, worked out
 * in fractions rather than floating point, so the answers are exact and the
 * smallest whole numbers possible.
 */
#ifndef BALANCE_H
#define BALANCE_H

#include "chem.h"

#define BAL_MAX_SPECIES  10
#define BAL_MAX_ELEMENTS 16

/* `coefficients` receives one number per species, reactants first.
 * Returns CHEM_ERR_RANGE when the equation cannot be balanced (the atoms on
 * the two sides do not match up) and CHEM_ERR_TOO_MANY when it is too big. */
chem_error_t bal_balance(const char *const *reactants, int n_reactants,
                         const char *const *products, int n_products,
                         int *coefficients);

#endif /* BALANCE_H */
