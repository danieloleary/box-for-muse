# Keeping the project current

Review weekly and before each connector release:

1. Search public posts by @levie for enterprise agents, Box, permissions, metadata,
   research and continuous work. Check new Box API/changelog documentation too. Review official Grok Bot and
   Codex changes against research/COMPARISON.md and the onboarding backlog.
2. Compare findings to research/SOURCES.md and the stable use-case IDs. Record
   original URL, read date, retrieval quality and a concise paraphrase.
3. Prepare a focused update with changed assumptions, affected cases and new tests.
   Do not infer runtime support or change permissions from a product announcement.
4. Run the catalog validator. Maintainer reviews the change before public merge.
5. For implementation changes, repeat relevant live Muse fixtures and update the
   compatibility matrix. Never silently change scopes, retention or output access.

There is no background X scraper or auto-publisher in this repository. Research
monitoring should prepare reviewable updates and remain quiet when nothing material
changes. Do not add paid API dependencies without an explicit decision.

Security reports: do not put secrets or exploitable details in a public issue.
Use GitHub private vulnerability reporting if enabled; otherwise open a sanitized
request for a private reporting channel. No security-response SLA is promised.
