/* test_screens.c - drives the add-in's real screens with scripted keypresses.
 *
 *   make -C test screens
 *
 * The screens, the menus and the entry fields are the ones that will run on
 * the calculator; only the screen and keypad are faked. Each test types what
 * a student would type and then checks what came out.
 */

#include "fake_gint.h"
#include "../src/screens/screens.h"
#include "../src/ui/ui.h"

#include <stdio.h>
#include <string.h>

static int passed, failed;

static void ok(const char *label, int condition, const char *detail)
{
    if (condition) {
        passed++;
        printf("  [PASS] %s\n", label);
    } else {
        failed++;
        printf("  [FAIL] %s\n         %s\n", label, detail ? detail : "");
    }
}

/* Check that the screen showed a piece of text. On failure, print the last
 * part of what was actually drawn, which is usually enough to see why. */
static void showed(const char *label, const char *wanted)
{
    const char *screen = fake_screen();
    int length = (int)strlen(screen);
    const char *tail = screen + (length > 300 ? length - 300 : 0);
    char detail[400];

    snprintf(detail, sizeof detail, "did not show \"%s\"; screen ended:\n%s",
             wanted, tail);
    ok(label, fake_screen_has(wanted), detail);
}

static void section(const char *title)
{
    printf("\n=== %s ===\n", title);
}

/* Choose an item from a menu by its number. The number keys move the cursor
 * straight to an entry, which is steady whatever the menu last remembered -
 * the menus keep their place between visits, as the calculator's own do. */
static void menu_pick(int item)
{
    static const int digits[10] = {
        KEY_0, KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, KEY_6, KEY_7, KEY_8, KEY_9
    };
    if (item >= 1 && item <= 9)
        fake_press(digits[item]);
    fake_press(KEY_EXE);
}

