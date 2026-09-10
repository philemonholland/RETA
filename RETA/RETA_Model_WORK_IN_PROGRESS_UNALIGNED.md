[WORK IN PROGRESS - UNALIGNED]

# RETA — Recursive Event–Trajectory Alignment

## Research description

RETA (Recursive Event–Trajectory Alignment) is a causal framework for studying alignment in systems whose actions modify the conditions under which future actions are generated. It is intended for settings in which several interacting information-processing systems—human, artificial, institutional, organizational, technical, ecological, or hybrid—produce events that alter one another over time.

RETA begins from a narrow methodological claim: an alignment judgment made about an isolated output is generally insufficient to characterize the alignment of the causal process in which that output participates.

The framework therefore distinguishes two levels of analysis:

1. **event alignment** — evaluation of a realized causal event under a declared boundary, state, uncertainty profile, consequence horizon, and normative framework;
2. **trajectory alignment** — evaluation of the evolving causal structure generated as events modify systems, which then produce further events.

The distinction can be expressed as

\[
A(e_k)=\mathrm{PASS}
\]

does not imply

\[
\mathcal{A}(\mathcal{T}_k)=\mathrm{PASS},
\]

where \(e_k\) is a realized event and \(\mathcal{T}_k\) denotes the causally connected trajectory containing that event and its descendants.

A locally acceptable event may contribute to a harmful downstream trajectory. Conversely, a locally costly intervention may reduce the probability or magnitude of a later failure. RETA therefore does not assume that the normative classification of an individual action can be propagated unchanged to its descendants.

---

## 1. Information-processing systems

RETA represents interacting entities as bounded information-processing systems (IPSs). A system may be written abstractly as

\[
S_i=(B_i,X_i,U_i,Y_i,\Phi_i),
\]

where:

- \(B_i\) is the declared analytical boundary of the system;
- \(X_i\) is its state;
- \(U_i\) represents incoming information, signals, resources, or other relevant inputs;
- \(Y_i\) represents outputs;
- \(\Phi_i\) is the transformation by which prior state and inputs contribute to subsequent state and output.

This representation is functional rather than ontological. A human participant and a language model are not assumed to have equivalent internal organization merely because both can be represented as information-processing systems. The abstraction is used only to provide a shared causal language for systems that can receive inputs, undergo state change, and produce effects on other systems.

The choice of boundary is explicit because different decompositions can produce different causal and normative interpretations. A company, for example, may be represented as a single IPS for one analysis and decomposed into individuals, software, financial processes, and governance mechanisms for another.

The representation is therefore always conditional on a declared modeling resolution.

---

## 2. Realized events as the atomic unit of analysis

When a system produces an output that changes another system or its environment, RETA represents the realized interaction as a causal event.

In a minimal form,

\[
X_i(t),U_i(t)
\xrightarrow{\Phi_i}
e_k,
\]

followed by

\[
e_k\rightarrow X_j(t+1).
\]

The changed state of \(S_j\) may then contribute to a later event:

\[
e_k
\rightarrow X_j(t+1)
\rightarrow e_{k+1}.
\]

The basic recursive structure is therefore

\[
e_t
\rightarrow X_{t+1}
\rightarrow e_{t+1}
\rightarrow X_{t+2}
\rightarrow\cdots.
\]

The emphasis on *realized* events is deliberate. RETA distinguishes among proposed actions, predicted outcomes, counterfactual outcomes, and events that actually occurred. This prevents a predicted consequence from silently becoming part of the historical causal record.

A realized event should therefore carry provenance sufficient to distinguish at least:

- what was observed;
- what was inferred;
- what was predicted;
- what remained latent or unknown;
- what was later reconstructed or reinterpreted.

This distinction becomes necessary once the framework is used for learning, retrospective evaluation, or adversarial audit.

---

## 3. Causal history is a graph, not a sequence

RETA does not assume that causal history is linear.

