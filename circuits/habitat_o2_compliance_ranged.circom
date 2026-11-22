pragma circom 2.1.6;

include "circomlib/circuits/bitify.circom";
include "circomlib/circuits/comparators.circom";

// Auto-generated range-checked compliance circuit from FRET export.

template HabitatComplianceCheck() {
    signal input habitat_mode_active;
    signal input o2_pressure;
    signal output all_constraints_satisfied;

    // Requirement HAB-O2-001: In habitat_mode life_support shall always satisfy o2_pressure >= 195
    // Bind habitat_mode_active == 1 via IsEqual comparator
    component HAB_O2_001_cond_eq = IsEqual();
    HAB_O2_001_cond_eq.in[0] <== habitat_mode_active;
    HAB_O2_001_cond_eq.in[1] <== 1;
    signal HAB_O2_001_cond_active;
    HAB_O2_001_cond_active <== HAB_O2_001_cond_eq.out;
    HAB_O2_001_cond_active * (1 - HAB_O2_001_cond_active) === 0;
    signal output HAB_O2_001_valid;
    signal input HAB_O2_001_slack_ge;
    // When active, target_var - threshold equals non-negative slack
    HAB_O2_001_cond_active * ((o2_pressure - 195) - HAB_O2_001_slack_ge) === 0;
    // Range check prevents modular wraparound over finite field
    component HAB_O2_001_range_ge = Num2Bits(16);
    HAB_O2_001_range_ge.in <== HAB_O2_001_slack_ge;
    HAB_O2_001_valid <== 1 - HAB_O2_001_cond_active * (1 - HAB_O2_001_cond_active);

    all_constraints_satisfied <== HAB_O2_001_valid;
}

component main = HabitatComplianceCheck();
