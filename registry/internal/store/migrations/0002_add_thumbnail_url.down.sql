-- Remove thumbnail_url column from block_versions table
ALTER TABLE block_versions DROP COLUMN IF EXISTS thumbnail_url;
