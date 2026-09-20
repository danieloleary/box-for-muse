# Agent comparison and product decisions

Research reviewed September 19, 2026. This is a documentation and tool-inventory
comparison, not a live head-to-head evaluation. Recommendations remain proposals
until tested in Muse. No company endorsement or measured advantage is implied.

| Reference | Evidence | Design implication |
| --- | --- | --- |
| [Grok Bot](https://docs.x.ai/grok-bot/overview) | Documents persistent context, background work, routines, and handoffs. | Make recurring jobs understandable and keep results actionable. |
| [Grok connectors](https://docs.x.ai/grok/connectors) | Lists Box in the OAuth connector catalog. Detailed Box write, metadata, and AI parity was not established. | Benchmark connection friction; test operation coverage separately. |
| [Codex plugins](https://developers.openai.com/plugins/concepts/plugins) | Skills guide repeatable workflows; MCP exposes controlled tools. The inspected Codex session exposed Box search, uploads, versions, metadata, Hubs, and AI extraction schemas. | Combine explicit operations with reusable workflows and inspectable results. Tool availability is not runtime proof or entitlement. |
| [Box AI](https://developer.box.com/guides/box-ai) | Documents permission-aware knowledge bases, invoice extraction, and RFP answer banks. | Build on Box content and metadata capabilities, with account-specific verification. |
| [Box Events](https://developer.box.com/guides/events) | User and enterprise feeds differ. Events can repeat or arrive out of order; enterprise feeds need additional authority. | Monitoring needs durable state and reconciliation beyond scheduled prompts. |

## Priorities from the discussion

The first experience should help someone connect Box and finish a useful task.
Offer search, source-linked summarization, and document comparison as the planned
starter path. Introduce save-back and recurring workflows after that first success.
Keep the 50-case catalog available for discovery without making it a setup burden.

For deeper workflows, prioritize an RFP reviewer, project-change monitoring, and
reviewed metadata intake. Follow with obligation tracking, approved-source briefs,
and separately authorized access-review evidence. This is a delivery priority
change, not a renumbering of the research catalog.

Dan's documented proof-harness design contributed the RFP fixture requirements:
stale answers, contradictions, audience restrictions, missing evidence, legal
review, and unsupported external claims. A documented design is not a completed
run. Broader historical Box usage was not established by this research; do not
invent customer anecdotes or present private examples as public evidence.

## Proposed comparison method

Use the same fictional deal folder, instructions, permissions, and expected
outcomes across agents. Record source accuracy, planted defects found and missed,
manual interventions, verified writes, and restart/retry behavior. Identify product
versions and account prerequisites. Leave unavailable operations explicitly
unverified. Compare complete workflows rather than raw tool counts.

Repeat the relevant tests after a connector or platform change. Public marketing
should cite actual outcomes, not infer performance from a feature announcement.
