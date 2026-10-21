-- AEA-10: spend ledger, exactly stage7/models.md section 6 (repository body: AEA-26).
CREATE TABLE IF NOT EXISTS spend_ledger (
  id INTEGER PRIMARY KEY,
  recorded_at TEXT NOT NULL,
  thread_id TEXT, turn_id TEXT, request_id TEXT,
  run_tag TEXT CHECK (run_tag IN ('live','eval','load')), run_id TEXT, agent_version TEXT,
  role TEXT, provider TEXT, model TEXT, attempt INTEGER, latency_ms INTEGER,
  input_tokens INTEGER, output_tokens INTEGER, cache_read_tokens INTEGER, cache_write_tokens INTEGER, thinking_tokens INTEGER,
  cost_usd REAL, cost_source TEXT, status TEXT, failure_kind TEXT, http_status INTEGER,
  provider_request_id TEXT, stop_reason TEXT
);
CREATE INDEX IF NOT EXISTS ix_spend_recorded_at ON spend_ledger (recorded_at);
CREATE INDEX IF NOT EXISTS ix_spend_turn ON spend_ledger (turn_id);
CREATE INDEX IF NOT EXISTS ix_spend_thread ON spend_ledger (thread_id);
