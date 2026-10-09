/* battery.c - see battery.h.
 *
 * gint takes over the whole screen, so the OS's status bar (and its battery
 * icon) never shows; this reads the same battery the OS does.
 *
 * Two OS syscalls (WikiPrizm, prizm.cemetech.net/Syscalls/):
 *   0x1186  int GetMainBatteryVoltage(int one)  - the voltage in centivolts
 *           (5.14 V reads 514); the argument must be 1.
 *   0x12D5  int GetBatteryType(void)  - the setting the OS itself uses to
 *           estimate the level: 1 alkaline, 2 Ni-MH (0 on the emulator).
 * Neither is wrapped by gint, and syscalls are only safe in the OS's world,
 * so they run inside gint_world_switch(), which takes a moment: hence the
 * 10-second cache, so that key handling never waits on it.
 */

#include "battery.h"

#include <gint/gint.h>
#include <gint/rtc.h>

#include <stdint.h>

#define REFRESH_TICKS (10 * 128)        /* rtc_ticks() counts 128 a second */

#ifdef __sh__
/* Casio's syscall convention: r0 is the number and r4... the arguments, called
 * through the entry point at 0x80020070 (the same as gint's own wrappers). */
static int os_syscall(int number, int arg)
{
    register int r0 __asm__("r0") = number;
    register int r4 __asm__("r4") = arg;

    __asm__ volatile("jsr @%2\n\tnop"
                     : "+r"(r0), "+r"(r4)
                     : "r"(0x80020070)
                     : "pr", "r1", "r2", "r3", "r5", "r6", "r7", "mach", "macl", "t", "memory");
    return r0;
}
#else
/* the PC tests answer for the OS */
int fake_os_syscall(int number, int arg);
#define os_syscall fake_os_syscall
#endif

/* No cell chemistry has a documented voltage-to-bars table, and Casio does not
 * publish theirs, so these are approximate, from typical AAA discharge curves
 * for 4 cells in series: an alkaline cell starts near 1.5 V and is flat to
 * about 1.3 V, then falls to about 1.1 V when nearly empty; a Ni-MH cell sits
 * near 1.2 V for most of its charge and drops below 1.1 V at the end. Each row
 * is the centivolts a reading must reach for 1, 2 and 3 bars. */
static const int bars_need[2][3] = {
    {450, 490, 540},        /* alkaline: 1.125, 1.225, 1.35 V a cell */
    {440, 460, 480},        /* Ni-MH:    1.10,  1.15,  1.20 V a cell */
};

int battery_bars(int centivolts, int type)
{
    const int *need = bars_need[type == 2];

    return (centivolts >= need[0]) + (centivolts >= need[1]) + (centivolts >= need[2]);
}

static int os_centivolts, os_type;

/* Runs in the OS's world; the answer is left in the statics for the caller. */
static int read_os(int unused)
{
    (void)unused;
    os_type = os_syscall(0x12D5, 0);
    os_centivolts = os_syscall(0x1186, 1);
    return 0;
}

int battery_level(void)
{
    static uint32_t read_at;
    static int bars, have;
    uint32_t now = rtc_ticks();

    /* unsigned, so it also refreshes when the clock wraps at midnight */
    if (!have || now - read_at >= REFRESH_TICKS) {
        gint_world_switch(GINT_CALL(read_os, 0));
        bars = os_centivolts > 0 ? battery_bars(os_centivolts, os_type) : -1;
        read_at = now;
        have = 1;
    }
    return bars;
}
