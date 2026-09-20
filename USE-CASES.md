# Top 50 Box agent use cases

Editorial build-priority ranking for Box for Muse and reusable Box agent tools. These are our proposals, not a list authored or endorsed by Aaron Levie. All are proposed, not implemented. Sources and limitations: [research notes](research/SOURCES.md).

Ranking favors useful content outcomes, reuse of core primitives, testability, and manageable permissions. Adjacent ranks are judgment calls, not measured ROI. Core is a dependency category, not a shipping claim.

| Rank | Use case | Trigger → result | Essential boundary | Gate | Theme |
| --- | --- | --- | --- | --- | --- |
| 1 | **Approved-source briefing** | On request → Find approved material and save a cited brief | Reject newer unapproved drafts | core | [L1](research/SOURCES.md#l1) |
| 2 | **Project change steward** | Folder changes → Maintain a change brief and decisions ledger | Deduplicate events and ignore own outputs | events | [L1](research/SOURCES.md#l1) |
| 3 | **Metadata completion steward** | Missing fields → Propose and apply reviewed business metadata | Preserve authoritative human values | metadata | [L5](research/SOURCES.md#l5) |
| 4 | **Contract obligation tracker** | New signed agreement → Extract obligations, owners and notice dates | Review clauses and date arithmetic | ai | [L4](research/SOURCES.md#l4) |
| 5 | **Permission-aware research memo** | Research question → Search across authorized sources and save synthesis | Disclose inaccessible or truncated sources | core | [L6](research/SOURCES.md#l6) |
| 6 | **Version conflict resolver** | Two conflicting documents → Compare versions and surface unresolved claims | Do not equate recency with approval | core | [L1](research/SOURCES.md#l1) |
| 7 | **Meeting preparation agent** | Before a meeting → Assemble a brief with decisions and questions | Do not invent commitments | core | [L3](research/SOURCES.md#l3) |
| 8 | **Policy freshness monitor** | Review date or revision → Find stale policies and draft update proposals | Require approval before publication | events | [L2](research/SOURCES.md#l2) |
| 9 | **Procurement packet intake** | New supplier packet → Extract fields and produce missing-item checklist | No supplier approval or payments | ai | [L3](research/SOURCES.md#l3) |
| 10 | **Audit evidence index** | Audit request → Match checklist to source-linked evidence | No compliance certification claims | core | [L2](research/SOURCES.md#l2) |
| 11 | **Contract renewal radar** | Approaching notice date → Prepare renewal review queue | Never send termination notices automatically | events | [L4](research/SOURCES.md#l4) |
| 12 | **Revenue opportunity review** | Portfolio review → Find contract clauses relevant to approved offers | No unsupported customer intent inference | ai | [L4](research/SOURCES.md#l4) |
| 13 | **Commercial usage rights finder** | Campaign request → Find documented brand and reference rights | Cite rights scope and expiry | metadata | [L5](research/SOURCES.md#l5) |
| 14 | **Signed MSA finder** | Natural-language query → Return agreements matching signature and business fields | Signature status must have evidence | metadata | [L5](research/SOURCES.md#l5) |
| 15 | **Clause deviation reviewer** | New contract draft → Compare clauses to an approved playbook | Human legal judgment retained | ai | [L7](research/SOURCES.md#l7) |
| 16 | **Vendor risk evidence assembler** | Vendor review → Collect certifications and documented gaps | No automated vendor risk decision | core | [L3](research/SOURCES.md#l3) |
| 17 | **Invoice extraction queue** | New invoice → Propose vendor, totals, currency and dates | Validate totals; no payment execution | ai | [B1](research/SOURCES.md#b1) |
| 18 | **Invoice duplicate reviewer** | New invoice → Find likely duplicates with source evidence | No automatic deletion or rejection | metadata | [L5](research/SOURCES.md#l5) |
| 19 | **Purchase-order reconciliation** | Invoice and PO arrive → Compare documented quantities and amounts | Report ambiguity and human-review differences | ai | [L5](research/SOURCES.md#l5) |
| 20 | **Financial report comparison** | Period-end upload → Explain changes across reports with sourced calculations | Deterministic arithmetic; no investment advice | core | [L6](research/SOURCES.md#l6) |
| 21 | **Customer onboarding checklist** | New customer folder → Track required documents and unresolved inputs | Keep visibility scoped to the customer | events | [L3](research/SOURCES.md#l3) |
| 22 | **Sales RFP answer draft** | RFP upload → Draft answers from approved source material | Flag missing support and stale claims | ai | [B1](research/SOURCES.md#b1) |
| 23 | **Account evidence brief** | Account review → Summarize contracts, notes and documented commitments | No external sends without authorization | core | [L3](research/SOURCES.md#l3) |
| 24 | **Customer feedback synthesis** | New survey batch → Correlate documented themes with product research | Minimize personal data and retain contrary evidence | ai | [L6](research/SOURCES.md#l6) |
| 25 | **Product launch readiness** | Launch review → Compare required assets to current approvals | Missing search result is not proof of absence | metadata | [L3](research/SOURCES.md#l3) |
| 26 | **Brand compliance draft review** | New campaign asset → Compare copy to approved brand guidance | No automatic public publication | core | [L6](research/SOURCES.md#l6) |
| 27 | **Asset expiration monitor** | License date approaches → Flag expired or expiring licensed content | Verify rights evidence; no automatic takedown | events | [L5](research/SOURCES.md#l5) |
| 28 | **Localization source steward** | Source copy revised → List translations potentially needing updates | Compare exact source versions | events | [L1](research/SOURCES.md#l1) |
| 29 | **Research literature synthesis** | Scoped research question → Produce a source-linked evidence matrix | Distinguish findings from hypotheses | ai | [L6](research/SOURCES.md#l6) |
| 30 | **Research contradiction monitor** | New study added → Identify changes to prior documented conclusions | Require domain review; no clinical decisions | events | [L4](research/SOURCES.md#l4) |
| 31 | **Technical specification traceability** | Spec changes → Map changed requirements to affected documents | Record links as proposed unless verified | metadata | [L1](research/SOURCES.md#l1) |
| 32 | **Incident handover brief** | Shift handoff → Summarize incident evidence and open questions | No secrets or unsupported attribution | core | [L2](research/SOURCES.md#l2) |
| 33 | **Access review packet** | Scheduled review → Assemble collaborator and sharing exceptions | Read-only first; no automatic revocation | admin | [L2](research/SOURCES.md#l2) |
| 34 | **Shared-link exposure review** | Link or access changes → Flag sharing inconsistent with approved baseline | No broad crawling or public-link creation | admin | [L2](research/SOURCES.md#l2) |
| 35 | **Classification recommendation queue** | New or unlabeled file → Recommend security labels from explicit rules | Labels can change enforcement; require approval | admin | [L2](research/SOURCES.md#l2) |
| 36 | **Retention evidence collector** | Review request → Collect authorized policy assignments and exceptions | Never remove holds or retention | admin | [L2](research/SOURCES.md#l2) |
| 37 | **Legal-hold evidence map** | Approved matter review → Index authorized held material and coverage gaps | No hold changes or legal determinations | admin | [L2](research/SOURCES.md#l2) |
| 38 | **Enterprise event timeline** | Investigation request → Correlate authorized events with file versions | Admin permission; state event coverage limits | admin | [L2](research/SOURCES.md#l2) |
| 39 | **Sensitive output destination check** | Before writing result → Compare source and destination access constraints | Block broader exposure; metadata alone is insufficient | admin | [L2](research/SOURCES.md#l2) |
| 40 | **Agent action receipts** | Every agent run → Save minimal input/version/action/output manifests | No secrets; does not replace Box audit logs | core | [L2](research/SOURCES.md#l2) |
| 41 | **Stale knowledge-base curator** | Review-date changes → Draft refreshed guides from approved sources | Keep old source provenance; no silent replacement | events | [L3](research/SOURCES.md#l3) |
| 42 | **New-team onboarding guide** | New project member request → Build authorized reading order and glossary | Do not reveal inaccessible file names | core | [L3](research/SOURCES.md#l3) |
| 43 | **Decision memory ledger** | Approved meeting record → Record decisions, owners and superseding evidence | Agent notes cannot self-promote to authority | metadata | [L1](research/SOURCES.md#l1) |
| 44 | **Multi-agent artifact handoff** | One agent finishes work → Write validated manifests for another agent to resume | Check version, ownership, schema and allowed actions | core | [L1](research/SOURCES.md#l1) |
| 45 | **Interrupted-run recovery** | Restart or timeout → Resume from verified checkpoints and reconcile writes | No duplicate outputs after uncertain responses | events | [L1](research/SOURCES.md#l1) |
| 46 | **Box AI evaluation bench** | Model or agent change → Compare extraction and citation accuracy on fixtures | Synthetic data and measured quality; no marketing extrapolation | ai | [L8](research/SOURCES.md#l8) |
| 47 | **Metadata quality dashboard** | Recurring validation → Measure completeness, invalid enums and conflicts | Limit report exposure and avoid sensitive field values | metadata | [L5](research/SOURCES.md#l5) |
| 48 | **Document workflow routing** | New content arrival → Propose destination and owner from approved rules | Moves can alter access; review first | metadata | [L3](research/SOURCES.md#l3) |
| 49 | **Data-room diligence index** | Approved transaction review → Map questions to evidence across a document set | Access boundaries; no autonomous transaction decisions | ai | [L6](research/SOURCES.md#l6) |
| 50 | **Community connector compatibility watch** | API or host change → Re-run documented fixtures and propose fixes | No silent permission expansion or automatic releases | core | [L8](research/SOURCES.md#l8) |

## Build order

1. Prove UC-01, 05, 06 and 07 with search/read/save and source versions.
2. Add UC-02 and 45: durable monitoring and restart-safe writes.
3. Add UC-03, 04 and 17: reviewed metadata and Box AI extraction.
4. Pilot admin workflows only after scope, roles, entitlement and enforcement checks.

## Capability gates

- **core:** user-authorized Box search, content and writes; Muse helper/runtime compatibility still requires implementation proof.
- **events:** durable state, event deduplication, bounded polling or a verified webhook receiver; no active monitor is implied.
- **metadata:** discover templates, types and permitted mutations; distinguish business metadata from security classification.
- **ai:** verify Box AI entitlement, scopes, format limits, truncation, cost and output quality.
- **admin:** separately approved enterprise access and product-specific APIs; ordinary user OAuth is not enterprise oversight.

All writes need an explicit destination, current access checks, conflict handling and readback. Source content is untrusted input. Derived output must not escape source restrictions. Human review remains necessary for legal, financial, security and other consequential decisions.
