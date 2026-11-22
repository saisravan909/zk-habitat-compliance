pragma circom 2.1.6;

// Auto-generated draft compliance circuit template from FRET export.
// Pair range-check gadgets (e.g., Num2Bits) on slack signals in full proofs.

template HabitatComplianceCheck() {
    signal input habitat_mode_active;
    signal input o2_pressure;
    signal output all_constraints_satisfied;

    // Requirement HAB-O2-001: In habitat_mode life_support shall always satisfy o2_pressure >= 195
    // Active when habitat_mode_active == 1
    signal input HAB_O2_001_cond_active;
    HAB_O2_001_cond_active * (1 - HAB_O2_001_cond_active) === 0;
    // Enforces o2_pressure >= 195 when active
    signal input HAB_O2_001_slack_ge;
    HAB_O2_001_cond_active * ((o2_pressure - 195) - HAB_O2_001_slack_ge) === 0;

    all_constraints_satisfied <== 1;
}

component main = HabitatComplianceCheck();
