#!/usr/bin/env python3
"""Generate the v1.0.0 research result bundle from fixed seeds.

Dependency-free. Run from release root with the supplied run_all.sh script.
"""
from __future__ import annotations
from pathlib import Path
import csv
import hashlib
import json
import statistics
from dataclasses import asdict, replace

from ips_recursive_sim import IPSRecursiveSimulation, Lens, VOWS, CHANNELS, sha256

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
VALIDATION = ROOT / "validation"
FIGURES = RESULTS / "figures"


def write_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: Path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def svg_line_chart(path: Path, rows, xkey: str, ys: list[tuple[str, str]], title: str, xlabel: str, ylabel: str):
    width, height = 900, 520
    lm, rm, tm, bm = 90, 30, 55, 75
    xs = [float(r[xkey]) for r in rows]
    vals = [float(r[k]) for k, _ in ys for r in rows]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(vals), max(vals)
    if ymax <= ymin:
        ymax = ymin + 1
    pad = (ymax - ymin) * .10
    ymin = max(0, ymin - pad)
    ymax = ymax + pad
    def sx(x): return lm + (x - xmin) / max(1e-12, xmax - xmin) * (width - lm - rm)
    def sy(y): return tm + (ymax - y) / max(1e-12, ymax - ymin) * (height - tm - bm)
    palette = ["#4f81bd", "#c0504d", "#9bbb59", "#8064a2"]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
           '<rect width="100%" height="100%" fill="white"/>',
           f'<text x="{width/2}" y="28" text-anchor="middle" font-family="sans-serif" font-size="18">{title}</text>']
    for i in range(6):
        yv = ymin + (ymax-ymin)*i/5
        yy = sy(yv)
        out.append(f'<line x1="{lm}" y1="{yy:.2f}" x2="{width-rm}" y2="{yy:.2f}" stroke="#dddddd" stroke-width="1"/>')
        out.append(f'<text x="{lm-10}" y="{yy+4:.2f}" text-anchor="end" font-family="monospace" font-size="11">{yv:.3f}</text>')
    out += [f'<line x1="{lm}" y1="{tm}" x2="{lm}" y2="{height-bm}" stroke="#333"/>',
            f'<line x1="{lm}" y1="{height-bm}" x2="{width-rm}" y2="{height-bm}" stroke="#333"/>']
    for i in range(6):
        xv = xmin + (xmax-xmin)*i/5
        xx = sx(xv)
        out.append(f'<text x="{xx:.2f}" y="{height-bm+22}" text-anchor="middle" font-family="monospace" font-size="11">{xv:g}</text>')
    for idx, (key, label) in enumerate(ys):
        pts = " ".join(f"{sx(float(r[xkey])):.2f},{sy(float(r[key])):.2f}" for r in rows)
        col = palette[idx % len(palette)]
        out.append(f'<polyline fill="none" stroke="{col}" stroke-width="2.4" points="{pts}"/>')
        for r in rows:
            out.append(f'<circle cx="{sx(float(r[xkey])):.2f}" cy="{sy(float(r[key])):.2f}" r="3" fill="{col}"/>')
        ly = 55 + idx*19
        out.append(f'<line x1="{width-260}" y1="{ly}" x2="{width-232}" y2="{ly}" stroke="{col}" stroke-width="3"/>')
        out.append(f'<text x="{width-225}" y="{ly+4}" font-family="sans-serif" font-size="11">{label}</text>')
    out.append(f'<text x="{width/2}" y="{height-18}" text-anchor="middle" font-family="sans-serif" font-size="13">{xlabel}</text>')
    out.append(f'<text x="18" y="{height/2}" transform="rotate(-90 18 {height/2})" text-anchor="middle" font-family="sans-serif" font-size="13">{ylabel}</text>')
    out.append('</svg>')
    path.write_text("\n".join(out), encoding="utf-8")


def baseline_experiment():
    sim = IPSRecursiveSimulation(seed=20260909, audit_depth=3, max_events=180, auto_response=True)
    initial_error = sim.network_model_error()
    root = sim.emit_output(channel="info", intensity=.72, label="v1.0 baseline root informational output", fanout=3, audit=True)
    sim.run(until=12.0)
    final_error = sim.network_model_error()
    sim.export_all(RESULTS, "baseline")
    write_json(RESULTS / "baseline_run_status.json", sim.run_status())
    outputs = [e for e in sim.events.values() if e.kind == "output"]
    governance = [e for e in sim.events.values() if e.kind in ("audit", "meta_audit", "gate", "postmortem", "lens_change_proposal", "lens_change_review", "lens_change_approval", "lens_change_rejection")]
    postmortems = [e for e in sim.events.values() if e.kind == "postmortem"]
    multi = [e for e in sim.events.values() if len(e.causes) > 1]
    return {
        "seed": sim.seed,
        "root_event": root.id,
        "events_total": len(sim.events),
        "output_events": len(outputs),
        "governance_events": len(governance),
        "postmortem_events": len(postmortems),
        "audit_packets": len(sim.audit_packets),
        "multi_cause_events": len(multi),
        "initial_network_model_error": initial_error,
        "final_network_model_error": final_error,
        "invariants": sim.validate_invariants(),
        "run_status": sim.run_status(),
        "roles": sim.roles,
    }, sim


