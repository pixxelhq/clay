---
rfc: 0001
title: Client Metadata in Block Specs
status: proposed
proposed_on: 2026-08-19
accepted_on: --
authors:
  - name: Riteek Srivastav
    github: https://github.com/riteeksrivastav
reviewers:
  - Marketplace team
  - name: Ravi Suhag
    github: https://github.com/ravisuhag
---

# RFC 0001: Client Metadata in Block Specs

## Status
Proposed · 2026-08-19

## Background

A block's `clay.yaml` tells the executor how to run the model, but it says little about what the outputs *mean*. Clients that consume block outputs — a rendering UI binding maps, legends, tables and charts; an LLM integration that compiles block metadata into a prompt; a notebook — end up keeping their own hand-written, per-model configuration: "this raster pairs with that CSV, this column is a percentage, this feature property carries the fill color." Maintained by hand, per client, that configuration drifts from what blocks actually produce.

Much of the needed metadata already has a home in the datatypes schema (`display_name`, `description`, `group`, `file_type`, `file_schema`); the rest has no field at all: column types and units, output roles, display intent, and vector attribute structure.

This RFC does two things:

1. Documents **how the existing fields can be used** so that clients can generate their bindings from the spec instead of hand-writing them.
2. Introduces **a small set of new fields** for what the schema cannot express today.

It defines the contract and its intended use only. How any given deployment fills these fields across its models, and what conventions it enforces at publish time, is that deployment's policy and lives outside this document.

## Decision

TBD. (Proposed: Approach A below.)

## Context

### Current state

The spec reaches the executor; clients never read it. Each client maintains its own hand-written model config, disconnected from the spec it describes.

```
+------------+   clay    +----------+      +------------+      +-----------+
| model repo | publish   | registry | ---> | blocks API | ---> | executors |
| clay.yaml  | --------> |          |      |            |      |           |
+------------+           +----------+      +------------+      +-----------+

                                        (spec unused by clients)

+---------------------------+           +------------------+
| hand-written model config | --------> | rendering client |
| (per model, per client;   |           +------------------+
|  drifts from the spec)    | --------> | LLM client       |
+---------------------------+           +------------------+
```

### Proposed state

The spec is the single source of truth for model facts. Client bindings are generated from it; each client keeps only its own rendering choices.

```
+------------+   clay    +----------+      +------------+      +-----------+
| model repo | publish   | registry | ---> | blocks API | ---> | executors |
| clay.yaml  | --------> |          |      |            |      |           |
+------------+           +----------+            |
                                                  v
                                         +--------------------+      +------------------+
                                         | generated client   | ---> | rendering client |
                                         | bindings           |      +------------------+
                                         | (facts from spec;  | ---> | LLM client       |
                                         |  rendering choices | ---> | notebook, ...    |
                                         |  stay client-side) |      +------------------+
                                         +--------------------+
```

### What the schema cannot express today

1. **Column-level truth for tables.** `TabularFileSchema` is a bare list of header strings — no types, no units. No client can format "12.4 km²" or pick a sensible chart from the spec alone.
2. **Vector attribute structure.** `VectorProperties` records only the geometry type. A block whose analytics payload lives in feature properties is undocumented by construction.
3. **Output roles.** Which raster is the "before" scene, which output is an internal mask, which CSV belongs to which raster — clients recover this by guessing from output names, and naming heuristics break as soon as names abbreviate or change.

### Constraints and non-goals

- **Client opinions stay client-side.** Derived display fields (column renames, concatenated labels) and composition choices (which charts to draw, how to build prompts) are the opinions of one client, not facts about the block. They get no fields here.
- **Back-compat.** Every addition is optional. Existing blocks keep publishing unchanged; clients fall back to their current behavior for blocks that don't populate the fields.
- **No enforcement rules in this RFC.** Whether descriptions must carry a role, whether headers must be verified, whether publishes are gated — deployment policy, out of scope.

## Approaches

### Approach A: typed columns + role on outputs + join-declared vector attributes (proposed)

**Using the fields that already exist.** Guidance, not rules — this is what each field is *for*:

| Field | Intended use |
|---|---|
| `display_name` | Short human title for the input/output ("Land Cover Map") |
| `description` | Plain prose a client can surface directly (tooltips, prompts). A deployment may layer a machine-readable convention on top — e.g. a leading `[role]` tag — until the typed `role` field below is available |
| `group` | Same slug on a raster and the table(s) describing it, so a client learns `ndvi_raster` goes with `ndvi_stats` without name heuristics |
| `properties.file_type` | The actual payload type of a tabular output (`csv`, `json`, ...) |
| `properties.file_schema.headers` | The exact header row the model writes |

**New fields.** Column-level truth and a typed role. Complete changed messages in `proto/data.proto` (unchanged fields listed with their existing numbers):

