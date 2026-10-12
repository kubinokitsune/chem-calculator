/* A stand-in for gint's rtc.h, used only by the PC tests: a clock that only
 * moves when the test says so (see fake_advance in fake_gint.h). */
#ifndef STUB_GINT_RTC_H
#define STUB_GINT_RTC_H

#include <stdint.h>

uint32_t rtc_ticks(void);        /* 128 ticks a second */

#endif
