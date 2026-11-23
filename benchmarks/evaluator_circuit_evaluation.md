# Evaluator–Circuit Agreement, Assumptions, and Test Matrix

## Scope and Limitations
- **Supported Specifications**: Single-oxygen requirement (`HAB-O2-001`) and three-requirement ECLSS set (`HAB-O2-001`, `HAB-CO2-002`, `HAB-VALVE-003`)[cite: 5, 7].
- **Supported Constructs**: Operational mode equality guard (`IsEqual`), integer `>=`, `<=`, and `==` checks, scaled oxygen integer units (`195` represents `19.5 kPa`), and bounded telemetry values[cite: 5, 7].
- **Out of Scope**: Arbitrary FRETish clauses, multi-step temporal trace proofs ("always" across full histories), and live `circom` / `snarkjs` hardware proving benchmarks[cite: 5].
- **Provenance**: All telemetry values and test cases are synthetic; no flight telemetry or simulated hardware proving timings are used[cite: 5, 7].

## Assumptions and Enforcement Boundary

| Assumption | Documented Rule | Enforcement Boundary |
| :--- | :--- | :--- |
| Units | Oxygen integer scaled (`195` = `19.5 kPa`); `co2_ppm` in integer ppm[cite: 5, 7] | Assumed by evaluation / surrounding system |
| Integer domain | Valid minimum and maximum permitted bounds per signal | Circuit (`Num2Bits` slack) / surrounding system |
| Boolean values | Mode and valve indicators constrained to `{0, 1}` (`1` = active/locked, `0` = standby/unlocked)[cite: 7] | Circuit (`IsEqual` / boolean check) / surrounding system |
| Mode semantics | Requirement active only when `habitat_mode` equals target mode (`1` = `life_support`)[cite: 7] | Circuit (`IsEqual` mode guard) + policy runner |
| Arithmetic | Modular arithmetic in BN254 prime field $\mathbb{F}_p$ ($p \approx 2^{254}$) with non-negative slack witness $s_i$[cite: 7] | Enforced in circuit |
| Public claim | Policy compliance holds iff circuit constraints hold and output equals `1` | Enforced in circuit + verifier policy |
| Temporal scope | Single-sample evaluation; does not by itself prove multi-step trace "always" behavior | Assumed by evaluation |

**Direct-Witness vs. API Boundary**: Input checks at an API or runner boundary do not restrict a prover who supplies a circuit witness directly[cite: 7]. Domain or boolean bounds required for soundness must be enforced inside the R1CS constraints[cite: 7].

## Equivalence Criterion and Deterministic Test Matrix

For valid-domain synthetic inputs, evaluate agreement using:

$$\text{Python allows} \iff \text{Circuit admits a satisfying witness with compliance output } 1$$

Do not treat witness-generation success alone as equivalent to compliance when a circuit can output `0`[cite: 7].

| Case ID | Area / Scenario | Mode | Oxygen | CO2 | Valve | Expected Outcome | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `DET-01` | Oxygen nominal | `1` | `208` | `800` | `1` | Compliant (`true`) | Matches `nominal_life_support` (`slack = 13`)[cite: 7] |
| `DET-02` | Oxygen boundary low | `1` | `194` | `800` | `1` | Non-compliant (`false`) | Just below `195` threshold[cite: 7] |
| `DET-03` | Oxygen boundary exact | `1` | `195` | `800` | `1` | Compliant (`true`) | Matches `boundary_life_support` (`slack = 0`)[cite: 7] |
| `DET-04` | Oxygen boundary high | `1` | `196` | `800` | `1` | Compliant (`true`) | One unit above `195` threshold[cite: 7] |
| `DET-05` | CO2 boundary low | `1` | `205` | `3999` | `1` | Compliant (`true`) | One unit below `4000` ceiling[cite: 7] |
| `DET-06` | CO2 boundary exact | `1` | `205` | `4000` | `1` | Compliant (`true`) | Exact `4000` ceiling[cite: 7] |
| `DET-07` | CO2 boundary high | `1` | `205` | `4001` | `1` | Non-compliant (`false`) | Exceeds `4000` ceiling[cite: 7] |
| `DET-08` | Valve state | `1` | `205` | `900` | `1` / `0` | `1`: Compliant / `0`: Non-compliant | Tests `relief_valve_locked == 1`[cite: 7] |
| `DET-09` | Combined failure | `1` | `172` | `4500` | `0` | Non-compliant (`false`) | Simultaneous hypoxia, high CO2, and unlocked valve[cite: 7] |
| `DET-10` | Inactive mode | `0` | `150` | `5000` | `0` | Compliant, guard inactive | Matches `standby_mode` (`IsEqual` guard inactive)[cite: 7] |
| `DET-11` | Domain edges | `1` | Min / Max | Min / Max | `0` / `1` | Per policy rule | Checks declared domain endpoints |
| `DET-12` | Invalid inputs | `1` | Negative / non-int / missing | Negative / non-int / missing | Non-boolean (`2`, `"yes"`) | Rejected / invalid input | Tested at input/schema boundary |

## Seeded Synthetic Evaluation Log Schema

Record every seeded run within declared valid domains and preserve every mismatch without filtering failures out:

```json
{
  "seed": 20270111,
  "num_cases": 250,
  "spec_id": "habitat_multi_compliance",
  "telemetry_provenance": "synthetic_only",
  "agreements": 250,
  "mismatches": []
}
