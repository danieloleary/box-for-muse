# Roadmap

Mission: built with love by Dan, available for everyone to use and improve.
The implementation goal is a reliable Box connector for Muse, with reusable
operation contracts for other agents. This public repository begins with research.

1. **Community foundation:** publish the 50-use-case catalog, sources, contribution
   forms and a reproducible catalog check. Status: prepared.
2. **Working core:** user OAuth; identity, search, browse, read, compare and save;
   source IDs/versions, permission-aware output and readback. Require actual Muse proof.
3. **Durability:** refresh and restart behavior, bounded pagination, rate limits,
   duplicate events, concurrent edits and uncertain-write recovery.
4. **Metadata and Box AI:** entitlement discovery, schema validation, reviewed
   extraction and measured accuracy on synthetic fixtures.
5. **Monitoring:** scoped owner-approved triggers, durable cursors, meaningful
   notifications, cost limits, stop controls and no self-triggering write loops.
6. **Enterprise pilots:** individually authorized access review, governance evidence
   and security timelines. Never equate a report with enforcement or certification.
7. **Release:** import only reviewed connector source and tests; document install,
   data flow, support and limitations; demonstrate the entire workflow in Muse.
8. **Launch assets:** original icon, actual screenshots and captioned video after
   the depicted features work. Community ownership stays visible; no logo reuse
   or implied endorsement. Directory requirements need direct verification.

Issue milestones should track these gates, not just feature completion. A use case
moves from proposed → specified → implemented → verified only with linked evidence.
Publishing a roadmap does not make the connector publicly installable.
