# zk-habitat-compliance

[![CI Status](https://img.shields.io/github/actions/workflow/status/saisravan909/zk-habitat-compliance/validate-translator.yml?label=Validate%20FRET-to-Circuit%20Tool%20Prototype)](https://github.com/saisravan909/zk-habitat-compliance/actions)
[![Target Venue](https://img.shields.io/badge/NFM%202027-Tool%20Paper%20(LNCS)-1f4e78)](#nfm-2027-manuscript)
[![Circuit Language](https://img.shields.io/badge/Circom-2.1.6-2b5b84)](#repository-layout)
[![Requirements](https://img.shields.io/badge/NASA%20FRET-FRETish%20to%20R1CS-0b3d91)](#overview)
[![License](https://img.shields.io/badge/License-Open%20Source-3b6e8c)](#authors-and-attribution)

**From FRET to Range-Checked Zero-Knowledge Proofs: Verifiable Safety Envelopes for Autonomous Deep-Space Habitats**

An open-source formal-methods and compliance pipeline that translates structured NASA Formal Requirements Elicitation Tool (FRET) safety specifications into range-checked Circom 2.1.6 circuits, runtime policy checks, and deterministic CI verification.

---

## Overview

Autonomous habitats and bandwidth-constrained deep-space life-support controllers must enforce strict safety envelopes during uncrewed operations and high-latency communication blackouts. Streaming complete raw sensor histories over constrained links is often impractical, whereas unverified status reports lack mathematical assurance.

`zk-habitat-compliance` bridges structured requirements engineering with verifiable arithmetic circuit synthesis:

* **Deterministic FRET-to-Circom Compilation:** Translates single- and multi-requirement JSON exports into reproducible Circom 2.1.6 templates verified via `diff -u` in GitHub Actions.
* **Wraparound-Safe Arithmetic Encoding:** Binds discrete operational modes using `IsEqual()` comparators and enforces inequality bounds (`>=`, `<=`, `==`) over prime field $\mathbb{F}_p$ with `Num2Bits(b)` range checks on non-negative slack witnesses to prevent modular wraparound.
* **Multi-Requirement Aggregation:** Chains per-requirement validity flags quadratically into `all_constraints_satisfied` across Environmental Control and Life-Support System (ECLSS) requirements (`HAB-O2-001`, `HAB-CO2-002`, and `HAB-VALVE-003`).
* **Explicit Artifact Provenance:** Separates deterministic synthetic telemetry evaluation (`scripts/run_prototype_check.py`) from deferred hardware `circom` / `snarkjs` proving benchmarks.

---

## Repository Layout

* `paper/tool_paper_8p.tex`: Springer LNCS 8-page (+ references) NFM 2027 tool paper manuscript (*From FRET to Range-Checked Zero-Knowledge Proofs: Verifiable Safety Envelopes for Autonomous Deep-Space Habitats*).
* `fret-extension/templates/`: Structured ECLSS requirement templates (`habitat_o2_requirement.json` and `habitat_multi_requirements.json`) with integer scaling and bit-width parameters.
* `fret-extension/fretish-to-zksnark/fret_to_circuit.py`: Python-to-Circom constraint generator emitting `IsEqual()` guards, slack constraints, `Num2Bits(b)` range checks, and `all_constraints_satisfied` aggregation.
* `circuits/`: Committed reference Circom 2.1.6 circuits (`habitat_o2_compliance_ranged.circom` and `habitat_multi_compliance.circom`).
* `scripts/run_prototype_check.py`: Deterministic synthetic telemetry policy evaluator.
* `.github/workflows/validate-translator.yml`: Automated CI workflow verifying single- and multi-requirement circuit generation diffs and synthetic policy checks.

---

## Quick Start and Reproduction

Run circuit synthesis, golden-circuit diff checks, and synthetic telemetry validation locally:

```bash
python fret-extension/fretish-to-zksnark/fret_to_circuit.py \
  --input fret-extension/templates/habitat_multi_requirements.json \
  --output /tmp/habitat_multi_compliance.circom

diff -u circuits/habitat_multi_compliance.circom /tmp/habitat_multi_compliance.circom
python scripts/run_prototype_check.py
