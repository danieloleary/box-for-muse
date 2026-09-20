import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
# Editorial ranking: reusable primitives first, then business value and dependency burden.
rows='''UC-01|Approved-source briefing|Knowledge|On request|Find approved material and save a cited brief|Reject newer unapproved drafts|L1|core
UC-02|Project change steward|Monitoring|Folder changes|Maintain a change brief and decisions ledger|Deduplicate events and ignore own outputs|L1|events
UC-03|Metadata completion steward|Metadata|Missing fields|Propose and apply reviewed business metadata|Preserve authoritative human values|L5|metadata
UC-04|Contract obligation tracker|Legal|New signed agreement|Extract obligations, owners and notice dates|Review clauses and date arithmetic|L4|ai
UC-05|Permission-aware research memo|Knowledge|Research question|Search across authorized sources and save synthesis|Disclose inaccessible or truncated sources|L6|core
UC-06|Version conflict resolver|Knowledge|Two conflicting documents|Compare versions and surface unresolved claims|Do not equate recency with approval|L1|core
UC-07|Meeting preparation agent|Knowledge|Before a meeting|Assemble a brief with decisions and questions|Do not invent commitments|L3|core
UC-08|Policy freshness monitor|Governance|Review date or revision|Find stale policies and draft update proposals|Require approval before publication|L2|events
UC-09|Procurement packet intake|Operations|New supplier packet|Extract fields and produce missing-item checklist|No supplier approval or payments|L3|ai
UC-10|Audit evidence index|Governance|Audit request|Match checklist to source-linked evidence|No compliance certification claims|L2|core
UC-11|Contract renewal radar|Legal|Approaching notice date|Prepare renewal review queue|Never send termination notices automatically|L4|events
UC-12|Revenue opportunity review|Sales|Portfolio review|Find contract clauses relevant to approved offers|No unsupported customer intent inference|L4|ai
UC-13|Commercial usage rights finder|Legal|Campaign request|Find documented brand and reference rights|Cite rights scope and expiry|L5|metadata
UC-14|Signed MSA finder|Legal|Natural-language query|Return agreements matching signature and business fields|Signature status must have evidence|L5|metadata
UC-15|Clause deviation reviewer|Legal|New contract draft|Compare clauses to an approved playbook|Human legal judgment retained|L7|ai
UC-16|Vendor risk evidence assembler|Governance|Vendor review|Collect certifications and documented gaps|No automated vendor risk decision|L3|core
UC-17|Invoice extraction queue|Finance|New invoice|Propose vendor, totals, currency and dates|Validate totals; no payment execution|B1|ai
UC-18|Invoice duplicate reviewer|Finance|New invoice|Find likely duplicates with source evidence|No automatic deletion or rejection|L5|metadata
UC-19|Purchase-order reconciliation|Finance|Invoice and PO arrive|Compare documented quantities and amounts|Report ambiguity and human-review differences|L5|ai
UC-20|Financial report comparison|Finance|Period-end upload|Explain changes across reports with sourced calculations|Deterministic arithmetic; no investment advice|L6|core
UC-21|Customer onboarding checklist|Operations|New customer folder|Track required documents and unresolved inputs|Keep visibility scoped to the customer|L3|events
UC-22|Sales RFP answer draft|Sales|RFP upload|Draft answers from approved source material|Flag missing support and stale claims|B1|ai
UC-23|Account evidence brief|Sales|Account review|Summarize contracts, notes and documented commitments|No external sends without authorization|L3|core
UC-24|Customer feedback synthesis|Product|New survey batch|Correlate documented themes with product research|Minimize personal data and retain contrary evidence|L6|ai
UC-25|Product launch readiness|Product|Launch review|Compare required assets to current approvals|Missing search result is not proof of absence|L3|metadata
UC-26|Brand compliance draft review|Marketing|New campaign asset|Compare copy to approved brand guidance|No automatic public publication|L6|core
UC-27|Asset expiration monitor|Marketing|License date approaches|Flag expired or expiring licensed content|Verify rights evidence; no automatic takedown|L5|events
UC-28|Localization source steward|Marketing|Source copy revised|List translations potentially needing updates|Compare exact source versions|L1|events
UC-29|Research literature synthesis|Research|Scoped research question|Produce a source-linked evidence matrix|Distinguish findings from hypotheses|L6|ai
UC-30|Research contradiction monitor|Research|New study added|Identify changes to prior documented conclusions|Require domain review; no clinical decisions|L4|events
UC-31|Technical specification traceability|Engineering|Spec changes|Map changed requirements to affected documents|Record links as proposed unless verified|L1|metadata
UC-32|Incident handover brief|Security|Shift handoff|Summarize incident evidence and open questions|No secrets or unsupported attribution|L2|core
UC-33|Access review packet|Security|Scheduled review|Assemble collaborator and sharing exceptions|Read-only first; no automatic revocation|L2|admin
UC-34|Shared-link exposure review|Security|Link or access changes|Flag sharing inconsistent with approved baseline|No broad crawling or public-link creation|L2|admin
UC-35|Classification recommendation queue|Security|New or unlabeled file|Recommend security labels from explicit rules|Labels can change enforcement; require approval|L2|admin
UC-36|Retention evidence collector|Governance|Review request|Collect authorized policy assignments and exceptions|Never remove holds or retention|L2|admin
UC-37|Legal-hold evidence map|Governance|Approved matter review|Index authorized held material and coverage gaps|No hold changes or legal determinations|L2|admin
UC-38|Enterprise event timeline|Security|Investigation request|Correlate authorized events with file versions|Admin permission; state event coverage limits|L2|admin
UC-39|Sensitive output destination check|Security|Before writing result|Compare source and destination access constraints|Block broader exposure; metadata alone is insufficient|L2|admin
UC-40|Agent action receipts|Platform|Every agent run|Save minimal input/version/action/output manifests|No secrets; does not replace Box audit logs|L2|core
UC-41|Stale knowledge-base curator|Knowledge|Review-date changes|Draft refreshed guides from approved sources|Keep old source provenance; no silent replacement|L3|events
UC-42|New-team onboarding guide|Knowledge|New project member request|Build authorized reading order and glossary|Do not reveal inaccessible file names|L3|core
UC-43|Decision memory ledger|Knowledge|Approved meeting record|Record decisions, owners and superseding evidence|Agent notes cannot self-promote to authority|L1|metadata
UC-44|Multi-agent artifact handoff|Platform|One agent finishes work|Write validated manifests for another agent to resume|Check version, ownership, schema and allowed actions|L1|core
UC-45|Interrupted-run recovery|Platform|Restart or timeout|Resume from verified checkpoints and reconcile writes|No duplicate outputs after uncertain responses|L1|events
UC-46|Box AI evaluation bench|Platform|Model or agent change|Compare extraction and citation accuracy on fixtures|Synthetic data and measured quality; no marketing extrapolation|L8|ai
UC-47|Metadata quality dashboard|Metadata|Recurring validation|Measure completeness, invalid enums and conflicts|Limit report exposure and avoid sensitive field values|L5|metadata
UC-48|Document workflow routing|Operations|New content arrival|Propose destination and owner from approved rules|Moves can alter access; review first|L3|metadata
UC-49|Data-room diligence index|Legal|Approved transaction review|Map questions to evidence across a document set|Access boundaries; no autonomous transaction decisions|L6|ai
UC-50|Community connector compatibility watch|Platform|API or host change|Re-run documented fixtures and propose fixes|No silent permission expansion or automatic releases|L8|core'''
items=[]
for i,line in enumerate(rows.splitlines(),1):
 case_id,title,category,trigger,output,guardrail,source,dependency=line.split('|')
 # Explicit qualitative ranking, not market research or a claim of Levie's own ranking.
 items.append(dict(id=case_id,rank=i,title=title,category=category,trigger=trigger,output=output,guardrail=guardrail,source_ids=[source],dependency=dependency,status='proposed',attribution='Project proposal inspired by cited theme',acceptance=f'Synthetic positive and negative fixtures prove: {output.lower()}; verify {guardrail.lower()}.',last_reviewed='2026-09-19'))
