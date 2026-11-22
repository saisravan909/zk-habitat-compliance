# zk-habitat-compliance

Prototype open-source tool pipeline translating NASA Formal Requirements Elicitation Tool (FRET) requirements into range-checked Circom compliance circuits and runtime safety policy checks for deep-space habitat life-support scenarios.

## Repository Layout

- `fret-extension/templates/habitat_o2_requirement.json`: Single-requirement template (`HAB-O2-001`) with integer scaling and `bit_width` metadata.
- `fret-extension/templates/habitat_multi_requirements.json`: Multi-requirement test bundle (`HAB-O2-001`, `HAB-CO2-002`, `HAB-VALVE-003`) covering `>=`, `<=`, and `==` bounds.
- `fret-extension/fretish-to-zksnark/fret_to_circuit.py`: Python translator that sanitizes signal identifiers, binds condition guards via `IsEqual()`, enforces non-negative slack via `Num2Bits` range checks to prevent modular wraparound in finite-field arithmetic, and chains validity flags into `all_constraints_satisfied`.
- `circuits/habitat_o2_compliance_ranged.circom`: Deterministic single-requirement Circom circuit output.
- `circuits/habitat_multi_compliance.circom`: Deterministic multi-requirement Circom circuit output.
- `scripts/run_prototype_check.py`: Evaluates synthetic telemetry scenarios against the `HAB-O2-001` safety check.
- `.github/workflows/validate-translator.yml`: GitHub Actions CI verifying deterministic circuit generation via `diff -u` and running the synthetic telemetry check.

## Running the Prototype

Generate the single- and multi-requirement Circom circuits:

```bash
python fret-extension/fretish-to-zksnark/fret_to_circuit.py \
  --input fret-extension/templates/habitat_o2_requirement.json \
  --output /tmp/habitat_o2_compliance_ranged.circom

python fret-extension/fretish-to-zksnark/fret_to_circuit.py \
  --input fret-extension/templates/habitat_multi_requirements.json \
  --output /tmp/habitat_multi_compliance.circom