def horizon_experiment():
    sim = IPSRecursiveSimulation(seed=20260910, audit_depth=0, max_events=20, auto_response=False)
    ev = sim.emit_output(channel="authority", intensity=.74, label="horizon sensitivity probe", fanout=3, audit=False)
    rows = []
    for h in range(1, 7):
        lens = Lens(version=h, horizon=h, note=f"counterfactual horizon H={h}")
        p = sim.evaluate_event(ev, sim.roles["primary_auditor"], 0, lens=lens, record=False)
        row = {
            "horizon": h,
            "gate": p.gate,
            "diagnostic_trace": p.diagnostic_trace,
            "max_tension": max(p.tensions.values()),
            "max_uncertainty": max(p.uncertainty.values()),
            "expected_nodes": p.projection["expected_nodes"],
            "domains": p.projection["domains"],
            "expected_impact": p.projection["expected_impact"],
        }
        rows.append(row)
    write_csv(RESULTS / "horizon_sensitivity.csv", rows, list(rows[0]))
    write_json(RESULTS / "horizon_sensitivity.json", rows)
    svg_line_chart(FIGURES / "horizon_sensitivity.svg", rows, "horizon", [("expected_nodes", "expected modeled reach"), ("max_uncertainty", "max uncertainty")], "Projection horizon changes the audit", "Horizon (graph hops)", "Illustrative value")
    return rows


def dag_experiment():
    sim = IPSRecursiveSimulation(seed=20260911, audit_depth=2, max_events=40, auto_response=False)
    target = sim.roles["actor"]
    # Two independent roots from different systems, then one event depending on both.
    s1 = next(n.id for n in sim.nodes if n.primary == "human" and n.id != sim.roles["human_gate"])
    s2 = next(n.id for n in sim.nodes if n.primary == "institution" and n.id != sim.roles["power_auditor"])
    e1 = sim.emit_output(source=s1, recipients=[target], channel="info", intensity=.45, label="DAG parent A", audit=False)
    e2 = sim.emit_output(source=s2, recipients=[target], channel="info", intensity=.52, label="DAG parent B", audit=False)
    sim.run(until=2.0)
    e3 = sim.emit_output(source=target, channel="info", intensity=.55, label="multi-cause synthesis", causes=[e1.id, e2.id], fanout=1, audit=True)
    inv = sim.validate_invariants()
    result = {
        "parents": [e1.id, e2.id],
        "child": e3.id,
        "child_causes": e3.causes,
        "parent_A_happens_before_child": sim.happens_before(e1.vector_clock, e3.vector_clock),
        "parent_B_happens_before_child": sim.happens_before(e2.vector_clock, e3.vector_clock),
        "child_vector_clock": e3.vector_clock,
        "invariants": inv,
    }
    write_json(RESULTS / "causal_dag_multi_parent.json", result)
    return result


def biased_auditor_experiment():
    sim = IPSRecursiveSimulation(seed=20260912, audit_depth=3, max_events=60, auto_response=False)
    ev = sim.emit_output(channel="authority", intensity=.86, label="biased-auditor challenge", fanout=3, audit=True, biased_primary=True, claim_confidence=.92)
    packets = [sim.audit_packets[i] for i in ev.audit_packet_ids]
    audit_events = [e for e in sim.events.values() if e.kind == "audit" and e.causes == [ev.id]]
    meta = [e for e in sim.events.values() if e.kind == "meta_audit" and ev.id in e.causes]
    result = {
        "target_event": ev.id,
        "final_gate": ev.gate_result,
        "target_packets": [asdict(p) for p in packets],
        "audit_events": [asdict(e) for e in audit_events],
        "meta_audit_events": [asdict(e) for e in meta],
        "recursive_audit_materialized": bool(audit_events and meta),
        "power_audit_detected_discrepancy": any(float(e.metadata.get("divergence", 0)) > .18 for e in meta),
    }
    write_json(RESULTS / "biased_auditor_recursive_check.json", result)
    return result


