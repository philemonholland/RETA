# HORTRAME IPS Alignment v1.0.0 — public edition 1

Guillaume Bolduc — Independant researcher — HORTRAME Systems
English: systems@hortrame.com / Français: systemes@hortrame.com
UNALIGNED — WORK IN PROGRESS. Public edition: 2026-09-09T21:27:00-04:00.

Open index.html (English) or fr.html (French). These self-contained pages replay the supplied 180-event scientific trace. The original viewer is retained under visualization/; the canonical executable is simulation/ips_recursive_sim.py. Its original source bytes are preserved.

Python standard library only. From this package directory:

    python simulation/ips_recursive_sim.py --out results/manual_run
    python simulation/run_experiments.py
    python simulation/recursive_self_validation.py

To run the supplied 17 unit tests, set PYTHONPATH to the simulation directory, then run:

    python -m unittest discover -s tests -v

The original release reports Python 3.13.5. Publication validation passed the supplied tests on Python 3.10.6; this is not a claim to have reproduced the entire experimental suite or empirical alignment results.

All quantities are synthetic and uncalibrated. This public package contains an explicit model/source/documentation allowlist. Private case inputs, protected source extracts, nested working archives and internal operational records are not included. Original model documents may refer to their original working-package context; consult REFERENCES.md for public scientific citations. Public archive: https://www.hortrame.com/alignment/archive/

Each file except SHA256SUMS.txt is covered by the internal SHA-256 manifest. Hashes prove byte identity, not scientific validity.

Presentation edition 2 adds animated replay of the same recorded run. Playback expands model time for legibility and may loop the frozen trace. It does not generate new experiments or agent behavior. Pulses use recorded realized deliveries; illustrative domain volumes do not encode measured physical geometry.

Presentation edition 3 adds a searchable PDF specification, an online HTML report, clearer research navigation and documented bibliography corrections. Scientific source, theory, recorded DATA and animation are unchanged. Original public editions remain in the online archive.

Frozen presentation release v1.1.0: continuous playback, non-pausing timeline/event navigation, and immediate looping of the same recorded trace. Explicit Pause and reduced-motion preferences remain supported. Scientific specification, Python engine and trace remain v1.0.0, with original source filenames and hashes preserved. Included report/reference HTML files are publication snapshots; their external links point to the public website.

Presentation v1.1 edition 2: explicit user language choice takes priority over browser preferences, English is the fallback, and the bilingual public-access statement is attributed to the author. The canonical engine, scientific theory, recorded trajectory, report PDF and continuous playback are unchanged.
