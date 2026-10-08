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


/* ---- a whole typed equation, e.g. "CH4+2O2->CO2+2H2O" ------------------- */

#define BAL_SPECIES_LEN 24      /* formula text incl. the NUL; matches the screens */

typedef struct {
    char formula[BAL_SPECIES_LEN];
    int coeff;                  /* 0 = none typed, else 1..999 */
} chem_species_t;

/* Split text into reactants (left) and products (right). The arrow is "->" or
 * "="; spaces are ignored; species are separated by "+"; an optional leading
 * whole number is the coefficient ("2O2"). Each formula is checked with
 * chem_parse_formula, so brackets "Ca(OH)2" and hydrates "CuSO4.5H2O" work;
 * ionic charges do not. On success *n_left / *n_right hold the counts, each
 * <= max_side (the arrays must hold max_side entries). Errors:
 *   CHEM_ERR_NO_ARROW, CHEM_ERR_TWO_ARROWS,
 *   CHEM_ERR_EMPTY            (nothing typed, an empty side or a species like A++B),
 *   CHEM_ERR_UNKNOWN_ELEMENT / CHEM_ERR_SYNTAX   (bad formula, from chem_parse_formula),
 *   CHEM_ERR_RANGE            (coefficient 0 or over 999),
 *   CHEM_ERR_TOO_MANY         (more than max_side species, or a formula over 23 chars). */
chem_error_t chem_parse_equation(const char *text, chem_species_t *left, int *n_left,
                                 chem_species_t *right, int *n_right, int max_side);

/* Atom economy (%) of product number `wanted` (0-based, within `right`).
 * Coefficient rule: if NO species has a coefficient the equation is balanced
 * with bal_balance first (CHEM_ERR_RANGE / CHEM_ERR_TOO_MANY if it cannot be);
 * otherwise the typed ones are used and any missing one counts as 1.
 * CHEM_ERR_RANGE also for a `wanted` outside 0..n_right-1. */
chem_error_t bal_atom_economy(const chem_species_t *left, int n_left,
                              const chem_species_t *right, int n_right,
                              int wanted, float *percent);

#endif /* BALANCE_H */