def lens_epoch_experiment():
    sim = IPSRecursiveSimulation(seed=20260913, audit_depth=1, max_events=30, auto_response=False)
    e1 = sim.emit_output(channel="info", intensity=.48, label="epoch-1 event", fanout=2, audit=True)
    frozen_ids = list(e1.audit_packet_ids)
    frozen_before = [asdict(sim.audit_packets[i]) for i in frozen_ids]
    new_lens = sim.commit_lens(approved=True, horizon=5, modify_threshold=.48, note="validated prospective test epoch")
    e2 = sim.emit_output(channel="info", intensity=.48, label="epoch-2 event", fanout=2, audit=True)
    frozen_after = [asdict(sim.audit_packets[i]) for i in frozen_ids]
    result = {
        "event_1": e1.id,
        "event_1_lens": e1.lens_version,
        "event_2": e2.id,
        "event_2_lens": e2.lens_version,
        "new_lens": asdict(new_lens),
        "governance_event_exists": new_lens.governance_event in sim.events,
        "governance_event_kind": sim.events[new_lens.governance_event].kind if new_lens.governance_event in sim.events else None,
        "governance_chain": [
            asdict(e) for e in sim.events.values()
            if e.kind in ("lens_change_proposal", "lens_change_review", "lens_change_approval", "lens_change_rejection")
        ],
        "historical_packet_unchanged": frozen_before == frozen_after,
        "historical_packet_sha256_before": hashlib.sha256(json.dumps(frozen_before, sort_keys=True).encode()).hexdigest(),
        "historical_packet_sha256_after": hashlib.sha256(json.dumps(frozen_after, sort_keys=True).encode()).hexdigest(),
    }
    write_json(RESULTS / "lens_epoch_immutability.json", result)
    return result


def evolution_learning_experiment(n_seeds=64, steps=120):
    checkpoints = list(range(0, steps + 1, 10))
    curves = {k: [] for k in checkpoints}
    per_seed = []
    for j in range(n_seeds):
        sim = IPSRecursiveSimulation(seed=303000 + j, audit_depth=0, max_events=steps + 10, auto_response=False, learning_enabled=True)
        learner = sim.nodes[sim.roles["actor"]]
        source = sim.roles["human_gate"]
        # Keep the controlled observation process stationary: this probe asks
        # whether recursive feedback changes the learned response transform,
        # not whether overload changes the effective response propensity.
        learner.state.adaptability = 1.0
        errors = {0: sim.node_model_error(learner)}
        learned_before = {c: sim.learned_response(learner, c) for c in CHANNELS}
        probe_event = None
        projection_before = None
        for step in range(1, steps + 1):
            ch = CHANNELS[(step - 1) % len(CHANNELS)]
            ev = sim.emit_output(
                source=source,
                recipients=[learner.id],
                channel=ch,
                intensity=.01,
                label=f"recursive feedback observation {step}",
                audit=False,
                claim_confidence=.50,
            )
            if probe_event is None:
                probe_event = ev
                # Projection is evaluated on a moderate-intensity counterfactual
                # copy of the same frozen event so the .01 calibration stimulus
                # itself does not suppress all second-hop reach at the 0.01
                # projection pruning threshold.
                projection_before = sim.project_trajectory(replace(probe_event, intensity=.65), 3)
            sim.run(until=sim.time + 2.0, max_deliveries=1)
            if step in curves:
                errors[step] = sim.node_model_error(learner)
        for k in checkpoints:
            curves[k].append(errors[k])
        learned_after = {c: sim.learned_response(learner, c) for c in CHANNELS}
        projection_after = sim.project_trajectory(replace(probe_event, intensity=.65), 3) if probe_event is not None else None
        per_seed.append({
            "seed": 303000 + j,
            "error_0": errors[0],
            "error_final": errors[steps],
            "events_materialized": len(sim.events),
            "feedback_deliveries_recorded": sum(len(e.metadata.get("deliveries", [])) for e in sim.events.values()),
            "learned_response_before": learned_before,
            "learned_response_after": learned_after,
            "projection_expected_nodes_before": projection_before["expected_nodes"] if projection_before else None,
            "projection_expected_nodes_after": projection_after["expected_nodes"] if projection_after else None,
        })
    rows = []
    for k in checkpoints:
        vals = curves[k]
        rows.append({
            "feedback_observations": k,
            "mean_model_error": statistics.mean(vals),
            "median_model_error": statistics.median(vals),
            "p10_model_error": sorted(vals)[max(0, int(.10 * (len(vals)-1)))],
            "p90_model_error": sorted(vals)[min(len(vals)-1, int(.90 * (len(vals)-1)))],
        })
    write_csv(RESULTS / "recursive_evolution_learning_curve.csv", rows, list(rows[0]))
    write_json(RESULTS / "recursive_evolution_learning_curve.json", {"n_seeds": n_seeds, "steps": steps, "curve": rows, "per_seed": per_seed})
    svg_line_chart(FIGURES / "recursive_evolution_learning_curve.svg", rows, "feedback_observations", [("mean_model_error", "mean model error"), ("median_model_error", "median model error")], "Adaptive model learning inside recursive evolution", "Observed feedback events", "Effective-response estimation error")
    return {
        "n_seeds": n_seeds,
        "steps": steps,
        "initial_mean": rows[0]["mean_model_error"],
        "final_mean": rows[-1]["mean_model_error"],
        "relative_change": (rows[-1]["mean_model_error"] - rows[0]["mean_model_error"]) / rows[0]["mean_model_error"],
        "mean_abs_projection_change": statistics.mean(abs(x["projection_expected_nodes_after"] - x["projection_expected_nodes_before"]) for x in per_seed),
        "all_runs_materialized_feedback": all(x["events_materialized"] == steps and x["feedback_deliveries_recorded"] == steps for x in per_seed),
    }


