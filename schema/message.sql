DO $$
  BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'message_type') THEN
      CREATE TYPE message_type AS ENUM (
        'prose',
        'upload',
        'system_event'
      );
    END IF;
  END
$$;


CREATE TABLE IF NOT EXISTS messages (
  id BIGSERIAL PRIMARY KEY,

  type message_type,
  channel_id BIGINT REFERENCES channels (id) NOT NULL,
  author_id BIGINT REFERENCES identities (id) NOT NULL,
  content JSONB NOT NULL,

  -- Realm (if applicable)
  realm_id BIGINT REFERENCES realms (id)
)
