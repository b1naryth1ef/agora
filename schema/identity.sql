CREATE TABLE IF NOT EXISTS identities (
  id UUID PRIMARY KEY,

  -- Public signing key for this identity
  key TEXT,

  -- This is our access token
  access_token BYTEA NOT NULL,

  -- The alias this identity goes by
  alias TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS identities_key_idx ON identities (key);
