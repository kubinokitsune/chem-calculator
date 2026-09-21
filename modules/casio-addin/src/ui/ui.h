/* ui.h - the screen furniture: title bar, softkeys, lists, entry fields.
 *
 * This is the part that makes ChemCalc behave like the calculator's own
 * applications: F1-F6 along the bottom, arrow keys to move, EXE to accept and
 * EXIT to go back.
 */
#ifndef UI_H
#define UI_H

#define UI_LINE_LEN   44      /* characters that fit across the screen */
#define UI_MAX_LINES  40      /* lines one result page can hold */

/* ---- frame -------------------------------------------------------------- */

/* Clear the screen and draw the title bar. Does not call dupdate(). */
void ui_frame(const char *title);

/* Draw the six softkey labels along the bottom. A NULL or "" label leaves
 * that key blank. Does not call dupdate(). */
void ui_softkeys(const char *const *labels);

/* ---- menus -------------------------------------------------------------- */

/* A list the user moves through with the arrows. `cursor` is kept between
 * calls so the list reopens where it was left. Returns the chosen index, or
 * -1 when the user pressed EXIT. */
int ui_menu(const char *title, const char *const *items, int count, int *cursor);

/* ---- entry fields ------------------------------------------------------- */

/* Type a formula or any other text. The keypad's printed letters are used
 * directly: ALPHA switches between letters and digits, SHIFT between capitals
 * and small letters, and F1-F3 put in ( ) and the hydrate dot.
 * Returns 1 when EXE was pressed, 0 when EXIT was. */
int ui_text_input(const char *title, const char *prompt, char *buffer, int length);

/* Type a number. DEL rubs out, (-) makes it negative and EXP adds a power of
 * ten. When `allow_blank` is set, pressing EXE on an empty field returns 1 and
 * leaves *value alone, which is how "solve for this one" is chosen.
 * Returns 1 on EXE, 0 on EXIT. */
int ui_number_input(const char *title, const char *prompt, double *value,
                    int allow_blank);

/* ---- result pages ------------------------------------------------------- */

void ui_result_begin(const char *title);
void ui_result_line(const char *text);
void ui_result_text(const char *label, const char *text);
void ui_result_value(const char *label, double value, const char *unit);
void ui_result_rule(void);
/* Show the page and wait. Scrolls with the arrows when there is more than a
 * screenful. Returns when EXIT or EXE is pressed. */
void ui_result_show(void);

/* A one-line message in the middle of the screen, dismissed with any key. */
void ui_message(const char *title, const char *message);

#endif /* UI_H */