def recursive_feedback_no_learning_control(n_seeds=24, steps=60):
    """Negative control: recursive state evolution continues while response-model learning is disabled."""
    rows = []
    for j in range(n_seeds):
        sim = IPSRecursiveSimulation(
            seed=353000 + j,
            audit_depth=0,
            max_events=steps + 10,
            auto_response=False,
            learning_enabled=False,
        )
        learner = sim.nodes[sim.roles["actor"]]
        source = sim.roles["human_gate"]
        learner.state.adaptability = 1.0
        error_before = sim.node_model_error(learner)
        alpha_before = dict(learner.state.response_alpha)
        beta_before = dict(learner.state.response_beta)
        ordinary_before = {
            "openness": learner.state.openness,
            "agency": learner.state.agency,
            "stability": learner.state.stability,
            "uncertainty": learner.state.uncertainty,
            "adaptability": learner.state.adaptability,
            "input_load": learner.state.input_load,
        }
        for step in range(1, steps + 1):
            ch = CHANNELS[(step - 1) % len(CHANNELS)]
            sim.emit_output(
                source=source,
                recipients=[learner.id],
                channel=ch,
                intensity=.01,
                label=f"negative-control recurrent feedback {step}",
                audit=False,
                claim_confidence=.50,
            )
            sim.run(until=sim.time + 2.0, max_deliveries=1)
        error_after = sim.node_model_error(learner)
        ordinary_after = {
            "openness": learner.state.openness,
            "agency": learner.state.agency,
            "stability": learner.state.stability,
            "uncertainty": learner.state.uncertainty,
            "adaptability": learner.state.adaptability,
            "input_load": learner.state.input_load,
        }
        rows.append({
            "seed": 353000 + j,
            "events_materialized": len(sim.events),
            "feedback_deliveries_recorded": sum(len(e.metadata.get("deliveries", [])) for e in sim.events.values()),
            "error_before": error_before,
            "error_after": error_after,
            "posterior_unchanged": alpha_before == learner.state.response_alpha and beta_before == learner.state.response_beta,
            "ordinary_state_changed": ordinary_before != ordinary_after,
            "ordinary_state_before": ordinary_before,
            "ordinary_state_after": ordinary_after,
            "recurrent_without_model_learning": learner.state.recurrent_without_model_learning,
        })
    result = {
        "n_seeds": n_seeds,
        "steps": steps,
        "all_histories_recurred": all(x["events_materialized"] == steps and x["feedback_deliveries_recorded"] == steps for x in rows),
        "all_posteriors_unchanged": all(x["posterior_unchanged"] for x in rows),
        "all_model_errors_unchanged": all(abs(x["error_after"] - x["error_before"]) < 1e-15 for x in rows),
        "all_ordinary_states_evolved": all(x["ordinary_state_changed"] for x in rows),
        "min_recurrent_without_model_learning": min(x["recurrent_without_model_learning"] for x in rows),
        "pass": all(
            x["events_materialized"] == steps
            and x["feedback_deliveries_recorded"] == steps
            and x["posterior_unchanged"]
            and x["ordinary_state_changed"]
            and abs(x["error_after"] - x["error_before"]) < 1e-15
            and x["recurrent_without_model_learning"] >= steps
            for x in rows
        ),
        "runs": rows,
    }
    write_json(VALIDATION / "recursive_feedback_no_learning_control.json", result)
    return result


