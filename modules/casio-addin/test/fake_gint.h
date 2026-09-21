/* fake_gint.h - the PC stand-in for the calculator's screen and keypad. */
#ifndef FAKE_GINT_H
#define FAKE_GINT_H

#include <gint/display.h>
#include <gint/keyboard.h>

#define FAKE_CAPTURE_LEN  8192
#define FAKE_KEY_QUEUE    512

/* Forget everything: no keys queued, nothing drawn. */
void fake_reset(void);

/* Queue one keypress. */
void fake_press(int key);

/* Queue the keys that type `text` into a formula field, working out the
 * ALPHA and SHIFT presses needed. Does NOT add EXE. */
void fake_press_text(const char *text);

/* Queue the keys that type a number, and then EXE. */
void fake_press_number(const char *text);

/* Everything that has been drawn since the last reset, one line per call. */
const char *fake_screen(void);
int fake_screen_has(const char *text);

/* Keys queued but never read - a sign the screen asked for less than
 * expected. And the opposite: how often a screen asked when nothing was left. */
int fake_keys_left(void);
int fake_ran_out_of_keys(void);

#endif
