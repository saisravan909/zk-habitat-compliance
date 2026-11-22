package habitat.safety

default allow := false

# Enforces HAB-O2-001: scaled O2 pressure >= 195 (19.5 kPa * 10) when life_support is active
allow if {
    input.habitat_mode_active == 1
    input.o2_pressure >= 195
}

# Non-active mode does not trigger the life_support O2 lower bound
allow if {
    input.habitat_mode_active != 1
}
