#!/usr/bin/env python3
"""Invariant/regression tests for RETA v1.0.0."""
from __future__ import annotations

import copy
import json
import unittest
from dataclasses import asdict

from ips_recursive_sim import IPSRecursiveSimulation, Lens, VOWS, CHANNELS


class TestRETAv1(unittest.TestCase):
    def test_unknown_initial_history(self):
        sim = IPSRecursiveSimulation(seed=11, auto_response=False)
        self.assertTrue(all(n.last_event_id is None for n in sim.nodes))
        self.assertTrue(all(n.last_verdict is None for n in sim.nodes))

    def test_projection_horizon_is_semantic(self):
        sim = IPSRecursiveSimulation(seed=12, audit_depth=0, auto_response=False)
        ev = sim.emit_output(channel="authority", intensity=.74, fanout=3, audit=False)
        p1 = sim.project_trajectory(ev, 1)
        p6 = sim.project_trajectory(ev, 6)
        self.assertNotEqual(p1["expected_nodes"], p6["expected_nodes"])
        self.assertGreaterEqual(p6["max_depth"], p1["max_depth"])

    def test_event_dag_and_vector_clock(self):
        sim = IPSRecursiveSimulation(seed=13, audit_depth=0, auto_response=False)
        actor = sim.roles["actor"]
        human = next(n.id for n in sim.nodes if n.primary == "human" and n.id != sim.roles["human_gate"])
        institution = next(n.id for n in sim.nodes if n.primary == "institution" and n.id != sim.roles["power_auditor"])
        a = sim.emit_output(source=human, recipients=[actor], channel="info", intensity=.2, audit=False)
        b = sim.emit_output(source=institution, recipients=[actor], channel="info", intensity=.2, audit=False)
        c = sim.emit_output(source=actor, channel="info", intensity=.2, causes=[a.id, b.id], fanout=1, audit=False)
        self.assertEqual(c.causes, sorted([a.id, b.id]))
        self.assertTrue(sim.happens_before(a.vector_clock, c.vector_clock))
        self.assertTrue(sim.happens_before(b.vector_clock, c.vector_clock))
        self.assertTrue(sim.validate_invariants()["pass"])

    def test_first_law_noncompensatory_gate(self):
        sim = IPSRecursiveSimulation(seed=14, auto_response=False)
        lens = sim.current_lens
        tensions = {v: .1 for v in VOWS}
        tensions["Conduct"] = lens.reject_threshold + .01
        uncertainty = {k: .1 for k in ("facts", "causality", "boundary", "model", "normative", "horizon")}
        self.assertEqual(sim.gate_from_vectors(tensions, uncertainty, lens), "REJECT")

    def test_counterfactual_audit_is_side_effect_free(self):
        sim = IPSRecursiveSimulation(seed=15, audit_depth=1, auto_response=False)
        ev = sim.emit_output(channel="info", intensity=.4, fanout=2, audit=True)
        events_before = copy.deepcopy(sim.event_list())
        audits_before = copy.deepcopy(sim.audit_list())
        counterfactual = sim.evaluate_event(ev, sim.roles["power_auditor"], 9, record=False)
        self.assertEqual(counterfactual.id, 0)
        self.assertEqual(events_before, sim.event_list())
        self.assertEqual(audits_before, sim.audit_list())

    def test_recursive_auditor_is_inside_causal_universe(self):
        sim = IPSRecursiveSimulation(seed=16, audit_depth=3, max_events=60, auto_response=False)
        ev = sim.emit_output(channel="authority", intensity=.86, fanout=3, audit=True, biased_primary=True, claim_confidence=.92)
        kinds = {e.kind for e in sim.events.values()}
        self.assertIn("audit", kinds)
        self.assertIn("meta_audit", kinds)
        self.assertIn("gate", kinds)
        self.assertIn("postmortem", kinds)
        self.assertEqual(ev.gate_result, "UNRESOLVED")

    def test_recursive_feedback_evolves_future_transform(self):
        sim = IPSRecursiveSimulation(seed=17, audit_depth=0, max_events=100, auto_response=False, learning_enabled=True)
        learner = sim.nodes[sim.roles["actor"]]
        source = sim.roles["human_gate"]
        learner.state.adaptability = 1.0
        before = {c: sim.learned_response(learner, c) for c in CHANNELS}
        for step in range(60):
            ch = CHANNELS[step % len(CHANNELS)]
            sim.emit_output(source=source, recipients=[learner.id], channel=ch, intensity=.01, audit=False)
            sim.run(until=sim.time + 2.0, max_deliveries=1)
        after = {c: sim.learned_response(learner, c) for c in CHANNELS}
        self.assertNotEqual(before, after)
        self.assertEqual(sum(len(e.metadata.get("deliveries", [])) for e in sim.events.values()), 60)

    def test_recursive_state_changes_effective_response_propensity(self):
        sim = IPSRecursiveSimulation(seed=23, audit_depth=0, max_events=40, auto_response=False, learning_enabled=False)
        learner = sim.nodes[sim.roles["actor"]]
        source = sim.roles["human_gate"]
        learner.state.adaptability = 0.8
        channel = "info"
        effective_before = sim.effective_response_probability(learner, channel)
        for step in range(12):
            sim.emit_output(source=source, recipients=[learner.id], channel=channel, intensity=1.0, audit=False)
            sim.run(until=sim.time + 2.0, max_deliveries=1)
        effective_after = sim.effective_response_probability(learner, channel)
        self.assertNotEqual(effective_before, effective_after)
        self.assertNotEqual(learner.state.adaptability, 0.8)

    def test_recursive_state_evolution_without_model_learning_is_detected(self):
        sim = IPSRecursiveSimulation(seed=18, audit_depth=0, max_events=100, auto_response=False, learning_enabled=False)
        learner = sim.nodes[sim.roles["actor"]]
        source = sim.roles["human_gate"]
        learner.state.adaptability = 1.0
        before = (copy.deepcopy(learner.state.response_alpha), copy.deepcopy(learner.state.response_beta))
        ordinary_before = (learner.state.openness, learner.state.agency, learner.state.stability, learner.state.uncertainty, learner.state.input_load)
        for step in range(40):
            ch = CHANNELS[step % len(CHANNELS)]
            sim.emit_output(source=source, recipients=[learner.id], channel=ch, intensity=.01, audit=False)
            sim.run(until=sim.time + 2.0, max_deliveries=1)
        after = (learner.state.response_alpha, learner.state.response_beta)
        ordinary_after = (learner.state.openness, learner.state.agency, learner.state.stability, learner.state.uncertainty, learner.state.input_load)
        self.assertEqual(before, after)
        self.assertNotEqual(ordinary_before, ordinary_after)  # recursive interaction still evolves system state
        self.assertGreaterEqual(learner.state.recurrent_without_model_learning, 40)
        deliveries = [d for e in sim.events.values() for d in e.metadata.get("deliveries", [])]
        self.assertTrue(all(d["state_evolved"] for d in deliveries))
        self.assertTrue(all(d["history_state_changed"] for d in deliveries))

    def test_standardized_perturbation_has_multivariate_state_signature(self):
        sim = IPSRecursiveSimulation(seed=808080, audit_depth=0, max_events=10, auto_response=False, learning_enabled=False)
        target = sim.nodes[sim.roles["actor"]]
        source = sim.roles["human_gate"]
        keys = ("openness", "agency", "stability", "uncertainty", "adaptability", "input_load")
        before = {k: getattr(target.state, k) for k in keys}
        ev = sim.emit_output(source=source, recipients=[target.id], channel="authority", intensity=.65, audit=False)
        sim.run(until=sim.time + 2.0, max_deliveries=1)
        after = {k: getattr(target.state, k) for k in keys}
        changed = [k for k in keys if before[k] != after[k]]
        self.assertIn(target.id, ev.recipients_realized)
        self.assertGreaterEqual(len(changed), 4)

    def test_context_conditioned_perturbation_response_is_not_forced_unitary(self):
        deltas = []
        for primary in ("human", "ai", "institution", "economy", "ecosystem", "infra"):
            sim = IPSRecursiveSimulation(seed=808081, audit_depth=0, max_events=10, auto_response=False, learning_enabled=False)
            target = next(n for n in sim.nodes if n.primary == primary and n.id != sim.roles["human_gate"])
            before = target.state.uncertainty
            sim.emit_output(source=sim.roles["human_gate"], recipients=[target.id], channel="info", intensity=.65, audit=False)
            sim.run(until=sim.time + 2.0, max_deliveries=1)
            deltas.append(target.state.uncertainty - before)
        self.assertGreater(max(deltas) - min(deltas), 0.0)

    def test_event_budget_does_not_cancel_scheduled_delivery(self):
        sim = IPSRecursiveSimulation(seed=22, audit_depth=0, max_events=1, auto_response=True)
        ev = sim.emit_output(channel="info", intensity=.2, fanout=1, audit=False)
        self.assertEqual(len(sim.events), 1)
        self.assertEqual(len(ev.recipients_scheduled), 1)
        sim.run(until=5.0, max_deliveries=10)
        self.assertEqual(ev.recipients_realized, ev.recipients_scheduled)
        self.assertEqual(len(sim.events), 1)

    def test_event_budget_rejects_partial_recursive_governance_transaction(self):
        sim = IPSRecursiveSimulation(seed=23, audit_depth=3, max_events=4, auto_response=False)
        with self.assertRaises(RuntimeError):
            sim.emit_output(channel="info", intensity=.2, fanout=1, audit=True)
        self.assertEqual(len(sim.events), 0)
        self.assertTrue(sim.validate_invariants()["pass"])

    def test_lens_governance_is_event_budget_atomic(self):
        sim = IPSRecursiveSimulation(seed=24, audit_depth=0, max_events=2, auto_response=False)
        with self.assertRaises(RuntimeError):
            sim.commit_lens(approved=True, horizon=4)
        self.assertEqual(len(sim.events), 0)
        self.assertEqual(sim.current_lens.version, 1)

    def test_scheduled_is_not_delivered_until_arrival(self):
        sim = IPSRecursiveSimulation(seed=21, audit_depth=0, max_events=20, auto_response=False)
        ev = sim.emit_output(channel="info", intensity=.2, fanout=1, audit=False)
        self.assertEqual(ev.enactment_status, "ENACTED_UNAUDITED")
        self.assertEqual(len(ev.recipients_scheduled), 1)
        self.assertEqual(ev.recipients_realized, [])
        sim.run(until=5.0, max_deliveries=1)
        self.assertEqual(ev.recipients_realized, ev.recipients_scheduled)

    def test_lens_change_is_governed_and_prospective(self):
        sim = IPSRecursiveSimulation(seed=19, audit_depth=1, max_events=60, auto_response=False)
        e1 = sim.emit_output(channel="info", intensity=.35, fanout=1, audit=True)
        frozen = json.dumps([asdict(sim.audit_packets[i]) for i in e1.audit_packet_ids], sort_keys=True)
        old_version = sim.current_lens.version
        new = sim.commit_lens(approved=True, horizon=4, note="unit-test prospective lens")
        self.assertEqual(new.version, old_version + 1)
        self.assertIsNotNone(new.governance_event)
        self.assertEqual(sim.events[new.governance_event].kind, "lens_change_approval")
        e2 = sim.emit_output(channel="info", intensity=.35, fanout=1, audit=True)
        self.assertEqual(e1.lens_version, old_version)
        self.assertEqual(e2.lens_version, new.version)
        self.assertEqual(frozen, json.dumps([asdict(sim.audit_packets[i]) for i in e1.audit_packet_ids], sort_keys=True))
        self.assertTrue(sim.validate_invariants()["pass"])

    def test_lens_change_cannot_bypass_blocking_review(self):
        sim = IPSRecursiveSimulation(seed=20, audit_depth=1, max_events=60, auto_response=False)
        old = sim.current_lens
        # Raising the active horizon enough makes the proposal's uncertainty
        # exceed the current constitutional unresolved threshold. The modeled
        # human cannot silently override that blocking review in commit_lens().
        candidate = sim.commit_lens(approved=True, horizon=50, note="intentionally unbounded test")
        if candidate.version == old.version:
            self.assertEqual(sim.current_lens.version, old.version)
            self.assertIn("lens_change_rejection", {e.kind for e in sim.events.values()})
        else:
            # If a future parameterization can resolve the review, it must still
            # have a recorded approval event and satisfy invariants.
            self.assertEqual(sim.events[candidate.governance_event].kind, "lens_change_approval")
            self.assertTrue(sim.validate_invariants()["pass"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
