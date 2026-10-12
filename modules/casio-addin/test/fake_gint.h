/* fake_gint.h - the PC stand-in for the calculator's screen and keypad. */
#ifndef FAKE_GINT_H
#define FAKE_GINT_H

#include <gint/display.h>
#include <gint/keyboard.h>

#define FAKE_CAPTURE_LEN  65536
#define FAKE_KEY_QUEUE    512

/* Forget everything: no keys queued, nothing drawn. */
void fake_reset(void);

/* Queue one keypress. */
void fake_press(int key);

/* Queue the keys that type `text` into a text field, working out the
 * ALPHA and SHIFT presses needed. '-' is the keypad's minus key; ( ) .
 * use F1-F3 (and = # are refused, see fake_press_bond). In an equation field
 * ( ) are F1 F2, '+' is F3 and "->" (or a lone '>') is F4; elsewhere F3 is '.'
 * and F4 is small letters. Any other character is a test bug and aborts rather
 * than being dropped. Does NOT add EXE. */
void fake_press_text(const char *text);

/* The same for a bond field, where F2 and F3 type = and # as well. */
void fake_press_bond(const char *text);

/* Queue the keys that type a number, and then EXE. '/' is the fraction key. */
void fake_press_number(const char *text);

/* Everything that has been drawn since the last reset, one line per call. */
const char *fake_screen(void);
int fake_screen_has(const char *text);

/* How many screens have been shown (dupdate calls) since the last reset. */
int fake_frames(void);

/* What the colours and the battery looked like: how many rectangles of
 * `colour` were drawn, and the colour the text `text` was last drawn in (-2 if
 * it never was). */
int fake_rects(int colour);
int fake_text_colour(const char *text);

/* The OS's status bar: its battery icon shows `bars` blue bars (0 to 3), or
 * -1 for the OS drawing no battery, or -2 for a stray line across the whole bar
 * instead. Time passes, since the add-in asks at most every 30 s: fake_battery
 * lets enough pass for the next draw to ask again. How often the add-in asked
 * is fake_os_reads(). fake_reset puts back three bars. fake_os_status() is the
 * status area's flags now (0x303 is the OS's default), plus 0x10000 if it is
 * enabled. */
void fake_battery(int bars);
void fake_advance(int seconds);
int fake_os_reads(void);
int fake_os_status(void);

/* Text or rectangles drawn past the last column of the OS's 384 x 216 area
 * since the program started (fake_reset does not clear it), and the first
 * offender. Text is measured in the font it was drawn in. */
int fake_overflows(void);
const char *fake_first_overflow(void);

/* Where the last rectangle drawn in `colour` was: x1 y1 x2 y2. Returns 0 if
 * there was none. */
int fake_last_rect(int colour, int *x1, int *y1, int *x2, int *y2);

/* Keys queued but never read - a sign the screen asked for less than
 * expected. And the opposite: how often a screen asked when nothing was left. */
int fake_keys_left(void);
int fake_ran_out_of_keys(void);

#endif