def recursive_state_evolution_probe(steps=20):
    """Show that recursive state evolution changes a future response law even with model learning frozen."""
    sim = IPSRecursiveSimulation(seed=353099, audit_depth=0, max_events=steps + 5, auto_response=False, learning_enabled=False)
    learner = sim.nodes[sim.roles["actor"]]
    source = sim.roles["human_gate"]
    channel = "info"
    learner.state.adaptability = .82
    learned_before = sim.learned_response(learner, channel)
    effective_before = sim.effective_response_probability(learner, channel)
    state_before = {
        "openness": learner.state.openness,
        "agency": learner.state.agency,
        "stability": learner.state.stability,
        "uncertainty": learner.state.uncertainty,
        "adaptability": learner.state.adaptability,
        "input_load": learner.state.input_load,
    }
    for _ in range(steps):
        sim.emit_output(source=source, recipients=[learner.id], channel=channel, intensity=1.0, audit=False)
        sim.run(until=sim.time + 2.0, max_deliveries=1)
    learned_after = sim.learned_response(learner, channel)
    effective_after = sim.effective_response_probability(learner, channel)
    state_after = {
        "openness": learner.state.openness,
        "agency": learner.state.agency,
        "stability": learner.state.stability,
        "uncertainty": learner.state.uncertainty,
        "adaptability": learner.state.adaptability,
        "input_load": learner.state.input_load,
    }
    result = {
        "seed": sim.seed,
        "steps": steps,
        "learning_enabled": sim.learning_enabled,
        "channel": channel,
        "learned_response_before": learned_before,
        "learned_response_after": learned_after,
        "learned_response_unchanged": learned_before == learned_after,
        "effective_response_probability_before": effective_before,
        "effective_response_probability_after": effective_after,
        "effective_response_probability_changed": effective_before != effective_after,
        "ordinary_state_before": state_before,
        "ordinary_state_after": state_after,
        "ordinary_state_changed": state_before != state_after,
        "feedback_deliveries_recorded": sum(len(e.metadata.get("deliveries", [])) for e in sim.events.values()),
        "invariants": sim.validate_invariants(),
    }
    result["pass"] = bool(
        result["learned_response_unchanged"]
        and result["effective_response_probability_changed"]
        and result["ordinary_state_changed"]
        and result["feedback_deliveries_recorded"] == steps
        and result["invariants"]["pass"]
    )
    write_json(VALIDATION / "recursive_state_evolution_probe.json", result)
    return result



