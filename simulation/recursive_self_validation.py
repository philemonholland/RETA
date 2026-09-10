#!/usr/bin/env python3
"""Recursive system-level validation for HORTRAME IPS Alignment v1.0.0.

This is not an alignment benchmark. It verifies that the executable model
materializes its own evaluators as causal events, feeds postmortem output into
later cycles, changes learned/runtime state under feedback, preserves a frozen
constitutional epoch unless a governed change is explicitly committed, and
continues to satisfy structural invariants.
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import hashlib
import json
import statistics

from ips_recursive_sim import IPSRecursiveSimulation

ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "validation"


def canonical_hash(obj) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def learned_state_payload(sim: IPSRecursiveSimulation):
    return [
        {
            "id": n.id,
            "alpha": n.state.response_alpha,
            "beta": n.state.response_beta,
            "prediction_error_ema": n.state.prediction_error_ema,
            "recent_learning_gain": n.state.recent_learning_gain,
            "recurrent_without_model_learning": n.state.recurrent_without_model_learning,
        }
        for n in sim.nodes
    ]


def ordinary_state_payload(sim: IPSRecursiveSimulation):
    return [
        {
            "id": n.id,
            "openness": n.state.openness,
            "agency": n.state.agency,
            "stability": n.state.stability,
            "uncertainty": n.state.uncertainty,
            "adaptability": n.state.adaptability,
            "input_load": n.state.input_load,
            "recent_inputs": list(n.recent_inputs),
        }
        for n in sim.nodes
    ]


def run_one(seed: int, cycles: int = 6):
    sim = IPSRecursiveSimulation(
        seed=seed,
        audit_depth=3,
        max_events=180,
        auto_response=False,
        audit_auto_responses=False,
        learning_enabled=True,
    )
    previous_postmortem = None
    previous_learning_hash = canonical_hash(learned_state_payload(sim))
    previous_ordinary_state_hash = canonical_hash(ordinary_state_payload(sim))
    rows = []

    for cycle in range(1, cycles + 1):
        causes = [previous_postmortem] if previous_postmortem is not None else []
        before_ids = set(sim.events)
        target = sim.emit_output(
            channel="authority" if cycle == 3 else "info",
            intensity=.82 if cycle == 3 else .34 + .03 * cycle,
            label=f"recursive self-validation cycle {cycle}",
            causes=causes,
            fanout=2,
            audit=True,
            biased_primary=(cycle == 3),
            claim_confidence=.92 if cycle == 3 else .62,
        )
        created = [sim.events[i] for i in sorted(set(sim.events) - before_ids)]
        postmortems = [e for e in created if e.kind == "postmortem" and target.id in e.causes]
        if len(postmortems) != 1:
            raise AssertionError(f"cycle {cycle}: expected one postmortem event, got {len(postmortems)}")
        postmortem = postmortems[0]

        # Materialize the recursive feedback events. The next cycle is then
        # explicitly causally dependent on this postmortem.
        sim.run(until=sim.time + 4.0, max_deliveries=500)
        current_learning_hash = canonical_hash(learned_state_payload(sim))
        learning_changed = current_learning_hash != previous_learning_hash
        current_ordinary_state_hash = canonical_hash(ordinary_state_payload(sim))
        ordinary_state_evolved = current_ordinary_state_hash != previous_ordinary_state_hash
        postmortem_delivered_to_actor = sim.roles["actor"] in postmortem.recipients_realized

        rows.append({
            "cycle": cycle,
            "target_event": target.id,
            "target_causes": list(target.causes),
            "target_gate": target.gate_result,
            "postmortem_event": postmortem.id,
            "events_created_this_cycle": [e.id for e in created],
            "event_kinds_created": [e.kind for e in created],
            "learning_state_sha256_before": previous_learning_hash,
            "learning_state_sha256_after": current_learning_hash,
            "learning_state_changed": learning_changed,
            "ordinary_state_sha256_before": previous_ordinary_state_hash,
            "ordinary_state_sha256_after": current_ordinary_state_hash,
            "ordinary_state_evolved": ordinary_state_evolved,
            "postmortem_delivered_to_actor": postmortem_delivered_to_actor,
            "network_model_error": sim.network_model_error(),
            "lens_version": sim.current_lens.version,
            "invariants": sim.validate_invariants(),
        })
        previous_postmortem = postmortem.id
        previous_learning_hash = current_learning_hash
        previous_ordinary_state_hash = current_ordinary_state_hash

    chain_closed = all(
        rows[i]["target_causes"] == [rows[i - 1]["postmortem_event"]]
        for i in range(1, len(rows))
    )
    all_recursive_layers = all(
        all(k in row["event_kinds_created"] for k in ("output", "audit", "meta_audit", "gate", "postmortem"))
        for row in rows
    )
    all_learning_changed = all(row["learning_state_changed"] for row in rows)
    all_ordinary_state_evolved = all(row["ordinary_state_evolved"] for row in rows)
    all_postmortems_delivered_to_actor = all(row["postmortem_delivered_to_actor"] for row in rows)
    all_invariants = all(row["invariants"]["pass"] for row in rows)
    biased_cycle_unresolved = rows[2]["target_gate"] == "UNRESOLVED" if cycles >= 3 else None
    constitution_frozen = all(row["lens_version"] == 1 for row in rows)

    return {
        "seed": seed,
        "cycles": rows,
        "chain_closed_postmortem_to_next_output": chain_closed,
        "all_recursive_layers_materialized": all_recursive_layers,
        "all_cycles_changed_learned_state": all_learning_changed,
        "all_cycles_evolved_ordinary_state": all_ordinary_state_evolved,
        "all_postmortems_delivered_to_actor": all_postmortems_delivered_to_actor,
        "biased_primary_cycle_forced_unresolved": biased_cycle_unresolved,
        "constitutional_epoch_remained_frozen": constitution_frozen,
        "all_invariants_pass": all_invariants,
        "pass": bool(chain_closed and all_recursive_layers and all_learning_changed and all_ordinary_state_evolved and all_postmortems_delivered_to_actor and all_invariants and constitution_frozen and biased_cycle_unresolved),
    }


def main():
    VALIDATION.mkdir(parents=True, exist_ok=True)
    seeds = [909001, 909002, 909003, 909004, 909005, 909006, 909007, 909008]
    runs = [run_one(seed) for seed in seeds]
    summary = {
        "purpose": "closed-loop recursive self-validation of executable semantics",
        "n_runs": len(runs),
        "cycles_per_run": 6,
        "all_runs_pass": all(r["pass"] for r in runs),
        "all_chains_closed": all(r["chain_closed_postmortem_to_next_output"] for r in runs),
        "all_recursive_layers_materialized": all(r["all_recursive_layers_materialized"] for r in runs),
        "all_runs_evolved_learned_state_each_cycle": all(r["all_cycles_changed_learned_state"] for r in runs),
        "all_runs_evolved_ordinary_state_each_cycle": all(r["all_cycles_evolved_ordinary_state"] for r in runs),
        "all_runs_postmortem_feedback_delivered_to_actor": all(r["all_postmortems_delivered_to_actor"] for r in runs),
        "all_biased_cycles_unresolved": all(r["biased_primary_cycle_forced_unresolved"] for r in runs),
        "all_constitutions_frozen_without_governed_change": all(r["constitutional_epoch_remained_frozen"] for r in runs),
        "final_network_model_error_mean": statistics.mean(r["cycles"][-1]["network_model_error"] for r in runs),
        "runs": runs,
    }
    out = VALIDATION / "recursive_self_validation.json"
    out.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    md = [
        "# Recursive self-validation",
        "",
        "This validation closes the executable loop by making each cycle's postmortem event a declared cause of the next actor output. Audits, meta-audits, gates, and postmortems are themselves events in the same DAG. Deliveries update recipient state and learned response models. The constitutional lens remains frozen unless a separate governed lens-change transaction is invoked.",
        "",
        f"Runs: {len(runs)} × 6 cycles.",
        f"All runs pass: {summary['all_runs_pass']}.",
        f"Postmortem → next-output causal chain closed: {summary['all_chains_closed']}.",
        f"Audit/meta-audit/gate/postmortem layers materialized every cycle: {summary['all_recursive_layers_materialized']}.",
        f"Learned state changed on every feedback cycle: {summary['all_runs_evolved_learned_state_each_cycle']}.",
        f"Ordinary recursive state evolved on every feedback cycle: {summary['all_runs_evolved_ordinary_state_each_cycle']}.",
        f"Postmortem feedback was realized at the actor before the next caused output: {summary['all_runs_postmortem_feedback_delivered_to_actor']}.",
        f"Injected biased-primary-auditor cycle ended UNRESOLVED in every run: {summary['all_biased_cycles_unresolved']}.",
        f"Constitution stayed at epoch 1 without an explicit governed change: {summary['all_constitutions_frozen_without_governed_change']}.",
        "",
        "This validates implementation semantics and reproducibility only; it does not establish that the Five Vows are a complete ethical theory or that the toy dynamics predict real socio-technical systems.",
    ]
    (VALIDATION / "RECURSIVE_SELF_VALIDATION.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "runs"}, indent=2, sort_keys=True))
    if not summary["all_runs_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
