# RFC 0001: Date validation in the block specification

- **Status:** Implemented (clay v1.3.0, #12)
- **Date:** 2026-09-18
- **Author:** shubhranil@pixxel.co.in

## Summary

Add `min_date`, `max_date`, and `date_format` to the `DateValidation` message,
document them, and reject malformed validation blocks at publish time. Runtime
enforcement is included but sequenced last.

## Motivation

Clay lets block authors declare validation rules on inputs: area bounds on
rasters and vectors, range/regex/enum constraints on numbers and strings. Dates
have no equivalent, so a block that only accepts imagery from a given time
window cannot say so.

These rules are a published part of a block's contract. Clients that render
inputs read them from the registry and constrain what a caller can submit, so a
missing rule means a block accepts input it cannot process and fails later than
it needs to.

`DateValidation` has been an empty placeholder since the validation messages
were introduced. This RFC fills it in.

## Background

`proto/data.proto:513-555` defines six validation messages, one per format:

| Format | Fields | Go | Python |
|---|---|---|---|
| raster | `min_area`, `max_area` | full | none |
| vector | `min_area`, `max_area` | full | none |
| string | `regex_match`, `allowed_values` | full | full |
| number | `min_value`, `max_value`, `allowed_values` | full | full |
| tabular | none | no-op stub | none |
| date | none | no-op stub | none |

Go dispatches through `DataSpecWrapper.ValidateWithInput`
(`proto/go/main.go:288`), which already routes all six formats;
`ValidateDate` (`main.go:465`) is a no-op stub with underscored parameters.
Python's `validate_input` (`proto/python/datatypes/data.py:414`) branches on
string and number only. The dispatch layer is complete and the date slot is
deliberately empty.

**The spec reaches its consumers as an opaque passthrough.** `inputs` is
`json.RawMessage` at every hop — `pkg/config/config.go:31`,
`pkg/registry/registry.go:39`, `registry/api/http/model.go:31` — and stored as
JSONB (`0001_init.up.sql:29`). `Specification.Validate()` only checks that
`inputs` is non-nil. So new fields reach consumers with no registry changes, and
nothing rejects a malformed validation block.

## Proposal

### 1. Schema

```protobuf
enum DateFormat {
  date_only = 0;  // YYYY-MM-DD
  date_time = 1;  // RFC 3339, e.g. 2024-03-01T12:00:00Z
}

message DateValidation {
  // Earliest allowed date, inclusive
  optional string min_date = 1;
  // Latest allowed date, inclusive
  optional string max_date = 2;
  // Required encoding for the input value
  optional DateFormat date_format = 3;
}
```

Bounds are inclusive and independently optional, matching `NumberValidation`.

`date_format` is an enum, not a format string, because patterns are not
portable — `%Y-%m-%d` is meaningless to Go, which uses reference layouts
(`2006-01-02`), so the two enforcement paths could disagree about the same spec.
An enum also gives clients a discrete mode to configure a date input with.

Regenerate both bindings per `proto/README.md`; commit `data.pb.go`,
`data_pb2.py`, `data_pb2.pyi`.

### 2. Reject malformed specs at publish time

Each input declares a `format`. Dispatch on it to the matching validation
message, then unmarshal that input's `validation` object into it with protojson
in strict mode:

```go
func validationMessageFor(format string) (proto.Message, error) {
	switch format {
	case "raster":  return &generated.RasterValidation{}, nil
	case "vector":  return &generated.VectorValidation{}, nil
	case "tabular": return &generated.TabularValidation{}, nil
	case "date":    return &generated.DateValidation{}, nil
	case "string":  return &generated.StringValidation{}, nil
	case "number":  return &generated.NumberValidation{}, nil
	}
	return nil, fmt.Errorf("unknown format %q", format)
}
```

Three classes of author error fail as a result:

- **Unknown keys** — protojson rejects fields absent from the message, so
  `min_dat` fails. Rejection is the default; `proto/go/main.go:410` explicitly
  opts out with `DiscardUnknown: true`, this path would not.
- **Wrong types** — `min_value: "abc"` fails.
- **Format mismatches** — `min_date` is not a field on `StringValidation`, so
  declaring it on a string input fails as an unknown field, no special casing.

**Scope is the `validation` object, not the whole input.** Strict-checking an
entire input against its `*Spec` message would catch more, but it would reject
valid specs: the Spec messages have no `default` field — `optional string
default = 9` exists only on the six Data messages (`data.proto:152-338`) — while
real specs do declare input defaults, e.g.
`python/tests/fixtures/blocks/dummy_block.yaml`. Confining the unmarshal to
`validation` avoids the mismatch.

The dispatch above is per-*format*: six entries, changing only if Clay gains a
seventh data format. What it avoids is a per-*field* list of legal keys, which
grows every time a field is added. `validate_input` (`data.py:433-448`) already
carries five hand-written `if "x" in validation` chains that must be extended by
hand per field; this avoids repeating that. `ValidateWithInput`
(`proto/go/main.go:288`) is the same six-way switch, so there is precedent.

The underlying problem is not hypothetical. `python/tests/runners/dummy-spec.yml`
declares `is_artiface: true` — a typo for `is_artifact`, in this repo's own
fixture, silently ignored for as long as it has existed. Note the lint above
would *not* catch it, since it sits at input level rather than inside
`validation`. Widening to whole inputs means first adding `default` to the Spec
messages; worth doing, but out of scope here.

Placement: immediately after `config.GetConfig` (`cmd/publish.go:59`), before
`buildImage` and `docker.Push`, so authors do not sit through a build and push
to learn they typo'd a key.

This checks shape, not meaning — `min_date: "hello"` is a valid proto string. An
explicit date parse on top catches that, sharing code with §3.

### 3. Runtime enforcement

`ValidateDate` (`proto/go/main.go:465`) and a `date` branch in `validate_input`
for callers who submit inputs directly rather than through a client that reads
the spec. Semantics in both:

- An empty value is treated as unset, not invalid — consistent with
  `ValidateRaster` tolerating a missing `value` when `stac_url` is present, and
  with `DateProperties.from_aoi` allowing a date to be derived.
- A malformed bound in the spec is a spec error, not silently skipped.
- Each bound is checked independently and inclusively.

`DataWrapperInterface` (`main.go:36`) exposes `SetField` but no field getter, so
`ValidateDate` cannot read `from_aoi` directly. The empty-value rule sidesteps
this; a stricter check would mean widening the interface.

Python needs two things Go does not: `datetime.fromisoformat` rejects a `Z`
suffix before 3.11 and Clay targets 3.10, so the suffix needs normalising; and
comparing naive against aware datetimes raises `TypeError` rather than
`ValidationError`, so `date_time` mode must require an offset or normalise to UTC.

No Go validator has tests today — `ValidateString`, `ValidateNumber`,
`ValidateRaster`, `ValidateVector` are all untested. `TestValidateDate` would be
the first.

## Defaults do not survive the passthrough

The spec travels YAML → JSON → JSONB and never through protobuf, so no
`[default = ...]` materialises for a consumer reading the registry API. An
omitted `date_format` appears as an absent key, not `date_only`. This applies to
every defaulted field in the schema.

`is_artifact` is the existing instance of this, not a counterexample to it. It
carries `[default = true]` on raster/vector/tabular and `[default = false]`
elsewhere, but an author who omits it still produces JSONB with no `is_artifact`
key. Defaults materialise only where something builds the message through
protobuf — `DataWrapper.__init__` (`data.py:101-113`) back-fills them by walking
the descriptor — which the registry path never does. Any consumer reading it
correctly today is applying the default on its own side, and the only place that
default is written down for them is a parenthetical in `mkdocs/docs/spec.md:229`.

This RFC proposes documenting the defaults in `mkdocs/docs/spec.md` and having
consumers apply them. The alternative — normalising through protobuf in
`clay publish` so stored JSONB is self-describing — removes the drift risk but
changes the bytes written, which is a storage-contract change that should not
ride along with a field addition.

## Compatibility

**Wire format:** compatible. Adding `optional` fields to an empty proto3 message
is backward and forward compatible; existing readers skip unknown fields.

**Existing blocks:** no block declares date validation today, so no spec newly
becomes invalid. But publish-time checking will start rejecting *pre-existing*
typos in number and string validation blocks — specs that publish cleanly today
could begin failing. See open questions.

**Distribution:** `pixxel-datatypes` publishes to PyPI on changes under
`proto/python/`; Go bindings live in the root module and ship via a clay tag.
`python/requirements/requirements.txt:7` lists `pixxel-datatypes` unpinned, so
blocks pick up validator changes on their next rebuild with no version gate.
Benign for a field nobody has declared yet, but it is the channel every future
enforcement change travels through and it has no brake. Worth addressing
separately.

## Alternatives considered

- **Mandate RFC 3339, drop `date_format`.** Simpler, natively parsed by both
  languages. Rejected: many inputs are naturally date-only, and forcing a time
  component pushes noise onto authors and callers.
- **A strptime pattern field.** Rejected for the portability reason in §1.
- **Relative bounds** ("within the last 30 days"). Useful, but cannot be a fixed
  ISO string; needs its own field and a defined evaluation time. Deferred rather
  than smuggled into `min_date`.
- **Do nothing, let consumers validate.** Client-side rules are advisory and
  bypassed by direct API callers. The schema is what makes the rule a contract.

## Out of scope

- `TabularValidation`, the other empty message. Same pattern, but its useful
  constraints are about column schema and need a larger design.
- Raster and vector area validation in Python — specified and documented
  (`mkdocs/docs/spec.md:245`) but implemented only in Go.
- Wiring `validate_input` into the Clay runner. It has no caller outside its own
  tests, so Python-side rules never fire during block execution. Fixing that
  changes behaviour for every block already declaring string or number
  validation and deserves its own RFC.

## Open questions

1. Should publish-time rejection be an error or a warning in its first release?
   Erroring is correct but will fail specs that publish successfully today. The
   blast radius depends on how many published specs declare `validation` at all,
   which we should measure against the registry before deciding.
2. Should `DateFormat` have an explicit `unspecified = 0` member? As written,
   proto3 makes an omitted `date_format` indistinguishable from `date_only`.
3. Should `clay publish` normalise specs through protobuf, and if so what
   happens to existing registry rows?

## Implementation plan

1. Proto fields and enum; regenerate and commit both bindings.
2. `mkdocs/docs/spec.md` — date validation subsection alongside number and
   string, plus explicit documentation of defaults.
3. Publish-time spec validation in `cmd/publish.go`, with tests.
4. `ValidateDate` in Go and the `date` branch in Python, with tests.
5. `pixxel-datatypes` version bump and a `CHANGELOG.md` entry.

Steps 1-3 deliver the contract and the author-facing feedback loop. Step 4 is
independent and can land separately.

## Outcome

Shipped in clay `v1.3.0` (#12) and enforced on dexter's create-inference path
(pixxelhq/dexter#504). Deviations from the plan above:

- The enum value `datetime` was renamed `date_time` in review: protobuf emits
  enum values as module-level constants and `datatypes` has no `__all__`, so
  the original name shadowed the stdlib module for star-importers.
- Both validators gate on one shared RFC 3339 regex before parsing, so the
  accepted set is identical by construction rather than by two parsers
  agreeing. Python normalises fractional seconds to six digits for 3.10.
- Unquoted YAML date bounds (which `yaml.safe_load` turns into date objects)
  are coerced via `isoformat()` instead of raising `TypeError`.
- Step 3 (publish-time lint in `clay publish`) was deferred. Review steered
  enforcement to inference time on the execution side, which the existing
  `ValidateWithInput` call already provides, and blocks reach that side
  through its own API rather than `clay publish`. Open question 1 therefore
  stays open; the lint remains available as OSS hygiene.
