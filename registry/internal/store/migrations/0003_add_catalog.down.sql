-- Remove the catalog column from block_versions.
ALTER TABLE block_versions DROP COLUMN IF EXISTS catalog;
