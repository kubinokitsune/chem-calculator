/* solution.h - gases, equilibrium, acids and bases.
 *
 * IB data booklet values: R = 8.31 J K-1 mol-1, Kw = 1.00e-14 at 298 K,
 * molar volume 22.7 dm3 mol-1 at STP.
 */
#ifndef SOLUTION_H
#define SOLUTION_H

#include "chem.h"

#define CHEM_R   8.31
#define CHEM_KW  1.00e-14

/* ---- gases -------------------------------------------------------------- */

/* pV = nRT with p in kPa, V in dm3, T in K. Exactly one of the four pointers
 * is NULL-free but zero: pass the value to solve for as 0 and the others as
 * their measurements. Returns CHEM_ERR_RANGE if the numbers cannot work. */
typedef struct {
    double pressure;      /* kPa */
    double volume;        /* dm3 */
    double moles;
    double temperature;   /* K */
} gas_state_t;

typedef enum {
    GAS_PRESSURE, GAS_VOLUME, GAS_MOLES, GAS_TEMPERATURE
} gas_unknown_t;

chem_error_t gas_ideal(gas_state_t *state, gas_unknown_t unknown);

/* p1V1/T1 = p2V2/T2. The member of `after` named by `unknown` is filled in;
 * a zero in `before` or `after` means "not changed". */
chem_error_t gas_combined(const gas_state_t *before, gas_state_t *after,
                          gas_unknown_t unknown);

/* Graham's law: rate1/rate2 = sqrt(M2/M1). */
chem_error_t gas_effusion_ratio(double molar_mass_1, double molar_mass_2,
                                double *ratio);

/* ---- equilibrium -------------------------------------------------------- */

/* Kc from Kp, or Kp from Kc: Kp = Kc (RT)^dn, with R in dm3 kPa K-1 mol-1. */
chem_error_t eq_kc_to_kp(double kc, double temperature, int delta_n, double *kp);
chem_error_t eq_kp_to_kc(double kp, double temperature, int delta_n, double *kc);

/* The ICE table for A + B <-> C + D with one unknown extent x, solved by
 * bisection so it works for any K. `a`,`b` are starting concentrations of the
 * reactants and `c`,`d` of the products; the coefficients are 1. */
chem_error_t eq_ice_extent(double a, double b, double c, double d,
                           double k, double *extent);

/* ---- acids and bases ---------------------------------------------------- */

double aqua_ph_from_h(double h);
double aqua_h_from_ph(double ph);
double aqua_poh_from_ph(double ph);
double aqua_oh_from_poh(double poh);

/* Strong acid or base: concentration -> pH. */
chem_error_t aqua_strong_acid_ph(double concentration, int basicity, double *ph);
chem_error_t aqua_strong_base_ph(double concentration, int acidity, double *ph);

/* Weak acid: [H+] = sqrt(Ka c) is the IB approximation; this solves the
 * quadratic instead, which matches it to 3 s.f. and stays right for large Ka. */
chem_error_t aqua_weak_acid_ph(double ka, double concentration, double *ph);
chem_error_t aqua_weak_base_ph(double kb, double concentration, double *ph);

/* Henderson-Hasselbalch: pH = pKa + log10([salt]/[acid]). */
chem_error_t aqua_buffer_ph(double ka, double acid, double salt, double *ph);

double aqua_pka_from_ka(double ka);
double aqua_ka_from_pka(double pka);
chem_error_t aqua_kb_from_ka(double ka, double *kb);

#endif /* SOLUTION_H */
