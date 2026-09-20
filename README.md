# Box for Muse ♥

**Built with love by Dan O'Leary. Built for everyone to help improve.**

An independent community project exploring a great Box connector for Muse and
reusable tools for agents working with Box. Dan is a Box and Meta alumnus. This
project is not sponsored, endorsed or maintained by Box or Meta.

The aim: agents that find trustworthy sources, understand changes, extract
structured facts, and save useful work while respecting enterprise controls.

## What is available today

This repository publishes a **research-backed roadmap and contribution framework**,
not an installable connector. The connector is being developed separately; no
working code, production readiness or directory availability is claimed here.

- [Top 50 use cases](USE-CASES.md), ranked for build priority.
- [Source register](research/SOURCES.md), including Levie posts and attribution limits.
- [Machine-readable catalog](data/use-cases.json).
- [Roadmap and release gates](ROADMAP.md).
- [How to contribute](CONTRIBUTING.md) and [maintenance process](MAINTENANCE.md).

Start with approved-source briefs, project-change monitoring, reviewed metadata
and contract obligations. Enterprise governance and security workflows follow
explicit permission and entitlement checks. Box AI is optional and account-dependent.

## Everyone can contribute

Open an issue with a real workflow, a correction, an API change or a synthetic
acceptance fixture. Send a pull request to improve the catalog or documentation.
Use the issue forms to include sources, permission needs and a measurable outcome.
Do not post customer documents, account identifiers, credentials or private logs.

The roadmap is openly available under the MIT license. Box/Muse accounts,
app approval, API charges and product entitlements may still be needed to run the
future connector. Open source does not make paid services free or guarantee access.

## Local validation

```sh
python3 scripts/validate.py
```

The validator checks catalog integrity and references. It does not prove Box API
compatibility, governance enforcement or a working Muse installation.
