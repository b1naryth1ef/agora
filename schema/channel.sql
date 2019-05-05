DO $$
  BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'channel_type') THEN
      CREATE TYPE channel_type AS ENUM (
        'realm_info',
        'realm_folder',
        'realm_text',
        'realm_voice',
        'group',
        'direct'
      );
    END IF;
  END
$$;

CREATE TABLE IF NOT EXISTS channels (
  id BIGSERIAL PRIMARY KEY,

  -- The realm (if applicable)
  realm_id BIGINT REFERENCES realms (id),

  -- Member ids (if group)
  member_identity_ids BIGINT[],

  -- The type of channel
  type channel_type,

  -- Name (all but direct)
  name TEXT,

  -- Topic
  topic TEXT
);
