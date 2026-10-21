-- AEA-10: identity tables, exactly stage7/graph-tools.md section 5 (repository body: AEA-27).
CREATE TABLE IF NOT EXISTS identity_threads (
  thread_id TEXT PRIMARY KEY,
  status TEXT NOT NULL CHECK (status IN ('not_checked','located','code_sent','verified','not_verified','locked')),
  customer_id TEXT NULL, masked_hint TEXT NULL,
  channel TEXT NULL CHECK (channel IN ('phone','email')),
  verified_at TEXT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS identity_codes (
  id INTEGER PRIMARY KEY AUTOINCREMENT, thread_id TEXT NOT NULL, customer_id TEXT NOT NULL,
  code_hmac TEXT NOT NULL, held_by TEXT NOT NULL, sent_at TEXT NOT NULL, expires_at TEXT NOT NULL,
  tries_left INTEGER NOT NULL CHECK (tries_left BETWEEN 0 AND 3), used_at TEXT NULL, inbox_message_id INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_identity_codes_thread ON identity_codes (thread_id, id);
CREATE TABLE IF NOT EXISTS demo_inbox (
  id INTEGER PRIMARY KEY AUTOINCREMENT, demo_session TEXT NOT NULL, thread_id TEXT NOT NULL,
  to_masked TEXT NOT NULL, sent_at TEXT NOT NULL, expires_at TEXT NOT NULL
);