int main(void)
{
    section("1. The periodic table screens");

    /* Look up iron by symbol: menu item 1, type Fe, EXE, read, back out. */
    fake_reset();
    menu_pick(1);                       /* Element lookup */
    fake_press_text("Fe");
    fake_press(KEY_EXE);                /* accept the formula */
    fake_press(KEY_EXIT);               /* leave the result page */
    fake_press(KEY_EXIT);               /* leave the topic menu */
    screen_periodic_table();
    showed("looking up Fe names iron", "Iron");
    showed("and gives its mass", "55.85");
    showed("and its group", "Group 8");
    showed("and its category", "Transition metal");
    ok("the screen did not run out of keys", fake_ran_out_of_keys() == 0, NULL);

    /* By atomic number this time. */
    fake_reset();
    menu_pick(1);
    fake_press(KEY_ALPHA);              /* text fields start on letters */
    fake_press_number("26");            /* digits, then EXE */
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_periodic_table();
    showed("looking up 26 also finds iron", "Iron");

    /* By name, in small letters. */
    fake_reset();
    menu_pick(1);
    fake_press_text("magnesium");
    fake_press(KEY_EXE);
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_periodic_table();
    showed("looking up a name works", "Magnesium");
    showed("magnesium is in group 2", "Group 2");
    showed("and forms +2", "+2");

    /* A group listing. */
    fake_reset();
    menu_pick(2);                       /* List a group */
    fake_press_number("17");
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_periodic_table();
    showed("group 17 lists fluorine", "Fluorine");
    showed("group 17 lists astatine", "Astatine");

    /* Bond type. */
    fake_reset();
    menu_pick(4);                       /* Bond type */
    fake_press_text("Na");
    fake_press(KEY_EXE);
    fake_press_text("Cl");
    fake_press(KEY_EXE);
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_periodic_table();
    showed("NaCl comes out ionic", "ionic");

    /* A made-up element must be reported, not accepted. */
    fake_reset();
    menu_pick(1);
    fake_press_text("Qz");
    fake_press(KEY_EXE);
    fake_press(KEY_EXIT);               /* dismiss the message */
    fake_press(KEY_EXIT);               /* leave the field */
    fake_press(KEY_EXIT);               /* leave the menu */
    screen_periodic_table();
    showed("a made-up element is reported", "No such element");

    section("2. The stoichiometry screens");

    /* 10 g of CaCO3 is 0.0999 mol - the answer the other two versions give. */
    fake_reset();
    menu_pick(1);                       /* Moles */
    menu_pick(1);                       /* Mass to moles */
    fake_press_text("CaCO3");
    fake_press(KEY_EXE);
    fake_press_number("10");
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_stoichiometry();
    showed("10 g of CaCO3 has the right molar mass", "100.1");
    showed("and is 0.0999 mol", "0.0999");

    /* Percentage composition of water. */
    fake_reset();
    menu_pick(2);                       /* Percent composition */
    fake_press_text("H2O");
    fake_press(KEY_EXE);
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_stoichiometry();
    showed("water is 11.2 % hydrogen", "11.2");
    showed("water is 88.8 % oxygen", "88.79");

    /* Empirical formula from percentages, then the molecular formula. */
    fake_reset();
    menu_pick(3);                       /* Empirical */
    fake_press_number("3");             /* three elements */
    fake_press_text("C");
    fake_press(KEY_EXE);
    fake_press_number("40");
    fake_press_text("H");
    fake_press(KEY_EXE);
    fake_press_number("6.7");
    fake_press_text("O");
    fake_press(KEY_EXE);
    fake_press_number("53.3");
    fake_press_number("180");           /* Mr, for the molecular formula */
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_stoichiometry();
    showed("the empirical formula is CH2O", "CH2O");
    showed("and the molecular formula is C6H12O6", "C6H12O6");

    section("3. The balancer screen");

    fake_reset();
    fake_press_text("C3H8");            /* reactant 1 */
    fake_press(KEY_EXE);
    fake_press_text("O2");              /* reactant 2 */
    fake_press(KEY_EXE);
    fake_press(KEY_EXE);                /* blank: done with reactants */
    fake_press_text("CO2");             /* product 1 */
    fake_press(KEY_EXE);
    fake_press_text("H2O");             /* product 2 */
    fake_press(KEY_EXE);
    fake_press(KEY_EXE);                /* blank: done with products */
    fake_press(KEY_EXIT);
    screen_balance();
    showed("propane balances as 1, 5, 3, 4", "1, 5, 3, 4");
    showed("and the equation is shown", "5 O2");

    section("4. The gas screens");

    /* 2.00 mol at 300 K in 5.00 dm3 gives 997 kPa. */
    fake_reset();
    menu_pick(1);                       /* pV = nRT */
    menu_pick(1);                       /* find pressure */
    fake_press_number("5");             /* V */
    fake_press_number("2");             /* n */
    fake_press_number("300");           /* T */
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_gases();
    showed("pV = nRT gives 997 kPa", "997");

    section("5. The acid and base screens");

    /* 0.10 mol dm-3 hydrochloric acid has pH 1. */
    fake_reset();
    menu_pick(2);                       /* Strong acid or base */
    menu_pick(1);                       /* strong acid */
    fake_press_number("0.1");
    fake_press_number("1");
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_acids();
    showed("0.10 mol dm-3 HCl has pH 1", "pH = 1");

    /* Ethanoic acid, Ka = 1.74e-5, 0.100 mol dm-3, pH 2.88. */
    fake_reset();
    menu_pick(3);                       /* Weak acid or base */
    menu_pick(1);                       /* weak acid */
    fake_press_number("1.74e-5");
    fake_press_number("0.1");
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_acids();
    showed("ethanoic acid has pH 2.88", "2.88");

    section("6. The energy screens");

    /* 100 g of water warmed 25 K takes 10450 J. */
    fake_reset();
    menu_pick(1);                       /* Calorimetry */
    fake_press_number("100");
    fake_press_number("4.18");
    fake_press_number("25");
    fake_press(KEY_EXE);                /* skip the moles */
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_energy();
    showed("q = mcdT is 10450 J", "10450");

    /* dG from dH and dS. */
    fake_reset();
    menu_pick(3);                       /* Gibbs */
    menu_pick(1);                       /* dG from dH and dS */
    fake_press_number("-92.2");
    fake_press_number("-198.8");
    fake_press_number("298");
    fake_press(KEY_EXIT);
    fake_press(KEY_EXIT);
    screen_energy();
    showed("dG comes out at -32.96 kJ/mol", "-32.96");
    showed("and it is called spontaneous", "spontaneous");

    printf("\n============================================================\n");
    printf("  Screen tests  Total: %d   Passed: %d   Failed: %d\n",
           passed + failed, passed, failed);
    return failed ? 1 : 0;
}
