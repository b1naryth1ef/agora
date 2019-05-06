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


CREATE TABLE IF NOT EXISTS realm_messages (
  id UUID PRIMARY KEY,

  type message_type NOT NULL,
  realm_channel_id UUID REFERENCES realm_channels (id) ON DELETE CASCADE NOT NULL,
  author_id UUID REFERENCES identities (id) NOT NULL,
  content JSONB NOT NULL
);
