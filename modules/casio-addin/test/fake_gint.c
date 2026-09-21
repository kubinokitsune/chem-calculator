/* fake_gint.c - the calculator's screen and keypad, faked for the PC tests.
 *
 * Text that the add-in draws is collected into one buffer, and getkey()
 * hands out keypresses that the test queued up. Together they let the tests
 * drive the real screens exactly as a student would, and then read what came
 * out - no calculator needed.
 */

#include "fake_gint.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static char captured[FAKE_CAPTURE_LEN];
static int captured_used;

static int queue[FAKE_KEY_QUEUE];
static int queue_used, queue_next;
static int keys_exhausted;

void fake_reset(void)
{
    captured[0] = 0;
    captured_used = 0;
    queue_used = 0;
    queue_next = 0;
    keys_exhausted = 0;
}

void fake_press(int key)
{
    if (queue_used < FAKE_KEY_QUEUE)
        queue[queue_used++] = key;
}

void fake_press_text(const char *text)
{
    /* Type a formula: letters come from the keypad's alpha letters, digits
     * from the number keys, with ALPHA switching between the two. */
    static const int letters[26] = {
        KEY_XOT, KEY_LOG, KEY_LN, KEY_SIN, KEY_COS, KEY_TAN,
        KEY_FRAC, KEY_FD, KEY_LEFTP, KEY_RIGHTP, KEY_COMMA, KEY_ARROW,
        KEY_7, KEY_8, KEY_9,
        KEY_4, KEY_5, KEY_6, KEY_MUL, KEY_DIV,
        KEY_1, KEY_2, KEY_3, KEY_ADD, KEY_SUB,
        KEY_0
    };
    static const int digits[10] = {
        KEY_0, KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, KEY_6, KEY_7, KEY_8, KEY_9
    };
    int alpha = 1;      /* text fields start in letters mode */
    int small = 0;
    int i;

    for (i = 0; text[i]; i++) {
        char c = text[i];

        if (c >= 'A' && c <= 'Z') {
            if (!alpha) { fake_press(KEY_ALPHA); alpha = 1; }
            if (small) { fake_press(KEY_SHIFT); small = 0; }
            fake_press(letters[c - 'A']);
        } else if (c >= 'a' && c <= 'z') {
            if (!alpha) { fake_press(KEY_ALPHA); alpha = 1; }
            if (!small) { fake_press(KEY_SHIFT); small = 1; }
            fake_press(letters[c - 'a']);
        } else if (c >= '0' && c <= '9') {
            if (alpha) { fake_press(KEY_ALPHA); alpha = 0; }
            fake_press(digits[c - '0']);
        } else if (c == '(') {
            fake_press(KEY_F1);
        } else if (c == ')') {
            fake_press(KEY_F2);
        } else if (c == '.') {
            fake_press(KEY_F3);
        }
    }
}

void fake_press_number(const char *text)
{
    static const int digits[10] = {
        KEY_0, KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, KEY_6, KEY_7, KEY_8, KEY_9
    };
    int i;

    for (i = 0; text[i]; i++) {
        char c = text[i];

        if (c >= '0' && c <= '9')
            fake_press(digits[c - '0']);
        else if (c == '.')
            fake_press(KEY_DOT);
        else if (c == '-')
            fake_press(KEY_NEG);
        else if (c == 'e' || c == 'E')
            fake_press(KEY_EXP);
    }
    fake_press(KEY_EXE);
}

const char *fake_screen(void)
{
    return captured;
}

int fake_keys_left(void)
{
    return queue_used - queue_next;
}

int fake_ran_out_of_keys(void)
{
    return keys_exhausted;
}

int fake_screen_has(const char *text)
{
    return strstr(captured, text) != NULL;
}

/* ---- the drawing calls the add-in makes --------------------------------- */

static void capture(const char *text)
{
    int length = (int)strlen(text);

    if (captured_used + length + 2 >= FAKE_CAPTURE_LEN)
        return;
    memcpy(captured + captured_used, text, (size_t)length);
    captured_used += length;
    captured[captured_used++] = '\n';
    captured[captured_used] = 0;
}

void dclear(int colour)
{
    (void)colour;
}

void drect(int x1, int y1, int x2, int y2, int colour)
{
    (void)x1; (void)y1; (void)x2; (void)y2; (void)colour;
}

void dtext(int x, int y, int fg, const char *text)
{
    (void)x; (void)y; (void)fg;
    capture(text);
}

void dtext_opt(int x, int y, int fg, int bg, int halign, int valign,
               const char *text, int size)
{
    (void)x; (void)y; (void)fg; (void)bg; (void)halign; (void)valign; (void)size;
    capture(text);
}

void dsize(const char *text, const font_t *font, int *width, int *height)
{
    (void)font;
    if (width != NULL)
        *width = 8 * (int)strlen(text);
    if (height != NULL)
        *height = 9;
}

void dupdate(void)
{
}

key_event_t getkey(void)
{
    key_event_t event;

    event.type = 1;
    event.shift = 0;
    event.alpha = 0;
    if (queue_next >= queue_used) {
        /* The screen asked for more input than the test provided. Rather than
         * spinning for ever, say EXIT and record that it happened. */
        keys_exhausted++;
        event.key = KEY_EXIT;
        if (keys_exhausted > 200) {
            fprintf(stderr, "fake_gint: a screen will not stop asking for keys\n");
            exit(2);
        }
        return event;
    }
    event.key = queue[queue_next++];
    return event;
}
