-- Catalog media (including catalog.yaml itself) is uploaded to object storage by
-- `clay block assets upload-catalog`, so the registry stores a URL to the
-- published catalog 
ALTER TABLE block_versions ADD COLUMN IF NOT EXISTS catalog_url TEXT;
