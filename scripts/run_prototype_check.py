import json
from pathlib import Path


def evaluate_o2_policy(habitat_mode_active: int, o2_pressure: int, threshold: int = 195) -> dict:
    """Mirrors policies/habitat_safety.rego for quick synthetic telemetry checks."""
    if habitat_mode_active != 1:
        allowed = True
        reason = "habitat_mode inactive; life_support O2 lower bound not triggered"
        slack = 0
    else:
        slack = o2_pressure - threshold
        allowed = o2_pressure >= threshold
        reason = "O2 pressure satisfies threshold" if allowed else "VIOLATION: O2 pressure below threshold"

    return {
        "habitat_mode_active": habitat_mode_active,
        "o2_pressure": o2_pressure,
        "threshold": threshold,
        "slack_if_compliant": max(slack, 0),
        "policy_allow": allowed,
        "reason": reason,
    }


def main() -> None:
    synthetic_traces = [
        {"case": "nominal_life_support", "habitat_mode_active": 1, "o2_pressure": 208},
        {"case": "boundary_life_support", "habitat_mode_active": 1, "o2_pressure": 195},
        {"case": "hypoxia_violation", "habitat_mode_active": 1, "o2_pressure": 172},
        {"case": "standby_mode", "habitat_mode_active": 0, "o2_pressure": 150},
    ]

    results = []
    for trace in synthetic_traces:
        verdict = evaluate_o2_policy(
            habitat_mode_active=trace["habitat_mode_active"],
            o2_pressure=trace["o2_pressure"],
        )
        results.append({"case": trace["case"], **verdict})

    out_path = Path("benchmarks/synthetic_trace_results.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"results": results}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"results": results}, indent=2))


if __name__ == "__main__":
    main()