def cohen_complex_systems_probe():
    """Perturbation-response probe motivated by the Cohen complex-systems corpus.

    This is an architectural diagnostic, not a biological model. It deliberately
    preserves a multivariate state signature, tests response across channel and
    context, and avoids promoting a single distance/entropy/"health" scalar to
    an authorization variable. The current engine has no autonomous recovery
    flow, so this probe does not claim to measure resilience or a critical
    transition; it measures immediate realized perturbation response only.
    """
    state_vars = ("openness", "agency", "stability", "uncertainty", "adaptability", "input_load")

    def snap(node):
        return {k: float(getattr(node.state, k)) for k in state_vars}

    def one_delivery(seed, target_primary, channel, intensity):
        sim = IPSRecursiveSimulation(
            seed=seed,
            audit_depth=0,
            max_events=8,
            auto_response=False,
            learning_enabled=False,
        )
        source = sim.roles["human_gate"]
        candidates = [n for n in sim.nodes if n.primary == target_primary and n.id != source]
        target = candidates[0]
        before = snap(target)
        ev = sim.emit_output(
            source=source,
            recipients=[target.id],
            channel=channel,
            intensity=intensity,
            label=f"standardized perturbation {target_primary}/{channel}/{intensity:.2f}",
            audit=False,
            claim_confidence=.50,
        )
        sim.run(until=sim.time + 2.0, max_deliveries=1)
        after = snap(target)
        delta = {k: after[k] - before[k] for k in state_vars}
        l2 = sum(v * v for v in delta.values()) ** 0.5
        changed = sum(abs(v) > 1e-12 for v in delta.values())
        return {
            "seed": seed,
            "target_primary": target_primary,
            "target_node": target.id,
            "channel": channel,
            "intensity": intensity,
            "before": before,
            "after": after,
            "delta": delta,
            "changed_dimensions": changed,
            "state_signature_l2": l2,
            "delivery_realized": target.id in ev.recipients_realized,
        }

    # Channel × intensity: one fixed actor context, isolated fresh runs from the
    # same network seed. A channel-specific vector is retained; the L2 norm is
    # descriptive only and never passed to the Vow gate.
    intensity_rows = []
    channel_runs = []
    for intensity in (.15, .45, .75):
        chart_row = {"intensity": intensity}
        for channel in CHANNELS:
            run = one_delivery(808080, "ai", channel, intensity)
            channel_runs.append(run)
            chart_row[f"{channel}_l2"] = run["state_signature_l2"]
        intensity_rows.append(chart_row)

    write_csv(
        RESULTS / "cohen_perturbation_response.csv",
        [
            {
                "seed": r["seed"],
                "target_primary": r["target_primary"],
                "target_node": r["target_node"],
                "channel": r["channel"],
                "intensity": r["intensity"],
                "changed_dimensions": r["changed_dimensions"],
                "state_signature_l2": r["state_signature_l2"],
                **{f"delta_{k}": r["delta"][k] for k in state_vars},
            }
            for r in channel_runs
        ],
        ["seed", "target_primary", "target_node", "channel", "intensity", "changed_dimensions", "state_signature_l2"]
        + [f"delta_{k}" for k in state_vars],
    )
    svg_line_chart(
        FIGURES / "cohen_perturbation_response.svg",
        intensity_rows,
        "intensity",
        [(f"{c}_l2", f"{c} response norm") for c in CHANNELS],
        "Standardized perturbation-response signatures (synthetic IPS model)",
        "Input intensity",
        "Multivariate state-change norm (descriptive only)",
    )

    # Context probe: identical info perturbation, identical network seed,
    # representative targets in each macro-domain. Differences are contextual
    # properties of this synthetic state-transition rule, not empirical claims
    # about humans, AIs, institutions, economies, ecosystems, or infrastructure.
    context_runs = [one_delivery(808081, macro, "info", .65) for macro in ("human", "ai", "institution", "economy", "ecosystem", "infra")]
    context_rows = [
        {
            "target_primary": r["target_primary"],
            "target_node": r["target_node"],
            "changed_dimensions": r["changed_dimensions"],
            "state_signature_l2": r["state_signature_l2"],
            **{f"delta_{k}": r["delta"][k] for k in state_vars},
        }
        for r in context_runs
    ]
    write_csv(
        RESULTS / "cohen_context_response.csv",
        context_rows,
        ["target_primary", "target_node", "changed_dimensions", "state_signature_l2"] + [f"delta_{k}" for k in state_vars],
    )

    signatures = {
        (r["channel"], r["intensity"]): tuple(round(r["delta"][k], 12) for k in state_vars)
        for r in channel_runs
    }
    channel_signature_count = len({sig for sig in signatures.values()})
    context_uncertainty_deltas = [r["delta"]["uncertainty"] for r in context_runs]
    context_l2 = [r["state_signature_l2"] for r in context_runs]
    result = {
        "interpretation_boundary": {
            "biological_equivalence_claimed": False,
            "single_privileged_health_or_alignment_scalar_claimed": False,
            "critical_transition_claimed": False,
            "resilience_or_recovery_measured": False,
            "reason_recovery_not_measured": "the v1.0 engine has event-driven state updates but no calibrated autonomous recovery/return-to-attractor process",
        },
        "design_constraints": [
            "distributed multivariate state is retained",
            "perturbation response is measured from realized state transitions",
            "channel/modular context is preserved",
            "context dependence is tested rather than assumed universal",
            "scalar norms are descriptive and never authorization variables",
            "state inference is not treated as network identification",
        ],
        "state_dimensions": list(state_vars),
        "channel_intensity_runs": channel_runs,
        "context_runs": context_runs,
        "distinct_channel_intensity_signatures": channel_signature_count,
        "context_uncertainty_delta_range": max(context_uncertainty_deltas) - min(context_uncertainty_deltas),
        "context_response_norm_range": max(context_l2) - min(context_l2),
        "all_deliveries_realized": all(r["delivery_realized"] for r in channel_runs + context_runs),
        "multivariate_response_present": all(r["changed_dimensions"] >= 4 for r in channel_runs + context_runs),
    }
    result["pass"] = bool(
        result["all_deliveries_realized"]
        and result["multivariate_response_present"]
        and result["distinct_channel_intensity_signatures"] > len(CHANNELS)
        and result["context_uncertainty_delta_range"] > 0
        and not any([
            result["interpretation_boundary"]["biological_equivalence_claimed"],
            result["interpretation_boundary"]["single_privileged_health_or_alignment_scalar_claimed"],
            result["interpretation_boundary"]["critical_transition_claimed"],
            result["interpretation_boundary"]["resilience_or_recovery_measured"],
        ])
    )
    write_json(RESULTS / "cohen_complex_systems_probe.json", result)
    return result

