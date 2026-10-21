-- AEA-10: ops and eval records (cases.md 1.1 and 8; data.md section 6). Repository bodies: AEA-32 and later.
CREATE TABLE IF NOT EXISTS health_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  at_wall TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('check_ok','check_failed','restart','alert_fired','alert_cleared')),
  alert_type TEXT NULL, reason_code TEXT NULL, value REAL NULL, threshold REAL NULL,
  agent_version TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_health_events_at ON health_events (at_wall);
CREATE TABLE IF NOT EXISTS deploy_records (
  deploy_id TEXT PRIMARY KEY,
  at_wall TEXT NOT NULL,
  agent_version TEXT NOT NULL,
  git_commit TEXT,
  image_digest TEXT,
  config_hash TEXT,
  trace_export_on INTEGER CHECK (trace_export_on IN (0,1)),
  status TEXT NOT NULL DEFAULT 'completed' CHECK (status IN ('started','completed','failed','incomplete'))
);
CREATE TABLE IF NOT EXISTS eval_runs (
  run_id TEXT PRIMARY KEY,
  suite TEXT NOT NULL CHECK (suite IN ('worked-pairs','retrieval','e2e','load')),
  split TEXT CHECK (split IN ('dev','held-out')),
  agent_version TEXT NOT NULL,
  harness_commit TEXT NOT NULL, harness_digest TEXT NOT NULL,
  experiment_id TEXT,
  repeats INTEGER NOT NULL,
  started_at TEXT NOT NULL, finished_at TEXT,
  status TEXT NOT NULL CHECK (status IN ('started','completed','failed','incomplete')),
  cases_expected INTEGER NOT NULL, cases_scored INTEGER NOT NULL,
  index_manifest_hash TEXT,
  judge_spend_usd REAL NOT NULL DEFAULT 0,
  summary_json TEXT NOT NULL DEFAULT '{}',
  loaded_at TEXT
);
CREATE TABLE IF NOT EXISTS eval_case_results (
  run_id TEXT NOT NULL, case_id TEXT NOT NULL, repeat INTEGER NOT NULL,
  thread_id TEXT,
  passed_hard INTEGER NOT NULL CHECK (passed_hard IN (0,1)),
  items TEXT NOT NULL DEFAULT '[]',
  outcome TEXT NOT NULL CHECK (outcome IN ('resolved','handed_off','degraded','environment_error')),
  in_scope INTEGER, topic TEXT,
  top3 TEXT NOT NULL DEFAULT '[]',
  below_floor INTEGER,
  PRIMARY KEY (run_id, case_id, repeat)
);
