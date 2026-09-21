/* balance.c - see balance.h.
 *
 * One row per element, one column per species, products counted negative.
 * Gaussian elimination in fractions gives the null space; the free column is
 * set to 1 and everything is scaled up to whole numbers at the end.
 */

#include "balance.h"

#include <string.h>

typedef struct {
    long long num;
    long long den;      /* always > 0 */
} frac_t;

static long long gcd_ll(long long a, long long b)
{
    if (a < 0) a = -a;
    if (b < 0) b = -b;
    while (b != 0) {
        long long t = a % b;
        a = b;
        b = t;
    }
    return a ? a : 1;
}

static frac_t frac_make(long long num, long long den)
{
    frac_t f;
    long long g;

    if (den < 0) {
        num = -num;
        den = -den;
    }
    if (den == 0)
        den = 1;
    g = gcd_ll(num, den);
    f.num = num / g;
    f.den = den / g;
    return f;
}

static frac_t frac_add(frac_t a, frac_t b)
{
    return frac_make(a.num * b.den + b.num * a.den, a.den * b.den);
}

static frac_t frac_mul(frac_t a, frac_t b)
{
    return frac_make(a.num * b.num, a.den * b.den);
}

static frac_t frac_div(frac_t a, frac_t b)
{
    return frac_make(a.num * b.den, a.den * b.num);
}

static frac_t frac_neg(frac_t a)
{
    frac_t f;
    f.num = -a.num;
    f.den = a.den;
    return f;
}

static long long lcm_ll(long long a, long long b)
{
    return a / gcd_ll(a, b) * b;
}

chem_error_t bal_balance(const char *const *reactants, int n_reactants,
                         const char *const *products, int n_products,
                         int *coefficients)
{
    char symbols[BAL_MAX_ELEMENTS][CHEM_SYMBOL_LEN];
    frac_t matrix[BAL_MAX_ELEMENTS][BAL_MAX_SPECIES];
    frac_t solution[BAL_MAX_SPECIES];
    chem_formula_t formula;
    chem_error_t error;
    int pivot_of_row[BAL_MAX_ELEMENTS];
    int n_species, n_elements = 0;
    int i, j, k, row, column, free_column;
    long long denominator, divisor;

    n_species = n_reactants + n_products;
    if (n_reactants < 1 || n_products < 1 || n_species > BAL_MAX_SPECIES)
        return CHEM_ERR_TOO_MANY;

    for (i = 0; i < BAL_MAX_ELEMENTS; i++) {
        for (j = 0; j < BAL_MAX_SPECIES; j++)
            matrix[i][j] = frac_make(0, 1);
    }

    /* Fill the matrix: + for a reactant, - for a product. */
    for (j = 0; j < n_species; j++) {
        const char *text = (j < n_reactants) ? reactants[j] : products[j - n_reactants];
        int sign = (j < n_reactants) ? 1 : -1;

        error = chem_parse_formula(text, &formula, NULL, 0);
        if (error != CHEM_OK)
            return error;
        for (k = 0; k < formula.n; k++) {
            int found = -1;
            for (i = 0; i < n_elements; i++) {
                if (strcmp(symbols[i], formula.atoms[k].symbol) == 0)
                    found = i;
            }
            if (found < 0) {
                if (n_elements >= BAL_MAX_ELEMENTS)
                    return CHEM_ERR_TOO_MANY;
                found = n_elements++;
                strcpy(symbols[found], formula.atoms[k].symbol);
            }
            matrix[found][j] = frac_add(matrix[found][j],
                                        frac_make(sign * (long long)formula.atoms[k].count, 1));
        }
    }

    /* Gaussian elimination, remembering which column each row pivots on. */
    for (i = 0; i < BAL_MAX_ELEMENTS; i++)
        pivot_of_row[i] = -1;

    row = 0;
    for (column = 0; column < n_species && row < n_elements; column++) {
        int pivot = -1;
        for (i = row; i < n_elements; i++) {
            if (matrix[i][column].num != 0) {
                pivot = i;
                break;
            }
        }
        if (pivot < 0)
            continue;
        if (pivot != row) {
            for (j = 0; j < n_species; j++) {
                frac_t swap = matrix[row][j];
                matrix[row][j] = matrix[pivot][j];
                matrix[pivot][j] = swap;
            }
        }
        {
            frac_t lead = matrix[row][column];
            for (j = 0; j < n_species; j++)
                matrix[row][j] = frac_div(matrix[row][j], lead);
        }
        for (i = 0; i < n_elements; i++) {
            if (i == row || matrix[i][column].num == 0)
                continue;
            {
                frac_t factor = matrix[i][column];
                for (j = 0; j < n_species; j++)
                    matrix[i][j] = frac_add(matrix[i][j],
                                            frac_neg(frac_mul(factor, matrix[row][j])));
            }
        }
        pivot_of_row[row] = column;
        row++;
    }

    /* One free column means one family of answers, which is what a balanced
     * equation is. No free column (or more than one) means it will not do. */
    free_column = -1;
    for (column = 0; column < n_species; column++) {
        int is_pivot = 0;
        for (i = 0; i < row; i++) {
            if (pivot_of_row[i] == column)
                is_pivot = 1;
        }
        if (!is_pivot) {
            if (free_column >= 0)
                return CHEM_ERR_RANGE;      /* ambiguous: more than one answer */
            free_column = column;
        }
    }
    if (free_column < 0)
        return CHEM_ERR_RANGE;              /* only the all-zero answer */

    for (j = 0; j < n_species; j++)
        solution[j] = frac_make(0, 1);
    solution[free_column] = frac_make(1, 1);
    for (i = 0; i < row; i++) {
        column = pivot_of_row[i];
        if (column >= 0)
            solution[column] = frac_neg(matrix[i][free_column]);
    }

    /* Scale to whole numbers: multiply by the lowest common denominator, then
     * divide by the greatest common divisor. */
    denominator = 1;
    for (j = 0; j < n_species; j++)
        denominator = lcm_ll(denominator, solution[j].den);
    for (j = 0; j < n_species; j++)
        coefficients[j] = (int)(solution[j].num * (denominator / solution[j].den));

    divisor = 0;
    for (j = 0; j < n_species; j++)
        divisor = gcd_ll(divisor, coefficients[j]);
    if (divisor == 0)
        return CHEM_ERR_RANGE;
    for (j = 0; j < n_species; j++)
        coefficients[j] /= (int)divisor;

    /* A negative coefficient means the equation cannot run as written. */
    if (coefficients[0] < 0) {
        for (j = 0; j < n_species; j++)
            coefficients[j] = -coefficients[j];
    }
    for (j = 0; j < n_species; j++) {
        if (coefficients[j] <= 0)
            return CHEM_ERR_RANGE;
    }
    return CHEM_OK;
}
