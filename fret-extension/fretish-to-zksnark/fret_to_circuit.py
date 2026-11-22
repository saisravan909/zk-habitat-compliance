import argparse
import json
import re
from pathlib import Path


def sanitize_identifier(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", name.strip())
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"sig_{cleaned}"
    return cleaned


def validate_bit_width(bits: int) -> int:
    if not isinstance(bits, int) or bits < 1 or bits > 252:
        raise ValueError(f"Invalid bit_width for BN254/finite-field range check: {bits}")
    return bits


def build_requirement_block(req: dict, default_bits: int) -> tuple[list[str], list[str], list[str]]:
    req_id = sanitize_identifier(req.get("reqid", "REQ_001"))
    cond_var = sanitize_identifier(req["condition_var"])
    cond_op = req.get("condition_op", "==")
    cond_val = int(req["condition_value"])

    target_var = sanitize_identifier(req["target_var"])
    target_op = req.get("target_op", ">=")
    target_val = int(req["target_value"])
    bits = validate_bit_width(int(req.get("bit_width", default_bits)))

    if cond_op != "==":
        raise ValueError(f"Unsupported condition operator: {cond_op}")

    input_vars = [cond_var, target_var]
    eq_cmp = f"{req_id}_cond_eq"
    cond_active = f"{req_id}_cond_active"
    valid_flag = f"{req_id}_valid"

    lines = [
        f"    // Requirement {req.get('reqid')}: {req.get('fretish', '')}",
        f"    // Bind {cond_var} == {cond_val} via IsEqual comparator",
        f"    component {eq_cmp} = IsEqual();",
        f"    {eq_cmp}.in[0] <== {cond_var};",
        f"    {eq_cmp}.in[1] <== {cond_val};",
        f"    signal {cond_active};",
        f"    {cond_active} <== {eq_cmp}.out;",
        f"    {cond_active} * (1 - {cond_active}) === 0;",
        f"    signal output {valid_flag};",
    ]

    if target_op == ">=":
        slack_var = f"{req_id}_slack_ge"
        range_cmp = f"{req_id}_range_ge"
        lines.extend([
            f"    signal input {slack_var};",
            f"    // When active, target_var - threshold equals non-negative slack",
            f"    {cond_active} * (({target_var} - {target_val}) - {slack_var}) === 0;",
            f"    // Range check prevents modular wraparound over finite field",
            f"    component {range_cmp} = Num2Bits({bits});",
            f"    {range_cmp}.in <== {slack_var};",
            f"    {valid_flag} <== 1 - {cond_active} * (1 - {cond_active});",
        ])
    elif target_op == "<=":
        slack_var = f"{req_id}_slack_le"
        range_cmp = f"{req_id}_range_le"
        lines.extend([
            f"    signal input {slack_var};",
            f"    // When active, threshold - target_var equals non-negative slack",
            f"    {cond_active} * (({target_val} - {target_var}) - {slack_var}) === 0;",
            f"    component {range_cmp} = Num2Bits({bits});",
            f"    {range_cmp}.in <== {slack_var};",
            f"    {valid_flag} <== 1 - {cond_active} * (1 - {cond_active});",
        ])
    elif target_op == "==":
        lines.extend([
            f"    // When active, target_var must equal threshold",
            f"    {cond_active} * ({target_var} - {target_val}) === 0;",
            f"    {valid_flag} <== 1 - {cond_active} * (1 - {cond_active});",
        ])
    else:
        raise ValueError(f"Unsupported target operator: {target_op}")

    return input_vars, [valid_flag], lines


def translate_requirements(input_path: Path, output_path: Path) -> str:
    data = json.loads(input_path.read_text(encoding="utf-8"))
    requirements = data.get("requirements", [])
    if not requirements:
        raise ValueError("No requirements found in input JSON.")

    default_bits = validate_bit_width(int(data.get("field_bit_width", 16)))

    all_inputs: set[str] = set()
    all_valid_signals: list[str] = []
    body_blocks: list[str] = []

    for req in requirements:
        req_inputs, req_valid, lines = build_requirement_block(req, default_bits)
        all_inputs.update(req_inputs)
        all_valid_signals.extend(req_valid)
        body_blocks.append("\n".join(lines))

    template = [
        "pragma circom 2.1.6;",
        "",
        'include "circomlib/circuits/bitify.circom";',
        'include "circomlib/circuits/comparators.circom";',
        "",
        "// Auto-generated range-checked compliance circuit from FRET export.",
        "",
        "template HabitatComplianceCheck() {",
    ]
    for sig in sorted(all_inputs):
        template.append(f"    signal input {sig};")
    template.append("    signal output all_constraints_satisfied;")
    template.append("")
    template.extend(body_blocks)
    template.append("")

    if len(all_valid_signals) == 1:
        template.append(f"    all_constraints_satisfied <== {all_valid_signals[0]};")
    else:
        acc_var = "req_acc_0"
        template.append(f"    signal {acc_var};")
        template.append(f"    {acc_var} <== {all_valid_signals[0]} * {all_valid_signals[1]};")
        for idx in range(2, len(all_valid_signals)):
            prev_acc = f"req_acc_{idx - 2}"
            cur_acc = f"req_acc_{idx - 1}"
            template.append(f"    signal {cur_acc};")
            template.append(f"    {cur_acc} <== {prev_acc} * {all_valid_signals[idx]};")
        template.append(f"    all_constraints_satisfied <== req_acc_{len(all_valid_signals) - 2};")

    template.append("}")
    template.append("")
    template.append("component main = HabitatComplianceCheck();")

    rendered = "\n".join(template) + "\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    return rendered


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Translate FRET JSON requirements into a range-checked ZK circuit."
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
        default=Path("circuits/habitat_o2_compliance_ranged.circom"),
        help="Destination path for generated circuit template",
    )
    args = parser.parse_args()
    translate_requirements(args.input, args.output)


if __name__ == "__main__":
    main()
