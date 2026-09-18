/* chem.h - the chemistry core of the fx-CG50 add-in.
 *
 * Plain C99 with nothing calculator-specific in it, so the same code is built
 * for the add-in and for the tests that run on a PC (test/test_core.c).
 *
 * Conventions follow the IB data booklet: relative atomic masses to 2 decimal
 * places, answers to 4 significant figures.
 */
#ifndef CHEM_H
#define CHEM_H

#define CHEM_ELEMENT_COUNT 118
#define CHEM_MAX_ATOMS     12    /* distinct elements in one formula */
#define CHEM_SYMBOL_LEN    4

typedef struct {
    const char *symbol;
    const char *name;
    float mass;        /* relative atomic mass */
    float en;          /* Pauling electronegativity, 0 when not tabulated */
} chem_element_t;

extern const chem_element_t chem_elements[CHEM_ELEMENT_COUNT];

typedef enum {
    CHEM_OK = 0,
    CHEM_ERR_UNKNOWN_ELEMENT,
    CHEM_ERR_SYNTAX,
    CHEM_ERR_TOO_MANY,
    CHEM_ERR_RANGE,
    CHEM_ERR_EMPTY
} chem_error_t;

/* A short message for the screen, e.g. "Unknown element". */
const char *chem_error_text(chem_error_t error);

/* ---- elements ---------------------------------------------------------- */

/* Element with atomic number z (1..118), or NULL. */
const chem_element_t *chem_element(int z);

/* Atomic number from an exact symbol ("Fe"), or 0. */
int chem_symbol_z(const char *symbol);

/* Atomic number from a symbol, a name or a number, any case; 0 if no match. */
int chem_find_element(const char *text);

/* Relative atomic mass of a symbol, or 0 when it is not an element. */
float chem_element_mass(const char *symbol);

int chem_group(int z);            /* 1..18; the f block counts as group 3 */
int chem_period(int z);           /* 1..7 */
int chem_is_f_block(int z);       /* lanthanoids and actinoids */
char chem_block(int z);           /* 's', 'p', 'd' or 'f' */
const char *chem_category(int z); /* "Alkali metal", "Halogen", ... */
const char *chem_state(int z);    /* state at room temperature */
const char *chem_usual_ion(int z);/* "+2", "-1", "varies", "none" */
const char *chem_bond_type(float en_gap);   /* from the electronegativity gap */

/* ---- formulas ---------------------------------------------------------- */

typedef struct {
    char symbol[CHEM_SYMBOL_LEN];
    int count;
} chem_atom_t;

typedef struct {
    chem_atom_t atoms[CHEM_MAX_ATOMS];
    int n;
} chem_formula_t;

/* Parse "Ca(OH)2" or "CuSO4.5H2O". `bad` (may be NULL) receives the symbol or
 * character that caused the failure, to put in the error message. */
chem_error_t chem_parse_formula(const char *text, chem_formula_t *out,
                                char *bad, int bad_len);

/* Relative molecular mass of a parsed formula. */
float chem_formula_mass(const chem_formula_t *formula);

/* Parse and weigh in one go. */
chem_error_t chem_molar_mass(const char *text, float *out);

/* Number of atoms of one element in a parsed formula (0 when absent). */
int chem_atom_count(const chem_formula_t *formula, const char *symbol);

/* ---- numbers ----------------------------------------------------------- */

/* Round to `figures` significant figures and write it the short way, using
 * scientific notation only outside 1e-4 .. 1e6. `out` should hold 24 chars. */
void chem_format(double value, int figures, char *out, int len);

#endif /* CHEM_H */
