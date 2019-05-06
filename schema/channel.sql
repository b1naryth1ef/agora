DO $$
  BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'realm_channel_type') THEN
      CREATE TYPE realm_channel_type AS ENUM (
        'info',
        'folder',
        'text',
        'voice'
      );
    END IF;
  END
$$;

CREATE TABLE IF NOT EXISTS realm_channels (
  id UUID PRIMARY KEY,

  -- The realm
  realm_id UUID REFERENCES realms (id) ON DELETE CASCADE NOT NULL,

  type realm_channel_type,
  name TEXT,
  topic TEXT
);

CREATE TABLE IF NOT EXISTS realm_channel_role_scope_layers (
  channel_id UUID REFERENCES realm_channels (id) ON DELETE CASCADE,
  role_id UUID REFERENCES realm_roles (id) ON DELETE CASCADE,

  -- Scopes this layer grants
  granted_scopes JSONB,

  -- Scopes this layer revokes
  revoked_scopes JSONB,

  PRIMARY KEY (channel_id, role_id)
);
