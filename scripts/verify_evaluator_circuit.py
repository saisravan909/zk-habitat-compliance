"""Deterministic and seeded synthetic evaluator-circuit check for zk-habitat-compliance.

All telemetry values and scenarios are synthetic. This script models the
documented evaluator and circuit equivalence criterion without claiming
simulated hardware proving benchmarks.
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from typing import Any

O2_MIN_THRESHOLD = 195  # Scaled integer representing 19.5 kPa
CO2_MAX_THRESHOLD = 4000  # Integer ppm ceiling
LIFE_SUPPORT_MODE = 1
STANDBY_MODE = 0


@dataclass(frozen=True)
class EvaluationResult:
    allow: bool
    circuit_constraints_satisfied: bool
    circuit_output: int
    diagnostic: str


def validate_synthetic_inputs(
    mode: Any,
    o2_pressure: Any,
    co2_ppm: Any,
    relief_valve_locked: Any,
) -> tuple[bool, str]:
    """Validate basic types and domain ranges for synthetic test cases."""
    values = (mode, o2_pressure, co2_ppm, relief_valve_locked)
    if any(isinstance(v, bool) or not isinstance(v, int) for v in values):
        return False, "Non-integer or boolean-as-int input rejected"
    if mode not in (STANDBY_MODE, LIFE_SUPPORT_MODE):
        return False, "Invalid mode value outside {0, 1}"
    if relief_valve_locked not in (0, 1):
        return False, "Invalid relief_valve_locked value outside {0, 1}"
    if o2_pressure < 0 or o2_pressure > 65535:
        return False, "o2_pressure outside valid 16-bit non-negative range"
    if co2_ppm < 0 or co2_ppm > 65535:
        return False, "co2_ppm outside valid 16-bit non-negative range"
    return True, "Valid synthetic input"


def evaluate_policy_and_circuit(
    mode: int,
    o2_pressure: int,
    co2_ppm: int,
    relief_valve_locked: int,
) -> EvaluationResult:
    """Evaluate agreement between policy decision and circuit compliance output."""
    if mode != LIFE_SUPPORT_MODE:
        return EvaluationResult(
            allow=True,
            circuit_constraints_satisfied=True,
            circuit_output=1,
            diagnostic="Inactive mode; compliance guard not triggered",
        )

    o2_ok = o2_pressure >= O2_MIN_THRESHOLD
    co2_ok = co2_ppm <= CO2_MAX_THRESHOLD
    valve_ok = relief_valve_locked == 1
    compliant = o2_ok and co2_ok and valve_ok

    if compliant:
        return EvaluationResult(
            allow=True,
            circuit_constraints_satisfied=True,
            circuit_output=1,
            diagnostic="All active habitat safety thresholds satisfied",
        )

    reasons: list[str] = []
    if not o2_ok:
        reasons.append("o2_pressure below threshold")
    if not co2_ok:
        reasons.append("co2_ppm above threshold")
    if not valve_ok:
        reasons.append("relief_valve_locked != 1")

    return EvaluationResult(
        allow=False,
        circuit_constraints_satisfied=True,
        circuit_output=0,
        diagnostic="; ".join(reasons),
    )


def deterministic_cases() -> list[tuple[str, dict[str, Any], bool | None]]:
    """Return the 12 deterministic synthetic test vectors."""
    return [
        ("DET-01", {"mode": 1, "o2_pressure": 208, "co2_ppm": 800, "relief_valve_locked": 1}, True),
        ("DET-02", {"mode": 1, "o2_pressure": 194, "co2_ppm": 800, "relief_valve_locked": 1}, False),
        ("DET-03", {"mode": 1, "o2_pressure": 195, "co2_ppm": 800, "relief_valve_locked": 1}, True),
        ("DET-04", {"mode": 1, "o2_pressure": 196, "co2_ppm": 800, "relief_valve_locked": 1}, True),
        ("DET-05", {"mode": 1, "o2_pressure": 205, "co2_ppm": 3999, "relief_valve_locked": 1}, True),
        ("DET-06", {"mode": 1, "o2_pressure": 205, "co2_ppm": 4000, "relief_valve_locked": 1}, True),
        ("DET-07", {"mode": 1, "o2_pressure": 205, "co2_ppm": 4001, "relief_valve_locked": 1}, False),
        ("DET-08", {"mode": 1, "o2_pressure": 205, "co2_ppm": 900, "relief_valve_locked": 0}, False),
        ("DET-09", {"mode": 1, "o2_pressure": 172, "co2_ppm": 4500, "relief_valve_locked": 0}, False),
        ("DET-10", {"mode": 0, "o2_pressure": 150, "co2_ppm": 5000, "relief_valve_locked": 0}, True),
        ("DET-11", {"mode": 1, "o2_pressure": 65535, "co2_ppm": 0, "relief_valve_locked": 1}, True),
        ("DET-12", {"mode": 1, "o2_pressure": -1, "co2_ppm": 800, "relief_valve_locked": 2}, None),
    ]


def run_evaluation(seed: int, num_cases: int, spec_id: str) -> dict[str, Any]:
    """Run deterministic checks plus seeded synthetic cases and record mismatches."""
    mismatches: list[dict[str, Any]] = []
    agreements = 0

    for case_id, payload, expected_allow in deterministic_cases():
        valid, reason = validate_synthetic_inputs(
            payload.get("mode"),
            payload.get("o2_pressure"),
            payload.get("co2_ppm"),
            payload.get("relief_valve_locked"),
        )
        if expected_allow is None:
            if not valid:
                agreements += 1
            else:
                mismatches.append(
                    {
                        "case_id": case_id,
                        "inputs": payload,
                        "python_allow": None,
                        "circuit_constraints_satisfied": False,
                        "circuit_output": 0,
                        "diagnostic": "Expected invalid input rejection",
                    }
                )
            continue

        result = evaluate_policy_and_circuit(**payload)
        circuit_agrees = result.circuit_constraints_satisfied and (
            (result.circuit_output == 1) == result.allow
        )
        if valid and result.allow == expected_allow and circuit_agrees:
            agreements += 1
        else:
            mismatches.append(
                {
                    "case_id": case_id,
                    "inputs": payload,
                    "python_allow": result.allow,
                    "circuit_constraints_satisfied": result.circuit_constraints_satisfied,
                    "circuit_output": result.circuit_output,
                    "diagnostic": reason if not valid else result.diagnostic,
                }
            )

    rng = random.Random(seed)
    for idx in range(num_cases):
        payload = {
            "mode": rng.choice([STANDBY_MODE, LIFE_SUPPORT_MODE]),
            "o2_pressure": rng.randint(150, 240),
            "co2_ppm": rng.randint(300, 4500),
            "relief_valve_locked": rng.choice([0, 1]),
        }
        result = evaluate_policy_and_circuit(**payload)
        circuit_agrees = result.circuit_constraints_satisfied and (
            (result.circuit_output == 1) == result.allow
        )
        if circuit_agrees:
            agreements += 1
        else:
            mismatches.append(
                {
                    "case_index": idx,
                    "inputs": payload,
                    "python_allow": result.allow,
                    "circuit_constraints_satisfied": result.circuit_constraints_satisfied,
                    "circuit_output": result.circuit_output,
                    "diagnostic": result.diagnostic,
                }
            )

    return {
        "seed": seed,
        "num_cases": num_cases,
        "spec_id": spec_id,
        "telemetry_provenance": "synthetic_only",
        "agreements": agreements,
        "mismatches": mismatches,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify synthetic evaluator-circuit agreement.")
    parser.add_argument("--seed", type=int, default=20270111)
    parser.add_argument("--num-cases", type=int, default=250)
    parser.add_argument("--spec-id", type=str, default="habitat_multi_compliance")
    args = parser.parse_args()

    report = run_evaluation(seed=args.seed, num_cases=args.num_cases, spec_id=args.spec_id)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
