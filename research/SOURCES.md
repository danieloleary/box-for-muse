# Research sources and attribution

Reviewed September 19, 2026. This is a targeted public-web search, not a complete
archive of Aaron Levie's timeline or an engagement-ranked analysis. X often
blocked direct retrieval. Original post URLs are provided when identifiable;
mirrors are explicitly labeled. No inaccessible post is treated as directly
verified. Relative dates on mirrors were not converted to claimed exact dates.
No endorsement by Aaron Levie, Box, Meta, or Muse is implied.

The 50 workflows are original project proposals inspired by broad themes, not
50 verbatim use cases from Levie. Each catalog row links to its motivating theme;
that link is not evidence that an API or proposed product feature works.

## L1

**Agent-speed infrastructure and files.** Levie discusses persistent agents,
search, file operations, permissions and versioning at machine scale.
[Original X post, March 29, 2026](https://x.com/levie/status/2038468564500537416).
Text available in indexed X result. Design inference: prioritize version-aware
retrieval, bounded concurrency and verified, recoverable writes.

## L2

**Systems of record still need governance.** Levie argues that agent activity
increases the importance of reliability, security, access controls and business
logic. [Original post](https://x.com/levie/status/2092087679240569126).
[Read via mirror](https://kyawgyii.twstalker.com/levie/status/2092087679240569126);
direct X retrieval failed. Design inference: administrative workflows need
separate authority and evidence, not a broader default connector scope.

## L3

**Enterprise workflow integration matters beyond the model.** Domain workflows,
system connections and human participation determine how agents become useful.
[Original post](https://x.com/levie/status/2089921630650925170).
[Thread Reader mirror, August 19](https://threadreaderapp.com/thread/2089921630650925170.html).
Direct X retrieval failed. Design inference: build end-to-end outcomes and
review experiences, rather than exposing an unstructured collection of tools.

## L4

**Previously unaffordable work becomes possible.** Examples include reviewing
contract portfolios for opportunities, auditing risks and researching existing
data. [Original post](https://x.com/levie/status/1994900315292979426).
[Thread Reader mirror, November 29, 2025](https://threadreaderapp.com/thread/1994900315292979426.html).
Read via mirror. Design inference: recurring scoped review can deliver more
value than another on-demand summary button.

## L5

**Turn unstructured content into queryable facts.** Levie describes extracting
business information and finding agreements using business criteria.
[Author's LinkedIn post](https://www.linkedin.com/posts/boxaaron_one-of-the-most-exciting-things-about-ai-activity-7491605800348446720-aptH).
Supplemental first-person source, not a tweet. Design inference: reviewed
metadata creates durable value and enables precise downstream queries.

## L6

**Research, search and extraction across enterprise content.** Levie describes
diligence, customer research and life-sciences research as examples.
[Author's LinkedIn announcement](https://www.linkedin.com/posts/boxaaron_today-box-announced-its-biggest-set-of-ai-activity-7328923587887669249-yF0B).
Supplemental first-person source, not a tweet. Design inference: reuse the same
retrieval and evidence primitives across domains; do not assume every workflow
is safe to automate without expert review.

## L7

**Contract review as an evidence task.** Box's template covers extracting clauses,
dates and summaries for legal reviewers.
[Box contract-review agent template](https://support.box.com/hc/en-us/articles/43062215441939-Contract-review-agent).
Box product source, not a Levie tweet. Supports the workflow shape, not a claim
that this connector implements it or guarantees legal accuracy.

## L8

**Expect the agent stack to keep improving.** Levie describes agent functionality
changing as new technical approaches improve it.
[Original indexed X post](https://x.com/levie/status/2016727602619453888).
Design inference: maintain reproducible evaluations and compatibility checks;
feature announcements alone cannot establish a safe upgrade.

## B1

**Current Box capability references.** Technical claims are checked against Box,
not inferred from social posts:

- [Box AI](https://developer.box.com/guides/box-ai): Q&A, generation and structured
  extraction. Endpoint limits and truncation matter; entitlement and runtime
  behavior must be verified in the target account.
- [Events](https://developer.box.com/guides/events): user versus enterprise event
  feeds; duplicate/out-of-order delivery requires reconciliation; enterprise
  feeds require additional administrative permissions.
- [Metadata queries](https://developer.box.com/guides/metadata/queries): structured
  discovery depends on actual templates, types, filters and limits.
- [Scopes](https://developer.box.com/guides/api-calls/permissions-and-errors/scopes):
  capabilities depend on both application scopes and user permissions; inspect
  each selected endpoint and product entitlement before implementation.

## Search method and limits

Queries included `site.x.com/levie agents use cases`, contracts, metadata,
permissions, enterprise documents and continuous workflows. Search coverage is
uneven. Failed X opens, mirror-only text, supplemental LinkedIn posts and Box
product documentation are deliberately distinguished above. We did not scrape a
private feed, purchase data, rank by likes or claim exhaustive coverage.

Refresh the source register and affected use cases together. Preserve a source's
original URL when it disappears; mark it unavailable and lower attribution
confidence rather than substituting an unsourced claim. Keep paraphrases short;
do not copy complete posts or article bodies into this repository.