```proto
// NEW message
message TabularColumnSpec {
  required string name  = 1;  // header exactly as written in the file
  optional string dtype = 2;  // "string" | "number" | "integer" | "date" | "bool"
  optional string unit  = 3;  // "sq_km" | "percent" | "mg_l" | ...
  optional string role  = 4;  // "key" | "label" | "color" | "title"; default "value"
}

// CHANGED message
message TabularFileSchema {
  repeated string headers = 1;             // existing, kept for back-compat
  repeated TabularColumnSpec columns = 2;  // NEW
}

// CHANGED messages: `role` is appended to each format message and its Spec
// variant (Raster/RasterSpec, Vector/VectorSpec, Tabular/TabularSpec,
// Date/DateSpec, String/StringSpec, Number/NumberSpec), using that message's
// next free field number. Shown complete on Tabular:
message Tabular {
  optional Format format = 1 [default = tabular];
  optional string type = 2;
  optional string name = 3 [default = ''];
  optional string description = 4;
  optional string display_name = 5;
  optional bool is_artifact = 6 [default = true];
  optional string group = 7;
  map<string, string> metadata = 8;
  optional string default = 9;
  optional string value = 10;
  optional double area = 11;
  optional AssetSource asset_source = 12;
  optional TabularProperties properties = 13;
  optional Version version = 14 [default = v2];
  optional string role = 15;  // NEW: "scene" | "before" | "after" | "measurement" |
                              // "uncertainty" | "mask" | "stats" | ... (open vocabulary)
}
```

- `dtype` and `unit` let a generic client format values, sort correctly, and pick charts with no per-model config — and they settle unit disputes at the source.
- Column `role` covers styling needs without format-specific fields: `label` is the name a legend groups by, `color` carries a fill hex, `title` is a per-feature caption, `key` marks a join column (below).
- Output `role` is an open vocabulary: it grows by PR, and clients must ignore roles they don't know.

Example — a class-statistics CSV declared with column roles, as it would appear in `clay.yaml`:

```yaml
outputs:
  - format: tabular
    name: class_stats
    properties:
      file_type: csv
      file_schema:
        columns:
          - { name: "region_id",  dtype: string, role: key }      # joins to a vector output
          - { name: "class name", dtype: string, role: label }    # the legend groups by this
          - { name: "color",      dtype: string, role: color }    # fill hex for the class
          - { name: "area",       dtype: number, unit: sq_km }    # role omitted -> "value"
          - { name: "coverage",   dtype: number, unit: percent }  # role omitted -> "value"
```

A client reading this needs no per-model config to render the table (formatted units), the legend (`label` + `color` rows), or a chart (`label` against any `value` column).

**Vector attributes via split outputs.** Instead of a parallel property-schema for GeoJSON, a vector output carries geometry only and its attributes ship as CSVs joined on a declared key:

```proto
// CHANGED message
message VectorProperties {
  optional string geometry = 1;             // existing
  optional string feature_id_property = 2;  // NEW: per-feature key, e.g. "region_id"
}

// NEW message, referenced from TabularProperties below. The join is declared
// from the CSV side: one vector can have many CSVs, but each CSV describes
// exactly one vector output.
message JoinSpec {
  required string output = 1;       // name of the vector output this CSV describes
  required string column = 2;       // the role:"key" column in this CSV
  optional string cardinality = 3;  // "one" = per-feature attributes, "many" = per-feature series
}

// CHANGED message — this is where JoinSpec lives
message TabularProperties {
  optional string file_type = 1;               // existing
  optional TabularFileSchema file_schema = 2;  // existing
  optional JoinSpec joins_to = 3;              // NEW: relational link to a vector output
}
```

Every schema question becomes a tabular one, already solved above. Time series become honest data — a plain `region_id, date, value` file instead of arrays packed into feature properties. `cardinality` removes guessing: "one" merges columns onto features, "many" groups rows per feature. Rendering clients join client-side (`promoteId` + feature-state, the standard web-map pattern), and a joined export can still hand analysts one self-contained file. Blocks that keep attributes inline remain valid — the split is what the schema *supports*, not what it mandates.

### Approach B: format-specific schema fields

Add a `VectorPropertySpec` list, `label_property`/`color_property`, a series-zipping declaration, plus table-shape flags (`shape: long`, index-column markers, dynamic-header patterns).

| Pros | Cons |
|---|---|
| Describes today's outputs exactly as they are, quirks included. | Two parallel schemas (tabular columns and vector properties) to keep consistent forever. |
| No change to what models emit. | Encodes producer quirks (pandas index columns, long tables) into the contract permanently instead of letting producers fix them. |
| | Series-as-parallel-arrays needs its own alignment semantics that a long CSV gets for free. |

### Approach C: convention in the `metadata` map

Express roles, pairing, and column types as agreed keys in the existing free-form `metadata` map.

| Pros | Cons |
|---|---|
| Zero schema changes. | Unvalidated and untyped — typos ship silently. |
| Deployments can start today. | Invisible to schema tooling and codegen; every client re-implements parsing. |
| | Conventions drift per deployment; the point was one contract. |

## Milestones and Stories

Scope: this repository and the datatypes schema only.

| # | Story | Points |
|---|---|---|
| 1 | Schema: `TabularColumnSpec`, `columns` on `TabularFileSchema`, `role` on DataSpecs | 3 |
| 2 | Schema: `feature_id_property` on `VectorProperties`, `JoinSpec` / `joins_to` on `TabularProperties` | 2 |
| 3 | Clay: parse and validate the new fields from `clay.yaml`; surface them in publish payloads | 3 |
| 4 | Docs: field reference + usage guidance for block authors and client implementers | 2 |

## Open Questions

- Role vocabulary governance: proposed — it lives with the datatypes schema, grows by PR, and clients must ignore unknown roles. Is a seed list published with the schema, or left entirely to deployments?
- Should `unit` be an open string (proposed) or a constrained enum?

## References

- Datatypes contract: `proto/data.proto` (this repository)

## Changelog

- 2026-08-19: Proposed
