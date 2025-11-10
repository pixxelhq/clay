-- Add thumbnail_url column to block_versions table
ALTER TABLE block_versions ADD COLUMN IF NOT EXISTS thumbnail_url TEXT;