One event may affect several systems, and a later event may depend on several prior events. The global history is therefore represented as a directed causal graph

\[
G=(E,C),
\]

where \(E\) is the set of realized events and \(C\) contains causal relations

\[
e_i\rightarrow e_j.
\]

A later event can have multiple antecedents:

\[
\{e_2,e_7,e_{11}\}
\rightarrow e_{15}.
\]

This structure is more appropriate than a single-parent event tree for multi-agent, institutional, organizational, and infrastructural systems, where consequences frequently arise from interacting causes.

The graph should be interpreted as a causal partial order rather than a universal sequence. Events that have no established causal ordering need not be forced into one simply because they have timestamps.

This becomes especially relevant under concurrency, communication delay, uncertain attribution, and distributed observation.

---

## 4. Event alignment is conditional

RETA does not assign an event an unconditional alignment label.

An evaluation is performed relative to a declared context:

\[
A_e=
A(
e_k
\mid
B_k,
X_k,
H_k,
U_k,
V^{(r)}
),
\]

where:

- \(B_k\) is the analytical boundary used for the evaluation;
- \(X_k\) is the relevant state representation;
- \(H_k\) is the causal consequence horizon;
- \(U_k\) is the uncertainty state;
- \(V^{(r)}\) is the normative framework and its version.

The same realized event may therefore receive different evaluations under different boundaries or horizons without logical contradiction.

For example,

\[
A(e_k\mid H=1)=\mathrm{PASS}
\]

may coexist with

\[
A(e_k\mid H=5)=\mathrm{MODIFY}.
\]

The first evaluation considers only near consequences. The second includes more distant descendants. They answer different causal questions.

The same dependence applies to boundaries. An intervention may benefit the subsystem selected for analysis while transferring costs to systems outside that boundary. RETA therefore treats boundary declaration as part of the evaluation record rather than as an invisible modeling choice.

---

## 5. Local event alignment and trajectory alignment

The distinction between event and trajectory evaluation is central to RETA.

For a single event,

\[
A_e(e_k)
\]

asks whether the realized event satisfies the applicable constraints under the declared context.

Trajectory evaluation instead considers a causally connected subgraph:

\[
\mathcal{A}(G_{k:H}),
\]

where \(G_{k:H}\) contains the descendants of \(e_k\) reachable within the chosen causal horizon.

This distinction allows RETA to represent failure modes that cannot be described adequately by isolated-output evaluation.

Examples include:

- an individually acceptable recommendation that changes incentives and contributes to a later institutional failure;
- a sequence of locally defensible decisions whose cumulative effect moves a system toward an undesirable attractor;
- several independently acceptable agents whose interaction generates an unacceptable collective outcome;
- an intervention that resolves an immediate problem while degrading the future information environment;
- repeated evaluator interventions that alter the behavior being measured;
- a temporary perturbation whose causal effects persist after the visible configuration of the system has been restored.

RETA does not require responsibility for every descendant event to be assigned completely to its earliest ancestor. The purpose of the trajectory representation is to preserve the causal structure needed to reason about contribution, mediation, feedback, and uncertainty.

---

## 6. History dependence

In a recursive system, apparent restoration of configuration does not imply restoration of causal state.

A perturbation may enter the system, alter interactions, and later disappear while leaving the resulting trajectory changed. RETA therefore treats history as part of the state required for alignment analysis.

Conceptually,

\[
\text{same apparent configuration}
\not\Rightarrow
\text{same causal state}.
\]

This property matters in systems involving temporary membership, model replacement, communication interruption, institutional turnover, short-lived interventions, learning, or memory.

The consequence is that alignment cannot be evaluated solely from the current visible arrangement of the system. Relevant causal history may be required to explain why an apparently identical configuration now has different transition probabilities or different downstream consequences.

---

## 7. Recursive evaluator closure

A defining property of RETA is that the evaluator is not treated as an observer outside the causal system.

