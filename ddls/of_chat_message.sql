CREATE TABLE of_chat_message (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  creator_id uuid REFERENCES creator(id),
  fan_id uuid REFERENCES fan(id),
  sender text NOT NULL CHECK (sender IN ('creator', 'fan')),
  content text NOT NULL,
  created_at timestamptz DEFAULT now(),
  metadata jsonb DEFAULT '{}'
);
