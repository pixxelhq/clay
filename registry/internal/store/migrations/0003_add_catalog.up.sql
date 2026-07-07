-- Persist a copy of the structured catalog documentation (RFC 0001) on each
-- block version. Validation stays with Dexter; the registry stores it verbatim
-- as jsonb. Additive only — existing rows get an empty object.
ALTER TABLE block_versions ADD COLUMN IF NOT EXISTS catalog JSONB NOT NULL DEFAULT '{}'::jsonb;