def audit_counterfactual_experiment(n_seeds=48):
    rows = []
    for j in range(n_seeds):
        seed = 404000 + j
        for audited in (False, True):
            sim = IPSRecursiveSimulation(seed=seed, audit_depth=3 if audited else 0, max_events=110, auto_response=True, audit_auto_responses=audited)
            sim.emit_output(channel="authority", intensity=.76, label="paired governance probe", fanout=3, audit=audited)
            sim.run(until=8.0)
            output_events = [e for e in sim.events.values() if e.kind == "output"]
            harmful_deliveries = 0
            total_deliveries = 0
            posthoc_blocked_outputs = 0
            for e in output_events:
                total_deliveries += len(e.recipients_realized)
                # Use a fresh, side-effect-free packet evaluation on the frozen event.
                p = sim.evaluate_event(e, sim.roles["power_auditor"], 9, record=False)
                if p.gate in ("REJECT", "UNRESOLVED"):
                    posthoc_blocked_outputs += 1
                    harmful_deliveries += len(e.recipients_realized)
            rows.append({
                "seed": seed,
                "mode": "recursive_audit" if audited else "no_gate",
                "output_events": len(output_events),
                "total_realized_deliveries": total_deliveries,
                "posthoc_blocked_outputs": posthoc_blocked_outputs,
                "deliveries_from_posthoc_blocked_outputs": harmful_deliveries,
            })
    write_csv(RESULTS / "recursive_audit_counterfactual.csv", rows, list(rows[0]))
    grouped = {}
    for mode in ("no_gate", "recursive_audit"):
        r = [x for x in rows if x["mode"] == mode]
        grouped[mode] = {
            "n": len(r),
            "mean_output_events": statistics.mean(x["output_events"] for x in r),
            "mean_total_deliveries": statistics.mean(x["total_realized_deliveries"] for x in r),
            "mean_deliveries_from_posthoc_blocked_outputs": statistics.mean(x["deliveries_from_posthoc_blocked_outputs"] for x in r),
        }
    write_json(RESULTS / "recursive_audit_counterfactual_summary.json", grouped)
    return grouped


def deterministic_replay_experiment():
    hashes = []
    payloads = []
    for _ in range(2):
        sim = IPSRecursiveSimulation(seed=505050, audit_depth=3, max_events=120, auto_response=True)
        sim.emit_output(channel="info", intensity=.61, label="determinism probe", fanout=2, audit=True)
        sim.run(until=7.0)
        payload = json.dumps({"events": sim.event_list(), "audits": sim.audit_list(), "network": sim.network_snapshot()}, sort_keys=True, separators=(",", ":"))
        payloads.append(payload)
        hashes.append(hashlib.sha256(payload.encode()).hexdigest())
    result = {"hash_run_1": hashes[0], "hash_run_2": hashes[1], "identical": hashes[0] == hashes[1] and payloads[0] == payloads[1]}
    write_json(VALIDATION / "deterministic_replay.json", result)
    return result


def initial_state_experiment():
    sim = IPSRecursiveSimulation(seed=606060, auto_response=False)
    result = {
        "nodes": len(sim.nodes),
        "nodes_with_fictional_last_event": sum(n.last_event_id is not None for n in sim.nodes),
        "nodes_with_fictional_verdict": sum(n.last_verdict is not None for n in sim.nodes),
        "pass": all(n.last_event_id is None and n.last_verdict is None for n in sim.nodes),
    }
    write_json(VALIDATION / "unknown_initial_state.json", result)
    return result


def first_law_experiment():
    sim = IPSRecursiveSimulation(seed=707070, auto_response=False)
    lens = sim.current_lens
    low = {v: .12 for v in VOWS}
    single = dict(low); single["Conduct"] = .82
    symmetric = {v: .82 for v in VOWS}
    unc = {"facts": .1, "causality": .1, "boundary": .1, "model": .1, "normative": .1, "horizon": .1}
    result = {
        "all_low": sim.gate_from_vectors(low, unc, lens),
        "single_severe": sim.gate_from_vectors(single, unc, lens),
        "symmetric_severe": sim.gate_from_vectors(symmetric, unc, lens),
        "pass": sim.gate_from_vectors(single, unc, lens) == "REJECT" and sim.gate_from_vectors(symmetric, unc, lens) == "REJECT",
    }
    write_json(VALIDATION / "first_law_gate.json", result)
    return result


def make_baseline_dag_csv(sim: IPSRecursiveSimulation):
    rows = []
    for e in sorted(sim.events.values(), key=lambda x: x.id):
        rows.append({
            "event_id": e.id,
            "kind": e.kind,
            "source": e.source,
            "causes": ";".join(map(str, e.causes)),
            "requested_recipients": ";".join(map(str, e.recipients_requested)),
            "scheduled_recipients": ";".join(map(str, e.recipients_scheduled)),
            "realized_recipients": ";".join(map(str, e.recipients_realized)),
            "enactment_status": e.enactment_status,
            "channel": e.channel,
            "intensity": e.intensity,
            "gate": e.gate_result or "",
            "time": e.created_at,
            "lens_version": e.lens_version or "",
        })
    write_csv(RESULTS / "causal_dag_probe.csv", rows, list(rows[0]))


