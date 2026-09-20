# Delivery backlog

This backlog captures the agreed onboarding-first direction. All entries below
are planned work, not claims about the separate connector implementation.
Link implementation and actual Muse evidence before marking an entry complete.

## P0: Connect and get a useful result

- [ ] **B01: Publish the supported setup path.** Verify the real installation and
  OAuth flow, account requirements, requested permissions, and disconnect path.
  Acceptance: a fresh user completes the documented flow without maintainer help;
  the connected account is verified and no secret appears in chat or screenshots.
- [ ] **B02: Provide three starter prompts.** Find files about a project; summarize
  a chosen document with a source link; compare two chosen documents.
  Acceptance: each prompt passes in Muse with fictional fixtures, traceable
  sources, and clear handling of missing access, unsupported formats, and
  incomplete extraction. Do not infer approval status from modification time.
- [ ] **B03: Explain and recover from setup failures.** Cover canceled OAuth,
  callback mismatch, expired authorization, unavailable scopes, and empty search.
  Acceptance: each documented failure gives an actionable next step tested against
  the actual flow; users can distinguish no matches from an access failure.
- [ ] **B04: Build the onboarding page.** Arrange Connect Box → Try a first task →
  Do more → Make it yours. Use Dan's writing voice throughout. Lead with a few
  proven jobs and link to the full catalog.
  Acceptance: keyboard-accessible, usable on mobile, and clear capability labels
  (tested, experimental, planned). “Get started” points to a verified install path;
  before that, keep “Follow the build” and “Explore the use cases.”
- [ ] **B05: Capture the first-task demo.** Show connection through a useful answer
  with inspectable sources. Produce an original icon, actual Muse screenshots,
  captions, and a video transcript after the workflow passes.
  Acceptance: fictional content, no credentials or private account details,
  visible community ownership, and labeled time cuts. Record setup completion,
  elapsed time, manual steps, and failures before making performance claims.

## P1: Give people reasons to keep using it

- [ ] **B06: Save a cited brief to Box.** Verify the destination and read back the
  saved result. Acceptance: uncertain outcomes and retries do not create duplicate
  files; citations identify source files and versions.
- [ ] **B07: RFP and deal-room reviewer.** Prioritize this as the first deeper demo.
  Acceptance: catch planted stale answers, conflicting sources, internal-only
  pricing, missing legal approval, and unsupported customer-facing claims.
  Produce a source-linked answer matrix without exposing restricted material.
- [ ] **B08: Project-change monitor.** Watch a selected folder, maintain a brief,
  and alert only on meaningful changes.
  Acceptance: durable cursor, duplicate and out-of-order event handling, restart
  recovery, stop controls, bounded cost, and no self-triggering write loop.
- [ ] **B09: Document intake and reviewed metadata.** Extract contract or invoice
  fields, flag uncertainty, validate schema, and write approved values.
  Acceptance: verify Box AI entitlement, distinguish extracted from validated
  values, and confirm saved metadata through a query/readback.
- [ ] **B10: Obligation and renewal monitor.** Attach deadlines and obligations to
  source clauses. Acceptance: missing evidence is distinct from confirmed absence;
  ambiguous dates and review requirements remain visible.
- [ ] **B11: Approved-source research brief.** Combine accessible sources, explain
  contradictions, and save the result. Acceptance: sources and versions are
  inspectable and unsupported conclusions are labeled.

## P2: Enterprise and community expansion

- [ ] **B12: Access-review evidence packet.** Assemble collaborator and sharing
  evidence under separately authorized administrative access. Acceptance: report
  coverage and limitations; permission changes require explicit authority.
- [ ] **B13: Repeatable cross-agent comparison.** Run the same synthetic fixture in
  Muse, Codex, and Grok Bot where access permits. Measure source accuracy, planted
  risks found/missed, manual steps, successful writes, and recovery. Publish the
  tested versions, date, conditions, and unknowns. Do not claim parity from docs.
- [ ] **B14: Community workflow contributions.** Provide a template for a real job,
  fictional input, expected output, access requirements, and evidence. Connect
  accepted examples to stable catalog IDs and the relevant backlog item.
- [ ] **B15: Maintain the comparison.** Review official Box, Grok Bot, and Codex
  changes alongside the Levie research. Record changed assumptions and prepare
  focused updates. Keep personal history and private examples out of public copy.

## Requirements across workflows

Action receipts, source/version tracking, access checks, appropriate output
destinations, recoverable writes, and interrupted-run recovery are release
requirements. They are not optional demo features. Distinguish user access from
enterprise authority and account entitlement from exposed tool schemas.

The open-source goal does not remove Box/Muse account, plan, or API requirements.
Document those requirements so people know what they can run.

## Community invitation and author links

- [ ] **B16: Invite people to start and review.** Place the first-task invitation
  near onboarding and in the footer. Before release, link to the plan; after a
  verified release, link to setup. Ask what worked, what failed, and what should
  come next, with a direct GitHub feedback link and an optional star link.
  Acceptance: every action reaches its intended destination, no unverified
  installation claim, and feedback guidance excludes private content.
- [ ] **B17: Add author and company links.** Add LinkedIn, X, and O'Leary Good links to
  the README and demo-site footer. Acceptance: the exact profiles are confirmed
  by Dan or a trusted first-party source; descriptive labels work with keyboards
  and screen readers. Dan confirmed the `danieloleary` handle for both profiles.
  README and writing-guide links are added; demo-site placement remains planned.
  LinkedIn was corroborated through indexed first-party content. Direct fetches
  were blocked by LinkedIn (999) and X (403), so browser navigation remains to
  be checked when the demo site is built.

  O'Leary Good Company: https://olearygood.com/. The homepage was retrieved
  successfully; README and writing-guide links are added.