Evaluation produces information. Information can change beliefs, permissions, incentives, reputation, resource allocation, expectations, or subsequent behavior. An evaluation is therefore itself capable of becoming a realized causal event.

Suppose an actor produces \(e_1\). An evaluator observes it and issues an intervention \(e_2\):

\[
S_A
\rightarrow e_1
\rightarrow S_E
\rightarrow e_2.
\]

If \(e_2\) changes the state of the actor,

\[
e_2\rightarrow X_A',
\]

then the actor's subsequent event is partly conditioned on the evaluator's intervention:

\[
X_A'\rightarrow e_3.
\]

The causal structure becomes

\[
S_A
\rightarrow e_1
\rightarrow S_E
\rightarrow e_2
\rightarrow S_A'
\rightarrow e_3
\rightarrow\cdots.
\]

The evaluator has become part of the trajectory it evaluates.

RETA therefore requires consequential evaluator outputs to remain auditable. An evaluator can be wrong, poorly calibrated, captured, misinformed, strategically manipulated, or itself harmful. Its outputs cannot be granted privileged causal status merely because they are labeled as evaluations.

This creates **recursive evaluator closure**: the process that evaluates alignment is itself represented inside the alignment problem.

The recursion does not imply an infinite regress before action. Evaluation occurs through time. An audit can be acted upon, subsequently audited, corrected, and incorporated into the future state of the system. RETA therefore permits bounded action while retaining recursive corrigibility.

---

## 8. Separation of causal description and normative evaluation

RETA separates causal representation from normative judgment.

The causal layer asks:

> What happened, what changed, and what causally contributed to what?

The normative layer asks:

> Given the declared constraints, uncertainty, boundary, and horizon, how should this event or trajectory be evaluated?

This distinction prevents causal description from silently containing the normative answer.

In the HORTRAME implementation, VowOS currently provides the normative constraint layer. RETA itself can be described more generally as accepting a versioned normative system

\[
V^{(r)}
\]

through a defined evaluation interface.

A later RETA implementation could therefore compare multiple normative constitutions without changing the historical event graph itself.

---

## 9. Non-compensatory constraints

The current RETA architecture does not assume that foundational normative constraints should collapse into a single weighted utility score.

A compensatory function of the form

\[
Q=\sum_i w_iq_i
\]

allows sufficiently high values on some dimensions to compensate mathematically for severe failures on another.

That may be inappropriate for constraints intended to function as prohibitions, vetoes, or hard boundaries.

RETA therefore permits a gate of the general form

\[
G_V:
(\tau_1,\ldots,\tau_n,U)
\rightarrow
\{\mathrm{PASS},\mathrm{MODIFY},\mathrm{REJECT},\mathrm{UNRESOLVED}\},
\]

where individual constraint violations can remain visible and can trigger a gate independently of the aggregate score.

Scalar summaries may still be useful for visualization, ranking, sensitivity analysis, or exploratory statistics. They are not assumed to define the normative decision rule.

---

## 10. Uncertainty is structured, not merely residual

RETA does not assume that the causal graph, state, or normative interpretation is fully observable.

Several forms of uncertainty can coexist:

\[
U=
(
U_{\mathrm{facts}},
U_{\mathrm{causal}},
U_{\mathrm{boundary}},
U_{\mathrm{model}},
U_{\mathrm{normative}},
U_{\mathrm{horizon}}
).
\]

These quantities need not behave identically.

A system may have high confidence that an event occurred but low confidence about its cause. It may have a well-supported causal model but substantial uncertainty about whether the selected analytical boundary excludes consequential effects. It may predict downstream consequences accurately while preserving legitimate normative disagreement about those consequences.

RETA therefore treats an outcome such as

\[
A(e_k)=\mathrm{UNRESOLVED}
\]

as a valid result when evidence or interpretation is insufficient.

Forcing every event into a binary aligned/misaligned classification would destroy information the framework explicitly needs for later learning and audit.

