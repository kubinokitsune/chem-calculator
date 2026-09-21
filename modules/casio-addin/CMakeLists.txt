# ChemCalc for the Casio fx-CG50.
# Configure and build with:  fxsdk build-cg
# The result is ChemCalc.g3a, which is copied to the calculator's storage.

cmake_minimum_required(VERSION 3.15)
project(ChemCalc C)

include(GenerateG3A)
include(Fxconv)
find_package(Gint 2.9 REQUIRED)

set(SOURCES
  src/main.c
  src/ui/ui.c
  src/core/chem.c
  src/core/elements.c
  src/core/stoich.c
  src/core/solution.c
  src/core/balance.c
  src/core/energy.c
  src/core/tools.c
  src/screens/common.c
  src/screens/ptable.c
  src/screens/stoich_screen.c
  src/screens/balance_screen.c
  src/screens/gas_screen.c
  src/screens/aqua_screen.c
  src/screens/energy_screen.c
  src/screens/tools_screen.c
)

add_executable(chemcalc ${SOURCES})
target_compile_options(chemcalc PRIVATE -Wall -Wextra -Os -std=c99)
target_link_libraries(chemcalc Gint::Gint)

if("${FXSDK_PLATFORM_LONG}" STREQUAL fxCG50)
  generate_g3a(TARGET chemcalc OUTPUT "ChemCalc.g3a"
    NAME "ChemCalc" ICONS assets-cg/icon-uns.png assets-cg/icon-sel.png)

  # The calculator makes itself a main-memory (MCS) directory named after the
  # add-in's INTERNAL name the first time it is started. generate_g3a leaves
  # that name empty, and an add-in without one can fail to start again after
  # its first run. Casio's convention is a short name beginning with '@'.
  # --edit rewrites the header but leaves the checksums as they were, so the
  # file has to be repaired afterwards or the calculator rejects it.
  add_custom_command(TARGET chemcalc POST_BUILD
    COMMAND fxgxa --edit "${CMAKE_CURRENT_SOURCE_DIR}/ChemCalc.g3a"
                  --internal=@CHEMCAL
    COMMAND fxgxa --repair "${CMAKE_CURRENT_SOURCE_DIR}/ChemCalc.g3a"
    COMMENT "Setting the internal name to @CHEMCAL and repairing checksums")
endif()
