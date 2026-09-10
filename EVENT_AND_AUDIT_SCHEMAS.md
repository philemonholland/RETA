# Event and audit packet schemas

## Event

Required semantic fields:

- `id`: deterministic serialization id.
- `roots[]`: causal episode roots inherited from all direct causes.
- `kind`: event class.
- `label`: human-readable event label.
- `created_at`: simulator time at event creation.
- `source`: IPS id.
- `causes[]`: direct causal dependencies; may contain several parents.
- `channel`: `info | resource | authority | physical | ecology`.
- `intensity`: synthetic [0,1] magnitude.
- `recipients_requested[]`: intended route.
- `recipients_scheduled[]`: queue entries actually created.
- `recipients_realized[]`: deliveries actually processed.
- `enactment_status`: lifecycle of output enactment.
- `evidence_status`: observed/source-supported/inferred/latent/synthetic class.
- `runtime_status`: provenance status used by the simulator.
- `boundary`: declared source boundary/memberships.
- `claim_confidence`: synthetic claimed certainty.
- `vector_clock`: sparse logical-clock map.
- `lens_version`: lens attached by an audit, if any.
- `gate_result`: gate applied to target output, if any.
- `audit_packet_ids[]`: backlinks to packets targeting this event.
- `metadata`: event-type-specific data and delivery state transitions.

## AuditPacket

- `id`
- `target_event_id`
- `auditor_node`
- `audit_depth`
- `lens_version`
- `horizon`
- `tensions{Purpose,Method,Conduct,Integrity,Evolution}`
- `uncertainty{facts,causality,boundary,model,normative,horizon}`
- `projection{expected_impact,agency_risk,irreversibility,model_uncertainty,evolution_risk,boundary_ambiguity,expected_nodes,domains,max_depth}`

`expected_nodes` is a discounted modeled reach/path-mass quantity used by the toy projection, not a count of unique physical nodes reached. A node can contribute through more than one causal depth/path.
- `gate`: `PASS | MODIFY | REJECT | UNRESOLVED`
- `diagnostic_trace`: visualization-only weakest-link trace.
- `frozen_at`
- `target_kind`
- `notes[]`

Audit packets are intended to be append-only historical evidence. v1.0 release validation rejects the known post-record mutation pattern that appeared during development.
