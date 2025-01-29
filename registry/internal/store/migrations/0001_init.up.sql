-- uuid-ossp extension provides functions to generate uuid
-- like public.uuid_generate_v4()
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE FUNCTION update_updated_on_column()
    RETURNS TRIGGER AS
$$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TABLE IF NOT EXISTS blocks (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL UNIQUE,
  kind TEXT NOT NULL,
  type TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS block_versions (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  version TEXT NOT NULL,
  block_id UUID NOT NULL REFERENCES blocks(id),
  specification JSONB NOT NULL,
  documentation_url TEXT,
  docker_image TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  CONSTRAINT unique_version_block UNIQUE (version, block_id)
);