def main():
    RESULTS.mkdir(exist_ok=True, parents=True)
    VALIDATION.mkdir(exist_ok=True, parents=True)
    FIGURES.mkdir(exist_ok=True, parents=True)
    summary = {}
    summary["baseline"], baseline_sim = baseline_experiment()
    make_baseline_dag_csv(baseline_sim)
    summary["horizon"] = horizon_experiment()
    summary["causal_dag"] = dag_experiment()
    summary["biased_auditor"] = biased_auditor_experiment()
    summary["lens_epoch"] = lens_epoch_experiment()
    summary["recursive_evolution"] = evolution_learning_experiment()
    summary["recursive_feedback_no_learning"] = recursive_feedback_no_learning_control()
    summary["recursive_state_evolution_probe"] = recursive_state_evolution_probe()
    summary["cohen_complex_systems_probe"] = cohen_complex_systems_probe()
    summary["audit_counterfactual"] = audit_counterfactual_experiment()
    summary["deterministic_replay"] = deterministic_replay_experiment()
    summary["unknown_initial_state"] = initial_state_experiment()
    summary["first_law"] = first_law_experiment()
    write_json(RESULTS / "EXPERIMENT_SUMMARY.json", summary)

    # Compact human-readable result table.
    lines = [
        "# v1.0.0 experiment result summary",
        "",
        "These are tests of the executable toy model and its invariants. They are not empirical evidence that VowOS or HORTRAME solves AI alignment.",
        "",
        f"- Baseline: {summary['baseline']['events_total']} total events, {summary['baseline']['audit_packets']} audit packets, {summary['baseline']['multi_cause_events']} multi-cause events; invariants={summary['baseline']['invariants']['pass']}.",
        f"- Horizon probe: expected modeled reach changes from {summary['horizon'][0]['expected_nodes']:.3f} at H=1 to {summary['horizon'][-1]['expected_nodes']:.3f} at H=6; max uncertainty changes from {summary['horizon'][0]['max_uncertainty']:.3f} to {summary['horizon'][-1]['max_uncertainty']:.3f}.",
        f"- DAG probe: two independent parents both happen-before their shared child={summary['causal_dag']['parent_A_happens_before_child'] and summary['causal_dag']['parent_B_happens_before_child']}.",
        f"- Biased-auditor probe: recursive audit materialized={summary['biased_auditor']['recursive_audit_materialized']}; discrepancy detected={summary['biased_auditor']['power_audit_detected_discrepancy']}; final gate={summary['biased_auditor']['final_gate']}.",
        f"- Lens epoch probe: historical packet unchanged={summary['lens_epoch']['historical_packet_unchanged']}; governance event={summary['lens_epoch']['governance_event_kind']}.",
        f"- Recursive evolution probe: mean effective-response model error moved from {summary['recursive_evolution']['initial_mean']:.4f} to {summary['recursive_evolution']['final_mean']:.4f} after {summary['recursive_evolution']['steps']} materialized feedback deliveries across {summary['recursive_evolution']['n_seeds']} seeds; all runs materialized feedback={summary['recursive_evolution']['all_runs_materialized_feedback']}.",
        f"- Frozen response-model-learning control: pass={summary['recursive_feedback_no_learning']['pass']}; recursive state evolution continues while learned response posteriors remain frozen.",
        f"- State-evolution probe: pass={summary['recursive_state_evolution_probe']['pass']}; with model learning frozen, evolved ordinary state changes the environment's effective next-response probability.",
        f"- Cohen complex-systems perturbation probe: pass={summary['cohen_complex_systems_probe']['pass']}; {summary['cohen_complex_systems_probe']['distinct_channel_intensity_signatures']} distinct channel/intensity state-change signatures; context uncertainty-delta range={summary['cohen_complex_systems_probe']['context_uncertainty_delta_range']:.6f}; recovery/critical-transition claims explicitly disabled.",
        f"- Deterministic replay: identical={summary['deterministic_replay']['identical']}.",
        f"- Unknown initial state: pass={summary['unknown_initial_state']['pass']}.",
        f"- First-law non-compensation: pass={summary['first_law']['pass']}.",
        "",
        "See the JSON/CSV files for exact values and fixed seeds.",
    ]
    (RESULTS / "RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
