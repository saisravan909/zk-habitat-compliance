import argparse
import json
import re
from pathlib import Path


def sanitize_identifier(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", name.strip())
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"sig_{cleaned}"
    return cleaned


def build_constraint_lines(req: dict) -> tuple[list[str], list[str]]:
    req_id = sanitize_identifier(req.get("reqid", "REQ_001"))
    cond_var = sanitize_identifier(req["condition_var"])
    cond_op = req.get("condition_op", "==")
    cond_val = int(req["condition_value"])

    target_var = sanitize_identifier(req["target_var"])
    target_op = req.get("target_op", ">=")
    target_val = int(req["target_value"])

    signals = sorted({cond_var, target_var, f"{req_id}_compliant"})
    lines = [f"    // Requirement {req.get('reqid')}: {req.get('fretish', '')}"]

    if cond_op != "==":
        raise ValueError(f"Unsupported condition operator: {cond_op}")

    # condition_met is 1 when cond_var == cond_val, else 0 (requires helper in full circuit)
    cond_helper = f"{req_id}_cond_active"
    signals.append(cond_helper)
    lines.append(f"    // Active when {cond_var} == {cond_val}")
    lines.append(f"    signal input {cond_helper};")
    lines.append(f"    {cond_helper} * (1 - {cond_helper}) === 0;")

    if target_op == ">=":
        diff_sig = f"{req_id}_slack_ge"
        signals.append(diff_sig)
        lines.append(f"    // Enforces {target_var} >= {target_val} when active")
        lines.append(f"    signal input {diff_sig};")
        lines.append(
            f"    {cond_helper} * (({target_var} - {target_val}) - {diff_sig}) === 0;"
        )
    elif target_op == "<=":
        diff_sig = f"{req_id}_slack_le"
        signals.append(diff_sig)
        lines.append(f"    // Enforces {target_var} <= {target_val} when active")
        lines.append(f"    signal input {diff_sig};")
        lines.append(
            f"    {cond_helper} * (({target_val} - {target_var}) - {diff_sig}) === 0;"
        )
    elif target_op == "==":
        lines.append(f"    // Enforces {target_var} == {target_val} when active")
        lines.append(f"    {cond_helper} * ({target_var} - {target_val}) === 0;")
    else:
        raise ValueError(f"Unsupported target operator: {target_op}")

    return signals, lines


def translate_requirements(input_path: Path, output_path: Path) -> str:
    data = json.loads(input_path.read_text(encoding="utf-8"))
    requirements = data.get("requirements", [])
    if not requirements:
        raise ValueError("No requirements found in input JSON.")

    all_signals: set[str] = set()
    body_blocks: list[str] = []

    for req in requirements:
        sigs, lines = build_constraint_lines(req)
        all_signals.update(sigs)
        body_blocks.append("\n".join(lines))

    input_signals = sorted(
        s for s in all_signals if not s.endswith("_compliant") and "_slack_" not in s and "_cond_active" not in s
    )

    template = [
        "pragma circom 2.1.6;",
        "",
        "// Auto-generated draft compliance circuit template from FRET export.",
        "// Pair range-check gadgets (e.g., Num2Bits) on slack signals in full proofs.",
        "",
        "template HabitatComplianceCheck() {",
    ]
    for sig in input_signals:
        template.append(f"    signal input {sig};")
    template.append("    signal output all_constraints_satisfied;")
    template.append("")
    template.extend(body_blocks)
    template.append("")
    template.append("    all_constraints_satisfied <== 1;")
    template.append("}")
    template.append("")
    template.append("component main = HabitatComplianceCheck();")

    rendered = "\n".join(template) + "\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    return rendered


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Translate FRET JSON requirements into a draft ZK circuit template."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("fret-extension/templates/habitat_o2_requirement.json"),
        help="Path to FRET JSON requirement export",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("circuits/habitat_o2_compliance_draft.circom"),
        help="Destination path for generated circuit template",
    )
    args = parser.parse_args()
    translate_requirements(args.input, args.output)


if __name__ == "__main__":
    main()
