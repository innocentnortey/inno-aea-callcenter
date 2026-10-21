-- AEA-10: core conversation tables (cases.md 1.1; graph-core 2; graph-nodes 1). Safe to re-apply on every boot.
CREATE TABLE IF NOT EXISTS conversations (
  thread_id TEXT PRIMARY KEY,
  demo_session TEXT NOT NULL,
  run_tag TEXT NOT NULL CHECK (run_tag IN ('live','eval','load','seed')),
  run_id TEXT,
  agent_version TEXT NOT NULL,
  started_at TEXT NOT NULL,
  started_wall_at TEXT,
  staffing_at_start TEXT CHECK (staffing_at_start IN ('nobody_online','simulated_on_shift')),
  outcome TEXT NOT NULL DEFAULT 'open' CHECK (outcome IN ('ai_resolved','handed_off','safety_reply','abandoned','open')),
  ended_wall_at TEXT,
  last_customer_wall_at TEXT,
  controller TEXT NOT NULL DEFAULT 'ai' CHECK (controller IN ('ai','human')),
  controller_name TEXT,
  controller_case_ref TEXT,
  live_state TEXT NOT NULL DEFAULT 'not_live' CHECK (live_state IN ('not_live','queued','joined','handed_back','closed')),
  live_since TEXT
);
CREATE INDEX IF NOT EXISTS ix_conversations_idle ON conversations (run_tag, outcome, last_customer_wall_at);
CREATE TABLE IF NOT EXISTS ended_threads (
  thread_id TEXT PRIMARY KEY,
  demo_session TEXT NOT NULL,
  ended_wall_at TEXT NOT NULL,
  reason TEXT NOT NULL,
  reset_id TEXT
);
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  thread_id TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('customer','assistant','representative')),
  text TEXT NOT NULL,
  at TEXT NOT NULL,
  turn_id TEXT,
  kind TEXT CHECK (kind IN ('text','choice','code','form')),
  card_id TEXT,
  choice_option TEXT
);
CREATE INDEX IF NOT EXISTS ix_messages_thread ON messages (thread_id, id);
CREATE TABLE IF NOT EXISTS turns (
  turn_id TEXT PRIMARY KEY,
  thread_id TEXT NOT NULL,
  request_id TEXT NOT NULL,
  run_tag TEXT NOT NULL CHECK (run_tag IN ('live','eval','load')),
  run_id TEXT,
  agent_version TEXT NOT NULL,
  sequence INTEGER NOT NULL,
  received_at TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('running','completed','failed')),
  gate_result TEXT CHECK (gate_result IN ('clear','safety','burning_unclear','danger','person_requested','ai_paused')),
  path TEXT,
  outcome TEXT CHECK (outcome IN ('answered','acted','safety_reply','handed_off','to_staff','degraded_handoff')),
  degrade_reason TEXT CHECK (degrade_reason IN ('model_error','tool_error','timeout','brake','spend_cap','rate_limit')),
  planner_model TEXT,
  planner_fallback_used INTEGER,
  planner_failure TEXT,
  plan_mode TEXT,
  plan_source TEXT,
  plan_intents TEXT,
  plan_handoff_request TEXT,
  plan_topic TEXT,
  planner_failed INTEGER,
  danger_raised INTEGER,
  specialists_run TEXT NOT NULL DEFAULT '[]',
  replied_at TEXT,
  server_ms INTEGER,
  model_calls INTEGER,
  input_tokens INTEGER,
  output_tokens INTEGER,
  cost_usd REAL,
  tool_calls INTEGER,
  trace_id TEXT,
  trace_export TEXT CHECK (trace_export IN ('off','sent','failed')),
  response TEXT
);
CREATE INDEX IF NOT EXISTS ix_turns_thread ON turns (thread_id, sequence);
CREATE INDEX IF NOT EXISTS ix_turns_status ON turns (status);
CREATE TABLE IF NOT EXISTS actions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  thread_id TEXT NOT NULL,
  turn_id TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('booked','moved','cancelled','change_request_sent','case_opened','followup_saved','verified')),
  record_id TEXT NOT NULL,
  records_json TEXT NOT NULL,
  before_json TEXT,
  after_json TEXT,
  at TEXT NOT NULL,
  UNIQUE (thread_id, turn_id, kind, record_id)
);
CREATE INDEX IF NOT EXISTS ix_actions_thread ON actions (thread_id, id);
CREATE TABLE IF NOT EXISTS lookup_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  thread_id TEXT NOT NULL,
  turn_id TEXT NOT NULL,
  message_id INTEGER NOT NULL REFERENCES messages(id),
  tool TEXT NOT NULL,
  record_ids TEXT NOT NULL,
  passage_ids TEXT NOT NULL,
  result_seen TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_lookup_thread ON lookup_log (thread_id, id);
CREATE TABLE IF NOT EXISTS check_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  thread_id TEXT NOT NULL,
  at TEXT,
  check_kind TEXT NOT NULL CHECK (check_kind IN ('completion','fact','brief_fact','brief_quote','gate','classifier','brake')),
  turn_id TEXT NOT NULL,
  result TEXT NOT NULL CHECK (result IN ('pass','trimmed','fallback','fired','raised')),
  removed INTEGER NOT NULL DEFAULT 0,
  claim_kinds TEXT NOT NULL DEFAULT '[]',
  codes TEXT NOT NULL DEFAULT '[]'
);
CREATE INDEX IF NOT EXISTS ix_check_events_thread ON check_events (thread_id, id);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  stream TEXT NOT NULL,
  type TEXT NOT NULL,
  payload TEXT NOT NULL,
  at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_events_stream ON events (stream, id);
CREATE INDEX IF NOT EXISTS ix_events_stream_type ON events (stream, type, id);
