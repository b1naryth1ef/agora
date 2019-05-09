CREATE TABLE IF NOT EXISTS realms (
  id UUID PRIMARY KEY,

  -- Name of the realm
  name TEXT NOT NULL,

  -- The owner of this realm
  owner_id UUID REFERENCES identities (id) NOT NULL,

  -- Whether this realm is publicly listed
  is_public BOOLEAN
);

CREATE TABLE IF NOT EXISTS realm_members (
  realm_id UUID REFERENCES realms (id) ON DELETE CASCADE,
  identity_id UUID REFERENCES identities (id),

  -- When this member joined the realm
  joined_at TIMESTAMP WITH TIME ZONE NOT NULL,

  -- Whether this member is a realm admin
  is_admin BOOLEAN,

  PRIMARY KEY (realm_id, identity_id)
);

CREATE TABLE IF NOT EXISTS realm_roles (
  id UUID PRIMARY KEY,

  -- Realm this role belongs too
  realm_id UUID REFERENCES realms (id) ON DELETE CASCADE,

  -- Name of this role
  name TEXT NOT NULL,

  -- Weight of this role (lower weight means higher priority)
  weight SMALLINT NOT NULL,

  -- Scopes this role grants to its members
  granted_scopes JSONB
);

-- TODO: figure out a better way to do this?
ALTER TABLE realms ADD COLUMN IF NOT EXISTS default_role_id UUID REFERENCES realm_roles (id);

CREATE TABLE IF NOT EXISTS realm_member_roles (
  role_id UUID REFERENCES realm_roles (id) ON DELETE CASCADE,
  identity_id UUID REFERENCES identities (id),
  realm_id UUID REFERENCES realms (id) ON DELETE CASCADE NOT NULL,

  FOREIGN KEY (realm_id, identity_id) REFERENCES realm_members (realm_id, identity_id) ON DELETE CASCADE,

  PRIMARY KEY (role_id, identity_id)
);

CREATE INDEX realm_member_roles_realm_id_idx
  ON realm_member_roles (realm_id);
