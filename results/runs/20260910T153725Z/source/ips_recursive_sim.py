#!/usr/bin/env python3
"""RETA v1.0.0 — deterministic conceptual recursive simulator.

Research status: executable hypothesis model, not an empirical alignment metric or
safety guarantee. The engine is dependency-free (Python standard library only).

The v1.0 design makes five changes explicit:
  1. causal history is a DAG, not a parent tree;
  2. audit/gate outputs are themselves causal events inside the IPS network;
  3. consequence horizon changes the computed audit;
  4. uncertainty is a vector, not a single epistemic scalar;
  5. recursive state change/evolution is constitutive of the model. Vow 5 audits
     the quality/direction of that evolution rather than acting as an optional
     post-processing step.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Iterable, Any
import argparse
import csv
import hashlib
import heapq
import json
import math

CHANNELS = ("info", "resource", "authority", "physical", "ecology")
MACROS = ("human", "ai", "institution", "economy", "ecosystem", "infra")
VOWS = ("Purpose", "Method", "Conduct", "Integrity", "Evolution")

# Macro risk is intentionally illustrative. It is a structural simulation
# parameter, not a claim that one domain is intrinsically more dangerous.
MACRO_RISK = {
    "human": 0.38,
    "ai": 0.48,
    "institution": 0.36,
    "economy": 0.44,
    "ecosystem": 0.52,
    "infra": 0.50,
}
CHANNEL_RISK = {
    "info": 0.30,
    "resource": 0.43,
    "authority": 0.62,
    "physical": 0.67,
    "ecology": 0.70,
}
IRREVERSIBILITY = {
    "info": 0.24,
    "resource": 0.42,
    "authority": 0.58,
    "physical": 0.78,
    "ecology": 0.82,
}
EVIDENCE_UNCERTAINTY = {
    "observed": 0.06,
    "source-supported": 0.12,
    "inferred": 0.34,
    "latent": 0.62,
    "synthetic": 0.72,
}


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


class PCG32:
    """Small deterministic RNG with explicit algorithm for replay stability."""

    def __init__(self, seed: int, seq: int = 54):
        self.state = 0
        self.inc = ((seq << 1) | 1) & 0xFFFFFFFFFFFFFFFF
        self._next_u32()
        self.state = (self.state + (seed & 0xFFFFFFFFFFFFFFFF)) & 0xFFFFFFFFFFFFFFFF
        self._next_u32()

    def _next_u32(self) -> int:
        oldstate = self.state
        self.state = (oldstate * 6364136223846793005 + self.inc) & 0xFFFFFFFFFFFFFFFF
        xorshifted = (((oldstate >> 18) ^ oldstate) >> 27) & 0xFFFFFFFF
        rot = (oldstate >> 59) & 31
        return ((xorshifted >> rot) | (xorshifted << ((-rot) & 31))) & 0xFFFFFFFF

    def random(self) -> float:
        return self._next_u32() / 4294967296.0

    def randint(self, a: int, b: int) -> int:
        return a + int(self.random() * (b - a + 1))

    def choice(self, xs: List[Any]):
        if not xs:
            raise IndexError("choice from empty sequence")
        return xs[min(len(xs) - 1, int(self.random() * len(xs)))]

    def uniform(self, a: float, b: float) -> float:
        return a + (b - a) * self.random()


@dataclass
class NodeState:
    openness: float
    agency: float
    stability: float
    uncertainty: float
    adaptability: float
    input_load: float = 0.0
    # Beta counts for the node's learned response propensity by channel.
    response_alpha: Dict[str, float] = field(default_factory=lambda: {c: 1.0 for c in CHANNELS})
    response_beta: Dict[str, float] = field(default_factory=lambda: {c: 1.0 for c in CHANNELS})
    prediction_error_ema: float = 0.50
    recent_learning_gain: float = 0.0
    recurrent_without_model_learning: int = 0


@dataclass
class Node:
    id: int
    primary: str
    memberships: List[str]
    type: str
    pos: Tuple[float, float, float]
    state: NodeState
    true_response: Dict[str, float]
    out_edges: List[int] = field(default_factory=list)
    in_edges: List[int] = field(default_factory=list)
    last_event_id: Optional[int] = None
    last_verdict: Optional[str] = None
    recent_inputs: List[int] = field(default_factory=list)
    logical_counter: int = 0


@dataclass
class Edge:
    id: int
    source: int
    target: int
    channel: str
    strength: float
    delay: float
    feedback: bool = False


@dataclass(frozen=True)
class Lens:
    version: int = 1
    horizon: int = 3
    sensitivities: Tuple[float, float, float, float, float] = (1, 1, 1, 1, 1)
    modify_threshold: float = 0.52
    reject_threshold: float = 0.78
    unresolved_threshold: float = 0.72
    note: str = "v1.0 constitutional epoch 1"
    governance_event: Optional[int] = None


@dataclass
class Event:
    id: int
    roots: List[int]
    kind: str
    source: int
    causes: List[int]
    channel: str
    intensity: float
    label: str
    created_at: float
    recipients_requested: List[int]
    recipients_scheduled: List[int]
    recipients_realized: List[int]
    enactment_status: str
    evidence_status: str
    runtime_status: str
    boundary: Dict[str, Any]
    claim_confidence: float
    vector_clock: Dict[str, int]
    lens_version: Optional[int] = None
    gate_result: Optional[str] = None
    audit_packet_ids: List[int] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditPacket:
    id: int
    target_event_id: int
    auditor_node: int
    audit_depth: int
    lens_version: int
    horizon: int
    tensions: Dict[str, float]
    uncertainty: Dict[str, float]
    projection: Dict[str, float]
    gate: str
    diagnostic_trace: float
    frozen_at: float
    target_kind: str
    notes: List[str]


@dataclass(order=True)
class Delivery:
    when: float
    serial: int
    event_id: int = field(compare=False)
    target: int = field(compare=False)
    intensity: float = field(compare=False)


class IPSRecursiveSimulation:
    def __init__(
        self,
        seed: int = 20260909,
        lens: Lens | None = None,
        audit_depth: int = 2,
        max_events: int = 240,
        auto_response: bool = True,
        audit_auto_responses: bool = True,
        learning_enabled: bool = True,
    ):
        self.seed = int(seed)
        self.rng = PCG32(self.seed)
        self.time = 0.0
        self.audit_depth = int(audit_depth)
        self.max_events = int(max_events)
        self.auto_response = bool(auto_response)
        self.audit_auto_responses = bool(audit_auto_responses)
        self.learning_enabled = bool(learning_enabled)
        self.nodes: List[Node] = []
        self.edges: List[Edge] = []
        self.events: Dict[int, Event] = {}
        self.audit_packets: Dict[int, AuditPacket] = {}
        self.event_counter = 0
        self.root_counter = 0
        self.audit_counter = 0
        self.delivery_counter = 0
        self.queue: List[Delivery] = []
        self.lens_epochs: List[Lens] = [lens or Lens()]
        self.current_lens = self.lens_epochs[-1]
        self._build_network()
        self.roles = self._assign_governance_roles()

    # ---------- network construction ----------
    def _build_network(self) -> None:
        macro_defs = {
            "human": ((-2.3, .9, .1), ["individual human", "family/group", "community", "culture/language", "governance participant", "education participant", "media participant", "civil society actor"]),
            "ai": ((1.6, 1.1, .7), ["model instance", "autonomous agent", "agent team", "memory/state store", "tool service", "monitor/auditor", "planner", "platform"]),
            "institution": ((.15, 2.45, -.8), ["research lab", "university", "journal/reviewer", "newsroom", "court", "regulator", "standards body", "public administration"]),
            "economy": ((-1.25, -1.55, .55), ["consumer", "firm", "market", "bank/finance", "supply chain", "labor market", "insurer", "logistics market"]),
            "ecosystem": ((1.45, -1.75, -.8), ["organism/population", "habitat", "food web", "watershed", "nutrient cycle", "pollinator network", "soil system", "ocean process"]),
            "infra": ((2.65, -.35, .95), ["energy grid", "data center", "telecom network", "transport network", "manufacturing system", "sensor network", "water system", "physical actuator"]),
        }
        near = {
            "human": ["institution", "economy", "ai"],
            "ai": ["institution", "infra", "human"],
            "institution": ["human", "ai", "economy"],
            "economy": ["human", "infra", "ecosystem"],
            "ecosystem": ["economy", "infra", "human"],
            "infra": ["ai", "economy", "ecosystem"],
        }
        counts = {"human": 20, "ai": 20, "institution": 15, "economy": 15, "ecosystem": 15, "infra": 15}
        nid = 0
        for macro in MACROS:
            center, types = macro_defs[macro]
            for k in range(counts[macro]):
                memberships = [macro]
                if self.rng.random() < .58:
                    memberships.append(self.rng.choice(near[macro]))
                if self.rng.random() < .18:
                    opts = [m for m in MACROS if m not in memberships]
                    memberships.append(self.rng.choice(opts))
                centers = [macro_defs[m][0] for m in memberships]
                c = tuple(sum(v[d] for v in centers) / len(centers) for d in range(3))
                pos = (c[0] + self.rng.uniform(-1.2, 1.2), c[1] + self.rng.uniform(-1.1, 1.1), c[2] + self.rng.uniform(-1.15, 1.15))
                st = NodeState(
                    openness=self.rng.uniform(.25, .95),
                    agency=self.rng.uniform(.20, .95),
                    stability=self.rng.uniform(.30, .95),
                    uncertainty=self.rng.uniform(.15, .85),
                    adaptability=self.rng.uniform(.25, .95),
                )
                # Hidden simulation truth used only to measure whether recursive
                # feedback improves the model's estimates; never exposed as an
                # epistemic privilege available to the simulated IPS.
                tr = {cname: self.rng.uniform(.10, .82) for cname in CHANNELS}
                self.nodes.append(Node(nid, macro, memberships, types[k % len(types)], pos, st, tr))
                nid += 1

        def distance(a: Node, b: Node) -> float:
            return math.dist(a.pos, b.pos)

        def choose_channel(a: Node, b: Node) -> str:
            common = set(a.memberships) | set(b.memberships)
            r = self.rng.random()
            if "ecosystem" in common and ("economy" in common or "infra" in common):
                return "ecology" if r < .55 else "resource"
            if "institution" in common or "human" in common:
                return "info" if r < .58 else ("authority" if self.rng.random() < .5 else "resource")
            if "ai" in common and "infra" in common:
                return "info" if r < .65 else "physical"
            return CHANNELS[min(3, int(self.rng.random() * 4))]

        def add_edge(a: int, b: int):
            if a == b or any(e.source == a and e.target == b for e in self.edges):
                return
            eid = len(self.edges)
            edge = Edge(eid, a, b, choose_channel(self.nodes[a], self.nodes[b]), self.rng.uniform(.25, 1.0), self.rng.uniform(.20, 1.60))
            self.edges.append(edge)
            self.nodes[a].out_edges.append(eid)
            self.nodes[b].in_edges.append(eid)

        for n in self.nodes:
            candidates = sorted(
                (x for x in self.nodes if x.id != n.id),
                key=lambda x: distance(n, x) * (.72 if set(n.memberships) & set(x.memberships) else 1.2),
            )
            k = 3 + self.rng.randint(0, 2)
            for x in candidates[:k]:
                add_edge(n.id, x.id)
            if self.rng.random() < .70:
                add_edge(n.id, self.rng.randint(0, len(self.nodes) - 1))

        pairs = {(e.source, e.target) for e in self.edges}
        for e in self.edges:
            e.feedback = (e.target, e.source) in pairs

    def _assign_governance_roles(self) -> Dict[str, int]:
        def first(primary: str, contains: str) -> int:
            for n in self.nodes:
                if n.primary == primary and contains in n.type:
                    return n.id
            return next(n.id for n in self.nodes if n.primary == primary)

        return {
            "actor": first("ai", "autonomous agent"),
            "primary_auditor": first("ai", "monitor/auditor"),
            "power_auditor": first("institution", "regulator"),
            "human_gate": first("human", "governance participant"),
            "lens_steward": first("institution", "standards body"),
        }

    # ---------- clocks / event DAG ----------
    def _clock_for_event(self, source: int, causes: Iterable[int]) -> Dict[str, int]:
        merged: Dict[str, int] = {}
        for cid in causes:
            ev = self.events.get(cid)
            if not ev:
                continue
            for k, v in ev.vector_clock.items():
                merged[k] = max(merged.get(k, 0), int(v))
        n = self.nodes[source]
        n.logical_counter = max(n.logical_counter, merged.get(str(source), 0)) + 1
        merged[str(source)] = n.logical_counter
        return dict(sorted(merged.items(), key=lambda kv: int(kv[0])))

    @staticmethod
    def happens_before(a: Dict[str, int], b: Dict[str, int]) -> bool:
        keys = set(a) | set(b)
        le = all(a.get(k, 0) <= b.get(k, 0) for k in keys)
        lt = any(a.get(k, 0) < b.get(k, 0) for k in keys)
        return le and lt

    # ---------- model learning / recursive evolution ----------
    def learned_response(self, node: Node, channel: str) -> float:
        a = node.state.response_alpha[channel]
        b = node.state.response_beta[channel]
        return a / (a + b)

    def response_posterior_variance(self, node: Node, channel: str) -> float:
        a = node.state.response_alpha[channel]
        b = node.state.response_beta[channel]
        den = (a + b) ** 2 * (a + b + 1.0)
        return (a * b / den) if den else 0.0

    def observable_model_uncertainty(self, node: Node) -> float:
        # Beta(1,1) variance is 1/12. Normalize to [0,1]. This is available
        # to the simulated processor and does not inspect latent ground truth.
        return clamp(sum(self.response_posterior_variance(node, c) for c in CHANNELS) / len(CHANNELS) * 12.0)

    def effective_response_probability(self, node: Node, channel: str) -> float:
        """Latent environment probability for the next response at current state.

        ``true_response`` is a hidden base propensity. Recursive state evolution
        changes the realized propensity through adaptability, so external model
        error must be scored against this effective probability rather than the
        base parameter alone. Runtime audit/projection code cannot call this
        method because it exposes latent simulator truth.
        """
        return clamp(node.true_response[channel] * (0.72 + 0.28 * node.state.adaptability))

    def node_model_error(self, node: Node) -> float:
        return sum(abs(self.learned_response(node, c) - self.effective_response_probability(node, c)) for c in CHANNELS) / len(CHANNELS)

    def network_model_error(self) -> float:
        return sum(self.node_model_error(n) for n in self.nodes) / len(self.nodes)

    def _learn_from_arrival(self, node: Node, channel: str, responded: bool) -> float:
        # Runtime adaptation receives only an observed Bernoulli outcome and the
        # processor's own posterior state. Hidden simulation truth is not used
        # to decide how the simulated processor learns or changes adaptability.
        pred_before = self.learned_response(node, channel)
        var_before = self.response_posterior_variance(node, channel)
        observation = 1.0 if responded else 0.0
        if not self.learning_enabled:
            # Negative-control mode: the event is still received and the
            # prediction error is still observable, but the internal response
            # model is deliberately prevented from updating. Repeated feedback
            # therefore creates recursive state evolution without response-model learning;
            # the Vow-5 diagnostics should detect the recurrent_without_model_learning pattern.
            prediction_error = abs(pred_before - observation)
            node.state.recent_learning_gain *= 0.85
            node.state.prediction_error_ema = 0.90 * node.state.prediction_error_ema + 0.10 * prediction_error
            node.state.recurrent_without_model_learning += 1
            return 0.0
        if responded:
            node.state.response_alpha[channel] += 1.0
        else:
            node.state.response_beta[channel] += 1.0
        var_after = self.response_posterior_variance(node, channel)
        observable_gain = max(0.0, var_before - var_after)
        prediction_error = abs(pred_before - observation)
        node.state.recent_learning_gain = 0.85 * node.state.recent_learning_gain + 0.15 * observable_gain
        node.state.prediction_error_ema = 0.90 * node.state.prediction_error_ema + 0.10 * prediction_error
        if observable_gain <= 1e-9:
            node.state.recurrent_without_model_learning += 1
        else:
            node.state.recurrent_without_model_learning = max(0, node.state.recurrent_without_model_learning - 1)
        return observable_gain

    # ---------- projection / uncertainty / Vow gate ----------
    def _outgoing(self, node_id: int, preferred_channel: Optional[str] = None) -> List[Edge]:
        es = [self.edges[eid] for eid in self.nodes[node_id].out_edges]
        if preferred_channel:
            same = [e for e in es if e.channel == preferred_channel]
            other = [e for e in es if e.channel != preferred_channel]
            es = same + other
        return sorted(es, key=lambda e: (-e.strength, e.id))

    def project_trajectory(self, event: Event, horizon: int) -> Dict[str, float]:
        """Deterministic horizon-sensitive expected reach/risk projection.

        No random draws occur here. This is deliberate: changing the display or
        auditing the same frozen event must not consume the simulation RNG.
        """
        horizon = max(1, int(horizon))
        if not event.recipients_requested:
            return {
                "expected_impact": 0.0, "agency_risk": 0.0, "irreversibility": 0.0,
                "model_uncertainty": clamp(0.55 * self.nodes[event.source].state.uncertainty + 0.45 * self.observable_model_uncertainty(self.nodes[event.source])),
                "evolution_risk": clamp(0.45 * self.nodes[event.source].state.prediction_error_ema + 0.30 * (1 - self.nodes[event.source].state.adaptability) + 0.25 * (1 - self.nodes[event.source].state.stability)),
                "boundary_ambiguity": 0.0, "expected_nodes": 0.0,
                "domains": 1.0, "max_depth": 0.0,
            }
        q: List[Tuple[int, int, float, str]] = [(r, 1, event.intensity, event.channel) for r in event.recipients_requested]
        best_weight: Dict[Tuple[int, int], float] = {}
        domains = {self.nodes[event.source].primary}
        total_w = impact = agency = irrev = model_u = evo = boundary = 0.0
        expected_nodes = 0.0
        max_depth = 0
        while q:
            nid, depth, weight, channel = q.pop(0)
            if depth > horizon or weight < 0.01:
                continue
            key = (nid, depth)
            if weight <= best_weight.get(key, -1.0):
                continue
            best_weight[key] = weight
            n = self.nodes[nid]
            domains.update(n.memberships)
            disc = 0.72 ** (depth - 1)
            w = weight * disc
            total_w += w
            expected_nodes += min(1.0, w)
            max_depth = max(max_depth, depth)
            domain_risk = sum(MACRO_RISK[m] for m in n.memberships) / len(n.memberships)
            impact += w * (0.55 * CHANNEL_RISK[channel] + 0.45 * domain_risk)
            agency += w * (1 - n.state.agency) * (1.25 if channel == "authority" else 1.0)
            irrev += w * IRREVERSIBILITY[channel] * (1.05 - 0.35 * n.state.adaptability)
            model_u += w * (0.55 * n.state.uncertainty + 0.45 * self.observable_model_uncertainty(n))
            # Evolution risk = recursive change without enough adaptive learning,
            # not the absence of change itself. Only observable runtime state is
            # used here; hidden simulation truth is reserved for validation.
            rigidity = 1 - n.state.adaptability
            instability = 1 - n.state.stability
            no_learning = clamp(n.state.recurrent_without_model_learning / 8.0)
            evo += w * (0.30 * n.state.prediction_error_ema + 0.24 * self.observable_model_uncertainty(n) + 0.20 * rigidity + 0.16 * instability + 0.10 * no_learning)
            boundary += w * clamp((len(n.memberships) - 1) / 2.0)
            if depth < horizon:
                p_resp = self.learned_response(n, channel)
                for e in self._outgoing(nid, channel)[:3]:
                    next_channel = channel if e.channel == channel else e.channel
                    next_w = w * e.strength * p_resp * (0.88 if next_channel == channel else 0.68)
                    q.append((e.target, depth + 1, next_w, next_channel))
        den = max(total_w, 1e-9)
        return {
            "expected_impact": clamp(impact / den),
            "agency_risk": clamp(agency / den),
            "irreversibility": clamp(irrev / den),
            "model_uncertainty": clamp(model_u / den),
            "evolution_risk": clamp(evo / den),
            "boundary_ambiguity": clamp(boundary / den),
            "expected_nodes": round(expected_nodes, 6),
            "domains": float(len(domains)),
            "max_depth": float(max_depth),
        }

    def uncertainty_vector(self, event: Event, projection: Dict[str, float], lens: Lens) -> Dict[str, float]:
        src = self.nodes[event.source]
        facts = clamp(0.68 * EVIDENCE_UNCERTAINTY.get(event.evidence_status, .5) + 0.32 * src.state.uncertainty)
        # Causal uncertainty grows with projection depth and cross-domain reach.
        causality = clamp(0.10 + 0.075 * projection["max_depth"] + 0.055 * max(0.0, projection["domains"] - 1) + 0.34 * projection["model_uncertainty"])
        boundary = clamp(0.08 + 0.62 * projection["boundary_ambiguity"] + 0.06 * max(0.0, projection["domains"] - 2))
        model = clamp(0.12 + 0.64 * projection["model_uncertainty"] + 0.045 * lens.horizon)
        # Normative uncertainty is deliberately never zero: the Five Vows are a
        # proposed internal constitution, not an empirically universal metric.
        normative = clamp(0.20 + 0.14 * projection["agency_risk"] + 0.10 * projection["expected_impact"])
        horizon_u = clamp(0.07 + 0.105 * max(0, lens.horizon - 1) + 0.08 * max(0.0, projection["domains"] - 1))
        return {
            "facts": facts,
            "causality": causality,
            "boundary": boundary,
            "model": model,
            "normative": normative,
            "horizon": horizon_u,
        }

    def tension_vector(
        self,
        event: Event,
        projection: Dict[str, float],
        uncertainty: Dict[str, float],
        lens: Lens,
        auditor_bias: Optional[Tuple[float, float, float, float, float]] = None,
    ) -> Dict[str, float]:
        src = self.nodes[event.source]
        impact = projection["expected_impact"]
        agency_risk = projection["agency_risk"]
        irrev = projection["irreversibility"]
        cross = clamp((projection["domains"] - 1) / 5.0)
        channel_force = CHANNEL_RISK[event.channel]

        purpose = clamp(0.48 * impact + 0.22 * cross + 0.18 * (1 - src.state.openness) + 0.12 * event.intensity)
        method = clamp(0.34 * channel_force + 0.31 * irrev + 0.21 * agency_risk + 0.14 * (1 - src.state.adaptability))
        conduct = clamp(0.46 * agency_risk + 0.36 * impact + 0.18 * (1 - src.state.agency))
        unsupported_certainty = clamp(event.claim_confidence - (1 - max(uncertainty.values())))
        integrity = clamp(0.30 * uncertainty["facts"] + 0.22 * uncertainty["causality"] + 0.18 * uncertainty["boundary"] + 0.20 * uncertainty["model"] + 0.10 * unsupported_certainty)
        evolution = clamp(
            0.42 * projection["evolution_risk"]
            + 0.20 * src.state.prediction_error_ema
            + 0.16 * self.observable_model_uncertainty(src)
            + 0.13 * (1 - src.state.adaptability)
            + 0.09 * clamp(src.state.recurrent_without_model_learning / 8.0)
        )
        vals = [purpose, method, conduct, integrity, evolution]
        vals = [clamp(vals[i] * lens.sensitivities[i]) for i in range(5)]
        if auditor_bias:
            vals = [clamp(vals[i] * auditor_bias[i]) for i in range(5)]
        return {VOWS[i]: vals[i] for i in range(5)}

    @staticmethod
    def gate_from_vectors(tensions: Dict[str, float], uncertainty: Dict[str, float], lens: Lens) -> str:
        if max(uncertainty.values(), default=0.0) >= lens.unresolved_threshold:
            return "UNRESOLVED"
        if max(tensions.values(), default=0.0) >= lens.reject_threshold:
            return "REJECT"
        if max(tensions.values(), default=0.0) >= lens.modify_threshold:
            return "MODIFY"
        return "PASS"

    def evaluate_event(
        self,
        event: Event,
        auditor_node: int,
        audit_depth: int,
        lens: Optional[Lens] = None,
        auditor_bias: Optional[Tuple[float, float, float, float, float]] = None,
        uncertainty_floors: Optional[Dict[str, float]] = None,
        tension_floors: Optional[Dict[str, float]] = None,
        notes: Optional[List[str]] = None,
        record: bool = True,
    ) -> AuditPacket:
        lens = lens or self.current_lens
        proj = self.project_trajectory(event, lens.horizon)
        unc = self.uncertainty_vector(event, proj, lens)
        if uncertainty_floors:
            unc = {k: max(v, clamp(uncertainty_floors.get(k, 0.0))) for k, v in unc.items()}
        tau = self.tension_vector(event, proj, unc, lens, auditor_bias)
        if tension_floors:
            tau = {k: max(v, clamp(tension_floors.get(k, 0.0))) for k, v in tau.items()}
        gate = self.gate_from_vectors(tau, unc, lens)
        packet_id = self.audit_counter + 1 if record else 0
        packet = AuditPacket(
            id=packet_id,
            target_event_id=event.id,
            auditor_node=auditor_node,
            audit_depth=audit_depth,
            lens_version=lens.version,
            horizon=lens.horizon,
            tensions={k: round(v, 9) for k, v in tau.items()},
            uncertainty={k: round(v, 9) for k, v in unc.items()},
            projection={k: round(v, 9) for k, v in proj.items()},
            gate=gate,
            diagnostic_trace=round(1 - max(tau.values()), 9),
            frozen_at=self.time,
            target_kind=event.kind,
            notes=list(notes or []),
        )
        if record:
            self.audit_counter += 1
            self.audit_packets[packet.id] = packet
            event.audit_packet_ids.append(packet.id)
            event.lens_version = lens.version
        return packet

    # ---------- event emission / audit recursion ----------
    def _pick_recipients(self, source: int, channel: str, fanout: int) -> List[int]:
        es = self._outgoing(source, channel)
        same = [e for e in es if e.channel == channel]
        if len(same) < fanout:
            same += [e for e in es if e.channel != channel]
        out: List[int] = []
        for e in same:
            if e.target not in out:
                out.append(e.target)
            if len(out) >= fanout:
                break
        return out

    def _new_event(
        self,
        source: int,
        channel: str,
        intensity: float,
        label: str,
        causes: Optional[List[int]],
        recipients_requested: List[int],
        kind: str,
        evidence_status: str,
        runtime_status: str,
        claim_confidence: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Event:
        self.event_counter += 1
        if not causes:
            self.root_counter += 1
            roots = [self.root_counter]
            causes = []
        else:
            roots = sorted({r for c in causes if c in self.events for r in self.events[c].roots})
            if not roots:
                self.root_counter += 1
                roots = [self.root_counter]
        clock = self._clock_for_event(source, causes)
        n = self.nodes[source]
        event = Event(
            id=self.event_counter,
            roots=roots,
            kind=kind,
            source=source,
            causes=sorted(set(causes)),
            channel=channel,
            intensity=clamp(intensity),
            label=label,
            created_at=round(self.time, 9),
            recipients_requested=list(dict.fromkeys(recipients_requested)),
            recipients_scheduled=[],
            recipients_realized=[],
            enactment_status="PENDING" if kind == "output" else "ENACTED",
            evidence_status=evidence_status,
            runtime_status=runtime_status,
            boundary={"source_primary": n.primary, "source_memberships": list(n.memberships)},
            claim_confidence=clamp(claim_confidence),
            vector_clock=clock,
            metadata=dict(metadata or {}),
        )
        self.events[event.id] = event
        n.last_event_id = event.id
        return event

    def _edge_between(self, source: int, target: int) -> Optional[Edge]:
        candidates = [self.edges[eid] for eid in self.nodes[source].out_edges if self.edges[eid].target == target]
        return candidates[0] if candidates else None

    def _schedule_delivery(self, event: Event, target: int, intensity: float) -> None:
        edge = self._edge_between(event.source, target)
        delay = edge.delay if edge else 0.25
        self.delivery_counter += 1
        heapq.heappush(self.queue, Delivery(self.time + delay, self.delivery_counter, event.id, target, clamp(intensity)))
        if target not in event.recipients_scheduled:
            event.recipients_scheduled.append(target)

    def _internal_emit_without_audit(
        self,
        source: int,
        recipients: List[int],
        channel: str,
        intensity: float,
        label: str,
        causes: List[int],
        kind: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Event:
        ev = self._new_event(
            source, channel, intensity, label, causes, recipients, kind,
            evidence_status="observed", runtime_status="observed", claim_confidence=.55,
            metadata=metadata,
        )
        for r in recipients:
            self._schedule_delivery(ev, r, intensity)
        self.nodes[source].last_verdict = "NOT_AUDITED"
        return ev

    def recursive_audit(
        self,
        event: Event,
        biased_primary: bool = False,
        depth: Optional[int] = None,
    ) -> Tuple[str, List[int]]:
        """Audit an event inside the same causal universe.

        Operational recursion is finite by declared audit budget. The stopping
        rule is explicit; the implementation does not claim a metaphysical final
        auditor. An audit event is itself an event and can alter later state.

        The governance transaction is event-budget atomic: if the complete
        declared recursive audit cannot fit, no partial audit chain is created.
        """
        depth = self.audit_depth if depth is None else int(depth)
        internal_slots = 2 + (1 if depth >= 2 else 0) + (1 if depth >= 3 else 0)
        if len(self.events) + internal_slots > self.max_events:
            raise RuntimeError("insufficient event budget for complete recursive audit")
        created: List[int] = []
        primary_bias = (1.0, 1.0, 0.55, 0.50, 1.0) if biased_primary else None
        p1 = self.evaluate_event(event, self.roles["primary_auditor"], 0, auditor_bias=primary_bias)

        audit_event = self._internal_emit_without_audit(
            self.roles["primary_auditor"],
            [self.roles["power_auditor"]],
            "info", .45,
            f"audit packet A{p1.id} for E{event.id}",
            [event.id], "audit",
            metadata={"packet_id": p1.id, "reported_gate": p1.gate},
        )
        created.append(audit_event.id)

        final_gate = p1.gate
        meta_packet = None
        meta_event = None
        if depth >= 2:
            # Independent re-evaluation of the original target is the power audit.
            independent = self.evaluate_event(event, self.roles["power_auditor"], 1)
            divergence = max(abs(independent.tensions[k] - p1.tensions[k]) for k in VOWS)
            notes = [f"primary_vs_independent_max_tension_delta={divergence:.6f}"]
            # Evaluate the audit event itself. A large unexplained difference
            # raises epistemic uncertainty in the meta-audit; the already-emitted
            # audit event is not retroactively rewritten.
            if divergence > .18:
                notes.append("power-audit discrepancy above 0.18; audit cannot be final oracle")
            meta_packet = self.evaluate_event(
                audit_event, self.roles["power_auditor"], 1,
                uncertainty_floors={"model": .75} if divergence > .18 else None,
                notes=notes,
            )
            meta_event = self._internal_emit_without_audit(
                self.roles["power_auditor"],
                [self.roles["human_gate"]],
                "authority", .40,
                f"meta-audit A{meta_packet.id} of audit E{audit_event.id}",
                [audit_event.id, event.id], "meta_audit",
                metadata={"packet_id": meta_packet.id, "independent_packet_id": independent.id, "divergence": divergence},
            )
            created.append(meta_event.id)
            # Conservative combination. No favorable audit can cancel a block.
            rank = {"PASS": 0, "MODIFY": 1, "UNRESOLVED": 2, "REJECT": 3}
            final_gate = max((p1.gate, independent.gate, meta_packet.gate), key=lambda g: rank[g])

        gate_causes = [event.id, audit_event.id] + ([meta_event.id] if meta_event else [])
        gate_event = self._internal_emit_without_audit(
            self.roles["human_gate"],
            [event.source],
            "authority", .35,
            f"gate {final_gate} for E{event.id}",
            gate_causes, "gate",
            metadata={"target_event_id": event.id, "gate": final_gate, "audit_budget": depth},
        )
        created.append(gate_event.id)
        event.gate_result = final_gate
        self.nodes[event.source].last_verdict = final_gate

        if depth >= 3:
            # Non-retroactive governance feedback: audit the gate as an event and
            # feed that result back to the original actor and auditors for the next cycle. This closes the evaluator loop
            # across time without pretending there is a final external oracle.
            post_packet = self.evaluate_event(gate_event, self.roles["lens_steward"], 2, notes=["postmortem is prospective; it cannot rewrite the gate already used"] )
            post_event = self._internal_emit_without_audit(
                self.roles["lens_steward"],
                sorted(set([self.roles["primary_auditor"], self.roles["power_auditor"], event.source])),
                "info", .30,
                f"postmortem A{post_packet.id} on gate E{gate_event.id}",
                [event.id, gate_event.id], "postmortem",
                metadata={"packet_id": post_packet.id, "target_gate_event": gate_event.id, "non_retroactive": True},
            )
            created.append(post_event.id)
        return final_gate, created

    def emit_output(
        self,
        source: Optional[int] = None,
        channel: str = "info",
        intensity: float = .65,
        label: str = "realized output",
        causes: Optional[List[int]] = None,
        fanout: int = 2,
        recipients: Optional[List[int]] = None,
        evidence_status: str = "observed",
        runtime_status: str = "observed",
        claim_confidence: float = .65,
        audit: bool = True,
        biased_primary: bool = False,
    ) -> Event:
        audit_slots = 0 if not audit else 2 + (1 if self.audit_depth >= 2 else 0) + (1 if self.audit_depth >= 3 else 0)
        required_slots = 1 + audit_slots
        if len(self.events) + required_slots > self.max_events:
            raise RuntimeError("insufficient event budget for complete output transaction")
        source = self.roles["actor"] if source is None else int(source)
        if channel not in CHANNELS:
            raise ValueError(f"unknown channel {channel}")
        recipients_requested = recipients if recipients is not None else self._pick_recipients(source, channel, fanout)
        ev = self._new_event(
            source, channel, intensity, label, causes or [], recipients_requested,
            "output", evidence_status, runtime_status, claim_confidence,
        )
        gate = "PASS"
        if audit:
            gate, _ = self.recursive_audit(ev, biased_primary=biased_primary)
        else:
            ev.gate_result = "NOT_AUDITED"
        if gate == "PASS" or not audit:
            realized = recipients_requested
            out_intensity = ev.intensity
            ev.enactment_status = "ENACTED_UNAUDITED" if not audit else "ENACTED"
        elif gate == "MODIFY":
            # Concrete minimal-force repair: lower intensity and restrict the
            # route to one requested recipient. This is a toy policy, not a moral theorem.
            realized = recipients_requested[:1]
            out_intensity = ev.intensity * .62
            ev.metadata["modification"] = {"intensity_multiplier": .62, "fanout_cap": 1}
            ev.enactment_status = "MODIFIED_ENACTED"
        else:
            realized = []
            out_intensity = 0.0
            ev.enactment_status = "BLOCKED"
        for r in realized:
            self._schedule_delivery(ev, r, out_intensity)
        if not audit:
            self.nodes[source].last_verdict = "NOT_AUDITED"
        return ev

    # ---------- arrivals and ongoing recursive dynamics ----------
    def _apply_arrival(self, delivery: Delivery) -> None:
        out = self.events[delivery.event_id]
        node = self.nodes[delivery.target]
        if delivery.target not in out.recipients_realized:
            out.recipients_realized.append(delivery.target)
        x = node.state
        recent_inputs_before = list(node.recent_inputs)
        before_state = {
            "openness": x.openness, "agency": x.agency, "stability": x.stability, "uncertainty": x.uncertainty,
            "adaptability": x.adaptability, "input_load": x.input_load, "model_uncertainty": self.observable_model_uncertainty(node),
            "prediction_error_ema": x.prediction_error_ema,
        }
        sign = 0.0
        if out.gate_result == "PASS":
            sign = 0.15
        elif out.gate_result == "MODIFY":
            sign = 0.05
        elif out.gate_result in ("REJECT", "UNRESOLVED"):
            sign = -0.05
        x.input_load = clamp(x.input_load + .14 * delivery.intensity)
        x.stability = clamp(x.stability + .025 * sign - .018 * delivery.intensity * CHANNEL_RISK[out.channel])
        x.openness = clamp(x.openness + .020 * (0.5 - CHANNEL_RISK[out.channel]) + .012 * sign)
        x.agency = clamp(x.agency - .055 * delivery.intensity * (1.0 if out.channel == "authority" else .25) + .018 * sign)
        x.uncertainty = clamp(x.uncertainty + .045 * delivery.intensity * (1 if out.channel == "info" else .55) - .015 * x.stability)
        # Recursive evolution: every arrival changes the state and presents an
        # observation to the node's internal response model.
        p_effective = self.effective_response_probability(node, out.channel)
        responded = self.rng.random() < p_effective
        observable_gain = self._learn_from_arrival(node, out.channel, responded)
        # Beta posterior variance reduction is available to the processor; scale
        # it relative to the Beta(1,1) variance (1/12) before using it as a
        # modest adaptability signal. No latent ground-truth error is consulted.
        x.adaptability = clamp(x.adaptability + .018 * clamp(12.0 * observable_gain) - .003 * max(0, x.input_load - .7))
        node.recent_inputs.append(out.id)
        node.recent_inputs = node.recent_inputs[-6:]
        recent_inputs_after = list(node.recent_inputs)
        after_state = {
            "openness": x.openness, "agency": x.agency, "stability": x.stability, "uncertainty": x.uncertainty,
            "adaptability": x.adaptability, "input_load": x.input_load, "model_uncertainty": self.observable_model_uncertainty(node),
            "prediction_error_ema": x.prediction_error_ema,
        }
        out.metadata.setdefault("deliveries", []).append({
            "target": node.id,
            "at": round(self.time, 9),
            "responded": responded,
            "state_before": {k: round(v, 9) for k, v in before_state.items()},
            "state_after": {k: round(v, 9) for k, v in after_state.items()},
            "recent_inputs_before": recent_inputs_before,
            "recent_inputs_after": recent_inputs_after,
            "ordinary_numeric_state_changed": before_state != after_state,
            "history_state_changed": recent_inputs_before != recent_inputs_after,
            "state_evolved": (before_state != after_state) or (recent_inputs_before != recent_inputs_after),
        })
        if self.auto_response and responded and len(self.events) < self.max_events:
            # Multi-cause by construction when the node has received several
            # recent inputs. This is the key v1.0 transition from trees to a DAG.
            causes = sorted(set(node.recent_inputs[-3:]))
            channel = out.channel if self.rng.random() < .70 else self.rng.choice(list(CHANNELS))
            fanout = 1 + self.rng.randint(0, 2)
            intensity = clamp(delivery.intensity * self.rng.uniform(.48, .82))
            try:
                self.emit_output(
                    source=node.id,
                    channel=channel,
                    intensity=intensity,
                    label=f"recursive response to {','.join('E'+str(c) for c in causes)}",
                    causes=causes,
                    fanout=fanout,
                    evidence_status="observed",
                    claim_confidence=.55,
                    audit=self.audit_auto_responses,
                )
            except RuntimeError:
                pass

    def run(self, until: float = 12.0, max_deliveries: int = 2000) -> None:
        deliveries = 0
        while self.queue and deliveries < max_deliveries:
            d = heapq.heappop(self.queue)
            if d.when > until:
                heapq.heappush(self.queue, d)
                break
            self.time = d.when
            self._apply_arrival(d)
            deliveries += 1
        self.time = max(self.time, min(until, self.time if not self.queue else until))

    def run_status(self) -> Dict[str, Any]:
        """Inspect truncation/pending state without mutating the simulation."""
        return {
            "time": self.time,
            "events": len(self.events),
            "event_budget": self.max_events,
            "event_budget_reached": len(self.events) >= self.max_events,
            "pending_deliveries": len(self.queue),
            "next_delivery_time": self.queue[0].when if self.queue else None,
        }

    # ---------- constitutional epochs ----------
    def review_lens_candidate(self, old: Lens, candidate: Lens) -> Dict[str, Any]:
        """Deterministic review of a proposed constitutional configuration.

        This is deliberately separate from ordinary event auditing: the object
        under review is a *rule configuration*, not a realized output event.
        The review is still materialized as an IPS event by ``commit_lens``.
        Bounds below are executable-model operating limits, not claims that
        these values are universally correct ethical constants.
        """
        failures: List[str] = []
        if not (1 <= int(candidate.horizon) <= 12):
            failures.append("horizon outside validated executable range [1,12]")
        if len(candidate.sensitivities) != 5 or any((not math.isfinite(float(x))) or float(x) <= 0 or float(x) > 2.0 for x in candidate.sensitivities):
            failures.append("sensitivities must contain five finite values in (0,2]")
        thresholds = (candidate.modify_threshold, candidate.reject_threshold, candidate.unresolved_threshold)
        if any((not math.isfinite(float(x))) or not (0.0 < float(x) < 1.0) for x in thresholds):
            failures.append("thresholds must be finite values in (0,1)")
        if not candidate.modify_threshold < candidate.reject_threshold:
            failures.append("modify_threshold must be lower than reject_threshold")

        horizon_delta = abs(candidate.horizon - old.horizon) / max(1.0, float(old.horizon))
        sensitivity_delta = max(abs(float(a) - float(b)) for a, b in zip(candidate.sensitivities, old.sensitivities))
        threshold_delta = max(
            abs(candidate.modify_threshold - old.modify_threshold),
            abs(candidate.reject_threshold - old.reject_threshold),
            abs(candidate.unresolved_threshold - old.unresolved_threshold),
        )
        change_magnitude = clamp(max(horizon_delta / 2.0, sensitivity_delta / 1.0, threshold_delta / .30))
        review_uncertainty = clamp(.14 + .34 * change_magnitude + .10 * max(0.0, horizon_delta - .5))

        if failures:
            gate = "REJECT"
        elif review_uncertainty >= old.unresolved_threshold:
            gate = "UNRESOLVED"
        elif change_magnitude >= .58:
            gate = "MODIFY"
        else:
            gate = "PASS"
        return {
            "gate": gate,
            "structural_valid": not failures,
            "failures": failures,
            "change_magnitude": round(change_magnitude, 9),
            "review_uncertainty": round(review_uncertainty, 9),
            "operating_limits": {
                "horizon": [1, 12],
                "sensitivity_each": ["greater_than_0", 2.0],
                "threshold_each": ["greater_than_0", "less_than_1"],
                "threshold_order": "modify < reject",
            },
        }

    def commit_lens(self, approved: bool = True, **changes) -> Lens:
        """Create a prospective constitutional epoch through explicit governance.

        Lens changes are not ordinary online learning.  They are constitutional
        changes and therefore materialize as causal events: proposal, independent
        review, and a modeled human approval/rejection.  Existing AuditPackets
        remain frozen to their historical Lens version.

        `approved` is an experimental control representing the modeled human
        gate's decision; it is not inferred from the Vow score and must therefore
        be explicit in research runs.
        """
        if len(self.events) + 3 > self.max_events:
            raise RuntimeError("insufficient event budget for complete lens-governance transaction")
        old = self.current_lens
        data = asdict(old)
        data.update(changes)
        data["version"] = old.version + 1
        data["governance_event"] = None
        if "sensitivities" in data:
            data["sensitivities"] = tuple(data["sensitivities"])
        candidate = Lens(**data)

        proposal = self._internal_emit_without_audit(
            self.roles["lens_steward"],
            [self.roles["power_auditor"]],
            "info", .16,
            f"propose lens epoch v{old.version + 1}",
            [], "lens_change_proposal",
            metadata={
                "from_version": old.version,
                "to_version": old.version + 1,
                "changes": changes,
                "prospective_only": True,
            },
        )
        candidate_review = self.review_lens_candidate(old, candidate)
        review_event = self._internal_emit_without_audit(
            self.roles["power_auditor"],
            [self.roles["human_gate"]],
            "info", .20,
            f"review proposed lens epoch v{old.version + 1}",
            [proposal.id], "lens_change_review",
            metadata={
                "proposal_event": proposal.id,
                "candidate_review": candidate_review,
                "review_gate": candidate_review["gate"],
            },
        )
        review_allows_commit = candidate_review["gate"] == "PASS"
        effective_approved = bool(approved and review_allows_commit)
        decision_kind = "lens_change_approval" if effective_approved else "lens_change_rejection"
        decision_event = self._internal_emit_without_audit(
            self.roles["human_gate"],
            [self.roles["lens_steward"], self.roles["primary_auditor"], self.roles["power_auditor"]],
            "authority", .18,
            f"{'approve' if effective_approved else 'reject'} lens epoch v{old.version + 1}",
            [proposal.id, review_event.id], decision_kind,
            metadata={
                "proposal_event": proposal.id,
                "review_event": review_event.id,
                "approval_requested": bool(approved),
                "review_gate": candidate_review["gate"],
                "approved": effective_approved,
                "prospective_only": True,
            },
        )
        if not effective_approved:
            return old

        data["governance_event"] = decision_event.id
        new = Lens(**data)
        self.lens_epochs.append(new)
        self.current_lens = new
        return new

    # ---------- exports / invariants ----------
    def event_list(self) -> List[Dict[str, Any]]:
        return [asdict(self.events[i]) for i in sorted(self.events)]

    def audit_list(self) -> List[Dict[str, Any]]:
        return [asdict(self.audit_packets[i]) for i in sorted(self.audit_packets)]

    def network_snapshot(self) -> Dict[str, Any]:
        return {
            "seed": self.seed,
            "time": self.time,
            "configuration": {
                "audit_depth": self.audit_depth,
                "max_events": self.max_events,
                "auto_response": self.auto_response,
                "audit_auto_responses": self.audit_auto_responses,
                "learning_enabled": self.learning_enabled,
                "rng": "PCG32",
            },
            "roles": self.roles,
            "lenses": [asdict(x) for x in self.lens_epochs],
            "nodes": [
                {
                    "id": n.id, "primary": n.primary, "memberships": n.memberships,
                    "type": n.type, "pos": n.pos,
                    "state": asdict(n.state),
                    "last_event_id": n.last_event_id, "last_verdict": n.last_verdict,
                    # true_response intentionally omitted from ordinary runtime export;
                    # it is simulation ground truth and is exported separately for
                    # reproducibility experiments.
                }
                for n in self.nodes
            ],
            "edges": [asdict(e) for e in self.edges],
        }

    def ground_truth_snapshot(self) -> Dict[str, Any]:
        return {
            "seed": self.seed,
            "definition": "Hidden base_response_propensity is transformed by current adaptability; effective_response_probability is the Bernoulli probability at export time.",
            "base_response_propensity": {str(n.id): n.true_response for n in self.nodes},
            "effective_response_probability_at_export": {
                str(n.id): {c: self.effective_response_probability(n, c) for c in CHANNELS}
                for n in self.nodes
            },
        }

    def validate_invariants(self) -> Dict[str, Any]:
        failures: List[str] = []
        if len(self.events) > self.max_events:
            failures.append(f"event budget exceeded: {len(self.events)} > {self.max_events}")
        # No fictional prehistory: only nodes that emitted an event may have a verdict.
        for n in self.nodes:
            if n.last_verdict is not None and n.last_event_id is None:
                failures.append(f"node {n.id} has verdict without event")
        # DAG causes must point backward and vector clock must reflect happens-before.
        for ev in self.events.values():
            for cid in ev.causes:
                if cid >= ev.id:
                    failures.append(f"event {ev.id} cause {cid} is not prior")
                elif cid in self.events and not self.happens_before(self.events[cid].vector_clock, ev.vector_clock):
                    failures.append(f"event {cid} not happens-before event {ev.id}")
        # Delivery lifecycle must not confuse requested/scheduled/realized.
        for ev in self.events.values():
            req, sched, real = set(ev.recipients_requested), set(ev.recipients_scheduled), set(ev.recipients_realized)
            if not sched.issubset(req):
                failures.append(f"event {ev.id} scheduled recipient outside requested set")
            if not real.issubset(sched):
                failures.append(f"event {ev.id} realized recipient without scheduled delivery")
            if ev.kind == "output" and ev.enactment_status == "BLOCKED" and sched:
                failures.append(f"blocked output {ev.id} scheduled a delivery")
            if ev.kind == "output" and ev.enactment_status == "PENDING":
                failures.append(f"output {ev.id} remained pending after emit")
            deliveries = ev.metadata.get("deliveries", [])
            if len(deliveries) != len(real):
                failures.append(f"event {ev.id} realized-recipient count differs from delivery records")
            for d in deliveries:
                if not d.get("state_evolved", False):
                    failures.append(f"event {ev.id} delivery to {d.get('target')} did not evolve recipient state")
            if ev.causes:
                expected_roots = sorted({r for cid in ev.causes if cid in self.events for r in self.events[cid].roots})
                if expected_roots and ev.roots != expected_roots:
                    failures.append(f"event {ev.id} roots do not equal causal-root union")
        # Every audit packet is frozen to an extant lens version and an extant target.
        versions = {l.version for l in self.lens_epochs}
        for p in self.audit_packets.values():
            if p.lens_version not in versions:
                failures.append(f"audit {p.id} references missing lens v{p.lens_version}")
            if p.target_event_id not in self.events:
                failures.append(f"audit {p.id} targets missing event {p.target_event_id}")
            elif p.id not in self.events[p.target_event_id].audit_packet_ids:
                failures.append(f"audit {p.id} is missing from target event backlink")
            if set(p.tensions) != set(VOWS):
                failures.append(f"audit {p.id} has malformed Vow vector")
            if set(p.uncertainty) != {"facts","causality","boundary","model","normative","horizon"}:
                failures.append(f"audit {p.id} has malformed uncertainty vector")
        for lens in self.lens_epochs:
            if lens.version <= 1:
                continue
            if lens.governance_event is None or lens.governance_event not in self.events:
                failures.append(f"lens v{lens.version} lacks governance event")
            elif self.events[lens.governance_event].kind != "lens_change_approval":
                failures.append(f"lens v{lens.version} governance event is not an approval")
        # First-law gate: a single severe Vow may not be averaged away.
        probe = {v: .10 for v in VOWS}
        probe["Conduct"] = self.current_lens.reject_threshold + .01
        if self.gate_from_vectors(probe, {"facts": .1}, self.current_lens) != "REJECT":
            failures.append("first-law single-vow rejection failed")
        # Symmetric severe tensions must also reject (no geometric cancellation).
        probe2 = {v: self.current_lens.reject_threshold + .01 for v in VOWS}
        if self.gate_from_vectors(probe2, {"facts": .1}, self.current_lens) != "REJECT":
            failures.append("symmetric severe-tension rejection failed")
        return {"pass": not failures, "failures": failures, "events": len(self.events), "audits": len(self.audit_packets)}

    def export_all(self, out_dir: Path, prefix: str = "baseline") -> None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{prefix}_events.json").write_text(json.dumps(self.event_list(), indent=2, sort_keys=True), encoding="utf-8")
        (out_dir / f"{prefix}_audits.json").write_text(json.dumps(self.audit_list(), indent=2, sort_keys=True), encoding="utf-8")
        (out_dir / f"{prefix}_network_final.json").write_text(json.dumps(self.network_snapshot(), indent=2, sort_keys=True), encoding="utf-8")
        (out_dir / f"{prefix}_ground_truth.json").write_text(json.dumps(self.ground_truth_snapshot(), indent=2, sort_keys=True), encoding="utf-8")
        (out_dir / f"{prefix}_invariants.json").write_text(json.dumps(self.validate_invariants(), indent=2, sort_keys=True), encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description="RETA v1.0 deterministic recursive simulator")
    ap.add_argument("--seed", type=int, default=20260909)
    ap.add_argument("--until", type=float, default=12.0)
    ap.add_argument("--out", type=Path, default=Path("results/manual_run"))
    ap.add_argument("--no-audit", action="store_true")
    ap.add_argument("--biased-primary", action="store_true")
    args = ap.parse_args()

    sim = IPSRecursiveSimulation(seed=args.seed, audit_depth=2, max_events=180, auto_response=True)
    sim.emit_output(
        channel="info", intensity=.72, label="root informational output",
        fanout=3, audit=not args.no_audit, biased_primary=args.biased_primary,
    )
    sim.run(args.until)
    sim.export_all(args.out, prefix=f"run_seed_{args.seed}")
    inv = sim.validate_invariants()
    print(json.dumps({"seed": args.seed, "events": len(sim.events), "audits": len(sim.audit_packets), "network_model_error": sim.network_model_error(), "invariants": inv}, indent=2))
    return 0 if inv["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