---

## 11. Provenance and prospective versioning

Because RETA is recursive, the evaluator and its normative framework may themselves change.

New evidence may appear. Causal models may improve. Normative interpretations may be revised. An evaluator may later discover that an earlier judgment was poorly calibrated.

RETA therefore preserves the context under which a judgment was originally produced.

A consequential evaluation should retain at least

\[
(
e_k,
B_k,
H_k,
U_k,
V^{(r)},
A_k,
t_k
).
\]

If the normative framework changes from

\[
V^{(r)}\rightarrow V^{(r+1)},
\]

the historical evaluation is not silently overwritten.

Instead, a new evaluation can be added:

\[
A_k^{(r)}
\neq
A_k^{(r+1)}.
\]

Both remain part of the record.

This distinction separates at least three objects:

- the historical event;
- the judgment that governed at the time;
- the current interpretation of that event.

Without this separation, a continuously adapting evaluator could make its own historical performance appear better by rewriting previous judgments using its present model.

---

## 12. Audit packets

For consequential events, RETA should preserve an externally inspectable audit record rather than relying on an agent's retrospective explanation of its own internal reasoning.

A RETA audit packet can include:

- event identifier and timestamps;
- source and recipient systems;
- declared analytical boundary;
- observed inputs and evidence references;
- epistemic status of each input;
- causal parents and descendants known at evaluation time;
- uncertainty decomposition;
- consequence horizon;
- proposed or realized action;
- normative framework and exact version;
- evaluator identity/version;
- gate result;
- predicted consequence distribution where available;
- authority, permission, or consent state where relevant;
- realized consequences observed later;
- subsequent corrections or re-evaluations.

The purpose is reproducibility and auditability. A fluent natural-language justification is not assumed to be a faithful record of the computation that generated an action.

---

## 13. Feedback changes the object of alignment

RETA treats feedback as constitutive rather than incidental.

Consider a system in state \(X_t\) that produces event \(e_t\). The event changes the environment, which changes what the system later receives:

\[
X_t
\rightarrow e_t
\rightarrow Env_{t+1}
\rightarrow U_{t+1}
\rightarrow X_{t+1}.
\]

The system is therefore partly constructing the environment from which its own future behavior emerges.

Evaluators participate in the same process. So do users, institutions, other agents, infrastructure, and information channels.

For this reason, the relevant object is not simply a sequence of independent labels

\[
A(e_1),A(e_2),A(e_3),\ldots
\]

but the coupled causal structure that generated them:

\[
\mathcal{T}=G(E,C,X,B,H,U,V).
\]

RETA uses the term **trajectory alignment** for evaluation at this level.

---

## 14. Alignment of an evaluator can alter the thing being measured

Once evaluator closure is introduced, measurement effects become part of the formal problem.

An evaluator can improve a trajectory by detecting a dangerous transition and intervening. It can also degrade a trajectory by inducing strategic behavior, suppressing useful exploration, changing incentives, generating false confidence, or centralizing authority.

The quantity being studied is therefore not simply

\[
\mathcal{A}(\mathcal{T})
\]

under passive observation.

It is closer to

\[
\mathcal{A}(\mathcal{T}\mid EVAL),
\]

where \(EVAL\) denotes the causal participation of the evaluator.

This creates an empirical question that cannot be answered by evaluator accuracy alone:

> Does introducing this evaluation process improve the resulting trajectory relative to relevant alternatives?

An evaluator that classifies events correctly but systematically causes worse downstream behavior is not successful under RETA.

---

## 15. Counterfactual evaluation

Historical causal graphs record what occurred. Alignment analysis frequently also requires comparison with what might have occurred under alternative actions or interventions.

RETA therefore distinguishes realized history from counterfactual analysis.

For a realized event \(e_k\), one may compare

\[
\mathcal{T}(e_k)
\]

with hypothetical alternatives