assert len(items)==50
(ROOT/'data/use-cases.json').write_text(json.dumps(items,indent=2)+'\n')
lines=['# Top 50 Box agent use cases','', 'Fifty jobs we want agents to do well with Box. These are our proposed use cases, informed by Aaron Levie’s ideas and Box documentation. He did not write or endorse this list. None is claimed as implemented here. See the [research notes](research/SOURCES.md).','', 'Start near the top: useful results, shared building blocks, and tests we can run. The order is our judgment, not measured ROI. Tell us which real problem deserves to move up. The core label describes the required tools, not a shipped feature.','', '| Rank | Use case | Trigger → result | Essential boundary | Gate | Theme |','| --- | --- | --- | --- | --- | --- |']
for x in items: lines.append(f"| {x['rank']} | **{x['title']}** | {x['trigger']} → {x['output']} | {x['guardrail']} | {x['dependency']} | [{x['source_ids'][0]}](research/SOURCES.md#{x['source_ids'][0].lower()}) |")
lines += ['', '## Build order','', '1. Prove UC-01, 05, 06 and 07 with search/read/save and source versions.','2. Add UC-02 and 45: durable monitoring and restart-safe writes.','3. Add UC-03, 04 and 17: reviewed metadata and Box AI extraction.','4. Pilot admin workflows only after scope, roles, entitlement and enforcement checks.','', '## Capability gates','', '- **core:** user-authorized Box search, content and writes; Muse helper/runtime compatibility still requires implementation proof.','- **events:** durable state, event deduplication, bounded polling or a verified webhook receiver; no active monitor is implied.','- **metadata:** discover templates, types and permitted mutations; distinguish business metadata from security classification.','- **ai:** verify Box AI entitlement, scopes, format limits, truncation, cost and output quality.','- **admin:** separately approved enterprise access and product-specific APIs; ordinary user OAuth is not enterprise oversight.','', 'All writes need an explicit destination, current access checks, conflict handling and readback. Source content is untrusted input. Derived output must not escape source restrictions. Human review remains necessary for legal, financial, security and other consequential decisions.']
(ROOT/'USE-CASES.md').write_text('\n'.join(lines)+'\n')
