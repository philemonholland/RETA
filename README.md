# HORTRAME IPS Alignment

AI-alignment research through a synthetic model of recursive causal governance across interacting information-processing systems.

**UNALIGNED - EVOLVING ACTIVELY AS OF 2026-09-09 [23:16] EDT. Work in progress.**

Guillaume Bolduc  
Independant researcher  
HORTRAME Systems

[Interactive model](https://www.hortrame.com/alignment/) · [Full research report](https://www.hortrame.com/alignment/paper/) · [French introduction](https://www.hortrame.com/alignment/fr/paper/) · [Version archive](https://www.hortrame.com/alignment/archive/)

## What this repository contains

This research-only mirror contains the files already published in **presentation v1.1.0, public edition 2**. Its canonical Python engine and scientific specification are **v1.0.0**. The distinction is deliberate: the later presentation adds continuous playback, language preferences and publication material without claiming a new scientific result.

- [Model specification](HORTRAME_IPS_ALIGNMENT_Model_Spec_v1.0.0.md): definitions, equations, event/audit semantics and explicit non-claims.
- [Scientific analysis](HORTRAME_IPS_ALIGNMENT_Analysis_v1.0.0.md) and [event/audit schemas](EVENT_AND_AUDIT_SCHEMAS.md).
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

Bolduc, Guillaume (2026). *HORTRAME IPS Alignment — Model Specification v1.0.0*. HORTRAME Systems. Technical report, working draft. [Report and citation metadata](https://www.hortrame.com/alignment/paper/).
