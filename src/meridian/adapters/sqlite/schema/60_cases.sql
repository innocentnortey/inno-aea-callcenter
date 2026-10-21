-- AEA-10: case store (cases.md 1.1). Safe to re-apply on every boot.
CREATE TABLE IF NOT EXISTS cases (
  case_ref TEXT PRIMARY KEY CHECK (case_ref GLOB 'MHC-C-[0-9][0-9][0-9][0-9]'),
  thread_id TEXT NOT NULL,
  turn_id TEXT,
  customer_id TEXT,
  reason TEXT NOT NULL,
  priority TEXT NOT NULL CHECK (priority IN ('P0','P1','P2','P3','P4')),
  rule_id TEXT NOT NULL,
  handoff_trigger TEXT NOT NULL,
  lifecycle TEXT NOT NULL CHECK (lifecycle IN ('live_queued','unassigned','claimed','in_progress','waiting','resolved','closed_unresolved')),
  owner_role TEXT CHECK (owner_role IN ('representative','supervisor','owner')),
  owner_since TEXT,
  due_at TEXT,
  wake_up_at TEXT,
  version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
  seed INTEGER NOT NULL DEFAULT 0 CHECK (seed IN (0,1)),
  safety_kind TEXT,
  change_request_json TEXT,
  alert TEXT CHECK (alert IN ('supervisor_now')),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  resolved_at TEXT,
  queued_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_cases_thread ON cases (thread_id, created_at);
CREATE INDEX IF NOT EXISTS ix_cases_lifecycle ON cases (lifecycle);
CREATE INDEX IF NOT EXISTS ix_cases_customer ON cases (customer_id);
CREATE TABLE IF NOT EXISTS case_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  case_ref TEXT NOT NULL REFERENCES cases(case_ref),
  kind TEXT NOT NULL,
  event_key TEXT NOT NULL DEFAULT '',
  actor_role TEXT NOT NULL CHECK (actor_role IN ('representative','supervisor','owner','ai','system')),
  job_run_id TEXT,
  detail_json TEXT NOT NULL DEFAULT '{}',
  at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_case_events_case ON case_events (case_ref, id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_case_events_key ON case_events (case_ref, kind, event_key) WHERE event_key <> '';
CREATE TABLE IF NOT EXISTS promises (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  case_ref TEXT NOT NULL REFERENCES cases(case_ref),
  policy_row TEXT NOT NULL,
  text TEXT NOT NULL,
  due_at TEXT,
  due_label TEXT,
  extra_lines TEXT NOT NULL DEFAULT '[]',
  live_queued INTEGER NOT NULL DEFAULT 0 CHECK (live_queued IN (0,1)),
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','kept','missed','changed')),
  created_at TEXT NOT NULL,
  status_at TEXT,
  status_reason TEXT
);
CREATE INDEX IF NOT EXISTS ix_promises_case ON promises (case_ref, id);
CREATE TABLE IF NOT EXISTS followups (
  case_ref TEXT PRIMARY KEY REFERENCES cases(case_ref),
  thread_id TEXT NOT NULL,
  channel TEXT NOT NULL CHECK (channel IN ('email','phone')),
  destination_label TEXT NOT NULL,
  destination TEXT,
  on_record INTEGER NOT NULL CHECK (on_record IN (0,1)),
  contact_window TEXT NOT NULL CHECK (contact_window IN ('morning','afternoon','any')),
  saved_line TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS activities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  case_ref TEXT NOT NULL REFERENCES cases(case_ref),
  kind TEXT NOT NULL CHECK (kind IN ('call','email')),
  outcome TEXT NOT NULL CHECK (outcome IN ('reached','no_answer','left_message')),
  note TEXT,
  actor_role TEXT NOT NULL CHECK (actor_role IN ('representative','supervisor','owner')),
  at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_activities_case ON activities (case_ref, at, id);
CREATE TABLE IF NOT EXISTS case_briefs (
  case_ref TEXT PRIMARY KEY REFERENCES cases(case_ref),
  thread_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('ready','being_written','failed')),
  brief_json TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS demo_state (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  demo_now TEXT NOT NULL,
  staffing TEXT NOT NULL CHECK (staffing IN ('nobody_online','simulated_on_shift'))
);
CREATE TABLE IF NOT EXISTS demo_events (
  demo_event_id TEXT PRIMARY KEY,
  at_wall TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('clock_advanced','staffing_changed')),
  step TEXT NULL, mode TEXT NULL,
  demo_before TEXT NOT NULL, demo_after TEXT NOT NULL,
  became_overdue INTEGER NULL, converted_cases INTEGER NULL,
  request_id TEXT NOT NULL, role TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS job_runs (
  job_run_id TEXT PRIMARY KEY,
  started_wall_at TEXT NOT NULL,
  finished_wall_at TEXT,
  demo_now TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('started','completed','failed')),
  error_kind TEXT,
  counts_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS ix_job_runs_started ON job_runs (started_wall_at);
CREATE TABLE IF NOT EXISTS reset_events (
  reset_id TEXT PRIMARY KEY,
  at_wall TEXT NOT NULL,
  asked_by_role TEXT NULL CHECK (asked_by_role IN ('customer','representative','supervisor','owner')),
  asked_by_session TEXT NULL,
  request_id TEXT,
  restored_json TEXT NOT NULL DEFAULT '{}',
  open_chats_ended INTEGER NOT NULL DEFAULT 0,
  roles_reset INTEGER NOT NULL DEFAULT 0,
  checkpoints_cleared INTEGER CHECK (checkpoints_cleared IN (0,1))
);
CREATE TABLE IF NOT EXISTS seed_events (
  seed_event_id TEXT PRIMARY KEY,
  at_wall TEXT NOT NULL,
  reset_id TEXT NULL,
  deploy_id TEXT NULL,
  seed_count INTEGER NOT NULL,
  label TEXT NOT NULL DEFAULT 'demo seed'
);