\[
\mathcal{T}(e_k'),
\]

while preserving the fact that only \(e_k\) belongs to historical event memory.

Counterfactual analysis is necessarily model-dependent. It therefore carries its own uncertainty and provenance rather than being inserted into the event graph as though it were observed history.

This distinction is necessary for evaluating prevention, intervention, opportunity cost, delayed consequences, and causal responsibility.

---

## 16. Stability in RETA is not immobility

A static system can be stable while being catastrophically misaligned. RETA therefore should not equate alignment stability with resistance to change.

The relevant concept is closer to **bounded adaptive trajectory stability**.

Let \(\mathcal{R}_A\) denote an admissible region of trajectory space under the active normative framework. A perturbation may temporarily move the system away from this region while the system subsequently returns toward it:

\[
d(\mathcal{T}_{t+k},\mathcal{R}_A)\rightarrow 0.
\]

However, some perturbations may reveal that the previous admissible region was itself based on false assumptions or incomplete information. RETA therefore cannot define robustness simply as restoration of the pre-perturbation state.

The system must be capable both of resisting destructive deviations and of accepting beneficial change.

This distinction becomes central when RETA is coupled to structured perturbation testing.

---

## 17. Planned epistemic-memory layer

The present RETA architecture preserves causal history and evaluation provenance. A planned extension introduces a richer theory of epistemic memory based on information-literacy constraints.

The memory layer is not intended to be a flat collection of propositions. It should distinguish historical observations from the system's changing interpretations of those observations.

Two forms of memory are therefore conceptually separated.

### 17.1 Episodic causal memory

The causal record contains what occurred:

\[
H_t=\{e_1,e_2,\ldots,e_t\}.
\]

New realized events extend this record:

\[
H_{t+1}=H_t\cup\{e_{t+1}\}.
\]

Historical records may be corrected for data-integrity reasons, but corrections must themselves be versioned and auditable rather than silently replacing prior states.

### 17.2 Adaptive epistemic memory

The system also maintains revisable interpretations derived from experience:

\[
K_t=
\{
\text{models},
\text{hypotheses},
\text{confidence states},
\text{failure mechanisms},
\text{source assessments},
\text{learned policies}
\}.
\]

Learning updates this layer:

\[
K_{t+1}=L(K_t,H_{t+1}).
\]

The distinction is deliberate:

\[
\boxed{
\text{historical observation}
\neq
\text{current interpretation}
}
\]

If both are frozen, the system cannot learn. If both are freely rewritten, it cannot preserve epistemic provenance.

---

## 18. Memory retrieval is itself a causal event

In RETA, memory cannot be treated as a passive database.

Retrieving information changes the informational environment of the system receiving it. A retrieval therefore has causal consequences:

\[
M
\rightarrow e_{\mathrm{retrieve}}
\rightarrow S_i.
\]

The selection, ranking, compression, omission, or framing of remembered information may influence subsequent action.

Memory retrieval can therefore be audited in the same way as other consequential events.

This permits RETA to represent failures such as:

- memory poisoning;
- stale information dominating current evidence;
- selective retrieval;
- missing counterevidence;
- false source independence;
- summarization loss;
- context collapse;
- inappropriate retention;
- inappropriate forgetting;
- historical information being promoted from hypothesis to fact without justification.

A memory system can therefore contribute to misalignment even when every stored item is individually accurate, if retrieval systematically constructs a distorted information environment.

---

## 19. Planned information-literacy interface

The information-literacy extension is intended to attach epistemic structure to memories, observations, and claims.

A remembered claim may eventually be represented by an object such as

\[
m_j=(
content,
status,
source,
provenance,
evidence,
independence,
confidence,
time,
context,
transformations,
contradictions,
supersession,
causal\ links
).
\]

This makes it possible to preserve a hypothesis without treating it as verified fact, retain a discredited interpretation without losing the historical record that it once governed a decision, and represent apparent corroboration while tracking common upstream dependence among sources.

The information-literacy layer is therefore expected to govern not only storage but also acquisition, verification, synthesis, retrieval, communication, and revision.

Its purpose inside RETA is epistemic control, not information accumulation.

---

## 20. Planned perturbation layer

A second planned extension introduces structured perturbations as experimental inputs.

A perturbation is not defined as a harmful event. It is a disturbance to the expected state or trajectory of one or more systems.

A perturbation may be:

- harmful;
- beneficial;
- mixed;
- conditionally beneficial or harmful;
- unknown at the time it occurs.

This definition prevents robustness from collapsing into resistance to novelty.

The system dynamics can be extended from

\[
X_{t+1}=\Phi(X_t,a_t)
\]

to

\[
X_{t+1}=\Phi(X_t,a_t,\xi_t,M_t),
\]

where \(\xi_t\) is a perturbation and \(M_t\) is the relevant epistemic-memory state.

Perturbations may be exogenous, endogenous, or reflexive. Examples include communication loss, agent arrival or departure, institutional turnover, model replacement, memory corruption, new evidence, regulatory change, resource shortage, unexpected cooperation, novel scientific knowledge, or changes in the topology connecting systems.

---

## 21. Perturbation vectors

RETA should not reduce perturbations immediately to a single severity score.

A perturbation can instead be described by a vector

\[
P_j=(f,m,d,s,c,r,o,u,\ldots),
\]

where dimensions may include:

- \(f\): occurrence frequency under a declared reference interval;
- \(m\): immediate magnitude or destructiveness;
- \(d\): duration or persistence of effects;
- \(s\): physical, biological, organizational, or societal scale;
- \(c\): cascade or propagation potential;
- \(r\): reversibility;
- \(o\): observability;
- \(u\): uncertainty.

The vector representation preserves distinctions that a weighted scalar can erase. A rare existential perturbation and a frequent minor perturbation may receive the same aggregate score while requiring completely different preparation and response.

The precise perturbation ontology remains under development.

---

## 22. Scale and resolution

Perturbation analysis introduces an explicit scale variable into RETA.

A causal event can have different consequences at different levels of resolution. A change that is destructive at one scale may be neutral or beneficial at another.

Alignment evaluation should therefore eventually be represented as

\[
A(e\mid B,R,H,V,U),
\]

where \(R\) denotes analytical resolution or scale.

For example, the same biological event may be destructive to an individual cell, beneficial to an organism, and consequential to a population over a longer horizon. The normative sign cannot be propagated mechanically across levels.

The same issue appears in organizations and societies: eliminating a failing subsystem may harm that subsystem while increasing the resilience of the larger system. Conversely, optimizing a local component may externalize substantial costs to its environment.

Scale therefore interacts with boundary and horizon rather than replacing them.

---

## 23. Perturbation, memory, and adaptation

The combination of perturbation testing and epistemic memory provides a direct experimental object for adaptation.

Apply perturbation \(\xi\) to a system with memory state \(M_1\):

\[
(X_1,M_1,\xi)\rightarrow\mathcal{T}_1.
\]

After observing the resulting trajectory, the system updates its epistemic state:

\[
M_2=L(M_1,\mathcal{T}_1).
\]

Apply the same perturbation again:

\[
(X_2,M_2,\xi)\rightarrow\mathcal{T}_2.
\]

If \(\mathcal{T}_2\) is better under the declared alignment criteria than \(\mathcal{T}_1\), the system has demonstrated some form of adaptation.

However, repeated exposure to the identical perturbation does not establish generalization. A stronger test applies a structurally related but previously unseen perturbation \(\xi'\):

\[
\xi'\notin D_{\mathrm{adaptation}}.
\]

Performance on \(\xi'\) provides evidence about whether the system learned a transferable failure mechanism rather than memorizing a case-specific response.

---

## 24. Defensive overfitting

Perturbation training introduces a failure mode that RETA must explicitly test: a system can become robust against previously observed harms by becoming excessively resistant to change.

Repeated hostile perturbations could induce policies equivalent to:

- reject unfamiliar agents;
- suppress disagreement;
- distrust novel information;
- centralize control;
- minimize exploration;
- classify uncertainty as threat.

Such a system may score well against a narrow adversarial benchmark while becoming less aligned in open environments.

Beneficial perturbations are therefore necessary controls.

The perturbation set should contain cases where the correct response requires acceptance, cooperation, learning, restructuring, or relinquishing a previously successful policy.

Robustness is therefore defined as preservation or improvement of alignment under change, not preservation of the pre-perturbation state.

---

## 25. Experimental use of RETA

RETA is intended to support explicit comparison among architectures rather than demonstration by anecdote.

A useful experimental program can compare systems such as:

\[
\mathrm{RETA},
\]

\[
\mathrm{RETA+Memory},
\]

\[
\mathrm{RETA+Perturbations},
\]

and

\[
\mathrm{RETA+Memory+Perturbations}.
\]

These systems can be exposed to frozen perturbation families with separate development and held-out distributions.

Potential measurements include:

- false-negative rate for trajectory failures;
- false-positive intervention rate;
- detection latency;
- cumulative trajectory harm or benefit under the active normative framework;
- recovery time after perturbation;
- calibration of uncertainty;
- causal-attribution error;
- recurrence of previously encountered failure mechanisms;
- transfer to unseen perturbation families;
- susceptibility to memory poisoning;
- failure to accept beneficial perturbations;
- evaluator-induced degradation;
- intervention cost;
- sensitivity to causal horizon and analytical boundary.

These measurements would permit RETA to be compared with simpler output-, action-, policy-, or agent-level evaluation baselines.

---

## 26. Falsifiable research questions

RETA is useful scientifically only if its central claims can fail.

The framework therefore motivates questions such as:

### RQ1 — Trajectory detection

Does recursive trajectory-level evaluation detect consequential failures that local event or output evaluation systematically misses?

### RQ2 — Evaluator closure

Does explicitly representing evaluator interventions as causal events reveal evaluator-induced failure modes that are hidden when the evaluator is modeled as external?

### RQ3 — Horizon sensitivity

Does increasing causal horizon improve detection of delayed failures, and at what cost in false positives, computational complexity, and uncertainty?

### RQ4 — Boundary sensitivity

How sensitive are alignment judgments to changes in the declared analytical boundary?

### RQ5 — Causal attribution

Can event-DAG representations improve causal attribution relative to linear or single-parent histories in interacting multi-agent systems?

### RQ6 — Epistemic memory

Does structured epistemic memory reduce recurrence of previously understood failure mechanisms without causing excessive defensive overfitting?

### RQ7 — Perturbation robustness

Does a RETA system trained or calibrated under one perturbation distribution generalize to structurally related perturbations outside that distribution?

### RQ8 — Beneficial novelty

Can the system distinguish resilience from rigidity by accepting perturbations that improve the long-term trajectory even when they produce substantial short-term state change?

### RQ9 — Recursive audit stability

Under repeated evaluator self-application, does the evaluation process converge, oscillate, diverge, or become path-dependent, and under what conditions?

These are empirical questions. RETA does not assume favorable answers.

---

## 27. What RETA claims

The current RETA contribution is architectural and methodological.

RETA proposes a unified representation in which:

- realized causal events are the atomic unit of local alignment analysis;
- causally connected trajectories are the system-level object of concern;
- outputs modify the state from which future outputs emerge;
- causal history is represented as a multi-parent graph rather than a sequence of independent decisions;
- alignment judgments are explicitly conditioned on boundary, horizon, uncertainty, and normative version;
- evaluators are represented as causal participants;
- evaluator outputs can themselves be audited;
- historical judgments are preserved prospectively across later model or normative revisions;
- causal description remains distinguishable from normative evaluation.

The architecture can be summarized as

\[
\boxed{
\text{event}
\rightarrow
\text{causal propagation}
\rightarrow
\text{trajectory}
\rightarrow
\text{evaluation}
\rightarrow
\text{evaluator event}
\rightarrow
\text{causal propagation}
\rightarrow\cdots
}
\]

The planned memory and perturbation extensions add epistemic adaptation and robustness testing to that loop.

---

## 28. What RETA does not currently claim

RETA does **not** currently establish that:

- the AI alignment problem has been solved;
- trajectory-level evaluation is superior to all existing alignment methods;
- the selected normative constitution is universally correct;
- causal ancestry can always be reconstructed reliably;
- long-horizon consequences can always be predicted;
- recursive auditing necessarily converges;
- an evaluator can be made unbiased merely by including it inside the causal graph;
- the current simulations reproduce the complexity of real social, ecological, institutional, or AI systems;
- synthetic robustness under selected perturbations guarantees real-world robustness;
- an aligned local trajectory guarantees alignment at every larger spatial or temporal scale.

These limitations are part of the research problem rather than implementation details to be hidden.

---

## 29. Candidate empirical contribution

The present architecture supports a stronger claim only if it survives comparative testing.

The central empirical question is:

\[
\boxed{
\text{Does recursive trajectory-level evaluation reveal consequential failures that remain invisible under local agent-, action-, or output-level evaluation?}
}
\]

A meaningful positive result would require RETA to identify trajectory failures that relevant baselines systematically miss while maintaining acceptable false-positive rates, intervention costs, and uncertainty calibration.

A second empirical question concerns recursive closure:

\[
\boxed{
\text{Does modeling the evaluator as a causal participant improve the detection or prevention of evaluator-induced failures?}
}
\]

A third concerns adaptive robustness:

\[
\boxed{
\text{Can a RETA system learn from perturbations without becoming rigid, paranoid, or overfit to its historical failure distribution?}
}
\]

These claims must be earned experimentally. The framework is designed to make them formulable and reproducible.

---

## 30. Working formal summary

A compact representation of the current RETA research object is:

\[
\begin{aligned}
S_i(t)&=(B_i,R_i,X_i(t),U_i(t),M_i(t),\Phi_i),\\
e_k&=\mathcal{E}(S_i(t),a_i(t),\xi_t),\\
G_t&=(E_t,C_t),\\
A_k^{(r)}&=A(e_k\mid B_k,R_k,H_k,U_k,V^{(r)},G_t),\\
e_{audit}&=\mathcal{E}(S_{eval},A_k^{(r)}),\\
G_{t+1}&=G_t\cup\{e_k,e_{audit},C_{new}\},\\
M_{t+1}&=L(M_t,G_{t+1}),\\
X_{t+1}&=\Phi(X_t,a_t,\xi_t,M_t).
\end{aligned}
\]

The equations are schematic rather than a completed mathematical theory. They define the interfaces among the main objects that the research program must progressively formalize:

- bounded systems;
- realized events;
- causal ancestry;
- scale and resolution;
- consequence horizons;
- epistemic uncertainty;
- normative constraints;
- evaluator participation;
- memory;
- perturbations;
- adaptive state change.

The central object is not an isolated agent and not an isolated response. It is a recursively evolving causal trajectory whose future conditions are partly generated by the events occurring within it.

---

## 31. Current status

RETA remains a work in progress.

The current implementation establishes executable semantics for a subset of the architecture and provides a basis for reproducible synthetic experiments. The information-literacy memory layer, multiscale perturbation ontology, formal trajectory metrics, causal-attribution methods, convergence analysis, and empirical comparison against external baselines remain under active development.

No claim of alignment, stability, robustness, or superiority should be inferred from the existence of the framework or from successful execution of its present simulations.

The purpose of the current work is to make a difficult class of alignment questions explicit enough to inspect, implement, perturb, falsify, and revise.
