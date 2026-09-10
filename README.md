# RETA — Recursive Event–Trajectory Alignment

AI-alignment research through a synthetic model of recursive causal governance across interacting information-processing systems.

**UNALIGNED - EVOLVING ACTIVELY AS OF 2026-09-09 [23:16] EDT. Work in progress.**

Guillaume Bolduc  
Independant researcher  
HORTRAME Systems

[Interactive model](https://www.hortrame.com/alignment/) · [Full research report](https://www.hortrame.com/alignment/paper/) · [French introduction](https://www.hortrame.com/alignment/fr/paper/) · [Version archive](https://www.hortrame.com/alignment/archive/)

## What this repository contains

This research-only mirror contains the files already published in **presentation v1.1.0, public edition 2**. Its canonical Python engine and scientific specification are **v1.0.0**. The distinction is deliberate: the later presentation adds continuous playback, language preferences and publication material without claiming a new scientific result.

- [Model specification](RETA_Model_Spec_v1.0.0.md): definitions, equations, event/audit semantics and explicit non-claims.
- [Scientific analysis](RETA_Analysis_v1.0.0.md) and [event/audit schemas](EVENT_AND_AUDIT_SCHEMAS.md).
- [Python engine](simulation/ips_recursive_sim.py), [experiments](simulation/run_experiments.py), [recursive structural validation](simulation/recursive_self_validation.py), and [supplied unit tests](tests/test_v1_model.py).
- [Browser explorer](index.html), its French presentation, report snapshots and searchable PDF.
- [References](REFERENCES.md), [bibliographic corrections](BIBLIOGRAPHIC_CORRECTIONS.json), and [source checksums](SOURCE_SHA256SUMS.txt).

## Scope and interpretation

The model distinguishes causal events, recursive audits, uncertainty components and prospective constitutional epochs. Its browser animation replays a supplied trace of 180 events and 206 deliveries; repeating the animation does not create new experimental evidence.

This is a deterministic, uncalibrated research prototype. Structural checks do not establish semantic instruction-following, empirical AI safety, universal robustness or extinction-prevention efficacy. The accompanying theory, assumptions and limitations are available for scrutiny and reproducibility.

## Run the supplied checks

Use Python 3.10 or newer; the engine uses the standard library.

```sh
python run_checks.py
python simulation/recursive_self_validation.py
```

The second command writes a local `validation/` directory. These checks concern the stated executable model. The full experimental sweep is available separately in `simulation/run_experiments.py` and can take longer.

## Public access

The author's public statement is preserved in [PUBLIC_ACCESS_STATEMENT.json](PUBLIC_ACCESS_STATEMENT.json). This mirror makes the already-published research easier to inspect and cite. It does not claim a new reuse license or ownership of cited third-party publications.

Research correspondence: [systems@hortrame.com](mailto:systems@hortrame.com). En français : [systemes@hortrame.com](mailto:systemes@hortrame.com).

## Cite the specification

Bolduc, Guillaume (2026). *RETA — Recursive Event–Trajectory Alignment — Model Specification v1.0.0*. HORTRAME Systems. Technical report, working draft. [Report and citation metadata](https://www.hortrame.com/alignment/paper/).

## Author statement and RETA naming revision

On September 10, 2026, the author requested replacement of this same v1.1 edition with the expanded bilingual acknowledgements and the name RETA. Read the [author’s statement, acknowledgements and thanks](author-statement/en.md), the [French statement](author-statement/fr.md), and the [author-supplied RETA explanation](RETA/RETA_Model_WORK_IN_PROGRESS_UNALIGNED.md).

The explanation includes proposed developments. Current playback remains a recorded trace; a live simulation is deferred to a future version. Naming, public documentation and interface changes do not alter the scientific equations or transition rules. Researchers acknowledged in the statement have not reviewed or approved the current model.

[Replacement history](https://www.hortrame.com/alignment/archive/v1.1.0-e2-replacement.json) records the prior and replacement hashes. The preceding source commit remains in this repository’s history. All earlier model packages, back to the first 2D model, remain available in the [complete archive](https://www.hortrame.com/alignment/archive/).

## Typography revision 3

The owner requested smaller normal reading sizes and replacement of this same current archive on September 10, 2026. Only the website presentation changed; the model and Python simulation source remain identical. Prior source revisions remain in Git history.

The closing personal statement was extended in English and French in publication revision 4. Model/scientific files and styling are unchanged.

The closing personal statement was extended in English and French in publication revision 5. Model/scientific files and styling are unchanged.

## Browser audit and report clarification — revision 6

Publication revision 6 repairs browser interactions and portable navigation, retains all original model/engine/data files, and incorporates the author’s revised closing sentence. Read [report 2](RETA_Model_Spec_v1.0.0_report-2.md), the [clarified analysis](RETA_Analysis_v1.0.0_revision-2.md), [correction history](CLAIM_CORRECTIONS.json), and [functional audit scope](FUNCTIONAL_AUDIT.json). The earlier specification, analysis and PDF remain included as historical sources.

The supplied 17 tests and fixed-seed component experiments were rerun against the unchanged engine. These are same-implementation software checks, not independent scientific replication, expert review or evidence of real-world alignment. Native generated state-export completion remains unconfirmed in browser automation.
