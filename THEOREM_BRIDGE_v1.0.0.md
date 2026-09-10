# Theorem Bridge — Priority-State Dynamics -> IPS Alignment v1.0.0

## Status

**SUPPORTED LOCAL MATHEMATICAL EXEMPLAR / GENERALIZATION NOT ESTABLISHED.**

## Source

Guillaume Bolduc, *Priority-State Dynamics in Open Multi-Agent Systems: Dynamic Membership and History-Dependent Consensus Endpoints*, working preprint, compact v07, September 7, 2026. Exact source bytes are included at `inputs/Priority_State_Dynamics_v07_Compact.pdf`.

## Exact theorem used

For the preprint's prescribed join–mix–depart history, Theorem 4.1 shows

\[
m(U)=\sum_{r=1}^{n}\theta_r w_r^\top+\theta_{n+1}q^\top.
\]

For positive newcomer influence, exact endpoint restoration requires the unique feasible

\[
q_*^\top=\frac{m(W)-\sum_{r=1}^{n}\theta_r w_r^\top}{\theta_{n+1}},
\]

with error

\[
m(U)-m(W)=\theta_{n+1}(q-q_*)^\top.
\]

Corollary 4.2 gives a simpler weighted-neighbor formula under equal retention and doubly stochastic mixing.

## Transferable structural result

The transfer into the alignment architecture is deliberately weaker than the theorem:

1. open membership changes state;
2. transient participation can leave persistent historical influence;
3. restoring membership does not imply restoring the previous endpoint;
4. the duration/mixing history of the transient interaction can matter;
5. any restoration claim requires explicit assumptions about state semantics and controllable variables.

## Non-transferable parts

No claim is made that:

- IPS states are stochastic priority matrices;
- the Five-Vow field is a consensus mean;
- theorem weights are real-world causal weights;
- autonomous AI priorities can be set to \(q_*\);
- the theorem solves coexistence or alignment.

## Research question created by the bridge

The theorem solves an input-design problem by selecting the newcomer state under fixed mixing. The no-control alignment premise reverses the controllability assumption. A future problem is therefore:

> For an autonomous entrant whose internal priority/output distribution is not selectable, characterize the interface, coupling, retention, or compensating-response conditions under which a declared system-level admissible region remains invariant or recoverable.

This is currently a research direction only.
