/* battery.c - see battery.h.
 *
 * gint takes over the whole screen, so the OS's status bar (and its battery
 * icon) never shows. There is no documented syscall for the battery *level*
 * the OS draws, and the voltage syscalls (0x1186 GetMainBatteryVoltage,
 * 0x12D5 GetBatteryType) give only a raw reading whose scale and thresholds
 * the OS keeps to itself, so a guess from them disagreed with the real icon.
 * Instead the OS draws its own icon, and this copies the pixels:
 *
 * Inside gint_world_switch() (syscalls are only safe in the OS's world), with
 * WikiPrizm's syscalls (prizm.cemetech.net/Syscalls/):
 *   0x01E6  GetVRAMAddress           - the OS's 384 x 216 RGB565 VRAM
 *   0x02B7  EnableStatusArea(opt)    - 0 enables, 3 disables
 *   0x02B8  DefineStatusAreaFlags(mode, flags, 0, 0) - mode 3 sets the icons
 *           shown (SAF_BATTERY = 1), mode 1 puts back the default
 *   0x1D81  DisplayStatusArea()      - draws the status area to that VRAM
 * The status area is drawn twice, without and with the battery; the pixels
 * that differ are the OS's battery icon, wherever and however it draws it.
 * If none differ, the OS drew nothing and no icon is shown, rather than a
 * made-up one. The OS draws into its VRAM, not gint's, so nothing of ours is
 * disturbed; the world switch takes a moment, hence the 30-second cache, so
 * that key handling never waits on it.
 *
 * ponytail: unverified on hardware here. The OS may keep its battery level
 * from when the add-in started rather than re-measure it while we run.
 */

#include "battery.h"

#include <gint/display.h>
#include <gint/gint.h>
#include <gint/rtc.h>

#include <stdint.h>

#define REFRESH_TICKS (30 * 128)        /* rtc_ticks() counts 128 a second */

#ifdef __sh__
/* Casio's syscall convention: r0 is the number and r4-r7 the arguments, called
 * through the entry point at 0x80020070 (the same as gint's own wrappers). */
static uintptr_t os_syscall(int number, uintptr_t a, uintptr_t b, uintptr_t c, uintptr_t d)
{
    register int r0 __asm__("r0") = number;
    register uintptr_t r4 __asm__("r4") = a;
    register uintptr_t r5 __asm__("r5") = b;
    register uintptr_t r6 __asm__("r6") = c;
    register uintptr_t r7 __asm__("r7") = d;

    __asm__ volatile("jsr @%5\n\tnop"
                     : "+r"(r0), "+r"(r4), "+r"(r5), "+r"(r6), "+r"(r7)
                     : "r"(0x80020070)
                     : "pr", "r1", "r2", "r3", "mach", "macl", "t", "memory");
    return (uintptr_t)r0;
}
#else
/* the PC tests answer for the OS */
uintptr_t fake_os_syscall(int number, uintptr_t a, uintptr_t b, uintptr_t c, uintptr_t d);
#define os_syscall fake_os_syscall
#endif

#define OS_WIDTH   384          /* the OS's VRAM: 384 x 216, 16 bits a pixel */
#define OS_LEFT    6            /* it sits 6 px in from the left of gint's screen */
#define SCAN_W     64           /* the part of the status area searched: the left */
#define SCAN_H     24           /* its 24 rows */
#define MAX_ICON_W 40           /* wider than this is not a battery icon */

/* The OS's icon: the picture of the differing pixels (the rest white, as the
 * strip is) in the box gx, gy, gw x gh of the OS's area; gw is 0 if it drew none. */
static uint16_t shot[SCAN_H][SCAN_W];
static int gx, gy, gw, gh;

/* Runs in the OS's world; the picture is left in the statics for the caller. */
static int read_os(int unused)
{
    const uint16_t *vram = (const uint16_t *)os_syscall(0x1E6, 0, 0, 0, 0);
    int x, y, x0 = SCAN_W, y0 = SCAN_H, x1 = -1, y1 = -1;

    (void)unused;
    os_syscall(0x2B7, 0, 0, 0, 0);                      /* enable the status area */
    os_syscall(0x2B8, 3, 0, 0, 0);                      /* no icons: the bare bar */
    os_syscall(0x1D81, 0, 0, 0, 0);
    for (y = 0; y < SCAN_H; y++)
        for (x = 0; x < SCAN_W; x++)
            shot[y][x] = vram[y * OS_WIDTH + x];

    os_syscall(0x2B8, 3, 1, 0, 0);                      /* the battery only */
    os_syscall(0x1D81, 0, 0, 0, 0);
    for (y = 0; y < SCAN_H; y++)
        for (x = 0; x < SCAN_W; x++) {
            uint16_t now = vram[y * OS_WIDTH + x];

            if (now == shot[y][x]) {
                shot[y][x] = 0xFFFF;
                continue;
            }
            shot[y][x] = now;
            x0 = x < x0 ? x : x0;
            y0 = y < y0 ? y : y0;
            x1 = x > x1 ? x : x1;
            y1 = y > y1 ? y : y1;
        }
    gx = x0;
    gy = y0;
    gw = x1 - x0 + 1;
    gh = y1 - y0 + 1;
    if (x1 < 0 || gw > MAX_ICON_W)
        gw = 0;

    os_syscall(0x2B8, 1, 0, 0, 0);                      /* leave the OS as found */
    os_syscall(0x2B7, 3, 0, 0, 0);
    return 0;
}

int battery_draw(void)
{
    static uint32_t read_at;
    static int have;
    uint32_t now = rtc_ticks();
    int x, y;

    /* unsigned, so it also refreshes when the clock wraps at midnight */
    if (!have || now - read_at >= REFRESH_TICKS) {
        gint_world_switch(GINT_CALL(read_os, 0));
        read_at = now;
        have = 1;
    }
    for (y = 0; y < gh && gw > 0; y++)
        for (x = 0; x < gw; x++)
            if (shot[gy + y][gx + x] != 0xFFFF)
                dpixel(OS_LEFT + gx + x, gy + y, shot[gy + y][gx + x]);
    return gw > 0;
}
