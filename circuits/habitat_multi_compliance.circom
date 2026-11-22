pragma circom 2.1.6;

include "circomlib/circuits/bitify.circom";
include "circomlib/circuits/comparators.circom";

// Auto-generated range-checked compliance circuit from FRET export.

template HabitatComplianceCheck() {
    signal input co2_ppm;
    signal input habitat_mode_active;
    signal input o2_pressure;
    signal input relief_valve_locked;
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
    // Requirement HAB-CO2-002: In habitat_mode life_support shall always satisfy co2_ppm <= 4000
    // Bind habitat_mode_active == 1 via IsEqual comparator
    component HAB_CO2_002_cond_eq = IsEqual();
    HAB_CO2_002_cond_eq.in[0] <== habitat_mode_active;
    HAB_CO2_002_cond_eq.in[1] <== 1;
    signal HAB_CO2_002_cond_active;
    HAB_CO2_002_cond_active <== HAB_CO2_002_cond_eq.out;
    HAB_CO2_002_cond_active * (1 - HAB_CO2_002_cond_active) === 0;
    signal output HAB_CO2_002_valid;
    signal input HAB_CO2_002_slack_le;
    // When active, threshold - target_var equals non-negative slack
    HAB_CO2_002_cond_active * ((4000 - co2_ppm) - HAB_CO2_002_slack_le) === 0;
    component HAB_CO2_002_range_le = Num2Bits(16);
    HAB_CO2_002_range_le.in <== HAB_CO2_002_slack_le;
    HAB_CO2_002_valid <== 1 - HAB_CO2_002_cond_active * (1 - HAB_CO2_002_cond_active);
    // Requirement HAB-VALVE-003: In habitat_mode life_support shall always satisfy relief_valve_locked == 1
    // Bind habitat_mode_active == 1 via IsEqual comparator
    component HAB_VALVE_003_cond_eq = IsEqual();
    HAB_VALVE_003_cond_eq.in[0] <== habitat_mode_active;
    HAB_VALVE_003_cond_eq.in[1] <== 1;
    signal HAB_VALVE_003_cond_active;
    HAB_VALVE_003_cond_active <== HAB_VALVE_003_cond_eq.out;
    HAB_VALVE_003_cond_active * (1 - HAB_VALVE_003_cond_active) === 0;
    signal output HAB_VALVE_003_valid;
    // When active, target_var must equal threshold
    HAB_VALVE_003_cond_active * (relief_valve_locked - 1) === 0;
    HAB_VALVE_003_valid <== 1 - HAB_VALVE_003_cond_active * (1 - HAB_VALVE_003_cond_active);

    signal req_acc_0;
    req_acc_0 <== HAB_O2_001_valid * HAB_CO2_002_valid;
    signal req_acc_1;
    req_acc_1 <== req_acc_0 * HAB_VALVE_003_valid;
    all_constraints_satisfied <== req_acc_1;
}

component main = HabitatComplianceCheck();
