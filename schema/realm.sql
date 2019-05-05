CREATE TABLE IF NOT EXISTS realms (
  id BIGSERIAL PRIMARY KEY,

  -- Name of the realm
  name TEXT,

  -- The owner of this realm
  owner_id BIGINT REFERENCES identities (id),

  -- Whether this realm is publically listed
  is_public BOOLEAN
);

CREATE TABLE IF NOT EXISTS realm_members (
  realm_id BIGINT REFERENCES realms (id),
  identity_id BIGINT REFERENCES identities (id),

  -- When this member joined the realm
  joined_at TIMESTAMP WITH TIME ZONE,

  -- Whether this member is a realm admin
  is_admin BOOLEAN,

  PRIMARY KEY (realm_id, identity_id)
);
