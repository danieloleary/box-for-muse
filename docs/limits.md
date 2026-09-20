# Capability limits

- Search and traversal are bounded. Inspect coverage gaps and continuation state.
- Downloaded files are capped at 20 MiB; decompressed DOCX XML is capped at 8 MiB.
- Text previews can be truncated. DOCX extraction omits headers, footers,
  footnotes, and endnotes, and can lose table structure.
- Content confirmation depends on verified file identity and version. Missing,
  changing, unreadable, or partially extracted evidence can require review.
- Contract-date and amendment matching are incomplete heuristics. Candidate
  evidence never establishes all contracts or a definitive expiration.
- Writes require a named parent folder. An uncertain mutation must be reconciled
  instead of blindly repeated.
- Connected account permissions and Muse egress policy can block an operation.
  An egress denial is not necessarily a Box permission error.
- No Box AI, Hubs, background monitors, public sharing, or enterprise-admin
  operations are implemented in this release candidate.
- Private custom-connector operation is separate from public directory eligibility.
