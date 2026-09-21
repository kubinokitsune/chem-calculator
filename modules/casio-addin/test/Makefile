# Builds and runs the core tests on a PC (no calculator toolchain needed).
# make's built-in default for CC is "cc", which is not always installed
ifeq ($(origin CC),default)
CC := gcc
endif
CFLAGS  ?= -std=c99 -Wall -Wextra -Werror -O1 -g
SOURCES  = test_core.c ../src/core/chem.c ../src/core/elements.c ../src/core/stoich.c ../src/core/solution.c ../src/core/balance.c ../src/core/energy.c

all: run

test_core: $(SOURCES) ../src/core/chem.h
	$(CC) $(CFLAGS) -o $@ $(SOURCES) -lm

run: test_core
	./test_core

clean:
	rm -f test_core

.PHONY: all run clean
