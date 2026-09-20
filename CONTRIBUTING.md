# Contributing

Help make Box for Muse useful, dependable and accessible.

For a use case, submit: the user and problem; trigger; source scope; desired output;
Box/Muse dependencies; permissions; approval boundaries; a synthetic test; a
source link; and whether the idea is a direct example or your own inference.

For a correction, identify the claim and supply a primary source. Label mirrors
and inaccessible originals. Never attribute a project proposal to Aaron Levie
without evidence, and never treat a social post as an API specification.

The source of truth for catalog content is scripts/build_catalog.py. Update its
rows or rendering logic, run it, then run scripts/validate.py. Commit generated
USE-CASES.md and data/use-cases.json together. Keep stable IDs; discuss deletions
or ranking changes so links and history remain useful.

A feature proposal must include a failure case as well as a happy path. Use
synthetic documents. No private data, tokens, client secrets, callback payloads
or personal account identifiers in issues, tests or screenshots.

Contributions use the repository's MIT license. Be respectful, explain tradeoffs,
and keep claims tied to evidence. Maintainer review is required before release;
a merged research proposal is not a tested connector capability.
