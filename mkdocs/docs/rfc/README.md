# RFCs

Index of design proposals for Clay and its block contract. Each RFC captures a problem, the approaches considered, and (once accepted) the decision and delivery plan.

## Index

| # | Title | Status | Proposed | Accepted | Authors |
|---|---|---|---|---|---|
| [0001](./0001-block-metadata-for-clients.md) | Client Metadata in Block Specs | proposed | 2026-08-19 | -- | [Riteek Srivastav](https://github.com/riteeksrivastav) |

## Conventions

- **Filename:** `NNNN-short-slug.md` (zero-padded RFC number).
- **Frontmatter:** every RFC starts with YAML frontmatter containing `rfc`, `title`, `status`, `proposed_on`, `accepted_on`, `authors`, `reviewers`.
- **Status values:** `proposed`, `accepted`, `rejected`, `superseded`, `withdrawn`.
- **Structure:** `Background` → `Decision` → `Context` → `Approaches` → `Milestones and Stories` → `Open Questions` → `References` → `Changelog`. Decision stays `TBD` until an approach is chosen.
- **Speak in terms of Clay and its clients.** This is a public repository: RFCs describe the block contract and generic client integrations, never internal product or service names.

## Adding a new RFC

1. Copy an existing RFC as a template; bump the number.
2. Fill in Background, Context, and Approaches. Leave Decision as TBD.
3. Add a row to the Index above.
4. Open a PR for review.
5. Once accepted, update `status`, `accepted_on`, and the Decision section.
