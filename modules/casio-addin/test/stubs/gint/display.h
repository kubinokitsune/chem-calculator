/* A stand-in for gint's display.h, used only by the PC tests.
 *
 * It draws into a text buffer instead of the screen, so the tests can read
 * what the add-in would have shown. The real header is used when building
 * for the calculator.
 */
#ifndef STUB_GINT_DISPLAY_H
#define STUB_GINT_DISPLAY_H

#define DWIDTH  396
#define DHEIGHT 224

#define C_WHITE 0xffff
#define C_BLACK 0x0000
#define C_NONE  (-1)
#define C_RGB(r, g, b) (((r) << 11) | ((g) << 5) | (b))

enum {
    DTEXT_LEFT = 0, DTEXT_CENTER = 1, DTEXT_RIGHT = 2,
    DTEXT_TOP = 0, DTEXT_MIDDLE = 1, DTEXT_BOTTOM = 2
};

typedef struct font font_t;

void dclear(int colour);
void drect(int x1, int y1, int x2, int y2, int colour);
void dtext(int x, int y, int fg, const char *text);
void dtext_opt(int x, int y, int fg, int bg, int halign, int valign,
               const char *text, int size);
void dsize(const char *text, const font_t *font, int *width, int *height);
void dupdate(void);

#endif
